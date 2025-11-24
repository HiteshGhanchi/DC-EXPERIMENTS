import socket
import threading
import json
import time
import argparse
import sys
import os

# Global State
NODE_ID = -1
NODE_ADDRESS = ('', -1)
NODES = {} # {pid: (host, port)}
COORDINATOR_ID = -1
IS_ALIVE = True

# --- Utility Functions ---

def log(message):
    print(f"[{NODE_ID}] {message}")

def load_nodes():
    """Loads node configurations from nodes.json."""
    global NODES, NODE_ADDRESS
    try:
        with open('nodes.json', 'r') as f:
            config = json.load(f)
        
        for node in config:
            NODES[node['pid']] = (node['host'], node['port'])
        
        # Set this node's address based on its PID
        NODE_ADDRESS = NODES[NODE_ID]

    except FileNotFoundError:
        log("Error: nodes.json not found.")
        sys.exit(1)
    except Exception as e:
        log(f"Error loading config: {e}")
        sys.exit(1)

def send_message(target_pid, message_type, data=None):
    """Sends a message to a specific PID."""
    if target_pid not in NODES:
        return False
        
    target_host, target_port = NODES[target_pid]
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5) # Short timeout for quick failure detection
        sock.connect((target_host, target_port))
        
        payload = {'type': message_type, 'sender_id': NODE_ID, 'data': data or {}}
        sock.sendall(json.dumps(payload).encode())
        sock.close()
        return True
    except (socket.timeout, ConnectionRefusedError):
        # This is expected during failure detection/elections
        return False
    except Exception as e:
        log(f"Error sending message to {target_pid}: {e}")
        return False

# --- Election Logic ---

def start_election():
    """Initiates an election by sending messages to all higher PIDs."""
    global COORDINATOR_ID
    
    log("Initiating election...")
    has_responded = False
    
    # 1. Send ELECTION message to all processes with higher PIDs
    for pid in sorted(NODES.keys()):
        if pid > NODE_ID:
            # We don't wait for a response here; we rely on the listener to handle OKs
            if send_message(pid, 'ELECTION'):
                # We sent the message, now we wait for an OK reply
                has_responded = True
                log(f"Sent ELECTION to {pid}.")
    
    # Wait briefly for higher nodes to process the ELECTION request
    time.sleep(1) 

    # 2. Check if any higher process replied with OK
    # (The actual OK response logic is in the listener)
    
    # This simplified logic assumes if we didn't receive an OK immediately, we win.
    # In a real system, we'd wait longer. Here, we check the global state.
    
    # A cleaner approach for this minimal test is to rely on the listener setting a flag
    # For now, we rely on the rule: if we sent election and received no OK, we win.
    
    # Since we can't easily check for a received OK without complex state, we wait,
    # and if the election is not taken over by a higher process, we assume we win.

    if not has_responded:
        # 3. If no higher process responded, declare self as coordinator
        declare_coordinator()
    else:
        log("Sent ELECTION messages. Waiting for COORDINATOR announcement.")


def declare_coordinator():
    """Broadcasts the COORDINATOR message."""
    global COORDINATOR_ID
    COORDINATOR_ID = NODE_ID
    
    log("I am the new COORDINATOR")
    
    # Broadcast COORDINATOR message to all other nodes
    for pid in NODES.keys():
        if pid != NODE_ID:
            send_message(pid, 'COORDINATOR', {'coordinator_id': NODE_ID})


# --- Heartbeat/Failure Detection ---

def check_coordinator():
    """Periodically pings the current coordinator to detect failure."""
    global COORDINATOR_ID
    
    # If we are the coordinator, skip the check
    if COORDINATOR_ID == NODE_ID:
        return
        
    # If coordinator is unknown, start an election
    if COORDINATOR_ID == -1:
        log("No coordinator known. Starting election.")
        start_election()
        return

    # Ping the current coordinator
    if not send_message(COORDINATOR_ID, 'HEARTBEAT_PING'):
        # Coordinator failed!
        log(f"Coordinator {COORDINATOR_ID} not responding -> starting election")
        COORDINATOR_ID = -1 # Reset the coordinator state
        start_election()


def heartbeat_loop():
    """Main loop for periodic coordinator checks."""
    while IS_ALIVE:
        try:
            check_coordinator()
            time.sleep(5) # Check every 5 seconds
        except Exception as e:
            log(f"Heartbeat error: {e}")
            time.sleep(5)


# --- Message Handling ---

def handle_message(message_type, sender_id, data):
    """Handles incoming messages based on type."""
    global COORDINATOR_ID
    
    if message_type == 'ELECTION':
        # 1. Received ELECTION message: reply with OK and start own election
        if NODE_ID > sender_id:
            # We have a higher ID, so we take over the election
            log(f"Received ELECTION from {sender_id}. Replying with OK.")
            send_message(sender_id, 'OK')
            # Immediately start our own election to assert dominance
            start_election()
        else:
            # Sender has a higher ID (shouldn't happen if they follow the rule), 
            # or IDs are equal (error). Ignore.
            pass
            
    elif message_type == 'OK':
        # 2. Received OK message: wait for the COORDINATOR announcement
        log(f"Received OK from higher process {sender_id}. Waiting for COORDINATOR announcement...")
        # We stop our own election process and wait for the winner (the sender or someone higher) to announce.
        # This is usually handled by stopping a timeout, but here we just wait.
        
    elif message_type == 'COORDINATOR':
        # 3. Received COORDINATOR announcement: record the new leader
        new_leader_id = data.get('coordinator_id')
        COORDINATOR_ID = new_leader_id
        log(f"Received COORDINATOR message: new coordinator = {COORDINATOR_ID}")
        
    elif message_type == 'HEARTBEAT_PING':
        # 4. Received PING: reply with ACK to confirm alive state
        send_message(sender_id, 'HEARTBEAT_ACK')
        
    elif message_type == 'HEARTBEAT_ACK':
        # 5. Received ACK: coordinator is alive (used by the check_coordinator logic)
        pass


# --- Network Listener ---

def network_listener():
    """Listens for incoming TCP messages."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(NODE_ADDRESS)
        server_socket.listen(5)
        log(f"Listening on {NODE_ADDRESS[0]}:{NODE_ADDRESS[1]}")

        while IS_ALIVE:
            conn, addr = server_socket.accept()
            data = conn.recv(1024).decode()
            conn.close()
            
            if data:
                payload = json.loads(data)
                handle_message(payload['type'], payload['sender_id'], payload['data'])

    except KeyboardInterrupt:
        pass
    except Exception as e:
        log(f"Listener error: {e}")
        
    finally:
        server_socket.close()


def run_node():
    """Main execution function."""
    global NODE_ID, IS_ALIVE
    
    parser = argparse.ArgumentParser(description="Bully Algorithm Node.")
    parser.add_argument("--pid", type=int, required=True, help="Unique process ID (PID).")
    args = parser.parse_args()
    
    NODE_ID = args.pid
    
    load_nodes()
    
    log("Starting initial election")
    
    # Start the network listener thread
    listener_thread = threading.Thread(target=network_listener)
    listener_thread.daemon = True
    listener_thread.start()
    
    # Start the heartbeat loop for failure detection
    heartbeat_thread = threading.Thread(target=heartbeat_loop)
    heartbeat_thread.daemon = True
    heartbeat_thread.start()
    
    # Allow listener to start, then initiate the first election
    time.sleep(1)
    start_election()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        IS_ALIVE = False
        log("Node shutting down.")
        sys.exit(0)

if __name__ == '__main__':
    # This implementation will not work if the user does not create nodes.json
    run_node()

# python node.py --pid 1
# python node.py --pid 2
# python node.py --pid 3
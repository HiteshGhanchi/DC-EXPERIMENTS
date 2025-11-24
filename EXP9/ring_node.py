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
NEXT_NODE_PID = -1
COORDINATOR_ID = -1
IS_ALIVE = True

# --- Configuration & Utility ---

def log(message):
    print(f"[{NODE_ID}] {message}")

def load_nodes():
    """Loads node configurations and determines the next node in the ring."""
    global NODES, NODE_ADDRESS, NEXT_NODE_PID
    try:
        with open('nodes.json', 'r') as f:
            config = json.load(f)
        
        # Sort nodes by PID to establish the ring order (P1 -> P2 -> P3 -> P1)
        sorted_nodes = sorted(config, key=lambda x: x['pid'])
        
        for node in sorted_nodes:
            NODES[node['pid']] = (node['host'], node['port'])
        
        # Set this node's address
        NODE_ADDRESS = NODES[NODE_ID]

        # Determine the next node in the logical ring
        pids = list(NODES.keys())
        my_index = pids.index(NODE_ID)
        next_index = (my_index + 1) % len(pids)
        NEXT_NODE_PID = pids[next_index]

    except FileNotFoundError:
        log("Error: nodes.json not found.")
        sys.exit(1)
    except Exception as e:
        log(f"Error loading config: {e}")
        sys.exit(1)

def send_message(target_pid, message_type, data=None):
    """Sends a message to a specific PID (non-blocking, short timeout)."""
    if target_pid not in NODES:
        return False
        
    target_host, target_port = NODES[target_pid]
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5) 
        sock.connect((target_host, target_port))
        
        payload = {'type': message_type, 'sender_id': NODE_ID, 'data': data or {}}
        sock.sendall(json.dumps(payload).encode())
        sock.close()
        return True
    except (socket.timeout, ConnectionRefusedError):
        # Failure detected
        return False
    except Exception as e:
        log(f"Error sending message to {target_pid}: {e}")
        return False

# --- Ring Election Logic ---

def initiate_election():
    """Starts the election by sending its PID to the next node."""
    log("Initiating election...")
    
    # The data payload is a list of PIDs participating in the election
    initial_data = {'participants': [NODE_ID], 'origin_id': NODE_ID}
    
    # Send the ELECTION message to the next node in the ring
    send_message(NEXT_NODE_PID, 'ELECTION', initial_data)


def handle_election_message(data):
    """Handles an ELECTION message received from a neighbor."""
    participants = data.get('participants', [])
    origin_id = data.get('origin_id')
    
    # 1. Check if the message is returning to the originator
    if origin_id == NODE_ID:
        # The message completed the ring!
        log(f"Election message returned to origin. participants={participants}")
        
        # 2. Determine the winner (highest PID)
        new_coordinator = max(participants)
        
        # 3. Broadcast the result
        declare_coordinator(new_coordinator, participants)
        
    else:
        # 4. Message is still circulating: append our ID and forward
        if NODE_ID not in participants:
            participants.append(NODE_ID)
        
        # Forward the message to the next node
        forward_data = {'participants': participants, 'origin_id': origin_id}
        send_message(NEXT_NODE_PID, 'ELECTION', forward_data)


def declare_coordinator(new_coordinator, participants):
    """Broadcasts the COORDINATOR message around the ring."""
    global COORDINATOR_ID
    COORDINATOR_ID = new_coordinator
    
    log(f"ELECTION result -> coordinator = {COORDINATOR_ID}")
    
    # Send the COORDINATOR message around the ring
    coord_data = {'coordinator_id': new_coordinator, 'participants': participants}
    send_message(NEXT_NODE_PID, 'COORDINATOR', coord_data)


# --- Failure Detection (Simplified Heartbeat) ---

def check_coordinator():
    """Periodically pings the current coordinator to detect failure."""
    global COORDINATOR_ID
    
    if COORDINATOR_ID == -1:
        # No coordinator known, start election
        log("No coordinator known. Starting initial election.")
        initiate_election()
        return
        
    if COORDINATOR_ID == NODE_ID:
        # We are the coordinator, skip check
        return

    # Ping the current coordinator
    if not send_message(COORDINATOR_ID, 'HEARTBEAT_PING'):
        # Coordinator failed!
        log(f"Coordinator {COORDINATOR_ID} not responding -> starting election")
        COORDINATOR_ID = -1 
        initiate_election()


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
        handle_election_message(data)
            
    elif message_type == 'COORDINATOR':
        # Received COORDINATOR announcement: record the new leader and forward announcement
        new_leader_id = data.get('coordinator_id')
        COORDINATOR_ID = new_leader_id
        
        log(f"Received COORDINATOR announcement: {COORDINATOR_ID}")
        
        # Forward the announcement to the next node
        if sender_id != NEXT_NODE_PID: # Avoid infinite loop
            send_message(NEXT_NODE_PID, 'COORDINATOR', data)
        
    elif message_type == 'HEARTBEAT_PING':
        # Received PING: reply with ACK to confirm alive state
        send_message(sender_id, 'HEARTBEAT_ACK')
        
    elif message_type == 'HEARTBEAT_ACK':
        # Received ACK: coordinator is alive (used by the check_coordinator logic)
        pass


# --- Network Listener ---

def network_listener():
    """Listens for incoming TCP messages."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(NODE_ADDRESS)
        log(f"Listening on {NODE_ADDRESS[0]}:{NODE_ADDRESS[1]} | next -> {NEXT_NODE_PID} @ {NODES[NEXT_NODE_PID][0]}:{NODES[NEXT_NODE_PID][1]}")
        server_socket.listen(5)

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
    
    parser = argparse.ArgumentParser(description="Ring Election Algorithm Node.")
    parser.add_argument("--pid", type=int, required=True, help="Unique process ID (PID).")
    args = parser.parse_args()
    
    NODE_ID = args.pid
    
    load_nodes()
    
    log("Starting node and listening...")
    
    # Start the network listener thread
    listener_thread = threading.Thread(target=network_listener)
    listener_thread.daemon = True
    listener_thread.start()
    
    # Start the heartbeat loop for failure detection
    heartbeat_thread = threading.Thread(target=heartbeat_loop)
    heartbeat_thread.daemon = True
    heartbeat_thread.start()
    
    # Allow listener to start, then initiate the first election (handled by heartbeat loop)
    time.sleep(2)
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        IS_ALIVE = False
        log("Node shutting down.")
        sys.exit(0)

if __name__ == '__main__':
    run_node()



# # Terminal 1 (P1)
# python ring_node.py --pid 1

# # Terminal 2 (P2)
# python ring_node.py --pid 2

# # Terminal 3 (P3)
# python ring_node.py --pid 3
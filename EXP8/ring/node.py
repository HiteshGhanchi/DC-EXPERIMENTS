import socket
import time
import sys
import threading
import argparse
import random # Import random for simulating continuous requests

# --- GLOBAL STATE VARIABLES (Non-OOP Approach) ---
BASE_PORT = 5000
CS_TIME = 3 # Time spent in Critical Section
PASS_THROUGH_TIME = 0.5 # Small delay when passing token without entering CS

# Node State variables (initialized by parse_args and run_node_logic)
NODE_ID = -1
N_NODES = -1
MY_PORT = -1
NEXT_PORT = -1
TOKEN_HELD = False
REQUEST_CS = False
# -----------------------------------------------

def log(message):
    """Logs messages prefixed with the Node ID and Port."""
    print(f"[P{NODE_ID} @ {MY_PORT}] {message}")

def enter_critical_section():
    """Simulates accessing the shared resource."""
    log(">>> ENTERING CRITICAL SECTION <<<")
    # Simulate work by sleeping
    time.sleep(CS_TIME) 
    log(f"<<< EXITING CRITICAL SECTION (Spent {CS_TIME}s) >>>")

def send_token():
    """Passes the token to the next node in the ring."""
    try:
        # Add a small, simulated network/processing delay before sending
        time.sleep(PASS_THROUGH_TIME) 
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', NEXT_PORT))
        
        token_message = "TOKEN"
        sock.sendall(token_message.encode())
        sock.close()
        log(f"Token passed to P{(NODE_ID + 1) % N_NODES} ({NEXT_PORT})")
        
    except ConnectionRefusedError:
        log(f"ERROR: Cannot connect to P{(NODE_ID + 1) % N_NODES} at {NEXT_PORT}. Ring is BROKEN.")
    except Exception as e:
        log(f"ERROR during token send: {e}")

def handle_token(token_message):
    """Called when the token is received. Mutates global state."""
    global TOKEN_HELD, REQUEST_CS
    
    TOKEN_HELD = True
    
    if REQUEST_CS:
        log("Token received and CS requested.")
        enter_critical_section()
        
        # Reset state and pass token
        REQUEST_CS = False 
        TOKEN_HELD = False 
        send_token()
        
        # --- NEW LOGIC: REREQUEST CS after a random delay ---
        # This forces continuous competition and makes the simulation realistic.
        threading.Thread(target=set_new_request).start()
        
    else:
        log("Token received, no CS requested. Passing immediately.")
        TOKEN_HELD = False
        send_token()

def set_new_request():
    """Simulates a node wanting to enter the CS again after a delay."""
    global REQUEST_CS
    # Wait a random time (1 to 5 seconds) before requesting CS again
    delay = random.uniform(1, 5) 
    log(f"Will request CS again in {delay:.2f}s...")
    time.sleep(delay)
    
    REQUEST_CS = True 
    log("CS request raised again.")


def listen_for_token():
    """The main loop for receiving the token."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', MY_PORT))
    server_socket.listen(1)
    log("Listening for token...")

    while True:
        try:
            conn, addr = server_socket.accept()
            token_message = conn.recv(1024).decode()
            conn.close()
            if token_message == "TOKEN":
                handle_token(token_message)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"Error in listener: {e}")
            break

def run_node_logic(args):
    """Initializes global state and starts the listener."""
    global NODE_ID, N_NODES, MY_PORT, NEXT_PORT, TOKEN_HELD, REQUEST_CS
    
    # 1. Initialize Global State from Arguments
    NODE_ID = args.id
    N_NODES = args.n
    MY_PORT = args.base_port + NODE_ID
    NEXT_PORT = args.base_port + (NODE_ID + 1) % N_NODES
    TOKEN_HELD = args.initial_holder
    
    log(f"Initialized. Port: {MY_PORT}, Next: {NEXT_PORT}")
    
    # 2. Start the listener thread
    listener_thread = threading.Thread(target=listen_for_token)
    listener_thread.daemon = True
    listener_thread.start()

    # 3. Simulate CS Request logic (Main Thread)
    # Initial request logic is now in a separate thread/call
    if not TOKEN_HELD:
        # All non-holders start by requesting CS after a brief delay
        time.sleep(2) 
        set_new_request() 
    
    # 4. If initial holder, start the circulation
    if TOKEN_HELD:
        time.sleep(1)
        log("Initial token holder, starting token circulation.")
        handle_token("TOKEN") # Immediately enter CS and pass

    # Keep the main thread alive to prevent daemon threads from exiting
    try:
        while listener_thread.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass


def parse_args():
    parser = argparse.ArgumentParser(description="Token Ring Node Simulation (Non-OOP).")
    parser.add_argument("--id", type=int, required=True, help="Unique node ID (0 to N-1).")
    parser.add_argument("--n", type=int, required=True, help="Total number of nodes in the ring.")
    parser.add_argument("--base-port", type=int, default=5000, help="Base port number.")
    parser.add_argument("--initial-holder", action="store_true", help="If set, this node starts with the token.")
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    if args.id < 0 or args.id >= args.n:
        print("Error: Node ID must be between 0 and N-1.")
        sys.exit(1)
    
    run_node_logic(args)
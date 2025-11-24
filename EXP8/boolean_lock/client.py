import socket
import threading
import json
import time
import argparse
import random
import sys

# Configuration
COORDINATOR_HOST = '127.0.0.1'
COORDINATOR_PORT = 5050
CS_TIME = 4 # Time spent in Critical Section
CLIENT_LISTEN_PORT = random.randint(5100, 60000) # Unique port for listening to GRANT

def log(client_id, message):
    print(f"[Client {client_id} @ {CLIENT_LISTEN_PORT}] {message}")

def send_request(client_id, action):
    """Sends REQUEST or RELEASE message to the coordinator."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((COORDINATOR_HOST, COORDINATOR_PORT))
        
        request = {
            'action': action, 
            'id': client_id, 
            'port': CLIENT_LISTEN_PORT
        }
        sock.sendall(json.dumps(request).encode())
        sock.close()
        
    except ConnectionRefusedError:
        log(client_id, f"ERROR: Coordinator not running at {COORDINATOR_HOST}:{COORDINATOR_PORT}")
        sys.exit(1)
    except Exception as e:
        log(client_id, f"ERROR sending {action} message: {e}")

def critical_section(client_id):
    """Simulates the critical section."""
    log(client_id, ">>> ENTERING CRITICAL SECTION (Acquired Lock) <<<")
    time.sleep(CS_TIME)
    log(client_id, f"<<< EXITING CRITICAL SECTION (Spent {CS_TIME}s) >>>")

    # Send RELEASE after finishing
    send_request(client_id, "RELEASE")
    log(client_id, "Sent RELEASE.")

def listen_for_grant(client_id):
    """Listens on a unique port for the GRANT signal from the coordinator."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', CLIENT_LISTEN_PORT))
    server_socket.listen(1)
    log(client_id, "Listening for GRANT...")

    while True:
        try:
            conn, addr = server_socket.accept()
            grant_message = conn.recv(1024).decode()
            conn.close()
            
            if grant_message == "GRANT":
                log(client_id, "Received GRANT from Coordinator.")
                # Execute the critical section logic
                critical_section(client_id)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(client_id, f"Error in listener: {e}")
            break

def run_client(client_id):
    # Start listening for the GRANT signal in a separate thread
    listener_thread = threading.Thread(target=listen_for_grant, args=(client_id,))
    listener_thread.daemon = True
    listener_thread.start()

    # Wait briefly for the listener to start up
    time.sleep(1) 
    
    # 1. Send the initial request
    log(client_id, "Sending initial REQUEST.")
    send_request(client_id, "REQUEST")

def parse_args():
    parser = argparse.ArgumentParser(description="Centralized Mutual Exclusion Client.")
    parser.add_argument("--id", type=str, required=True, help="Unique client identifier (e.g., A, B, C).")
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    run_client(args.id)
    # Keep the main thread alive to keep the listener thread running
    while True:
        time.sleep(1)
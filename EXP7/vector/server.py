import socket
import json
import threading
import sys
import time

# Configuration
HOST = '0.0.0.0'
PORT = 6001
NUM_PROCESSES = 2 # Total processes in the system (Server P1, Client P2)
SERVER_ID = 0     # Server is Process 0
VECTOR_CLOCK = [0] * NUM_PROCESSES # [P1, P2] -> [0, 0]

def update_vector_clock(received_vector):
    """Updates the server's vector clock based on the received vector from client (P2)."""
    global VECTOR_CLOCK
    
    # 1. Update local entry for internal event
    VECTOR_CLOCK[SERVER_ID] += 1
    
    # 2. Rule: vector[i] = max(local_vector[i], received_vector[i])
    for i in range(NUM_PROCESSES):
        VECTOR_CLOCK[i] = max(VECTOR_CLOCK[i], received_vector[i])
        
    return list(VECTOR_CLOCK) # Return a copy of the updated vector

def handle_client(conn, addr):
    """Handles messages from a client process (P2)."""
    try:
        data = conn.recv(1024).decode('utf-8')
        if not data:
            return

        message = json.loads(data)
        client_vector = message.get('vector_clock', [0, 0])
        
        # 1. Update clock based on received vector
        new_vector = update_vector_clock(client_vector)
        
        # 2. Output results
        print("-" * 50)
        print(f"[Server P{SERVER_ID}] Connection established with {addr}")
        print(f"[Server P{SERVER_ID}] Received client vector clock: {client_vector}")
        print(f"[Server P{SERVER_ID}] Updated server vector clock: {new_vector}")
        
    except json.JSONDecodeError:
        print(f"[Server P{SERVER_ID}] Received invalid JSON from {addr}")
    except Exception as e:
        print(f"[Server P{SERVER_ID}] Error handling client {addr}: {e}")
        
    finally:
        conn.close()

def start_server():
    """Starts the TCP server and handles incoming connections."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"Starting Vector Clock Server (P{SERVER_ID})...")
        print(f"Server is listening on {HOST}:{PORT}")
        print(f"Initial Vector Clock: {VECTOR_CLOCK}")
        print("-" * 50)
        
        while True:
            conn, addr = server_socket.accept()
            # Handle client connection in a new thread
            threading.Thread(target=handle_client, args=(conn, addr)).start()
            
    except KeyboardInterrupt:
        print("\n[Server] Shutting down.")
    except Exception as e:
        print(f"[Server] Fatal error: {e}")
        
    finally:
        server_socket.close()

if __name__ == '__main__':
    import threading
    start_server()
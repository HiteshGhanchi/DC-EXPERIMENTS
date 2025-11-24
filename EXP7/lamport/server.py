import socket
import time
import sys
import threading
import json

# Configuration
HOST = '0.0.0.0' # Listen on all interfaces
PORT = 6000
SERVER_CLOCK = 0 # Initial Lamport clock value

def update_lamport_clock(received_time):
    """Updates the server's Lamport clock based on the received timestamp."""
    global SERVER_CLOCK
    
    # Rule: clock = max(local_clock, received_timestamp) + 1
    SERVER_CLOCK = max(SERVER_CLOCK, received_time) + 1
    return SERVER_CLOCK

def handle_client(conn, addr):
    """Handles messages from a single client."""
    global SERVER_CLOCK
    
    try:
        # Receive the JSON message from the client
        data = conn.recv(1024).decode('utf-8')
        if not data:
            return

        message = json.loads(data)
        client_time = message.get('timestamp', 0)
        
        # 1. Update clock based on received time
        new_server_clock = update_lamport_clock(client_time)
        
        # 2. Output results
        print("-" * 50)
        print(f"[Server] Connection established with {addr}")
        print(f"[Server] Received client time: {client_time}")
        print(f"[Server] Updated server clock: {new_server_clock}")
        
    except json.JSONDecodeError:
        print(f"[Server] Received invalid JSON from {addr}")
    except Exception as e:
        print(f"[Server] Error handling client {addr}: {e}")
        
    finally:
        conn.close()

def start_server():
    """Starts the TCP server and handles incoming connections."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print("Starting Lamport Clock Server...")
        print(f"Server is listening on {HOST}:{PORT}")
        print("-" * 50)
        
        while True:
            # Server waits for incoming client connections
            conn, addr = server_socket.accept()
            # Handle each client connection in a new thread
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
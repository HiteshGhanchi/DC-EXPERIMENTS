import socket
import threading
import json
import time

# Configuration
HOST = '0.0.0.0'
PORT = 5050
CS_LOCK = False
REQUEST_QUEUE = [] # FIFO Queue for pending requests: [(client_id, client_addr)]

def log(message):
    print(f"[Coordinator] {message}")

def handle_client(conn, addr):
    """Handles incoming REQUEST or RELEASE messages."""
    global CS_LOCK, REQUEST_QUEUE
    
    try:
        data = conn.recv(1024).decode()
        if not data:
            return
            
        request = json.loads(data)
        action = request.get('action')
        client_id = request.get('id')
        client_port = request.get('port')

        if action == "REQUEST":
            log(f"Received REQUEST from Client {client_id} ({addr})")
            
            if not CS_LOCK:
                # 1. Lock is free: GRANT permission immediately
                CS_LOCK = True
                log(f"GRANTing lock to Client {client_id}")
                
                # Send GRANT signal back to client's listening port
                threading.Thread(target=send_message, args=(client_id, client_port, "GRANT")).start()
            else:
                # 2. Lock is busy: Queue the request
                REQUEST_QUEUE.append((client_id, client_port))
                log(f"Lock is busy. Client {client_id} added to queue. Queue size: {len(REQUEST_QUEUE)}")
                
        elif action == "RELEASE":
            log(f"Received RELEASE from Client {client_id}")
            CS_LOCK = False
            
            if REQUEST_QUEUE:
                # 3. Lock released & queue is non-empty: GRANT to the next client
                next_client_id, next_client_port = REQUEST_QUEUE.pop(0)
                CS_LOCK = True
                log(f"Queue not empty. GRANTing lock to next Client {next_client_id}")
                threading.Thread(target=send_message, args=(next_client_id, next_client_port, "GRANT")).start()
            else:
                log("Lock is now free and queue is empty.")

    except Exception as e:
        log(f"Error handling request from {addr}: {e}")

def send_message(client_id, client_port, message):
    """Helper function to send the GRANT message back to the client's listening port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', client_port))
        sock.sendall(message.encode())
        sock.close()
    except Exception as e:
        log(f"ERROR: Could not send {message} to Client {client_id} at {client_port}: {e}")

def start_coordinator():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    log(f"Coordinator listening on {HOST}:{PORT}")

    while True:
        try:
            conn, addr = server_socket.accept()
            # Handle client interaction in a new thread
            threading.Thread(target=handle_client, args=(conn, addr)).start()
        except KeyboardInterrupt:
            log("\nShutting down.")
            break
        finally:
            pass
            
if __name__ == '__main__':
    start_coordinator()
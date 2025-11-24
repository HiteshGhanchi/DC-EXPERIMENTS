import socket
import threading
import sys

HOST = '127.0.0.1'
PORT = 4000

def handle_client(conn, addr):
    """Function executed by the dedicated thread."""
    print(f"[Thread {threading.current_thread().name}] Connected by {addr}")
    with conn:
        while True:
            try:
                data = conn.recv(1024)
                if not data: break
                
                message = data.decode('utf-8')
                response = f"Thread {threading.current_thread().name} processed: {message.upper()}"
                conn.sendall(response.encode('utf-8'))
            except:
                break
    print(f"[Thread {threading.current_thread().name}] Disconnected.")

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
    print(f"Listening on {HOST}:{PORT}. Server is ready.")

    while True:
        try:
            # CRITICAL STEP 1: Main thread blocks, waiting for connection.
            conn, addr = server_socket.accept()
            
            # CRITICAL STEP 2: Hand off connection to a new thread.
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()
            print(f"[MAIN] Dispatched connection to {client_thread.name}. Awaiting next client...")
        except KeyboardInterrupt:
            print("\nServer Shutting Down.")
            break
        except Exception as e:
            print(f"Error: {e}")
            break
    server_socket.close()

if __name__ == '__main__':
    start_server()
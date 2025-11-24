import socket
import multiprocessing
import os

HOST = '127.0.0.1'
PORT = 4001 # New Port to avoid conflict

def handle_client(conn, addr):
    """Function executed by the dedicated child process."""
    print(f"[Process {os.getpid()}] Connected by {addr}. Handling request...")
    with conn:
        data = conn.recv(1024)
        if data:
            message = data.decode('utf-8')
            # Response includes PID to prove isolation
            response = f"Process {os.getpid()} processed: {message.upper()}"
            conn.sendall(response.encode('utf-8'))
    # IMPORTANT: Child process must exit after handling to prevent resource leaks
    sys.exit(0) 

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
    print(f"Listening on {HOST}:{PORT}. Server is ready (Multiprocess).")

    while True:
        try:
            conn, addr = server_socket.accept()
            
            # CRITICAL STEP: Create a new Process instead of a Thread
            client_process = multiprocessing.Process(target=handle_client, args=(conn, addr))
            client_process.start()
            
            # Close the connection handle in the parent process immediately
            conn.close() 
            
            print(f"[MAIN {os.getpid()}] Dispatched connection to {client_process.pid}. Awaiting next client...")
        except KeyboardInterrupt:
            print("\nServer Shutting Down.")
            break
        except Exception as e:
            print(f"Error: {e}")
            break
    server_socket.close()

if __name__ == '__main__':
    # Ensure processes are joined/cleaned up, though the OS handles much of this
    try:
        start_server()
    except:
        pass
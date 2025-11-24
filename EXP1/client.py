import socket

# --- Configuration ---
HOST = '127.0.0.1'
PORT = 4000

def send_request(client_socket, method, route, values):
    """
    Formats and sends the request to the server, then prints the reply.
    """
    # 1. Format the 3-line message
    request_message = f"{method}\n{route}\n{values}\n"
    
    print("-" * 20)
    print(f"SENDING: {method} {route} with values: '{values}'")
    
    # 2. Send the message
    client_socket.sendall(request_message.encode('utf-8'))

    # 3. Receive the response (blocks until reply is received)
    data = client_socket.recv(1024)
    server_reply = data.decode('utf-8')

    # 4. Print the response
    print("\n--- SERVER RESPONSE ---")
    print(server_reply)
    print("-----------------------\n")


def run_client_tests():
    """Connects to the server and runs a sequence of API tests."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            client_socket.connect((HOST, PORT))
            print(f"[INFO] Successfully connected to API server at {HOST}:{PORT}")

            # --- TEST 1: Simple Calculation (GET /add) ---
            send_request(client_socket, "/GET", "/add", "15.5,4.5")
            
            # --- TEST 2: Name Creation (POST /add_name) ---
            # This is a persistent connection, so the state (USER_DATABASE) is maintained.
            send_request(client_socket, "/POST", "/add_name", "Charlie Smith")

            # --- TEST 3: Name Update (PUT /update_name) ---
            # We assume Charlie got ID 3, so we update it.
            send_request(client_socket, "/PUT", "/update_name", "3,Charlie M. Smith")
            
            # --- TEST 4: Get All Names (GET /get_all_names) ---
            send_request(client_socket, "/GET", "/get_all_names", "")
            
            # --- TEST 5: Error Handling (GET /div by zero) ---
            send_request(client_socket, "/GET", "/div", "100,0")
            
        except ConnectionRefusedError:
            print(f"\n[ERROR] Connection refused. Is the server running on {HOST}:{PORT}?")
        except Exception as e:
            print(f"\n[ERROR] An error occurred: {e}")
            
    print("[INFO] Client connection closed.")

if __name__ == '__main__':
    run_client_tests()
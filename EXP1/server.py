import socket

HOST = '127.0.0.1' 
PORT = 4000

USER_DATABASE = {
    '1': 'Alice',
    '2': 'Bob',
}
next_user_id = 3

def handle_calculation(method, route, values):
    """Handles /add, /sub, /mul, /div routes."""
    try:
        num1, num2 = map(float, values.split(','))
    except ValueError:
        return 400, "ERROR: Invalid number format. Use two numbers separated by a comma (e.g., 10,5)."

    if route == '/add':
        result = num1 + num2
    elif route == '/sub':
        result = num1 - num2
    elif route == '/mul':
        result = num1 * num2
    elif route == '/div':
        if num2 == 0:
            return 400, "ERROR: Cannot divide by zero."
        result = num1 / num2
    else:
        return 404, f"ERROR: Unknown route for method {method}."
    
    return 200, f"RESULT: {result}"

def handle_name_operation(method, route, values):
    """Handles /add_name, /update_name routes."""
    global next_user_id
    
    if method == '/GET' and route == '/get_all_names':
        names_list = [f"ID {uid}: {name}" for uid, name in USER_DATABASE.items()]
        return 200, f"USER LIST:\n" + "\n".join(names_list)
    
    elif method == '/POST' and route == '/add_name':
        new_name = values.strip()
        if not new_name:
            return 400, "ERROR: Name cannot be empty."
        
        user_id = str(next_user_id)
        USER_DATABASE[user_id] = new_name
        next_user_id += 1
        return 201, f"CREATED: User '{new_name}' added with ID {user_id}"

    elif method == '/PUT' and route == '/update_name':
        try:
            # Expects format: ID, NewName
            user_id, new_name = map(str.strip, values.split(',', 1))
        except ValueError:
            return 400, "ERROR: Invalid format. Expected ID,NewName (e.g., 1,Jane Doe)."

        if user_id in USER_DATABASE:
            old_name = USER_DATABASE[user_id]
            USER_DATABASE[user_id] = new_name
            return 200, f"UPDATED: ID {user_id} changed from '{old_name}' to '{new_name}'"
        else:
            return 404, f"ERROR: User ID {user_id} not found."
    
    return 404, f"ERROR: Unknown route or unsupported method for resource management."


def process_request(request_data):
    """Parses the 3-line message and routes the request."""
    lines = request_data.split('\n', 2)
    
    if len(lines) != 3:
        return 400, "ERROR: Message format must be exactly 3 lines: [Method], [Route], [Values]."

    method = lines[0].strip().upper()
    route = lines[1].strip().lower()
    values = lines[2].strip()

    # Routing based on the API functionality
    if route in ['/add', '/sub', '/mul', '/div']:
        status, response = handle_calculation(method, route, values)
    elif route in ['/add_name', '/update_name', '/get_all_names']:
        status, response = handle_name_operation(method, route, values)
    else:
        status, response = 404, f"ERROR: API route '{route}' not found."

    # Return the formatted API response
    return f"{status} OK\n{response}"


# --- Socket Server Setup and Loop ---

def start_server():
    """Initializes and runs the main socket server loop."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"--- Custom API Server Initialized ---")
        print(f"Server is listening on {HOST}:{PORT}")
        print(f"Current User DB: {USER_DATABASE}")
        print("-------------------------------------")

        while True:
            # This is the blocking call waiting for a new client connection
            conn, addr = server_socket.accept()
            print(f"\n[INFO] New connection from: {addr}")
            
            # Inner loop for persistent communication with this client
            with conn:
                while True:
                    try:
                        # Receive up to 1024 bytes (blocks until data arrives)
                        data = conn.recv(1024)
                        if not data:
                            print(f"[INFO] Client {addr} disconnected gracefully.")
                            break # Break the inner while loop to close the connection

                        client_message = data.decode('utf-8')
                        print(f"[RECV] Raw Message:\n---\n{client_message}\n---")

                        # Process the request and generate the response
                        response_message = process_request(client_message)

                        # Send the API response back
                        conn.sendall(response_message.encode('utf-8'))
                        print(f"[SENT] Response Status: {response_message.splitlines()[0]}")
                        
                    except ConnectionResetError:
                        print(f"[INFO] Client {addr} closed connection abruptly.")
                        break
                    except Exception as e:
                        error_response = f"500 INTERNAL_ERROR\nServer processing failed: {e}"
                        conn.sendall(error_response.encode('utf-8'))
                        print(f"[ERROR] Exception during connection handling: {e}")
                        break

    except socket.error as e:
        print(f"[CRITICAL ERROR] Could not start server: {e}")
        print("Check if the IP is correct or if the port is already in use.")
    finally:
        server_socket.close()

if __name__ == '__main__':
    start_server()
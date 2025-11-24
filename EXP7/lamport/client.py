import socket
import time
import sys
import json
import random

# Configuration
# !!! CHANGE 'SERVER_IP' to the actual IP address of the Server Machine !!!
SERVER_HOST = '127.0.0.1' 
SERVER_PORT = 6000
CLIENT_CLOCK = 0 
CLIENT_ID = random.randint(10, 99) 

def update_local_clock():
    """Rule 1: Increments local clock before every event."""
    global CLIENT_CLOCK
    CLIENT_CLOCK += 1
    return CLIENT_CLOCK

def send_message(message_content):
    """Rule 2 & 3: Increments clock, sends message with timestamp."""
    global CLIENT_CLOCK
    
    # 1. Simulate local event and increment clock
    current_time = update_local_clock() 
    
    # 2. Prepare message with timestamp
    message = {
        'sender_id': CLIENT_ID,
        'timestamp': current_time,
        'content': message_content
    }
    
    print(f"[Client {CLIENT_ID}] Local clock before sending: {current_time - 1}")
    print(f"[Client {CLIENT_ID}] Sending message with timestamp: {current_time}")
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        client_socket.sendall(json.dumps(message).encode('utf-8'))
        
    except ConnectionRefusedError:
        print(f"[Client {CLIENT_ID}] ERROR: Connection refused. Server not running at {SERVER_HOST}:{SERVER_PORT}")
    except Exception as e:
        print(f"[Client {CLIENT_ID}] An error occurred: {e}")
        
    finally:
        client_socket.close()
        
def start_client():
    time.sleep(random.randint(0, 5))
    # Simulate a few local events and sends
    update_local_clock() # Initial local event 1
    update_local_clock() # Initial local event 2
    
    # Send message 1
    send_message("First Request") 
    time.sleep(0.5)
    
    update_local_clock() # Local event 3
    
    # Send message 2
    send_message("Second Request") 
    
if __name__ == '__main__':
    start_client()
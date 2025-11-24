import socket
import time
import sys
import json
import random

# Configuration
# !!! CHANGE 'SERVER_IP' to the actual IP address of the Server Machine !!!
SERVER_HOST = '127.0.0.1' 
SERVER_PORT = 6001
NUM_PROCESSES = 2
CLIENT_ID = 1     # Client is Process 1
VECTOR_CLOCK = [0] * NUM_PROCESSES 

def update_local_clock():
    """Rule 1: Increments its own entry in the vector before every local event."""
    global VECTOR_CLOCK
    VECTOR_CLOCK[CLIENT_ID] += 1
    return list(VECTOR_CLOCK)

def send_message(message_content):
    """Rule 2: Increments clock and sends message with its entire vector."""
    global VECTOR_CLOCK
    
    # 1. Simulate local event and increment clock (MUST happen before send)
    current_vector = update_local_clock() 
    
    # 2. Prepare message with vector timestamp
    message = {
        'sender_id': CLIENT_ID,
        'vector_clock': current_vector,
        'content': message_content
    }
    
    print(f"[Client P{CLIENT_ID}] Local vector clock on sending: {current_vector}")
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        client_socket.sendall(json.dumps(message).encode('utf-8'))
        
    except ConnectionRefusedError:
        print(f"[Client P{CLIENT_ID}] ERROR: Connection refused. Server not running at {SERVER_HOST}:{SERVER_PORT}")
    except Exception as e:
        print(f"[Client P{CLIENT_ID}] An error occurred: {e}")
        
    finally:
        client_socket.close()
        
def start_client():
    # Simulate a few local events before sending
    update_local_clock() 
    
    # Send message 1
    send_message("First Event from P2") 
    time.sleep(0.5)
    
    update_local_clock() # Local event 
    
    # Send message 2
    send_message("Second Event from P2") 
    
if __name__ == '__main__':
    start_client()
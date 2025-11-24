import socket
import time
import sys
import random

# --- Configuration ---
MASTER_HOST = '127.0.0.1'
MASTER_PORT = 5001
# Random port for this node to LISTEN on for the Master's adjustment command
NODE_LISTEN_PORT = random.randint(5002, 60000) 

# Simulate initial clock drift (MUST be global/mutable for adjustment)
# This node's clock is up to +/- 5 seconds off the true system time
initial_drift = random.uniform(-5.0, 5.0) 
system_time_simulated = time.time() + initial_drift 
# ---------------------

def get_current_time():
    """Simulates reading the local clock with drift."""
    # We maintain the simulated time relative to the true time.
    global system_time_simulated
    return system_time_simulated

def adjust_time(offset):
    """Adjusts the simulated clock by the received offset."""
    global system_time_simulated
    
    print(f"\n[Node {NODE_LISTEN_PORT}] Local clock before sync: {system_time_simulated:.6f}")
    
    # Apply the offset to the simulated clock
    system_time_simulated += offset
    
    print(f"[Node] Offset received: {offset:.6f}")
    print(f"[Node] Local clock after sync: {system_time_simulated:.6f}")
    
    
def start_node():
    """Initializes the node, sends time to Master, and listens for adjustment."""
    
    # 1. Inform Master of our existence and time
    try:
        # Client socket to send time to Master
        master_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        master_conn.connect((MASTER_HOST, MASTER_PORT))
        
        # Send current simulated local time AND our unique listening port
        current_time_data = f"{get_current_time()},{NODE_LISTEN_PORT}"
        master_conn.sendall(current_time_data.encode('utf-8'))
        master_conn.close()
        
        print(f"[Node {NODE_LISTEN_PORT}] Initial drift: {initial_drift:.6f}s")
        print(f"[Node] Sent time to Master. Now listening for adjustment...")
        
    except ConnectionRefusedError:
        print(f"[Node {NODE_LISTEN_PORT}] ERROR: Master server not running at {MASTER_HOST}:{MASTER_PORT}")
        return
        
    # 2. Listen for adjustment command from Master
    node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind to our unique listening port
    node_socket.bind(('0.0.0.0', NODE_LISTEN_PORT)) 
    node_socket.listen(1)
    
    # Wait for the Master to connect back
    conn, addr = node_socket.accept()
    
    # Receive the offset command from the Master
    offset_data = conn.recv(1024).decode()
    offset = float(offset_data)
    
    # Apply the adjustment
    adjust_time(offset)
    
    conn.close()
    node_socket.close()

if __name__ == '__main__':
    start_node()
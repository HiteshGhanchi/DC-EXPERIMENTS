import time
import sys
import threading
import socket

# --- Configuration ---
HOST = '127.0.0.1'
PORT = 5001
MAX_NODES = 3    # Wait for this many nodes before calculating average
# ---------------------

def start_leader():
    """Starts the master clock server and performs the synchronization cycle."""
    leader_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    leader_socket.bind((HOST, PORT))
    leader_socket.listen(MAX_NODES)
    print(f"[Master] Listening on {HOST}:{PORT}...")

    # Stores { (ip, node_listen_port): time_value }
    node_data = {} 
    master_time = time.time() # Master's uncorrected time is the initial reference

    # --- Step 1: Collect times from nodes ---
    print(f"[Master] Waiting for {MAX_NODES} nodes to send their time...")
    
    while len(node_data) < MAX_NODES:
        try:
            conn, addr = leader_socket.accept()
            
            # Receive node's reported time and listening port
            data_str = conn.recv(1024).decode('utf-8')
            T_node_str, node_port_str = data_str.split(',')
            
            T_node = float(T_node_str)
            node_listen_port = int(node_port_str)
            
            # Estimate RTT/Delay for correction (Simplification: assume 10ms for RTT)
            estimated_delay = 0.010 
            T_node_corrected = T_node + estimated_delay
            
            # Store the node's listening address (for sending the adjustment back) and the corrected time
            node_data[(addr[0], node_listen_port)] = T_node_corrected
            
            print(f"[Master] Received time {T_node:.6f} from {addr}, Corrected: {T_node_corrected:.6f}")
            conn.close()
            
        except KeyboardInterrupt:
            print("\n[Master] Shutting down.")
            leader_socket.close()
            return
        except Exception as e:
            print(f"[Master] Error during connection acceptance: {e}")
            
    # --- Step 2: Compute the average time ---
    all_corrected_times = list(node_data.values())
    all_corrected_times.append(master_time) # Include the master's time in the average
    
    total_time = sum(all_corrected_times)
    average_time = total_time / len(all_corrected_times)
    
    print(f"\n[Master] Master clock time (Reference): {master_time:.6f}")
    print(f"[Master] Computed Average time: {average_time:.6f}")
    
    # --- Step 3: Send offset adjustments ---
    for (node_ip, node_port), T_node_corrected in node_data.items():
        # Offset = Average Time - Node's Corrected Time
        offset = average_time - T_node_corrected
        
        try:
            adjust_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Reconnect to the client's listening port to send the adjustment
            adjust_socket.connect((node_ip, node_port)) 
            
            offset_str = str(offset)
            adjust_socket.sendall(offset_str.encode('utf-8'))
            
            print(f"[Master] Sent offset {offset:.6f} to Node-{node_port}")
            adjust_socket.close()
            
        except Exception as e:
            print(f"[Master] WARNING: Could not send offset to Node-{node_port}: {e}")

    # --- Step 4: Adjust the master's own clock ---
    master_offset = average_time - master_time
    print(f"[Master] Adjusting master by {master_offset:.6f} seconds")

    leader_socket.close()

if __name__ == '__main__':
    start_leader()
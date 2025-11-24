from flask import Flask, jsonify
import threading
import time
import os

app = Flask(__name__)

# NOTE: This function is copied from app_cpu_bound.py
def is_prime(n):
    if n < 2: return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True

# --- Multithreading Implementation ---
# NOTE: This setup is deliberately inefficient for CPU work due to the GIL.

def count_primes_worker_thread(start, end, result_list, index):
    """Worker function executed by a separate thread."""
    count = 0
    # This loop holds the GIL almost constantly, preventing other threads from running.
    for n in range(start, end):
        if is_prime(n):
            count += 1
    # Simple IPC: Use a list (must be carefully protected in a real app)
    # Since this is a simple append, we assume it's atomic enough for this demo.
    result_list[index] = count 

def run_heavy_task_threaded(N_max=1000000, num_threads=4):
    """Attempts to run heavy task in parallel using threads."""
    
    threads = []
    # Using a list for IPC (Simple Shared Memory)
    result_list = [0] * num_threads 
    
    chunk_size = N_max // num_threads
    
    for i in range(num_threads):
        start = i * chunk_size
        end = N_max if i == num_threads - 1 else (i + 1) * chunk_size
        
        # Create a new thread (GIL is NOT released during computation)
        t = threading.Thread(target=count_primes_worker_thread, args=(start, end, result_list, i))
        threads.append(t)
        t.start()
        
    # Synchronization: Wait for all threads to finish
    for t in threads:
        t.join()
        
    total_count = sum(result_list)
    return total_count

@app.route("/cpu-thread-task")
def cpu_thread_endpoint():
    N = 500000 # Use the smaller N for faster comparison
    t0 = time.time()
    
    # This task will run sequentially due to the GIL, even though 4 threads were created.
    prime_count = run_heavy_task_threaded(N_max=N, num_threads=4)
    
    t1 = time.time()
    
    return jsonify({
        "status": "ok",
        "method": "Multithreading (CPU-Bound)",
        "gil_effect": "True Parallelism Prevented",
        "execution_time_sec": round(t1 - t0, 4),
        "primes_found": prime_count,
        "process_id": os.getpid()
    })

@app.route("/")
def index():
    return "CPU-Bound Multithreading API"
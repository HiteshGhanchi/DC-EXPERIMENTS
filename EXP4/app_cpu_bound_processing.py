from flask import Flask, jsonify
import multiprocessing as mp
import time
import os
import sys

app = Flask(__name__)

def is_prime(n):
    """Heavy calculation task (CPU-Bound)."""
    if n < 2: return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True

def count_primes_worker(start, end, result_queue):
    """Worker function executed by a separate process."""
    count = 0
    # Simulate slightly longer run to show core utilization
    search_limit = end 
    for n in range(start, search_limit):
        if is_prime(n):
            count += 1
    # IPC: Send the partial result back to the main process
    result_queue.put(count)
    # The child process should exit cleanly
    sys.exit(0) 

def run_heavy_task(N_max=1000000, num_processes=4):
    """Divides the heavy task across multiple independent processes."""
    
    result_queue = mp.Queue() # IPC queue for results
    procs = []
    chunk_size = N_max // num_processes
    
    for i in range(num_processes):
        start = i * chunk_size
        end = N_max if i == num_processes - 1 else (i + 1) * chunk_size
        
        # Create a new, independent process (bypassing the GIL)
        p = mp.Process(target=count_primes_worker, args=(start, end, result_queue))
        procs.append(p)
        p.start()
        
    total_count = 0
    
    # Synchronization: Wait for all processes to finish
    for p in procs:
        p.join()
        
    # Communication: Collect results
    while not result_queue.empty():
        total_count += result_queue.get()
        
    return total_count

@app.route("/cpu-task")
def cpu_endpoint():
    N = 1000000 
    t0 = time.time()
    
    # Run the heavy work in parallel processes (4 processes = 4 CPU cores working simultaneously)
    prime_count = run_heavy_task(N_max=N, num_processes=4)
    
    t1 = time.time()
    
    return jsonify({
        "status": "ok",
        "method": "Multiprocessing (CPU-Bound)",
        "execution_time_sec": round(t1 - t0, 4),
        "primes_found": prime_count,
        "process_id": os.getpid()
    })

@app.route("/")
def index():
    return "CPU-Bound Multiprocessing API"
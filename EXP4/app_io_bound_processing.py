from flask import Flask, jsonify
import multiprocessing as mp
import time
import sys

app = Flask(__name__)

def simulate_io_worker(delay_seconds, result_queue):
    """Worker function executed by a separate process."""
    # Process creation and termination is heavy overhead for a quick 0.5s wait.
    time.sleep(delay_seconds)
    result_queue.put("I/O Task completed by process.")
    sys.exit(0) # Ensure clean exit

def run_io_parallel(delay, num_processes=4):
    """Starts multiple processes to wait concurrently."""
    result_queue = mp.Queue()
    procs = []
    
    for _ in range(num_processes):
        p = mp.Process(target=simulate_io_worker, args=(delay, result_queue))
        procs.append(p)
        p.start()
        
    # Wait for all processes to finish
    for p in procs:
        p.join()
        
    results = [result_queue.get() for _ in range(num_processes)]
    return results

@app.route("/io-process-task")
def io_process_endpoint():
    delay = 0.5 # Same 500ms delay as the threading app
    num_procs = 4 # Use 4 processes for comparison
    t0 = time.time()

    # The overhead of starting/stopping 4 processes will dominate the 0.5s wait time
    results = run_io_parallel(delay, num_procs)

    t1 = time.time()
    
    return jsonify({
        "status": "ok",
        "method": "Multiprocessing (I/O-Bound)",
        "overhead_observed": "High Process Startup Cost",
        "execution_time_sec": round(t1 - t0, 4),
        "result": results[0] 
    })

@app.route("/")
def index():
    return "I/O-Bound Multiprocessing API"
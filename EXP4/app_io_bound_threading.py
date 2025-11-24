from flask import Flask, jsonify 
import time
import threading

app = Flask(__name__)

def simulate_io_task(delay_seconds):
    #Simulates a network or disk I/O operation.
    # The GIL is released during this sleep, allowing other threads to work.
    time.sleep(delay_seconds)
    return "IO Task completed"

@app.route('/io_task')
def io_endpoint():
    delay = 0.5
    t0 = time.time()

    result = simulate_io_task(delay)

    t1 = time.time()
    
    return jsonify({
        "status": "ok",
        "method": "Multithreading (I/O-Bound)",
        "worker_thread": threading.get_ident(),
        "execution_time_sec": round(t1 - t0, 4),
        "result": result
    })

@app.route("/")
def index():
    return "I/O-Bound Multithreading API"
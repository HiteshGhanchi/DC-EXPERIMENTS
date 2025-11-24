import time
from flask import Flask , jsonify
import threading 
import sys

PORT = 5000
HOST = '0.0.0.0'

app = Flask(__name__)

@app.route('/get_time',methods=['GET'])
def get_time():
    server_time = time.time()

    response = jsonify({'time':server_time})
    threading.Thread(target=lambda: print(f"[Server] Sent time {server_time:.6f}")).start()
    return response

def start_server():
    print(f"Server started on {HOST}:{PORT}")
    app.run(host=HOST,port=PORT, debug=False, use_reloader=False)

if __name__ == "__main__":
    start_server()


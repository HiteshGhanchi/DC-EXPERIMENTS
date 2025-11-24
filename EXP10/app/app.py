from flask import Flask
import socket
import time

# Create a Flask instance
app = Flask(__name__)
# Suppress Flask start messages for clean logs
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route("/")
def index():
    """
    Returns a simple greeting indicating which server (hostname) handled the request.
    """
    hostname = socket.gethostname()
    
    # Simulate a small, variable processing time to differentiate response times
    # This is useful for observing true resource contention in dynamic scenarios later.
    delay = random.uniform(0.01, 0.1) 
    time.sleep(delay)

    print(f"Handled request at {time.time()} on {hostname}")
    return f"Hello from {hostname}"

if __name__ == '__main__':
    import random
    # Note: Flask will run on port 5000 inside the container, 
    # as exposed in the docker-compose.yml file.
    app.run(host='0.0.0.0', port=5000, debug=False)
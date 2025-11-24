import requests
import time
import random

SERVER_URL = "http://127.0.0.1:5000/get_time"
CLIENT_ID = random.randint(1, 100)

def get_time_from_server():
    try:
        t0 = time.time()

        response = requests.get(SERVER_URL, timeout=5)
        response.raise_for_status()

        t1 = time.time()

        data = response.json()
        T_server = data['time']

        RTT = t1 - t0
        one_way_delay = RTT / 2

        T_adjusted = T_server + one_way_delay

        print("\n","="*40) 
        print(f"[Client {CLIENT_ID}] Synchronization Results:")
        print(f"[Client] Sent request at t0 = {t0:.6f}")
        print(f"[Client] Received server time = {T_server:.6f} at t1 = {t1:.6f}")
        print(f"[Client] RTT (Round Trip Time) = {RTT:.6f} seconds")
        print(f"[Client] Estimated one-way delay = {one_way_delay:.6f} seconds")
        print(f"[Client] Current Local Clock (t1) = {t1:.6f}")
        print(f"[Client] Adjusted Synchronized Time = {T_adjusted:.6f}")
        print("="*80)

    except Exception as e:
        print(f"[Client {CLIENT_ID}] Error: {e}")

    

if __name__ == "__main__":
    get_time_from_server()

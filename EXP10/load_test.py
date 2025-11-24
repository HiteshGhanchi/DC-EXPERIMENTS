import requests
import time
from collections import defaultdict
import sys

def run_load_test(url, num_requests=1000):
    """Sends requests and logs which backend server handled the request."""
    counter = defaultdict(int)
    errors = 0
    start_time = time.time()
    
    print(f"Sending {num_requests} requests to load balancer at {url}...\n")
    
    for i in range(num_requests):
        try:
            # Connect to the Nginx Load Balancer (localhost:8080)
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            # The response body is "Hello from [hostname]"
            hostname = response.text.strip().split()[-1]
            counter[hostname] += 1
            # print(f"[{i+1}] Handled by: {hostname}") # Uncomment for detailed log
            
        except requests.exceptions.ConnectionError:
            errors += 1
            print(f"[{i+1}] Error: Connection refused (Is Docker running?)", file=sys.stderr)
        except Exception as e:
            errors += 1
            print(f"[{i+1}] Error: {e}", file=sys.stderr)
    
    end_time = time.time()
    
    print("\n--- Load Distribution Summary ---")
    print(f"Total time for {num_requests} requests: {end_time - start_time:.2f} seconds")
    
    total_handled = sum(counter.values())
    
    # Calculate percentage distribution
    for name, count in sorted(counter.items()):
        percent = (count / total_handled) * 100 if total_handled else 0
        print(f"{name}: {count} requests ({percent:.2f}%)")
        
    print(f"\nFailed requests: {errors}")


if __name__ == "__main__":
    # Ensure requests library is installed: pip install requests
    LB_URL = "http://localhost:8080"
    run_load_test(LB_URL, num_requests=1000)
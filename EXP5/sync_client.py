from heavy_computation import perform_heavy_task
import time

def run_synchronous_experiment(data):
    print("---------------------------------------------------------")
    print(f"*** [Client] Request received for data: {data} ***")
    print("*** [Client] WARNING: Main thread will be blocked now! ***")
    
    start_time = time.time()
    
    task_id, result = perform_heavy_task(data)
    
    end_time = time.time()
    
    print(f"\n*** [Client] Response received after waiting. Task ID: {task_id[:8]} ***")
    print(f"*** [Client] Total time waited: {end_time - start_time:.2f} seconds ***")
    print("---------------------------------------------------------")

if __name__ == "__main__":
    run_synchronous_experiment("Quarterly Sales Report (SYNC)")
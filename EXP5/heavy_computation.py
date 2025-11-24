import time
import uuid

def perform_heavy_task(task_data):
    task_id = str(uuid.uuid4())
    print(f"\n--- [Worker] Starting Task ID: {task_id[:8]} with data: {task_data} ---")

    time.sleep(5) 

    result = f"COMPLETED: Report generated for '{task_data}'"
    print(f"--- [Worker] Task ID: {task_id[:8]} Finished. Result: {result} ---\n")
    
    return task_id, result

if __name__ == "__main__":
    print("Testing the heavy computation function...")
    perform_heavy_task("Test Report")
1) INSTALL THE DOCKER IMAGE of RABBITMQ AND RUN IT

```
docker run -d --hostname my-rabbit --name rabbitmq -p 5673:5672 -p 15673:15672 rabbitmq:3-management
```

2) VERIFY USING
```
docker ps
```
also can view on the url : 
```
http://localhost:15673
```
id - guest
passowrd - guest

3) I will be using pika library so download it

```
pip install pika
```

4) Codes : 

heavy_computation.py

```
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
```

sync_client.py
```
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
```

async_prodcuer.py

```
import pika
import time
import json
import uuid

def send_task_to_queue(task_data):
    # Use the port 5673 from your Docker setup
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', port=5673))
    channel = connection.channel()
    
    # Declare a durable queue for work tasks (Work Queue Pattern)
    queue_name = 'heavy_tasks_queue'
    channel.queue_declare(queue=queue_name, durable=True)
    
    task_id = str(uuid.uuid4())
    # Package the task details into a JSON message
    task_message = json.dumps({'task_id': task_id, 'data': task_data, 'timestamp': time.time()})

    start_time = time.time()
    
    # Publish the message (task) to the queue
    channel.basic_publish(
        exchange='',  # Use the default exchange for simple queueing
        routing_key=queue_name, 
        body=task_message,
        properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE # Ensures message survives broker restart
        )
    )
    end_time = time.time()
    
    # This simulates the instantaneous response the user receives
    print(f"*** [API Server/Producer] Task ID {task_id[:8]} published successfully! ***")
    print(f"*** [API Server/Producer] Immediate wait time: {end_time - start_time:.4f} seconds ***")
    print(f"*** [API Server/Producer] Full computation runs in the background. ***\n")

    connection.close()

if __name__ == "__main__":
    send_task_to_queue("End-of-Year Audit Report (ASYNC)")
```

async_consumer.py

```
import pika
import json
import sys
# Import the slow function
from heavy_computation import perform_heavy_task 

def worker_callback(ch, method, properties, body):
    # Decode the JSON message to get the task data
    task = json.loads(body.decode())
    data = task['data']
    
    print(f"--- [Background Worker] Received task for: {data}. Starting heavy work... ---")
    
    # 1. Execute the heavy task (THIS BLOCKS THE WORKER, but NOT the API Server)
    task_id, result = perform_heavy_task(data)
    
    # 2. Acknowledge the message to tell RabbitMQ the task is done
    # This is crucial for reliability; RabbitMQ will delete the message only now.
    ch.basic_ack(delivery_tag=method.delivery_tag) 
    
    sys.stdout.flush() # Ensure print statements appear immediately

# --- Setup RabbitMQ connection for the worker ---
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', port=5673))
channel = connection.channel()

queue_name = 'heavy_tasks_queue'
channel.queue_declare(queue=queue_name, durable=True)

# Important for load balancing: tells RabbitMQ not to send a new message until the worker ACKs the previous one.
channel.basic_qos(prefetch_count=1) 

print(' [*] Background Worker is waiting for heavy tasks. To exit press CTRL+C')
channel.basic_consume(queue=queue_name, on_message_callback=worker_callback)
channel.start_consuming()
```

5) Check : 
We can run the sync_client.py, it will take 5 seconds and both the client is stuck doing nithing till then.

6) Run teh consumer : 
```
python async_consumer.py
```
import pika
import json
import sys
import os
from heavy_computation import perform_heavy_task 

RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = 5673
WORKER_QUEUE = 'heavy_tasks_queue'

def worker_callback(ch, method, properties, body):
    try:
        task = json.loads(body.decode())
        data = task['data']
        
        print(f"--- [Worker] Received task for: {data}. Starting heavy work (5s)... ---")
        
        # 1. Execute the heavy task (THIS BLOCKS THE WORKER, not the Producer)
        task_id, result_message = perform_heavy_task(data)
        
        # 2. Print result for verification (no reply needed in this simple non-RPC setup)
        print(f"--- [Worker] Task {task_id[:8]} Finished. Result: {result_message} ---")
        
        # 3. Acknowledge the message (crucial for reliability)
        ch.basic_ack(delivery_tag=method.delivery_tag) 
        
    except Exception as e:
        print(f"FATAL ERROR in worker: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag) 
    
    sys.stdout.flush()

try:
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST, port=RABBITMQ_PORT))
    channel = connection.channel()

    channel.queue_declare(queue=WORKER_QUEUE, durable=True)
    
    # Load Balancing: Prefetch count of 1 ensures the worker only gets one task at a time.
    channel.basic_qos(prefetch_count=1) 

    print(' [*] Background Worker is waiting for heavy tasks. To exit press CTRL+C')
    channel.basic_consume(queue=WORKER_QUEUE, on_message_callback=worker_callback, auto_ack=False)
    channel.start_consuming()

except pika.exceptions.AMQPConnectionError:
    print(f"ERROR: Could not connect to RabbitMQ on {RABBITMQ_HOST}:{RABBITMQ_PORT}. Ensure the Docker container is running.")
    sys.exit(1)

finally:
    if 'connection' in locals() and connection.is_open:
        connection.close()
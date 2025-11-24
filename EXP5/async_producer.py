import pika
import time
import json
import uuid
import sys
import os

RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = 5673
WORKER_QUEUE = 'heavy_tasks_queue'

def send_task_to_queue(task_data):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST, port=RABBITMQ_PORT))
        channel = connection.channel()
        
        # Declare a durable queue for work tasks
        channel.queue_declare(queue=WORKER_QUEUE, durable=True)
        
        task_id = str(uuid.uuid4())
        task_message = json.dumps({'task_id': task_id, 'data': task_data, 'timestamp': time.time()})

        start_time = time.time()
        
        # Publish the message (task) to the queue
        channel.basic_publish(
            exchange='',  # Default exchange
            routing_key=WORKER_QUEUE, 
            body=task_message.encode(),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE # Durable message
            )
        )
        end_time = time.time()
        
        print(f"*** [API Server/Producer] Task ID {task_id[:8]} published successfully! ***")
        print(f"*** [API Server/Producer] Immediate wait time: {end_time - start_time:.4f} seconds ***\n")

        connection.close()

    except pika.exceptions.AMQPConnectionError:
        print(f"ERROR: Could not connect to RabbitMQ on {RABBITMQ_HOST}:{RABBITMQ_PORT}. Ensure the Docker container is running.")
        sys.exit(1)

if __name__ == "__main__":
    task_name = sys.argv[1] if len(sys.argv) > 1 else "Default Task"
    send_task_to_queue(task_name)
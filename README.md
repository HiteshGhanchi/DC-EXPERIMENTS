# Distributed Computing Experiments

This repository contains a collection of implementations demonstrating core concepts in Distributed Computing, ranging from basic IPC mechanisms to advanced parallel processing and consensus algorithms.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Experiment 1: Inter-Process Communication (IPC)](#experiment-1-inter-process-communication-ipc)
- [Experiment 2: 3-Tier Web Architecture](#experiment-2-3-tier-web-architecture)
- [Experiment 3: Remote Procedure Calls (RPC)](#experiment-3-remote-procedure-calls-rpc)
- [Experiment 4: Concurrency (Threading vs. Multiprocessing)](#experiment-4-concurrency-threading-vs-multiprocessing)
- [Experiment 5: Asynchronous Messaging (Message Queues)](#experiment-5-asynchronous-messaging-message-queues)
- [Experiment 6: Clock Synchronization](#experiment-6-clock-synchronization)
- [Experiment 7: Logical Clocks & Event Ordering](#experiment-7-logical-clocks--event-ordering)
- [Experiment 8: Distributed Mutual Exclusion](#experiment-8-distributed-mutual-exclusion)
- [Experiment 9: Leader Election Algorithms](#experiment-9-leader-election-algorithms)
- [Experiment 10: Load Balancing](#experiment-10-load-balancing)
- [Experiment 11: Parallel Computing with MPI](#experiment-11-parallel-computing-with-mpi)

---

## Prerequisites
To run these experiments, you will need:
* **Python 3.x** (for most logic/algorithms)
* **Node.js & npm** (for EXP2)
* **Docker & Docker Compose** (for EXP5 and EXP10)
* **PostgreSQL** (for EXP2)
* **MPI implementation** (e.g., MPICH or OpenMPI) and `mpi4py` (for EXP11)
* **Additional Libraries:** `Pyro5`, `grpcio`, `grpcio-tools` (for EXP3)

---

## Experiment 1: Inter-Process Communication (IPC)
**Goal:** Demonstrate low-level communication between processes using Sockets (TCP/IP).

* **Files:** `server.py`, `client.py`
* **Description:**
    * **Server:** Implements a custom persistent TCP server that maintains a stateful user database (`USER_DATABASE`). It processes string-based commands for arithmetic (`/add`, `/div`) and resource management (`/add_name`, `/update_name`).
    * **Client:** Connects to the server and sends a sequence of formatted request messages, demonstrating persistent connection handling and error management.

## Experiment 2: 3-Tier Web Architecture
**Goal:** Implement a standard distributed web application structure involving a Presentation, Application, and Data tier.

* **Files:** `backend/server.js`, `index.html`, `package.json`
* **Description:**
    * **Data Tier:** A PostgreSQL database storing user credentials (`student_db`).
    * **Application Tier:** An Express.js (Node.js) backend that connects to the database using `pg` (connection pooling) to verify login credentials via a REST API (`/api/login`).
    * **Presentation Tier:** A simple HTML/JS frontend (`index.html`) that sends user input to the backend.

## Experiment 3: Remote Procedure Calls (RPC)
**Goal:** Implement Remote Procedure Calls (RPC) using different frameworks and protocols to understand how methods can be executed on remote servers as if they were local.

* **Description:**
    * **Pyro5 (Python Remote Objects):** Demonstrates transparent remote method calls where Python objects distributed over the network can be called just like local objects.
    * **XML-RPC:** Implements a client-server model using XML encoding over HTTP, allowing for lightweight, cross-platform remote function execution.
    * **gRPC:** Uses Protocol Buffers (protobuf) to define services and messages, facilitating high-performance, low-latency, and strongly-typed communication between microservices.

## Experiment 4: Concurrency (Threading vs. Multiprocessing)
**Goal:** Analyze the performance differences between Multithreading and Multiprocessing for CPU-bound vs. I/O-bound tasks in Python.

* **Files:** `app_cpu_bound_processing.py`, `app_io_bound_threading.py`, `test.sh`
* **Description:**
    * **CPU-Bound:** Uses `multiprocessing` to bypass the Global Interpreter Lock (GIL) and utilize multiple CPU cores for heavy calculations (checking prime numbers).
    * **I/O-Bound:** Uses `threading` to handle tasks that spend time waiting (simulated via `time.sleep`), showing how threads allow concurrency during wait times.

## Experiment 5: Asynchronous Messaging (Message Queues)
**Goal:** Decouple components using a Message Queue to handle heavy computation tasks asynchronously.

* **Files:** `async_producer.py`, `async_consumer.py`, `heavy_computation.py`, `steps.md`
* **Description:**
    * Uses **RabbitMQ** (running in Docker) as the message broker.
    * **Producer:** Sends a task to a persistent queue (`heavy_tasks_queue`) and returns immediately, simulating a non-blocking API response.
    * **Consumer:** A background worker listens to the queue, picks up tasks, and performs the "heavy" computation (simulated 5s delay), ensuring the main application remains responsive.

## Experiment 6: Clock Synchronization
**Goal:** Implement algorithms to synchronize physical clocks across distributed nodes.

* **Files:** `berkley/leader.py`, `berkley/node.py`, `cristian/server.py`, `cristian/client.py`
* **Description:**
    * **Berkeley Algorithm:** A centralized "leader" polls all nodes for their time, calculates an average (accounting for RTT), and sends time adjustment offsets back to each node (including itself) to synchronize them.
    * **Cristian's Algorithm:** A client requests the time from a server. The client calculates the synchronized time by adding half the Round Trip Time (RTT) to the server's returned timestamp.

## Experiment 7: Logical Clocks & Event Ordering
**Goal:** Implement logical clocks to maintain the order of events in a distributed system without relying on physical time.

* **Files:** `lamport/server.py`, `vector/server.py`, `client.py`
* **Description:**
    * **Lamport Clocks:** Maintains a single integer counter. The clock is updated as `max(local_clock, received_clock) + 1` upon receiving a message, ensuring a partial ordering of events.
    * **Vector Clocks:** Maintains an array of counters (one for each process). This allows the system to distinguish between causally related events and concurrent events by comparing vector indices.

## Experiment 8: Distributed Mutual Exclusion
**Goal:** Coordinate access to a shared resource (Critical Section) among multiple processes.

* **Files:** `boolean_lock/coordinator.py`, `ring/node.py`
* **Description:**
    * **Centralized (Coordinator):** A central server manages a `CS_LOCK` and a Request Queue. Clients must send a `REQUEST` and wait for a `GRANT` message before entering the critical section.
    * **Token Ring:** Nodes are organized in a logical ring. A "Token" message is passed sequentially. Only the node holding the token can enter the critical section. If a node doesn't need the resource, it passes the token immediately.

## Experiment 9: Leader Election Algorithms
**Goal:** Elect a coordinator from a group of processes after a failure.

* **Files:** `node.py` (Bully), `ring_node.py` (Ring)
* **Description:**
    * **Bully Algorithm:** Processes have unique PIDs. When a process notices the coordinator is down, it sends an `ELECTION` message to all processes with *higher* PIDs. The highest PID alive "bullies" the others and becomes the coordinator.
    * **Ring Algorithm:** An `ELECTION` message circulates the logical ring, collecting active PIDs. Once the message returns to the initiator, the highest PID found in the list is declared the coordinator.

## Experiment 10: Load Balancing
**Goal:** Distribute incoming network traffic across multiple backend servers using Nginx.

* **Files:** `docker-compose.yml`, `nginx/nginx.conf`, `app/app.py`
* **Description:**
    * Uses **Docker Compose** to spin up 3 identical instances of a Flask application (`app1`, `app2`, `app3`).
    * **Nginx** is configured as a reverse proxy and load balancer to distribute incoming HTTP requests among these three containers (likely using Round Robin), increasing reliability and throughput.

## Experiment 11: Parallel Computing with MPI
**Goal:** Perform high-performance parallel computation using the Message Passing Interface (MPI).

* **Files:** `mpi_matrix_multiply.py`
* **Description:**
    * Demonstrates parallel matrix multiplication using `mpi4py`.
    * **Scatter:** The root process (Rank 0) divides Matrix A into chunks and distributes them to all worker processes.
    * **Broadcast:** Matrix B is sent to all processes entirely.
    * **Gather:** Each process computes a portion of the result (Dot Product) and sends it back to the root to assemble the final Matrix C.
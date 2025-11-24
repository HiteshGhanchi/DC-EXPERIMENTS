#!/bin/bash

# --- Configuration ---
IO_PORT_THREAD=8001
IO_PORT_PROCESS=8003
CPU_PORT_PROCESS=8002
CPU_PORT_THREAD=8004

echo "========================================================"
echo " Starting Full Concurrency Comparison Lab (Cores: $WORKERS)"
echo "========================================================"

# --- 1. Start I/O-Bound Server (Multithreading - EFFICIENT CONCURRENCY) ---
# Goal: Threads release GIL during time.sleep(), allowing high concurrency.
echo -e "\n--- 1. Starting I/O-THREAD Server on :$IO_PORT_THREAD (1 Proc, 4 Threads) ---"
gunicorn -w 1 --threads 4 -b 127.0.0.1:$IO_PORT_THREAD app_io_bound_threading:app &
IO_THREAD_PID=$!
sleep 2

# --- 2. Start CPU-Bound Server (Multiprocessing - TRUE PARALLELISM) ---
# Goal: Processes bypass GIL, utilizing $WORKERS cores for calculation.
echo -e "\n--- 2. Starting CPU-PROCESS Server on :$CPU_PORT_PROCESS (4 Procs) ---"
gunicorn -w 4 -b 127.0.0.1:$CPU_PORT_PROCESS app_cpu_bound_processing:app &
CPU_PROCESS_PID=$!
sleep 2

# --- 3. Start I/O-Bound Server (Multiprocessing - INEFFICIENCY TEST) ---
# Goal: Measure overhead of using heavy processes for a simple waiting task.
echo -e "\n--- 3. Starting I/O-PROCESS Server on :$IO_PORT_PROCESS (4 Procs, I/O-Bound) ---"
gunicorn -w 4 -b 127.0.0.1:$IO_PORT_PROCESS app_io_bound_processing:app &
IO_PROCESS_PID=$!
sleep 2

# --- 4. Start CPU-Bound Server (Multithreading - GIL BOTTLENECK TEST) ---
# Goal: Measure slowdown caused by GIL during heavy computation.
echo -e "\n--- 4. Starting CPU-THREAD Server on :$CPU_PORT_THREAD (1 Proc, 4 Threads, CPU-Bound) ---"
gunicorn -w 1 --threads 4 -b 127.0.0.1:$CPU_PORT_THREAD app_cpu_bound_threading:app &
CPU_THREAD_PID=$!
sleep 2

# --- Benchmark Execution ---
echo -e "\n==================== BENCHMARK RESULTS ===================="

# --- TEST A: I/O-Bound Task Comparison (Concurrency vs. Overhead) ---
echo -e "\n--- A. I/O-BOUND CONCURRENCY (40 requests, 10 clients) ---"
echo "A1: THREADING (Low Overhead, Expected High RPS)"
ab -n 40 -c 10 http://127.0.0.1:$IO_PORT_THREAD/io-task | grep -E "Requests per second:|Time per request:|Failed requests:"

echo "A2: MULTIPROCESSING (High Overhead, Expected Lower RPS)"
ab -n 40 -c 10 http://127.0.0.1:$IO_PORT_PROCESS/io-process-task | grep -E "Requests per second:|Time per request:|Failed requests:"


# --- TEST B: CPU-Bound Task Comparison (Parallelism vs. GIL) ---
echo -e "\n--- B. CPU-BOUND PARALLELISM (10 requests, 10 clients) ---"

# B1: MULTIPROCESSING (True Parallelism) - Expected FASTEST execution time
echo "B1: MULTIPROCESSING (Fastest Time - Bypasses GIL)"
ab -n 10 -c 10 http://127.0.0.1:$CPU_PORT_PROCESS/cpu-task | grep -E "Requests per second:|Time per request:|Failed requests:"

# B2: MULTITHREADING (GIL Bottleneck) - Expected SLOWEST execution time
echo "B2: MULTITHREADING (Slowest Time - GIL Enforces Sequential)"
ab -n 10 -c 10 http://127.0.0.1:$CPU_PORT_THREAD/cpu-thread-task | grep -E "Requests per second:|Time per request:|Failed requests:"


# --- Cleanup ---
echo -e "\n--- Cleaning up all servers ---"
kill $IO_THREAD_PID $CPU_PROCESS_PID $IO_PROCESS_PID $CPU_THREAD_PID
wait $IO_THREAD_PID $CPU_PROCESS_PID $IO_PROCESS_PID $CPU_THREAD_PID 2>/dev/null
echo "Cleanup complete. Deactivate your virtual environment when done."
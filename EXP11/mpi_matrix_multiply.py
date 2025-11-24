from mpi4py import MPI
import numpy as np
import sys
import time

# --- Configuration ---
# Use square matrices for simplicity: N x N
MATRIX_SIZE = 4
# ---------------------

def log(rank, message):
    """Utility function for logging specific to the process rank."""
    print(f"[P{rank}] {message}")

def run_mpi_matrix_multiplication():
    # Initialize MPI environment
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()  # Rank (ID) of the current process (0 to size-1)
    size = comm.Get_size()  # Total number of processes available

    # Ensure matrix size is divisible by the number of processes
    if MATRIX_SIZE % size != 0:
        if rank == 0:
            print(f"Error: Matrix size ({MATRIX_SIZE}) must be divisible by number of processes ({size}).")
        sys.exit(1)

    # Calculate the number of rows each process handles
    rows_per_process = MATRIX_SIZE // size

    # Initialize matrices (all processes declare storage, but only rank 0 initializes values)
    A = None  # Full matrix A (only used by root for distribution/collection)
    B = np.zeros((MATRIX_SIZE, MATRIX_SIZE), dtype=np.int32)
    C = None  # Full result matrix C (only used by root)

    # Local matrices for each process
    local_A = np.zeros((rows_per_process, MATRIX_SIZE), dtype=np.int32)
    local_C = np.zeros((rows_per_process, MATRIX_SIZE), dtype=np.int32)

    # --- 1. Root Process Initialization (Rank 0) ---
    if rank == 0:
        log(rank, "Initializing matrices A and B.")
        A = np.random.randint(0, 10, size=(MATRIX_SIZE, MATRIX_SIZE), dtype=np.int32)
        B = np.random.randint(0, 10, size=(MATRIX_SIZE, MATRIX_SIZE), dtype=np.int32)
        C = np.zeros((MATRIX_SIZE, MATRIX_SIZE), dtype=np.int32)
        
        print("\n--- INPUT MATRICES ---")
        print(f"Matrix A ({MATRIX_SIZE}x{MATRIX_SIZE}):\n{A}")
        print(f"Matrix B ({MATRIX_SIZE}x{MATRIX_SIZE}):\n{B}")
        print("-" * 30)
        
        # Start timer for performance comparison
        start_time = time.time()

    # --- 2. Collective Communication Phase ---
    
    # 2a. Broadcast Matrix B to all processes (MPI_Bcast)
    # Since all processes need B entirely, B must be broadcasted.
    comm.Bcast([B, MPI.INT], root=0)
    log(rank, f"Received Matrix B via Bcast.")

    # 2b. Scatter Matrix A (rows) to all processes (MPI_Scatter)
    # Divides A into chunks and sends one chunk to each process (including rank 0).
    comm.Scatter([A, rows_per_process * MATRIX_SIZE, MPI.INT],
                 [local_A, rows_per_process * MATRIX_SIZE, MPI.INT],
                 root=0)
    log(rank, f"Received local A (Rows: {rows_per_process}).")
    
    # --- 3. Local Computation Phase (Parallel Multiplication) ---
    
    # Each process computes its assigned portion of the result matrix C
    # local_C = local_A * B
    log(rank, "Starting local matrix multiplication...")
    local_C = np.dot(local_A, B)
    log(rank, "Local multiplication complete.")
    
    # --- 4. Gather Results Phase ---

    # Gather all the local_C portions back to the root process (Rank 0)
    comm.Gather([local_C, rows_per_process * MATRIX_SIZE, MPI.INT],
                [C, rows_per_process * MATRIX_SIZE, MPI.INT],
                root=0)

    # --- 5. Final Output (Rank 0) ---
    if rank == 0:
        end_time = time.time()
        
        print("\n--- FINAL RESULT (Matrix C) ---")
        print(f"Result Matrix C (A x B):\n{C}")
        print("-" * 30)
        print(f"Total parallel computation time ({size} processes): {end_time - start_time:.4f} seconds")

# Finalize the MPI environment
if __name__ == '__main__':
    try:
        run_mpi_matrix_multiplication()
        # MPI.Finalize() is generally called implicitly when using the mpi4py context.
        
    except Exception as e:
        if MPI.COMM_WORLD.Get_rank() == 0:
            print(f"A runtime error occurred: {e}")
        sys.exit(1)


# /usr/bin/mpiexec -n 4 /home/hitesh/conda_root/bin/python mpi_matrix_multiply.py

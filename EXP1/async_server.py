import asyncio

HOST = '127.0.0.1'
PORT = 4002 # New Port

async def handle_client(reader, writer):
    """
    This coroutine handles the client connection.
    It uses 'await' instead of blocking calls.
    """
    addr = writer.get_extra_info('peername')
    print(f"[Task] Accepted connection from {addr}")
    
    while True:
        # CRITICAL STEP: 'await' tells the loop to switch tasks 
        # while waiting for data (non-blocking).
        data = await reader.read(1024) 
        if not data: 
            break
        
        message = data.decode('utf-8')
        response = f"Async Task processed: {message.upper()}"
        
        # 'await' here also ensures non-blocking write
        writer.write(response.encode('utf-8')) 
        await writer.drain() # Wait until the buffer is flushed

    print(f"[Task] Client {addr} closed.")
    writer.close()
    await writer.wait_closed()


async def main():
    # start_server creates the listening socket and manages the event loop
    server = await asyncio.start_server(
        handle_client, HOST, PORT)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f"Listening on {addrs} (Async I/O).")

    async with server:
        # Serve_forever keeps the event loop running
        await server.serve_forever()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer Shutting Down.")
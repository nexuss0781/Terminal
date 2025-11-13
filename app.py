import asyncio
import os
import pty
import fcntl
import struct
import termios
import uvicorn  # <-- Import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

# In a real app, you might serve this from a file, but for simplicity
# we assume index.html is in the same directory.
try:
    with open("index.html", "r") as f:
        html_content = f.read()
except FileNotFoundError:
    html_content = "<h1>Error: index.html not found</h1><p>Please create an index.html file in the same directory.</p>"


def set_winsize(fd, row, col, xpix=0, ypix=0):
    """Set window size of a pseudo-terminal."""
    winsize = struct.pack("HHHH", row, col, xpix, ypix)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

@app.get("/")
async def get():
    """Serves the HTML page."""
    return HTMLResponse(html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handles the WebSocket connection for the terminal session."""
    await websocket.accept()

    # Create a new pseudo-terminal
    master_fd, slave_fd = pty.openpty()

    # Create a new bash process and connect it to the pseudo-terminal
    pid = os.fork()
    if pid == 0:  # Child process
        os.setsid()
        os.dup2(slave_fd, 0)  # stdin
        os.dup2(slave_fd, 1)  # stdout
        os.dup2(slave_fd, 2)  # stderr
        os.close(master_fd)
        os.environ['TERM'] = 'xterm-256color' # Use a common term for color support
        # Launch bash
        os.execlp("bash", "bash")
    else:  # Parent process
        os.close(slave_fd)

    # Set initial window size
    set_winsize(master_fd, 50, 80) # Default size

    async def read_and_forward_pty_output():
        """Reads output from the pty and forwards it to the WebSocket."""
        while True:
            try:
                # Use a small sleep to prevent a busy loop
                await asyncio.sleep(0.01)
                output = os.read(master_fd, 1024)
                if output:
                    await websocket.send_text(output.decode(errors="ignore"))
                else: # When the process exits, os.read returns empty bytes
                    break
            except (IOError, OSError):
                break
        await websocket.close()


    # Start the task that reads from the PTY
    output_task = asyncio.create_task(read_and_forward_pty_output())

    try:
        while True:
            # Wait for input from the WebSocket
            data = await websocket.receive_text()
            
            # Check for special resize command from frontend
            if data.startswith('{"type":"resize"'):
                import json
                resize_data = json.loads(data)
                rows = resize_data.get('rows', 50)
                cols = resize_data.get('cols', 80)
                set_winsize(master_fd, rows, cols)
            else:
                # Forward user input to the pty
                os.write(master_fd, data.encode())
    except Exception:
        pass
    finally:
        # Clean up when the connection is closed
        output_task.cancel()
        os.kill(pid, 15) # Send SIGTERM to the bash process
        os.close(master_fd)
        print(f"Session for pid {pid} closed.")


# ======================================================================
# NEW SECTION: This block runs the server when the script is executed
# ======================================================================
if __name__ == "__main__":
    print("Starting Web Terminal server...")
    print("Access it at http://<your-ip-address>:8000")
    
    # We use the string "app:app" to allow for --reload to work correctly
    # host="0.0.0.0" makes the server accessible from your network
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
# ======================================================================

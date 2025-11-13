import asyncio
import os
import pty
import fcntl
import struct
import termios
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

# HTML content to serve the frontend
# In a real app, you'd serve this from a file.
with open("index.html", "r") as f:
    html_content = f.read()

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
    # The master file descriptor (master_fd) is connected to our Python code.
    # The slave file descriptor (slave_fd) is what the child shell process uses.
    master_fd, slave_fd = pty.openpty()

    # Create a new bash process and connect its stdin, stdout, and stderr
    # to the slave end of the pseudo-terminal.
    pid = os.fork()
    if pid == 0:  # Child process
        os.setsid()
        os.dup2(slave_fd, 0)  # stdin
        os.dup2(slave_fd, 1)  # stdout
        os.dup2(slave_fd, 2)  # stderr
        os.close(master_fd)
        os.environ['TERM'] = 'xterm' # Emulate a standard terminal
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
                # Use a small timeout to avoid blocking forever
                await asyncio.sleep(0.01)
                output = os.read(master_fd, 1024)
                if output:
                    await websocket.send_text(output.decode(errors="ignore"))
                else: # When the process exits, os.read returns empty bytes
                    break
            except Exception:
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

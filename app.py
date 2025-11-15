import asyncio
import os
import pty
import fcntl
import struct
import termios
import uvicorn
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from pty_process import PtyProcess # Import the new class

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# In a real app, you might serve this from a file, but for simplicity
# we assume index.html is in the same directory.
try:
    with open("index.html", "r") as f:
        html_content = f.read()
except FileNotFoundError:
    html_content = "<h1>Error: index.html not found</h1><p>Please create an index.html file in the same directory.</p>"


@app.get("/")
async def get():
    """Serves the HTML page."""
    return HTMLResponse(html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handles the WebSocket connection for the terminal session."""
    await websocket.accept()
    client_host = f"{websocket.client.host}:{websocket.client.port}"
    logger.info(f"WebSocket accepted from {client_host}")

    pty_process = PtyProcess(websocket, asyncio.get_event_loop())
    try:
        await pty_process.spawn()
        pty_process.set_winsize(50, 80) # Default size

        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received from WebSocket ({client_host}): {data[:50]}...")
            
            if data.startswith('{"type":"resize"'):
                import json
                resize_data = json.loads(data)
                rows = resize_data.get('rows', 50)
                cols = resize_data.get('cols', 80)
                pty_process.set_winsize(rows, cols)
                logger.info(f"Resized PTY for {client_host} to {rows}x{cols}")
            else:
                pty_process.write(data.encode())
                logger.debug(f"Sent to PTY ({client_host}): {data[:50]}...")
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for {client_host}.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in WebSocket loop for {client_host}: {e}")
    finally:
        pty_process.close()
        logger.info(f"Session for {client_host} closed.")


if __name__ == "__main__":
    logger.info("Starting Web Terminal server...")
    logger.info("Access it at http://0.0.0.0:8000")
    
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    logger.info("Starting Web Terminal server...")
    logger.info("Access it at http://0.0.0.0:8000")
    
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

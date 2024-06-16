
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import subprocess
import asyncio
import websockets.exceptions

app = FastAPI()

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dictionary to store active websocket connections
websocket_connections = {}

# Websocket route for interactive CLI
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_connections[websocket] = True  # Store connection status

    try:
        while True:
            command = await websocket.receive_text()
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            output = stdout.decode() + stderr.decode()
            await websocket.send_text(output)
    except websockets.exceptions.ConnectionClosed as e:
        del websocket_connections[websocket]  # Remove connection on disconnect
    finally:
        await websocket.close()

# Route to serve index.html
@app.get("/")
async def get():
    return HTMLResponse(content=open("static/index.html", "r").read(), status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

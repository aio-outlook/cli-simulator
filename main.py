from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import socketio
import subprocess
from loguru import logger

# Initialize FastAPI app
app = FastAPI()

# CORS configuration
origins = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Socket.IO server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=origins)
app_asgi = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path='/socket.io')

@app.get("/")
async def get():
    with open("templates/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

@sio.event
async def execute_command(sid, data):
    command = data.get('command')
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in iter(process.stdout.readline, ''):
            await sio.emit('command_output', {'output': line}, to=sid)
        process.stdout.close()
        process.wait()
        if process.returncode != 0:
            for line in iter(process.stderr.readline, ''):
                await sio.emit('command_output', {'output': line}, to=sid)
        process.stderr.close()
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        await sio.emit('command_output', {'output': str(e)}, to=sid)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(str(request))
    logger.info(f"Started {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Completed {request.method} {request.url} - {response.status_code}")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app_asgi, host="0.0.0.0", port=8000)

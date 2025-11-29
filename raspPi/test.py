import socketio
from aiohttp import web

sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
sio.attach(app)

# ---------------------
# EVENTS
# ---------------------
@sio.event
async def connect(sid, environ):
    print(f"Device connected: {sid}")

@sio.on("coords")
async def coords(sid, data):
    print(f"📍 Received coords from {sid}: {data}")

@sio.event
async def disconnect(sid):
    print(f"Device disconnected: {sid}")

# ---------------------
# START SERVER
# ---------------------
if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8765)

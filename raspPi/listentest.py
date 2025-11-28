import socketio

# Create a Socket.IO server
sio = socketio.AsyncServer(cors_allowed_origins='*', async_mode="asgi")
app = socketio.ASGIApp(sio)

# Event for client connection
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

# Event for receiving data
@sio.event
async def location(sid, data):
    lat = data.get("lat")
    lon = data.get("lon")
    if lat is not None and lon is not None:
        print(f"Received from {sid}: lat={lat:.6f}, lon={lon:.6f}")
    await sio.emit("ack", {"status": "received"}, to=sid)  # optional ack

# Event for disconnection
@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

if __name__ == "__main__":
    import uvicorn
    # Run ASGI app
    uvicorn.run(app, host="0.0.0.0", port=8765)

import asyncio
import socketio
import math
import time

# ----------------------------
# Socket.IO server
# ----------------------------
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*'
    )
app = socketio.ASGIApp(sio)

# ----------------------------
# Stability config
# ----------------------------
STABILITY_ROOM = 3  # degrees
STABILITY_TIME = 3  # seconds

# ----------------------------
# State for the single client
# ----------------------------
last_coords = None
stable_since = None
request_sent = False

# ----------------------------
# Helper function
# ----------------------------
def coords_within_room(c1, c2, room):
    """Check if two (lat, lon) coordinates are within `room` degrees."""
    return math.isclose(c1[0], c2[0], abs_tol=room) and math.isclose(c1[1], c2[1], abs_tol=room)

# ----------------------------
# Socket.IO events
# ----------------------------
@sio.event
async def connect(sid, environ):
    global last_coords, stable_since, request_sent
    print(f"Client connected: {sid}")
    last_coords = None
    stable_since = None
    request_sent = False

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.on("coords")
async def coords(sid, data):
    global last_coords, stable_since, request_sent

    lat = data.get("lat")
    lon = data.get("lon")
    if lat is None or lon is None:
        return

    print(f"Received coords: lat={lat}, lon={lon}")


    # Stability check
    if last_coords is None:
        last_coords = (lat, lon)
        stable_since = time.time()
        request_sent = False
    else:
        if coords_within_room((lat, lon), last_coords, STABILITY_ROOM):
            # Coordinates are stable
            if time.time() - stable_since >= STABILITY_TIME and not request_sent:
                print(f"Coordinates stable for {STABILITY_TIME} seconds! ✅")
                request_sent = True
                await sio.emit("stable", {"lat": lat, "lon": lon}, to=sid)
        else:
            # Reset if moved outside the room
            last_coords = (lat, lon)
            stable_since = time.time()
            request_sent = False

# ----------------------------
# Run server
# ----------------------------
if __name__ == "__main__":
    import uvicorn
    print("Starting Socket.IO server on 0.0.0.0:8765...")
    uvicorn.run(app, host="0.0.0.0", port=8765)

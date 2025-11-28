import asyncio
import socketio
import random
import time

# ----------------------------
# Socket.IO client
# ----------------------------
sio = socketio.AsyncClient()

SERVER_URI = "http://0.0.0.0:8765"  # your server

@sio.event
async def connect():
    print("✅ Connected to server!")

@sio.event
async def disconnect():
    print("❌ Disconnected from server")

@sio.event
async def ack(data):
    print("Server ACK:", data)

# ----------------------------
# Continuous sending loop
# ----------------------------
async def send_test_locations(interval=1.0):
    """
    Send random latitude/longitude every `interval` seconds
    """
    while True:
        # Example: random test coordinates
        lat = random.uniform(-90, 90)
        lon = random.uniform(-180, 180)
        message = {"lat": lat, "lon": lon}

        await sio.emit("location", message)
        print(f"Sent: {message}")

        await asyncio.sleep(interval)  # wait before sending next

# ----------------------------
# Entry point
# ----------------------------
async def main():
    await sio.connect(SERVER_URI)
    await send_test_locations(interval=0.5)  # send every 0.5s for testing

if __name__ == "__main__":
    asyncio.run(main())

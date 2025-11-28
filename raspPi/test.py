import asyncio
import socketio

sio = socketio.AsyncClient()
WS_URI = "http://192.168.166.154:8765"

@sio.event
async def connect():
    print("✅ Connected to server!")

@sio.event
async def disconnect():
    print("❌ Disconnected from server")

async def main():
    await sio.connect(WS_URI)
    print("Connected, starting sending loop...")
    try:
        for i in range(5):
            await sio.emit("message", {"lat": i, "lon": i})
            print(f"Sent coords: {i}, {i}")
            await asyncio.sleep(1)
    finally:
        # Disconnect cleanly in the same loop
        await sio.disconnect()

asyncio.run(main())

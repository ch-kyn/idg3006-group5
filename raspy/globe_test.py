import asyncio
import socketio
import time

# Socket.IO client
sio = socketio.AsyncClient()
SERVER_URI = "https://acrocarpous-masonically-dannielle.ngrok-free.dev"

@sio.event
async def connect():
    print("Connected to server!")

@sio.event
async def disconnect():
    print("Disconnected from server")

async def send_locations(interval=0.5):
    coords_sequence = [
        {"lat": 35.8, "long": 137.7},      # Tokyo-ish
        {"lat": 40.4168, "long": -3.7038}  # Madrid
    ]
    switch_interval = 10  # seconds

    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        current_index = int(elapsed // switch_interval) % len(coords_sequence)
        coords = coords_sequence[current_index]

        if sio.connected:
            await sio.emit("coords", coords)
            print(f"📍 Sent coordinates: {coords}")
        else:
            print("⚠️ Not connected, skipping emit")

        await asyncio.sleep(interval)

async def main():
    await sio.connect(SERVER_URI)
    print("🌙 Starting coordinate sending...")
    await send_locations()

if __name__ == "__main__":
    asyncio.run(main())

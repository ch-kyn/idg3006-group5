import asyncio
import socketio
import time
import random

# Socket.IO client
sio = socketio.AsyncClient()
SERVER_URI = "http://localhost:3000"

active_sending = False # State flag

@sio.event
async def connect():
    print("Connected to server!")

@sio.event
async def disconnect():
    print("Disconnected from server")

# Listen for "calibrate" event
@sio.on("calibrateDone")
async def on_calibrate(data):
    global active_sending
    print("Calibrate clicked! Starting active sending.")

    await sio.emit("calibrateRestart", {"reset": True})
    print("Emitted calibrateRestart to reset Node-RED context")

    # Send 0,0 once
    # await sio.emit("coords", {"lat": 0.0, "long": 0.0})
    # print("Sent: {'lat': 0.0, 'long': 0.0}s")

    # Activate sending loop
    active_sending = True

# Listen for "stableCoordinatesSent" event
@sio.on("stableCoordinatesSent")
async def on_stable(data):
    global active_sending
    print("✅ Stable coordinates reached. Stopping sending.")
    print(data)
    active_sending = False
    await sio.emit("calibrate", {"calibrate": False})

# Continuous sending loop
# async def send_locations(interval=0.5):
#     global active_sending
#     while True:
#         if active_sending:
#             # Send random coordinates while active
#             coords = {"lat": random.uniform(-90, 90), "long": random.uniform(-180, 180)}
#             await sio.emit("coords", coords)
#             print(f"Sent: {coords}")
#         await asyncio.sleep(interval)
        
# After `delay` seconds, send stable coordinates once and notify the server.

async def send_locations_stable(interval=0.5):
    global active_sending

    coords_sequence = [
        {"lat": 35.8, "long": 137.7},      # Tokyo-ish
        {"lat": 40.4168, "long": -3.7038}  # Madrid
    ]
    switch_interval = 10  # seconds

    while True:  # keep the task alive forever
        # Wait until active_sending becomes True
        while not active_sending:
            await asyncio.sleep(0.05)

        print("🟢 Active sending detected. Starting coordinate sending...")

        start_time = time.time()
        current_index = 0

        while active_sending:
            # Switch coordinates every `switch_interval` seconds
            elapsed = time.time() - start_time
            current_index = int(elapsed // switch_interval) % len(coords_sequence)
            coords = coords_sequence[current_index]

            if sio.connected:
                await sio.emit("coords", coords)
                print(f"📍 Sent coordinates: {coords}")
            else:
                print("⚠️ Not connected, skipping emit")

            await asyncio.sleep(interval)

        print("⏹️ Active sending stopped. Waiting for next calibration...")

async def main():
    await sio.connect(SERVER_URI)
    print("🌙 Starting in sleep mode. Waiting for calibration...")
    asyncio.create_task(send_locations_stable())
    await sio.wait()

if __name__ == "__main__":
    asyncio.run(main())

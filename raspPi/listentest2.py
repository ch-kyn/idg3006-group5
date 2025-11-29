import asyncio
import websockets
import json
import time
import math
import requests

HOST = "0.0.0.0"
PORT = 8765

RED_URI= "http://127.0.0.1:1880/coords"

# stability configs
stability_room = 3  # degrees
stability_time = 3  # seconds
request_sent = False

# store last coordinates and timestamp
last_coords = None
stable_since = None

def coords_within_room(c1, c2, room):
    """Check if coordinates c1 and c2 are within `room` degrees"""
    return math.isclose(c1[0], c2[0], abs_tol=room) and math.isclose(c1[1], c2[1], abs_tol=room)

async def handle_client(websocket):
    global request_sent, last_coords, stable_since

    print(f"New client connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                lat = data.get("lat")
                lon = data.get("lon")
                if lat is not None and lon is not None:
                    print(f"Received: lat={lat:.6f}, lon={lon:.6f}")

                    if last_coords is None:
                        last_coords = (lat, lon)
                        stable_since = time.time()
                    else:
                        if coords_within_room((lat, lon), last_coords, stability_room):
                            # coordinates are stable
                            if time.time() - stable_since >= stability_time and not request_sent:
                                print("Coordinates stable, sending request...")
                                payload = {
                                    "lat": lat,
                                    "long": lon
                                }
                                response = requests.post(RED_URI, json=payload)
                                print("response:", response.text)
                                request_sent = True
                                # here you can send a request or trigger an action
                        else:
                            # reset if coordinates moved
                            last_coords = (lat, lon)
                            stable_since = time.time()
                            request_sent = False

            except json.JSONDecodeError:
                print("Received invalid JSON:", message)
    except websockets.ConnectionClosed:
        print("Client disconnected.")

async def main():
    async with websockets.serve(handle_client, HOST, PORT):
        print(f"WebSocket server running on ws://{HOST}:{PORT}")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())

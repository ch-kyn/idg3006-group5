import asyncio
import websockets
import json

HOST = "0.0.0.0"
PORT = 8765

connected_sensors = set()  # store clients if you want to broadcast

async def handle_sensor(websocket):  # <-- MUST include 'path'
    print(f"Sensor connected: {websocket.remote_address}")
    connected_sensors.add(websocket)
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                lat = data.get("lat")
                lon = data.get("lon")
                if lat is not None and lon is not None:
                    print(f"Received from sensor: lat={lat}, lon={lon}")

                    # Broadcast to all connected clients (Node-RED or frontend)
                    for ws in connected_sensors:
                        if ws != websocket:  # optional: skip sender
                            await ws.send(json.dumps({"lat": lat, "long": lon}))
            except json.JSONDecodeError:
                print("Invalid JSON:", message)
    except websockets.ConnectionClosed:
        print(f"Sensor disconnected: {websocket.remote_address}")
    finally:
        connected_sensors.remove(websocket)

async def main():
    async with websockets.serve(handle_sensor, HOST, PORT):
        print(f"WebSocket server running on ws://{HOST}:{PORT}")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())

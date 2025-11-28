import asyncio
import websockets
import json

# WebSocket server config
HOST = "0.0.0.0"  # listen on all interfaces
PORT = 8765       # match the sender's WS_URI port

async def handle_client(websocket, path):
    print(f"New client connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                lat = data.get("lat")
                lon = data.get("lon")
                if lat is not None and lon is not None:
                    print(f"Received: lat={lat:.6f}, lon={lon:.6f}")
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
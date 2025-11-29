import asyncio
import socketio
import time
import math
import board
import busio
import digitalio
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR

# ----------------------------
# RESET PIN + SENSOR INIT
# ----------------------------
reset_pin = digitalio.DigitalInOut(board.D17)
reset_pin.direction = digitalio.Direction.OUTPUT
i2c = busio.I2C(board.SCL, board.SDA)

def init_sensor():
    print("Initializing BNO08X...")

    reset_pin.value = False
    time.sleep(0.01)
    reset_pin.value = True
    time.sleep(0.25)

    sensor = BNO08X_I2C(i2c, address=0x4A)
    sensor.enable_feature(BNO_REPORT_ROTATION_VECTOR)
    return sensor

sensor = init_sensor()

# ----------------------------
# QUAT + VECTOR MATH
# ----------------------------
def quat_conjugate(q):
    x, y, z, w = q
    return (-x, -y, -z, w)

def quat_mul(q1, q2):
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return (
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    )

def rotate_vector_by_quat(v, q):
    vx, vy, vz = v
    vq = (vx, vy, vz, 0)
    qc = quat_conjugate(q)
    return quat_mul(quat_mul(q, vq), qc)[:3]

def vector_to_latlon(v):
    vx, vy, vz = v
    mag = math.sqrt(vx*vx + vy*vy + vz*vz)
    if mag == 0:
        return None, None

    vx /= mag; vy /= mag; vz /= mag
    lat = math.degrees(math.asin(vz))
    lon = math.degrees(math.atan2(vy, vx))

    if lon >= 180: lon -= 360
    if lon < -180: lon += 360

    return lat, lon

# ----------------------------
# SENSOR AXIS
# ----------------------------
sensor_axis = (1.0, 0.0, 0.0)

# ----------------------------
# SOCKET.IO SETUP
# ----------------------------
sio = socketio.AsyncClient()
SERVER_URI = "https://acrocarpous-masonically-dannielle.ngrok-free.dev"

@sio.event
async def connect():
    print("Connected to server!")

@sio.event
async def disconnect():
    print("Disconnected from server")

# ----------------------------
# RAW CONTINUOUS STREAM LOOP
# ----------------------------
async def stream_sensor(interval=0.05):
    print("Python ready. Streaming sensor data...")

    while True:
        if sio.connected:
            # Read quaternion
            x, y, z, w = sensor.quaternion
            if (x, y, z, w) == (0, 0, 0, 0):
                await asyncio.sleep(interval)
                continue

            raw_q = (x, y, z, w)

            # Convert direction → lat/lon
            world_vec = rotate_vector_by_quat(sensor_axis, raw_q)
            lat, lon = vector_to_latlon(world_vec)

            if lat is not None:
                await sio.emit("coords", {"lat": lat, "long": lon})
                print(f"📡 Sent coords: lat={lat:.2f}, lon={lon:.2f}")

        await asyncio.sleep(interval)

# ----------------------------
# MAIN
# ----------------------------
async def main():
    await sio.connect(SERVER_URI)
    asyncio.create_task(stream_sensor())
    await sio.wait()

if __name__ == "__main__":
    asyncio.run(main())

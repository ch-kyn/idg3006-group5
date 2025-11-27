import asyncio
import websockets
import json
import time
import math
import board
import busio
import digitalio
import sys
import select

from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR

# ----------------------------
# WebSocket config
# ----------------------------
WS_URI = "ws://192.168.166.154:8765"

# ----------------------------
# RESET PIN (REQUIRED)
# ----------------------------
reset_pin = digitalio.DigitalInOut(board.D17)
reset_pin.direction = digitalio.Direction.OUTPUT

# ----------------------------
# I2C INIT
# ----------------------------
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
# Quaternion helpers
# ----------------------------
def quat_conjugate(q):
    x, y, z, w = q
    return (-x, -y, -z, w)

def quat_mul(q1, q2):
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return (
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
        w1*w2 - x1*x2 - y1*y2 - z1*z2
    )

def normalize_quat(q):
    x, y, z, w = q
    mag = math.sqrt(x*x + y*y + z*z + w*w)
    if mag == 0: 
        return (0, 0, 0, 1)
    return (x/mag, y/mag, z/mag, w/mag)

def slerp(q1, q2, alpha):
    """Spherical linear interpolation of two quaternions."""
    if q1 is None:
        return q2  # first sample

    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2

    dot = x1*x2 + y1*y2 + z1*z2 + w1*w2

    # If dot < 0, invert q2 for shortest path
    if dot < 0:
        dot = -dot
        q2 = (-x2, -y2, -z2, -w2)

    # If quaternions are very close, use linear interpolation
    if dot > 0.9995:
        lerped = (
            x1 + alpha*(x2 - x1),
            y1 + alpha*(y2 - y1),
            z1 + alpha*(z2 - z1),
            w1 + alpha*(w2 - w1),
        )
        return normalize_quat(lerped)

    theta = math.acos(dot)
    sin_theta = math.sin(theta)

    w1 = math.sin((1 - alpha) * theta) / sin_theta
    w2 = math.sin(alpha * theta) / sin_theta

    return (
        x1*w1 + x2*w2,
        y1*w1 + y2*w2,
        z1*w1 + z2*w2,
        w1*w1 + w2*w2  # careful: w-component is similar form
    )

def rotate_vector_by_quat(v, q):
    vx, vy, vz = v
    vq = (vx, vy, vz, 0.0)
    qc = quat_conjugate(q)
    return quat_mul(quat_mul(q, vq), qc)[:3]

def vector_to_latlon(v):
    vx, vy, vz = v
    mag = math.sqrt(vx*vx + vy*vy + vz*vz)
    if mag == 0:
        return None, None

    vx /= mag
    vy /= mag
    vz /= mag

    lat = math.degrees(math.asin(vz))
    lon = math.degrees(math.atan2(vy, vx))

    if lon >= 180: lon -= 360
    if lon < -180: lon += 360

    return lat, lon

# ----------------------------
# CONFIG
# ----------------------------
sensor_axis = (1.0, 0.0, 0.0)
calibration_quat = (0.0, 0.0, 0.0, 1.0)

def calibrate(q):
    global calibration_quat
    calibration_quat = quat_conjugate(q)
    print("\n🎯 Calibration updated!\n")

# ----------------------------
# Quaternion filter state
# ----------------------------
filtered_q = None
ALPHA = 0.15   # smoothing factor for SLERP

# ----------------------------
# Keyboard input helper
# ----------------------------
def key_pressed():
    dr, dw, de = select.select([sys.stdin], [], [], 0)
    return dr != []

# ----------------------------
# Main async loop
# ----------------------------
async def send_coordinates():
    global sensor, filtered_q

    async with websockets.connect(WS_URI) as websocket:
        print("Connected to WebSocket server!")

        while True:

            # Check for "c" key
            if key_pressed():
                ch = sys.stdin.read(1)
                if ch.lower() == "c":
                    calibrate(sensor.quaternion)

            try:
                # Read quaternion
                q = sensor.quaternion
                if q == (0.0, 0.0, 0.0, 0.0):
                    await asyncio.sleep(0.01)
                    continue

                raw_q = normalize_quat(q)
                corrected_q = quat_mul(calibration_quat, raw_q)
                corrected_q = normalize_quat(corrected_q)

                # ----------------------------
                # Apply SLERP quaternion smoothing
                # ----------------------------
                filtered_q = slerp(filtered_q, corrected_q, ALPHA)
                filtered_q = normalize_quat(filtered_q)

                # Compute pointing direction
                world_vec = rotate_vector_by_quat(sensor_axis, filtered_q)
                lat, lon = vector_to_latlon(world_vec)
                if lat is None:
                    await asyncio.sleep(0.01)
                    continue

                # Send filtered result
                msg = json.dumps({
                    "lat": round(lat, 3),
                    "lon": round(lon, 3)
                })
                await websocket.send(msg)
                print("Sent:", msg)

                await asyncio.sleep(0.1)

            except OSError:
                print("\n⚠️ I2C hiccup — resetting sensor...")
                sensor = init_sensor()
                await asyncio.sleep(0.2)

            except Exception as e:
                print("Unexpected error:", e)
                await asyncio.sleep(0.2)

# ----------------------------
# Entry point
# ----------------------------
if __name__ == "__main__":
    import tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        asyncio.run(send_coordinates())
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

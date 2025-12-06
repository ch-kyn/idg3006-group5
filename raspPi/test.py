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
# RESET PIN
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

def invert_quat(q):
    return quat_conjugate(q)

def quat_mul(q1, q2):
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return (
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
    )

def rotate_vector_by_quat(v, q):
    vx, vy, vz = v
    vq = (vx, vy, vz, 0.0)
    qc = quat_conjugate(q)
    return quat_mul(quat_mul(q, vq), qc)[:3]

# ----------------------------
# Rotate sensor vector for 90° left sensor placement
# ----------------------------
def rotate_z_90_left(v):
    x, y, z = v
    # Rotate 90° left around Z axis
    return (-y, x, z)

# ----------------------------
# Convert vector to lat/lon
# ----------------------------
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
    return lat, lon

# ----------------------------
# CONFIG
# ----------------------------
sensor_axis = (1.0, 0.0, 0.0)  # your sensor's forward direction
calibration_quat = (0, 0, 0, 1)  # identity

# ----------------------------
# Calibration
# ----------------------------
def calibrate(q_current):
    global calibration_quat
    q_target = (0, 0, 0, 1)  # Null Island alignment
    calibration_quat = quat_mul(invert_quat(q_current), q_target)
    print("\n🎯 Calibration set! Orientation now aligns to 0° lat / 0° lon.\n")

# ----------------------------
# Keyboard helper
# ----------------------------
def key_pressed():
    dr, dw, de = select.select([sys.stdin], [], [], 0)
    return dr != []

# ----------------------------
# Main async loop
# ----------------------------
async def send_coordinates():
    global sensor
    async with websockets.connect(WS_URI) as websocket:
        print("Connected to WebSocket server!")

        while True:
            # Calibration trigger
            if key_pressed():
                ch = sys.stdin.read(1)
                if ch.lower() == "c":
                    calibrate(sensor.quaternion)

            try:
                # Read quaternion
                x, y, z, w = sensor.quaternion
                if (x, y, z, w) == (0, 0, 0, 0):
                    await asyncio.sleep(0.01)
                    continue

                raw_q = (x, y, z, w)
                corrected_q = quat_mul(calibration_quat, raw_q)

                # Rotate forward vector by quaternion
                world_vec = rotate_vector_by_quat(sensor_axis, corrected_q)

                # Apply 90° left sensor rotation
                world_vec = rotate_z_90_left(world_vec)

                # Convert to lat/lon
                lat, lon = vector_to_latlon(world_vec)
                if lat is None:
                    await asyncio.sleep(0.01)
                    continue

                msg = json.dumps({
                    "lat": round(lat, 3),
                    "lon": round(lon, 3),
                })
                await websocket.send(msg)
                print("Sent:", msg)

                await asyncio.sleep(0.1)  # ~10 Hz

            except OSError:
                print("\n⚠️ I2C error — resetting sensor…")
                sensor = init_sensor()
                await asyncio.sleep(0.2)
            except Exception as e:
                print("Unexpected error:", e)
                await asyncio.sleep(0.2)

# ----------------------------
# Entry
# ----------------------------
if __name__ == "__main__":
    import tty, termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        asyncio.run(send_coordinates())
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

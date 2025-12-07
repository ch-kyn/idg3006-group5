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
WS_URI = "ws://10.22.62.39:8765"

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
def quat_mul(q1, q2):
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return (
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
    )

def quat_conjugate(q):
    x, y, z, w = q
    return (-x, -y, -z, w)

def rotate_vector(q, v):
    # q must be (x, y, z, w)
    vx, vy, vz = v
    vq = (vx, vy, vz, 0)
    return quat_mul(quat_mul(q, vq), quat_conjugate(q))[:3]

# ----------------------------
# DEVICE ORIENTATION VECTORS
# ----------------------------
# Your sensor is rotated 90° LEFT
# → OLD forward(+Z) becomes left(-X)
# → OLD up(+Y) stays the same

UP_VEC = (0, 1, 0)
FORWARD_VEC = (-1, 0, 0)   # rotated 90° left

lat_offset = 0.0
lon_offset = 0.0
calibration_quat = (0, 0, 0, 1)

# ----------------------------
# Convert vectors → lat/lon
# ----------------------------
def vectors_to_lat_lon(up, forward):
    ux, uy, uz = up
    fx, fy, fz = forward

    uz = max(-1, min(1, uz))
    latitude = math.degrees(math.asin(-uz))

    lon_rad = math.atan2(fy, fx)
    longitude = -math.degrees(lon_rad)

    if longitude > 180: longitude -= 360
    if longitude < -180: longitude += 360

    return latitude, longitude

# ----------------------------
# Calibration
# ----------------------------
def calibrate(q_current, lat_unoffset, lon_unoffset):
    global calibration_quat, lat_offset, lon_offset

    # Make current orientation be identity
    calibration_quat = quat_conjugate(q_current)

    # Adjust offsets so current pointing becomes (0,0)
    lat_offset = -lat_unoffset
    lon_offset = -lon_unoffset

    print("\n🎯 Calibration complete!")
    print(f"lat_offset={lat_offset}, lon_offset={lon_offset}\n")

# ----------------------------
# Keyboard helper
# ----------------------------
def key_pressed():
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    return bool(dr)

# ----------------------------
# Main loop
# ----------------------------
async def send_coordinates():
    global sensor

    async with websockets.connect(WS_URI) as websocket:
        print("Connected to WebSocket server!")

        while True:
            try:
                x, y, z, w = sensor.quaternion
                if (x, y, z, w) == (0, 0, 0, 0):
                    await asyncio.sleep(0.01)
                    continue

                raw_q = (x, y, z, w)

                # Apply calibration quaternion
                corrected_q = quat_mul(calibration_quat, raw_q)

                # Rotate the UP and FORWARD vectors into world space
                up_w = rotate_vector(corrected_q, UP_VEC)
                forward_w = rotate_vector(corrected_q, FORWARD_VEC)

                # Convert to lat/lon
                lat, lon = vectors_to_lat_lon(up_w, forward_w)

                # Apply zero-point offsets
                lat_unoffset = lat
                lon_unoffset = lon
                lat += lat_offset
                lon += lon_offset

                # Handle calibration key AFTER computing coords
                if key_pressed():
                    ch = sys.stdin.read(1)
                    if ch.lower() == "c":
                        calibrate(corrected_q, lat_unoffset, lon_unoffset)
                        continue

                msg = json.dumps({
                    "lat": round(lat, 3),
                    "lon": round(lon, 3),
                })

                await websocket.send(msg)
                print("Sent:", msg)

                await asyncio.sleep(0.1)

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

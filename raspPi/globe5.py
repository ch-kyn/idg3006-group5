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

# ----------------------------
# Rotate vector by quaternion
# ----------------------------
def rotate_vector(quat, v):
    w, x, y, z = quat
    vx, vy, vz = v
    rx = (1 - 2*(y*y + z*z))*vx + 2*(x*y - w*z)*vy + 2*(x*z + w*y)*vz
    ry = 2*(x*y + w*z)*vx + (1 - 2*(x*x + z*z))*vy + 2*(y*z - w*x)*vz
    rz = 2*(x*z - w*y)*vx + 2*(y*z + w*x)*vy + (1 - 2*(x*x + y*y))*vz
    return rx, ry, rz

# ----------------------------
# Device reference vectors
# ----------------------------
UP_VEC = (0, 1, 0)       # points "up" on device
FORWARD_VEC = (0, 0, 1)  # points "forward" on device

# ----------------------------
# Convert rotated vectors to lat/lon
# ----------------------------
def vectors_to_lat_lon(up, forward):
    ux, uy, uz = up
    fx, fy, fz = forward

    # Clamp uz to [-1,1] to avoid asin domain errors
    uz = max(-1.0, min(1.0, uz))

    # Latitude: angle from equator plane
    latitude = math.degrees(math.asin(-uz))

    # Longitude: projection of forward vector onto XY-plane
    lon_rad = math.atan2(fy, fx)
    longitude = math.degrees(-lon_rad)

    # Normalize longitude to -180..180
    if longitude > 180:
        longitude -= 360
    elif longitude < -180:
        longitude += 360

    return latitude, longitude

# ----------------------------
# Calibration storage
# ----------------------------
calibration_quat = (0, 0, 0, 1)  # identity
lat_ref = 0.0
lon_ref = 0.0

# ----------------------------
# Keyboard helper
# ----------------------------
def key_pressed():
    dr, dw, de = select.select([sys.stdin], [], [], 0)
    return dr != []

# ----------------------------
# Calibrate orientation + reference lat/lon
# ----------------------------
def calibrate(q_current, lat, lon):
    global calibration_quat, lat_ref, lon_ref
    calibration_quat = quat_mul(invert_quat(q_current), (0,0,0,1))
    lat_ref = lat
    lon_ref = lon
    print("\n🎯 Calibration complete!")
    print(f"Reference lat/lon: {lat_ref:.6f}, {lon_ref:.6f}\n")

# ----------------------------
# Main async loop
# ----------------------------
async def send_coordinates():
    global sensor, calibration_quat, lat_ref, lon_ref
    async with websockets.connect(WS_URI) as websocket:
        print("Connected to WebSocket server!")

        while True:
            try:
                # Read quaternion
                x, y, z, w = sensor.quaternion
                if (x, y, z, w) == (0, 0, 0, 0):
                    await asyncio.sleep(0.01)
                    continue

                raw_q = (x, y, z, w)

                # Apply calibration
                corrected_q = quat_mul(calibration_quat, raw_q)

                # Rotate reference vectors
                up_world = rotate_vector(corrected_q, UP_VEC)
                forward_world = rotate_vector(corrected_q, FORWARD_VEC)

                # Compute lat/lon
                lat, lon = vectors_to_lat_lon(up_world, forward_world)

                # Apply calibration reference
                lat_cal = lat - lat_ref
                lon_cal = lon - lon_ref
                # Wrap longitude difference to [-180,180]
                lon_cal = ((lon_cal + 180) % 360) - 180

                # Handle calibration key AFTER computing lat/lon
                if key_pressed():
                    ch = sys.stdin.read(1)
                    if ch.lower() == "c":
                        calibrate(raw_q, lat, lon)
                        continue  # skip sending this sample

                msg = json.dumps({
                    "lat": round(lat_cal, 3),
                    "lon": round(lon_cal, 3),
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
# Entry point
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

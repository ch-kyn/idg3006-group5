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

def rotate_vector(quat, v):
    x, y, z, w = quat
    vx, vy, vz = v
    rx = (1 - 2*(y*y + z*z))*vx + 2*(x*y - w*z)*vy + 2*(x*z + w*y)*vz
    ry = 2*(x*y + w*z)*vx + (1 - 2*(x*x + z*z))*vy + 2*(y*z - w*x)*vz
    rz = 2*(x*z - w*y)*vx + 2*(y*z + w*x)*vy + (1 - 2*(x*x + y*y))*vz
    return rx, ry, rz

# ----------------------------
# Reference vectors
# ----------------------------
UP_VEC = (0, 1, 0)       # up on device
FORWARD_VEC = (0, 0, 1)  # forward on device

# Calibration offsets
calibration_quat = (0,0,0,1)
lat_offset = 0.0
lon_offset = 0.0

# ----------------------------
# Lat/Lon computation
# ----------------------------
def vectors_to_lat_lon(up, forward):
    # latitude from up vector z-component
    ux, uy, uz = up
    lat = math.degrees(math.asin(-uz))

    # longitude from forward vector projected onto XY-plane
    fx, fy, fz = forward
    lon = math.degrees(math.atan2(fy, fx))
    if lon > 180: lon -= 360
    if lon < -180: lon += 360

    return lat, lon

# ----------------------------
# Calibration
# ----------------------------
def calibrate(raw_q, lat_measured, lon_measured):
    global calibration_quat, lat_offset, lon_offset
    calibration_quat = quat_mul(invert_quat(raw_q), (0,0,0,1))
    lat_offset = -lat_measured
    lon_offset = -lon_measured
    print("\n🎯 Calibration complete!")
    print(f"lat_offset={lat_offset}, lon_offset={lon_offset}\n")

# ----------------------------
# Keyboard helper
# ----------------------------
def key_pressed():
    dr, dw, de = select.select([sys.stdin], [], [], 0)
    return dr != []

# ----------------------------
# Main loop
# ----------------------------
async def send_coordinates():
    global sensor, lat_offset, lon_offset
    async with websockets.connect(WS_URI) as websocket:
        print("Connected to WebSocket server!")

        while True:
            try:
                x, y, z, w = sensor.quaternion
                if (x, y, z, w) == (0,0,0,0):
                    await asyncio.sleep(0.01)
                    continue
                raw_q = (x,y,z,w)

                # Apply calibration
                corrected_q = quat_mul(calibration_quat, raw_q)

                # Rotate reference vectors
                up_world = rotate_vector(corrected_q, UP_VEC)
                forward_world = rotate_vector(corrected_q, FORWARD_VEC)

                # Compute lat/lon
                lat, lon = vectors_to_lat_lon(up_world, forward_world)

                # Apply offsets
                lat += lat_offset
                lon += lon_offset

                # Handle calibration key
                if key_pressed():
                    ch = sys.stdin.read(1)
                    if ch.lower() == "c":
                        calibrate(raw_q, lat, lon)
                        continue  # skip sending this sample

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

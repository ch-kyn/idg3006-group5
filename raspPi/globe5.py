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
# Quaternion helpers (q = (x,y,z,w))
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
    # rotate vector v by quaternion q (q is x,y,z,w)
    vx, vy, vz = v
    vq = (vx, vy, vz, 0.0)
    tmp = quat_mul(q, vq)
    res = quat_mul(tmp, quat_conjugate(q))
    return res[:3]

# ----------------------------
# Device vectors (adjust if your mounting differs)
# ----------------------------
UP_VEC = (0, 1, 0)        # device "up"
FORWARD_VEC = (0, 0, 1)  # device "forward" after your 90° left mounting

# Calibration state
lat_offset = 0.0
lon_offset = 0.0
calibration_quat = (0, 0, 0, 1)

# ----------------------------
# Convert world up/forward vectors -> lat/lon (un-offset)
# ----------------------------
def vectors_to_lat_lon(up, forward):
    ux, uy, uz = up
    fx, fy, fz = forward

    uz = max(-1.0, min(1.0, uz))
    lat = math.degrees(math.asin(-uz))

    lon_rad = math.atan2(fy, fx)
    lon = -math.degrees(lon_rad)

    # normalize lon to [-180, 180)
    lon = (lon + 180.0) % 360.0 - 180.0

    return lat, lon

# ----------------------------
# Calibration (uses corrected quaternion and un-offset lat/lon)
# ----------------------------
def calibrate(q_current, lat_unoffset, lon_unoffset):
    global calibration_quat, lat_offset, lon_offset
    # make current orientation identity (so quat_mul(calibration_quat, q_current) ~= identity)
    calibration_quat = quat_conjugate(q_current)
    # coordinate offsets so the present un-offset lat/lon become (0,0)
    lat_offset = -lat_unoffset
    lon_offset = -lon_unoffset
    # normalize lon_offset into [-180,180)
    lon_offset = (lon_offset + 180.0) % 360.0 - 180.0
    print("\n🎯 Calibration complete!")
    print(f"lat_offset={lat_offset:.6f}, lon_offset={lon_offset:.6f}\n")

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
    global sensor, lat_offset, lon_offset, calibration_quat
    async with websockets.connect(WS_URI) as websocket:
        print("Connected to WebSocket server!")

        while True:
            try:
                # read quaternion from sensor (x,y,z,w)
                x, y, z, w = sensor.quaternion
                if (x, y, z, w) == (0, 0, 0, 0):
                    await asyncio.sleep(0.01)
                    continue
                raw_q = (x, y, z, w)

                # apply calibration quaternion to bring current orientation to our reference frame
                corrected_q = quat_mul(calibration_quat, raw_q)

                # rotate device reference vectors into world
                up_world = rotate_vector(corrected_q, UP_VEC)
                forward_world = rotate_vector(corrected_q, FORWARD_VEC)

                # compute un-offset lat/lon
                lat_unoffset, lon_unoffset = vectors_to_lat_lon(up_world, forward_world)

                # BEFORE applying offsets, allow calibration if user pressed C
                if key_pressed():
                    ch = sys.stdin.read(1)
                    if ch.lower() == "c":
                        # debug info printed for you
                        print("DEBUG (pre-cal): up_world =", [round(v,4) for v in up_world],
                              "forward_world =", [round(v,4) for v in forward_world])
                        print("DEBUG (pre-cal): lat_unoffset =", round(lat_unoffset,6),
                              "lon_unoffset =", round(lon_unoffset,6))
                        calibrate(corrected_q, lat_unoffset, lon_unoffset)
                        continue  # skip sending this sample

                # apply offsets
                lat = lat_unoffset + lat_offset
                lon = lon_unoffset + lon_offset

                # normalize longitude after applying offsets to avoid large values
                lon = (lon + 180.0) % 360.0 - 180.0

                # clamp latitude strictly to [-90,90] for safety
                lat = max(-90.0, min(90.0, lat))

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

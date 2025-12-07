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

def rotate_vector_by_quat(v, q):
    vx, vy, vz = v
    vq = (vx, vy, vz, 0.0)
    qc = quat_conjugate(q)
    return quat_mul(quat_mul(q, vq), qc)[:3]

# ----------------------------
# Rotate vector function
# ----------------------------
def rotate_vector(quat, v):
    w, x, y, z = quat
    vx, vy, vz = v
    rx = (1 - 2*(y*y + z*z))*vx + 2*(x*y - w*z)*vy + 2*(x*z + w*y)*vz
    ry = 2*(x*y + w*z)*vx + (1 - 2*(x*x + z*z))*vy + 2*(y*z - w*x)*vz
    rz = 2*(x*z - w*y)*vx + 2*(y*z + w*x)*vy + (1 - 2*(x*x + y*y))*vz
    return rx, ry, rz

# ----------------------------
# Vectors to latitude/longitude
# ----------------------------
UP_VEC = (0, 1, 0)
FORWARD_VEC = (0, 0, 1)

def vectors_to_lat_lon(up, forward):
    """
    Compute geographic latitude and longitude from rotated UP and FORWARD vectors.
    Latitude: north/south from UP vector Y
    Longitude: east/west from FORWARD vector X/Z
    """
    ux, uy, uz = up
    fx, fy, fz = forward

    # Latitude: positive north, negative south
    uy = max(-1.0, min(1.0, uy))
    latitude = math.degrees(math.asin(uy))

    # Longitude: atan2 of X/Z from FORWARD vector for east/west heading
    longitude = math.degrees(math.atan2(fx, fz))

    # Normalize longitude
    if longitude > 180:
        longitude -= 360
    elif longitude < -180:
        longitude += 360

    return latitude, longitude


# ----------------------------
# CONFIG
# ----------------------------
calibration_quat = (0, 0, 0, 1)

def calibrate(q_current):
    global calibration_quat
    q_target = (0, 0, 0, 1)
    calibration_quat = quat_mul(invert_quat(q_current), q_target)
    print("\n🎯 Calibration set! Orientation now aligns to 0° lat / 0° lon.\n")

def key_pressed():
    dr, dw, de = select.select([sys.stdin], [], [], 0)
    return dr != []

# Offset latitude with proper polar wrap
def offset_lat(lat, offset):
    lat_new = lat + offset
    while lat_new > 90 or lat_new < -90:
        if lat_new > 90:
            lat_new = 180 - lat_new  # reflect over north pole
        elif lat_new < -90:
            lat_new = -180 - lat_new  # reflect over south pole
    return lat_new

# ----------------------------
# Main loop
# ----------------------------
async def send_coordinates():
    global sensor
    async with websockets.connect(WS_URI) as websocket:
        print("Connected to WebSocket server!")

        while True:
            if key_pressed():
                ch = sys.stdin.read(1)
                if ch.lower() == "c":
                    calibrate(sensor.quaternion)

            try:
                x, y, z, w = sensor.quaternion
                if (x, y, z, w) == (0, 0, 0, 0):
                    await asyncio.sleep(0.01)
                    continue

                raw_q = (x, y, z, w)
                corrected_q = quat_mul(calibration_quat, raw_q)

                up_world = rotate_vector(corrected_q, UP_VEC)
                forward_world = rotate_vector(corrected_q, FORWARD_VEC)

                lat, lon = vectors_to_lat_lon(up_world, forward_world)

                # Force latitude offset with proper hemisphere handling
                lat = offset_lat(lat, 65)

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

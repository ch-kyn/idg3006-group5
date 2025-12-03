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
WS_URI = "ws://10.22.16.94:8765"

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
    time.sleep(0.1)
    reset_pin.value = True
    time.sleep(1.0)
    sensor = BNO08X_I2C(i2c, address=0x4A)
    time.sleep(0.2)
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

def normalize(v):
    mag = math.sqrt(sum([x*x for x in v]))
    if mag == 0:
        return (0,0,0)
    return tuple(x/mag for x in v)

def dot(a,b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def sub(a,b):
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])

def scale(v,s):
    return (v[0]*s, v[1]*s, v[2]*s)

# ----------------------------
# CONFIG
# ----------------------------
sensor_axis = (0.0, 0.0, -1.0)  # points roughly downward
calibration_quat = (0,0,0,1)

# Two-point calibration storage
north_unit = None
east_unit = None
ref_axis = None

# ----------------------------
# Keyboard helper
# ----------------------------
def key_pressed():
    dr, dw, de = select.select([sys.stdin], [], [], 0)
    return dr != []

# ----------------------------
# Calibration with timeout
# ----------------------------
async def calibrate_point(point_name, timeout=30):
    global north_unit, east_unit, ref_axis
    print(f"Point at {point_name} and press 'c' (or wait {timeout}s to skip)")
    start_time = time.time()
    while True:
        if key_pressed():
            ch = sys.stdin.read(1)
            if ch.lower() == 'c':
                q = sensor.quaternion
                if not q or len(q)!=4 or q==(0,0,0,0):
                    continue
                world_vec = rotate_vector_by_quat(sensor_axis, q)
                world_vec = normalize(world_vec)
                if point_name=="North Pole":
                    north_unit = world_vec
                    print("✅ North vector recorded")
                elif point_name=="Null Island":
                    proj = sub(world_vec, scale(north_unit, dot(world_vec, north_unit)))
                    east_unit = normalize(proj)
                    ref_axis = east_unit
                    print("✅ East/reference vector recorded")
                return
        if time.time() - start_time > timeout:
            print(f"⏱ Timeout reached for {point_name}, skipping calibration.")
            return
        await asyncio.sleep(0.05)

# ----------------------------
# Convert vector to lat/lon using two-point calibration
# ----------------------------
def vector_to_latlon_2point(v):
    if north_unit is None or east_unit is None or ref_axis is None:
        return None,None
    v = normalize(v)
    lat = math.degrees(math.asin(dot(v, north_unit)))
    lon = math.degrees(math.atan2(dot(v, east_unit), dot(v, ref_axis)))
    lon = (lon+180)%360 -180
    return lat, lon

# ----------------------------
# Main loop
# ----------------------------
async def send_coordinates():
    global sensor
    async with websockets.connect(WS_URI) as websocket:
        print("Connected to WebSocket server!")

        # Two-point calibration
        await calibrate_point("North Pole")
        await calibrate_point("Null Island")

        print("✅ Two-point calibration done! Sending coordinates...")

        while True:
            try:
                q = sensor.quaternion
                if not q or len(q)!=4 or q==(0,0,0,0):
                    await asyncio.sleep(0.01)
                    continue
                world_vec = rotate_vector_by_quat(sensor_axis, q)
                lat, lon = vector_to_latlon_2point(world_vec)
                if lat is None or lon is None:
                    # fallback if calibration skipped
                    lat, lon = 0.0, 0.0
                msg = json.dumps({"lat": round(lat,3), "lon": round(lon,3)})
                await websocket.send(msg)
                print("Sent:", msg)
                await asyncio.sleep(0.1)
            except OSError:
                print("\n⚠️ I2C error — resetting sensor…")
                time.sleep(1.0)
                sensor = init_sensor()
                await asyncio.sleep(0.2)
            except Exception as e:
                print("Unexpected error:", e)
                await asyncio.sleep(0.2)

# ----------------------------
# Entry
# ----------------------------
if __name__=="__main__":
    import tty, termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        asyncio.run(send_coordinates())
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

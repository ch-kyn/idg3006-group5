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
    mag = math.sqrt(sum(x*x for x in v))
    if mag == 0:
        return (0,0,0)
    return tuple(x/mag for x in v)

def dot(a,b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def cross(a,b):
    return (
        a[1]*b[2]-a[2]*b[1],
        a[2]*b[0]-a[0]*b[2],
        a[0]*b[1]-a[1]*b[0]
    )

def sub(a,b):
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])

def scale(v,s):
    return (v[0]*s, v[1]*s, v[2]*s)

# ----------------------------
# CONFIG
# ----------------------------
sensor_axis = (0.0, 0.0, -1.0)  # sensor pointing downward

north_unit = None
east_unit = None
ref_axis = None
origin_vec = None  # vector at Null Island for zero reference

# ----------------------------
# Keyboard helper
# ----------------------------
def key_pressed():
    dr, dw, de = select.select([sys.stdin], [], [], 0)
    return dr != []

# ----------------------------
# Two-point calibration
# ----------------------------
async def calibrate_point(name, timeout=30):
    global north_unit, east_unit, ref_axis, origin_vec
    print(f"Point at {name} and press 'c' (timeout {timeout}s)")
    start = time.time()
    while True:
        if key_pressed():
            ch = sys.stdin.read(1)
            if ch.lower()=='c':
                q = sensor.quaternion
                if not q or len(q)!=4 or q==(0,0,0,0):
                    continue
                vec = rotate_vector_by_quat(sensor_axis,q)
                vec = normalize(vec)
                if name=="North Pole":
                    north_unit = vec
                    print("✅ North vector recorded")
                elif name=="Null Island":
                    origin_vec = vec  # store origin for zero
                    ref_axis = normalize(cross(north_unit, origin_vec))
                    east_unit = normalize(cross(ref_axis, north_unit))
                    print("✅ Null Island / east/reference vector recorded")
                return
        if time.time()-start > timeout:
            print(f"⏱ Timeout reached for {name}, skipping")
            return
        await asyncio.sleep(0.05)

# ----------------------------
# Convert vector to lat/lon relative to Null Island
# ----------------------------
def vector_to_latlon_2point(v):
    if not north_unit or not east_unit or not ref_axis or origin_vec is None:
        return None, None
    v = normalize(v)
    lat = math.degrees(math.asin(dot(v, north_unit)))
    lon = math.degrees(math.atan2(dot(v, east_unit), dot(v, ref_axis)))
    
    # subtract origin longitude to make Null Island (0,0)
    lon_origin = math.degrees(math.atan2(dot(origin_vec, east_unit),
                                         dot(origin_vec, ref_axis)))
    lon -= lon_origin
    
    # normalize longitude to -180..180
    lon = (lon + 180) % 360 - 180
    return lat, lon

# ----------------------------
# Main loop
# ----------------------------
async def send_coordinates():
    global sensor
    async with websockets.connect(WS_URI) as websocket:
        print("Connected to WebSocket server!")

        # Run two-point calibration
        await calibrate_point("North Pole")
        await calibrate_point("Null Island")
        print("✅ Two-point calibration done, sending coordinates...")

        while True:
            try:
                q = sensor.quaternion
                if not q or len(q)!=4 or q==(0,0,0,0):
                    await asyncio.sleep(0.01)
                    continue
                vec = rotate_vector_by_quat(sensor_axis,q)
                lat, lon = vector_to_latlon_2point(vec)
                if lat is None or lon is None:
                    lat, lon = 0.0, 0.0
                msg = json.dumps({"lat":round(lat,3),"lon":round(lon,3)})
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
if __name__=="__main__":
    import tty, termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        asyncio.run(send_coordinates())
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

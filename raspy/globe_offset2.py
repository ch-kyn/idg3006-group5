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

def normalize(v):
    mag = math.sqrt(sum(x*x for x in v))
    if mag == 0:
        return (0.0, 0.0, 0.0)
    return tuple(x/mag for x in v)

# ----------------------------
# Global config
# ----------------------------
sensor_axis = (0.0, 0.0, -1.0)  # sensor pointing downward
calibration_quat = (0, 0, 0, 1)  # identity
calibration_points = []

# ----------------------------
# Keyboard helper
# ----------------------------
def key_pressed():
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    return dr != []

# ----------------------------
# 4-point globe calibration
# ----------------------------
GLOBE_POINTS = [
    "Equator & Prime Meridian (0°, 0°)",
    "Equator & 90°E (0°, 90°E)",
    "Equator & 90°W (0°, 90°W)",
    "North Pole (90°, 0°)"
]

def record_calibration_point():
    q = sensor.quaternion
    if not q or len(q)!=4 or q==(0,0,0,0):
        print("❌ Invalid quaternion, try again")
        return
    calibration_points.append(q)
    print(f"✅ Calibration point recorded ({len(calibration_points)}/4): {GLOBE_POINTS[len(calibration_points)-1]}")
    if len(calibration_points) == 4:
        print("🎯 4 points recorded, press 'a' to apply calibration")

def apply_calibration():
    global calibration_quat
    if len(calibration_points) != 4:
        print("⚠️ You must record all 4 calibration points first!")
        return
    # Basic method: invert the first point
    # Can be improved with quaternion averaging
    calibration_quat = invert_quat(calibration_points[0])
    print("🎯 Calibration applied! Sensor now aligned globally.")

# ----------------------------
# Convert vector to lat/lon
# ----------------------------
def vector_to_latlon(v):
    v = normalize(v)
    vx, vy, vz = v
    lat = math.degrees(math.asin(-vz))  # down vector toward Earth center
    lon = math.degrees(math.atan2(vy, vx))
    lon = (lon + 180) % 360 - 180
    return lat, lon

# ----------------------------
# Main loop
# ----------------------------
async def send_coordinates():
    global sensor
    async with websockets.connect(WS_URI) as websocket:
        print("Connected! Press 'c' to record calibration points, 'a' to apply calibration.")

        while True:
            if key_pressed():
                ch = sys.stdin.read(1)
                if ch.lower() == "c":
                    record_calibration_point()
                elif ch.lower() == "a":
                    apply_calibration()

            try:
                x, y, z, w = sensor.quaternion
                if (x, y, z, w) == (0,0,0,0):
                    await asyncio.sleep(0.01)
                    continue
                raw_q = (x, y, z, w)
                corrected_q = quat_mul(calibration_quat, raw_q)
                world_vec = rotate_vector_by_quat(sensor_axis, corrected_q)
                lat, lon = vector_to_latlon(world_vec)
                msg = json.dumps({"lat": round(lat,3), "lon": round(lon,3)})
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

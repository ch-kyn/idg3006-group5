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
# Global configuration
# ----------------------------
sensor_axis = (0.0, 0.0, -1.0)  # sensor pointing down
calibration_quat = (0,0,0,1)    # identity by default

# ----------------------------
# Keyboard helper
# ----------------------------
def key_pressed():
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    return dr != []

# ----------------------------
# Multi-point calibration (optional)
# ----------------------------
calibration_vectors = []

def calibrate_point():
    """
    Press 'c' while pointing sensor in a known orientation.
    Collect multiple points for better calibration.
    """
    global calibration_vectors
    q = sensor.quaternion
    if not q or len(q)!=4 or q==(0,0,0,0):
        print("❌ Invalid quaternion, try again")
        return
    calibration_vectors.append(q)
    print(f"✅ Calibration point recorded ({len(calibration_vectors)} points)")

def compute_calibration():
    """
    Compute average calibration quaternion from multiple points.
    For simplicity, we just take the first point if only one is recorded.
    """
    global calibration_quat, calibration_vectors
    if not calibration_vectors:
        print("⚠️ No calibration points recorded")
        return
    # For real applications, you can compute best-fit rotation here
    calibration_quat = invert_quat(calibration_vectors[0])
    print("🎯 Calibration applied!")

# ----------------------------
# Convert rotated vector to global lat/lon
# ----------------------------
def vector_to_latlon(v):
    v = normalize(v)
    vx, vy, vz = v

    # Latitude from down vector
    lat = math.degrees(math.asin(-vz))  # negative because down points toward Earth center

    # Longitude from XY-plane
    lon = math.degrees(math.atan2(vy, vx))

    # Normalize longitude to -180..180
    lon = (lon + 180) % 360 - 180
    return lat, lon

# ----------------------------
# Main loop
# ----------------------------
async def send_coordinates():
    global sensor
    async with websockets.connect(WS_URI) as websocket:
        print("Connected to WebSocket server!")
        print("Press 'c' to record calibration points, then 'a' to apply calibration")

        while True:
            # Keyboard check
            if key_pressed():
                ch = sys.stdin.read(1)
                if ch.lower() == "c":
                    calibrate_point()
                elif ch.lower() == "a":
                    compute_calibration()

            try:
                # Read quaternion
                x, y, z, w = sensor.quaternion
                if (x, y, z, w) == (0,0,0,0):
                    await asyncio.sleep(0.01)
                    continue
                raw_q = (x, y, z, w)

                # Apply calibration
                corrected_q = quat_mul(calibration_quat, raw_q)

                # Rotate sensor down vector into world frame
                world_vec = rotate_vector_by_quat(sensor_axis, corrected_q)

                # Convert to lat/lon
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

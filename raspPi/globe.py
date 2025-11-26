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
WS_URI = "ws://192.168.1.100:8765"  # replace with your server

# ----------------------------
# RESET PIN (REQUIRED)
# ----------------------------
reset_pin = digitalio.DigitalInOut(board.D17)  # GPIO17 (Pin 11)
reset_pin.direction = digitalio.Direction.OUTPUT

# ----------------------------
# I2C INIT
# ----------------------------
i2c = busio.I2C(board.SCL, board.SDA)

def init_sensor():
    print("Initializing BNO08X...")

    # Hardware reset pulse
    reset_pin.value = False
    time.sleep(0.01)
    reset_pin.value = True
    time.sleep(0.25)

    sensor = BNO08X_I2C(i2c, address=0x4A)
    sensor.enable_feature(BNO_REPORT_ROTATION_VECTOR)
    return sensor

sensor = init_sensor()

# ----------------------------
# Quaternion + vector helpers
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
        w1*w2 - x1*x2 - y1*y2 - z1*z2
    )

def rotate_vector_by_quat(v, q):
    vx, vy, vz = v
    vq = (vx, vy, vz, 0.0)
    qc = quat_conjugate(q)
    return quat_mul(quat_mul(q, vq), qc)[:3]

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

    if lon >= 180: lon -= 360
    if lon < -180: lon += 360

    return lat, lon

# ----------------------------
# CONFIG
# ----------------------------
sensor_axis = (1.0, 0.0, 0.0)  # +X is pointing direction
calibration_quat = (0.0, 0.0, 0.0, 1.0)  # identity

def calibrate(q):
    """Set calibration so this quaternion becomes zero orientation."""
    global calibration_quat
    calibration_quat = invert_quat(q)
    print("\n🎯 Calibration set! Current orientation is now 0° latitude / 0° longitude.\n")

# ----------------------------
# Keyboard input helper
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
            # --- Keyboard calibration ---
            if key_pressed():
                ch = sys.stdin.read(1)
                if ch.lower() == "c":
                    calibrate(sensor.quaternion)

            try:
                # Read quaternion
                x, y, z, w = sensor.quaternion
                if (x, y, z, w) == (0.0, 0.0, 0.0, 0.0):
                    await asyncio.sleep(0.01)
                    continue

                raw_q = (x, y, z, w)
                corrected_q = quat_mul(calibration_quat, raw_q)
                world_vec = rotate_vector_by_quat(sensor_axis, corrected_q)
                lat, lon = vector_to_latlon(world_vec)
                if lat is None:
                    await asyncio.sleep(0.01)
                    continue

                # Send over WebSocket
                message = json.dumps({"lat": lat, "lon": lon})
                await websocket.send(message)
                print(f"Sent: {message}")

                await asyncio.sleep(0.1)  # update rate ~10 Hz
            except OSError:
                print("\n⚠️ I2C hiccup — resetting sensor...")
                sensor = init_sensor()
                await asyncio.sleep(0.2)
            except Exception as e:
                print("Unexpected error:", e)
                await asyncio.sleep(0.2)

# ----------------------------
# Entry point
# ----------------------------
if __name__ == "__main__":
    # Make stdin non-blocking for keyboard input
    import tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        asyncio.run(send_coordinates())
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

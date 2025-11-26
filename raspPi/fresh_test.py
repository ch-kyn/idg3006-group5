import time
import math
import board
import busio
import digitalio
import sys
import select
import tty
import termios

from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR


# ----------------------------
#  RESET PIN (REQUIRED)
# ----------------------------
reset_pin = digitalio.DigitalInOut(board.D17)  # GPIO17 (Pin 11)
reset_pin.direction = digitalio.Direction.OUTPUT


# ----------------------------
#  I2C INIT
# ----------------------------
i2c = busio.I2C(board.SCL, board.SDA)


def init_sensor():
    print("Initializing BNO08X...")

    # Hardware reset pulse
    reset_pin.value = False
    time.sleep(0.01)
    reset_pin.value = True
    time.sleep(0.25)

    # Create BNO sensor object (no reset_pin argument!)
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
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
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

    vx /= mag; vy /= mag; vz /= mag
    lat = math.degrees(math.asin(vz))
    lon = math.degrees(math.atan2(vy, vx))

    if lon >= 180: lon -= 360
    if lon < -180: lon += 360

    return lat, lon

# ----------------------------
# CONFIG
# ----------------------------
sensor_axis = (1.0, 0.0, 0.0)   # use +X as pointing direction

# Calibration quaternion (identity until set)
calibration_quat = (0.0, 0.0, 0.0, 1.0)


def calibrate(q):
    """Set calibration so this quaternion becomes zero orientation."""
    global calibration_quat
    calibration_quat = invert_quat(q)
    print("\n🎯 Calibration set! Current orientation is now 0° latitude / 0° longitude.\n")


# ----------------------------
# KEYBOARD INPUT
# ----------------------------
def key_pressed():
    dr, dw, de = select.select([sys.stdin], [], [], 0)
    return dr != []


while True:
    try:
        # Keyboard check
        if key_pressed():
            ch = sys.stdin.read(1)
            if ch.lower() == "c":
                calibrate((sensor.quaternion[0], sensor.quaternion[1],
                           sensor.quaternion[2], sensor.quaternion[3]))

        # Read quaternion
        x, y, z, w = sensor.quaternion
        if (x, y, z, w) == (0.0, 0.0, 0.0, 0.0):
            continue

        raw_q = (x, y, z, w)

        # Apply calibration
        corrected_q = quat_mul(calibration_quat, raw_q)

        # Rotate sensor axis → world vector
        world_vec = rotate_vector_by_quat(sensor_axis, corrected_q)

        # Convert to lat/lon
        lat, lon = vector_to_latlon(world_vec)
        if lat is None:
            continue

        current = (lat, lon)

        print(f"lat is: {lat}. lon is: {lon}")
    except OSError:
        print("\n⚠️  I2C hiccup — resetting sensor...")
        time.sleep(0.2)
        sensor = init_sensor()

    except Exception as e:
        print("Unexpected error:", e)
        time.sleep(0.2)

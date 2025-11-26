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
    """Initialize sensor with reset."""
    print("Initializing BNO08X...")
    sensor = BNO08X_I2C(i2c, reset_pin=reset_pin, address=0x4A, debug=False)
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


# ---------------------

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
# Quaternion Helpers
# ----------------------------
def quat_conjugate(q):
    x, y, z, w = q
    return (-x, -y, -z, w)


def quat_norm(q):
    x, y, z, w = q
    n = math.sqrt(x*x + y*y + z*z + w*w)
    if n == 0:
        return (0.0, 0.0, 0.0, 1.0)
    return (x/n, y/n, z/n, w/n)


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
    """Rotate vector v by quaternion q."""
    qn = quat_norm(q)
    vx, vy, vz = v
    vq = (vx, vy, vz, 0.0)
    qc = quat_conjugate(qn)
    r = quat_mul(quat_mul(qn, vq), qc)
    return r[:3]


# ======================================================
#           LATITUDE / LONGITUDE MATH
# ======================================================
# IMU +Y points toward SOUTH pole
# => North pole is -Y direction
#
# Outward direction vector is obtained by rotating (0,0,1)
# ======================================================

def vector_to_latlon(world_vec):
    wx, wy, wz = world_vec

    mag = math.sqrt(wx*wx + wy*wy + wz*wz)
    if mag == 0:
        return None, None

    wx /= mag
    wy /= mag
    wz /= mag

    # LATITUDE:
    # wy > 0 → pointing toward south (negative latitude)
    # wy < 0 → pointing toward north (positive latitude)
    lat = math.degrees(math.asin(-wy))

    # LONGITUDE:
    lon = math.degrees(math.atan2(wx, wz))

    return lat, lon


# ======================================================
#                SIMPLE CALIBRATION
# ======================================================
# Pressing “c” sets the current lat/lon to become (0,0)
# by storing offsets.
# ======================================================

sensor_axis = (0.0, 0.0, 1.0)  # outward direction
calib_lat = 0.0
calib_lon = 0.0


def calibrate(q_current):
    """Make CURRENT direction become (0°,0°)."""
    global calib_lat, calib_lon

    qc = quat_norm(q_current)

    # Outward vector
    world_vec = rotate_vector_by_quat(sensor_axis, qc)

    lat, lon = vector_to_latlon(world_vec)
    if lat is None:
        print("Calibration failed.")
        return

    # Store offsets
    calib_lat = lat
    calib_lon = lon

    print("\n🎯 Calibration OK — this direction is now (0°,0°)\n")


def key_pressed():
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    return dr != []


# ======================================================
#                MAIN LOOP
# ======================================================
def main_loop():
    global sensor, calib_lat, calib_lon

    print("Running. Press 'c' to calibrate (set current direction to 0° lat, 0° lon).")

    while True:
        if key_pressed():
            ch = sys.stdin.read(1)
            if ch.lower() == "c":
                calibrate(sensor.quaternion)

        try:
            x, y, z, w = sensor.quaternion
            if (x, y, z, w) == (0, 0, 0, 0):
                time.sleep(0.01)
                continue

            raw_q = quat_norm((x, y, z, w))

            # Outward direction
            world_vec = rotate_vector_by_quat(sensor_axis, raw_q)

            lat, lon = vector_to_latlon(world_vec)
            if lat is None:
                continue

            # Apply calibration offsets
            lat -= calib_lat
            lon -= calib_lon

            # Normalize lon into [-180, 180]
            if lon > 180:
                lon -= 360
            if lon < -180:
                lon += 360

            print(f"lat: {lat:.3f}, lon: {lon:.3f}")

            time.sleep(0.1)

        except OSError:
            print("\n⚠️ I2C error — resetting sensor…")
            sensor = init_sensor()
            time.sleep(0.2)

        except Exception as e:
            print("Unexpected error:", e)
            time.sleep(0.2)


# ======================================================
#                ENTRY POINT
# ======================================================
if __name__ == "__main__":
    import tty, termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        main_loop()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
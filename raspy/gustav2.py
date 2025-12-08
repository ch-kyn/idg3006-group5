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
    """
    Rotate vector v by quaternion q.
    """
    qn = quat_norm(q)
    vx, vy, vz = v
    vq = (vx, vy, vz, 0.0)
    qc = quat_conjugate(qn)
    r = quat_mul(quat_mul(qn, vq), qc)
    return r[:3]


# ======================================================
#   Axis remap: IMU frame -> Globe frame
# ======================================================
def imu_vec_to_globe_vec(imu_vec):
    """
    Map the IMU/world vector into the globe's logical axes.

    imu_vec = (wx, wy, wz) from rotate_vector_by_quat(sensor_axis, q)

    We discovered from WORLD_VEC inspection that the IMU's
    axes don't match how the globe is mounted. This mapping
    rotates them into a 'globe' frame where:

      - gz = pointing outward on the globe
      - gy = south pole axis
      - gx = around the equator

    Adjusted mapping (derived from your data):

        gx =  wz
        gy = -wx
        gz = -wy
    """
    wx, wy, wz = imu_vec
    gx = wz
    gy = -wx
    gz = -wy
    return (gx, gy, gz)


# ======================================================
#           Correct latitude/longitude
# ======================================================
def vector_to_latlon(globe_vec):
    gx, gy, gz = globe_vec

    # Normalize
    mag = math.sqrt(gx*gx + gy*gy + gz*gz)
    if mag == 0:
        return None, None
    gx /= mag
    gy /= mag
    gz /= mag

    # LATITUDE:
    # gy > 0  -> pointing more toward south pole  -> negative latitude
    # gy < 0  -> pointing more toward north pole  -> positive latitude
    lat = -math.degrees(math.asin(gy))

    # LONGITUDE:
    # rotation around the south-pole axis (gy)
    # using gx (equator direction) and gz (forward/back along equator)
    lon = math.degrees(math.atan2(gx, gz))

    return lat, lon


# ======================================================
#              Calibration (OPTION A: manual)
# ======================================================

# Z axis is the sensor's physical "outward" axis.
sensor_axis = (0.0, 0.0, 1.0)

# Identity quaternion
calibration_quat = (0, 0, 0, 1)


def quat_from_two_vectors(v_from, v_to):
    fx, fy, fz = v_from
    tx, ty, tz = v_to

    # Cross product
    cross = (
        fy*tz - fz*ty,
        fz*tx - fx*tz,
        fx*ty - fy*tx,
    )
    dot = fx*tx + fy*ty + fz*tz

    w = math.sqrt((fx*fx + fy*fy + fz*fz) *
                  (tx*tx + ty*ty + tz*tz)) + dot

    q = (cross[0], cross[1], cross[2], w)
    return quat_norm(q)


def calibrate(q_current):
    """
    Manual calibration (Option A):
    Make the CURRENT pointing direction = (lat=0°, lon=0°).

    That means:
      - Whatever the globe is pointing at when you press 'c'
        becomes the new geographic origin.
    """
    global calibration_quat

    qc = quat_norm(q_current)

    # Current IMU-space pointing direction of +Z
    fwd_imu = rotate_vector_by_quat(sensor_axis, qc)

    # Convert to globe-space vector
    fwd_globe = imu_vec_to_globe_vec(fwd_imu)

    mag = math.sqrt(sum(c*c for c in fwd_globe))
    if mag == 0:
        print("Calibration failed (zero vector)")
        return

    fwd_globe = (
        fwd_globe[0] / mag,
        fwd_globe[1] / mag,
        fwd_globe[2] / mag,
    )

    # Target: +X in globe-space is our definition of (0°,0°)
    target = (1.0, 0.0, 0.0)

    # Quaternion rotating current globe direction → target
    q_align = quat_from_two_vectors(fwd_globe, target)

    calibration_quat = q_align

    print("\n🎯 Full 3D calibration complete — this direction is now (0°,0°)\n")


# ----------------------------
# Keyboard Helper
# ----------------------------
def key_pressed():
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    return dr != []


# ----------------------------
# Main Loop
# ----------------------------
def main_loop():
    global sensor
    print("Running. Press 'c' to calibrate (OPTION A: current direction -> 0°,0°).")

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

            raw_q = (x, y, z, w)

            # Apply calibration
            corrected_q = quat_mul(calibration_quat, raw_q)
            corrected_q = quat_norm(corrected_q)

            # IMU-space forward vector
            world_vec_imu = rotate_vector_by_quat(sensor_axis, corrected_q)

            # Convert to globe-space
            world_vec_globe = imu_vec_to_globe_vec(world_vec_imu)

            # If you still want to debug:
            # print("IMU_VEC:", world_vec_imu, "GLOBE_VEC:", world_vec_globe)

            lat, lon = vector_to_latlon(world_vec_globe)
            if lat is None:
                time.sleep(0.01)
                continue

            print(f"lat: {lat:.3f}, lon: {lon:.3f}")

            time.sleep(0.1)

        except OSError:
            print("\n⚠️ I2C error — resetting sensor…")
            sensor = init_sensor()
            time.sleep(0.2)

        except Exception as e:
            print("Unexpected error:", e)
            time.sleep(0.2)


# ----------------------------
# Entry
# ----------------------------
if __name__ == "__main__":
    import tty, termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        main_loop()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
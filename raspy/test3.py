import time
import math
import board
import busio
import digitalio
import sys
import select

from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import (
    BNO_REPORT_ROTATION_VECTOR,
    BNO_REPORT_ACCELEROMETER,
    BNO_REPORT_GYROSCOPE
)

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
    sensor.enable_feature(BNO_REPORT_ACCELEROMETER)
    sensor.enable_feature(BNO_REPORT_GYROSCOPE)
    return sensor

sensor = init_sensor()

# ----------------------------
# Quaternion helpers
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
    qn = quat_norm(q)
    vx, vy, vz = v
    vq = (vx, vy, vz, 0.0)
    qc = quat_conjugate(qn)
    r = quat_mul(quat_mul(qn, vq), qc)
    return r[:3]

# ----------------------------
# Vector to lat/lon (up = top of globe)
# ----------------------------
def vector_to_latlon(forward, up):
    ux, uy, uz = up
    # Latitude from top vector
    lat = math.degrees(math.asin(uz))  # +90 top, -90 bottom

    # Project forward vector onto plane perpendicular to up
    fx, fy, fz = forward
    dot = fx*ux + fy*uy + fz*uz
    hx = fx - dot*ux
    hy = fy - dot*uy
    hz = fz - dot*uz
    # Longitude in plane
    lon = -math.degrees(math.atan2(hy, hx))
    return lat, lon

# ----------------------------
# CONFIG
# ----------------------------
sensor_forward = (1.0, 0.0, 0.0)  # Red arrow forward
sensor_up      = (0.0, 0.0, 1.0)  # Blue arrow pointing top
calibration_quat = None            # Auto-set on startup

# ----------------------------
# Calibration
# ----------------------------
def calibrate(q_current):
    global calibration_quat
    qc = quat_norm(q_current)
    fwd = rotate_vector_by_quat(sensor_forward, qc)
    angle = math.atan2(fwd[1], fwd[0])
    sin_h = math.sin(-angle/2)
    cos_h = math.cos(-angle/2)
    calibration_quat = (0, 0, sin_h, cos_h)
    print("\n🎯 Calibration set! 0° longitude aligned.\n")

# ----------------------------
# Keyboard helper
# ----------------------------
def key_pressed():
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    return dr != []

# ----------------------------
# Main loop
# ----------------------------
def main_loop():
    global sensor, calibration_quat
    print("Press 'c' to recalibrate 0° longitude\n")

    # Auto-set calibration at startup
    calibrate(sensor.quaternion)

    while True:
        if key_pressed():
            ch = sys.stdin.read(1)
            if ch.lower() == "c":
                calibrate(sensor.quaternion)

        try:
            # Read sensor data
            try:
                accel = sensor.acceleration
                print("Accel:", tuple(round(a,4) for a in accel))
            except:
                print("Accel: N/A")

            try:
                gyro = sensor.gyro
                print("Gyro:", tuple(round(g,4) for g in gyro))
            except:
                print("Gyro: N/A")

            try:
                quat = sensor.quaternion
                quat = quat_norm(quat)
                print("Raw Quat:", tuple(round(q,4) for q in quat))
            except:
                quat = (0,0,0,1)
                print("Quat: N/A")

            # Apply calibration
            corrected_q = quat_mul(calibration_quat, quat)
            corrected_q = quat_norm(corrected_q)

            world_forward = rotate_vector_by_quat(sensor_forward, corrected_q)
            world_up      = rotate_vector_by_quat(sensor_up, corrected_q)

            # Compute latitude and longitude
            lat, lon = vector_to_latlon(world_forward, world_up)

            print("Corrected Quat:", tuple(round(c,4) for c in corrected_q))
            print("Forward Vector:", tuple(round(f,4) for f in world_forward))
            print("Up Vector:", tuple(round(u,4) for u in world_up))
            print(f"Latitude: {lat:.3f}°, Longitude: {lon:.3f}°")
            print("-------------------------------")

            time.sleep(0.1)

        except OSError:
            print("⚠️ I2C error — resetting sensor")
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

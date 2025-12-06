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
    return lat, lon

# ----------------------------
# Config
# ----------------------------
sensor_forward = (1.0, 0.0, 0.0)  # Red arrow
sensor_up      = (0.0, 0.0, 1.0)  # Blue arrow
BASE = None  # Base orientation for reference

# ----------------------------
# Calibration
# ----------------------------
def calibrate():
    global BASE
    BASE = quat_norm(sensor.quaternion)
    print("\n🎯 BASE orientation set!")
    print("Current quaternion stored as BASE:", BASE, "\n")

# ----------------------------
# Keyboard helper
# ----------------------------
def key_pressed():
    dr, dw, de = select.select([sys.stdin], [], [], 0)
    return dr != []

# ----------------------------
# Main loop
# ----------------------------
def main_loop():
    import tty, termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        print("Press 'c' to set BASE orientation")
        while True:
            if key_pressed():
                ch = sys.stdin.read(1)
                if ch.lower() == "c":
                    calibrate()

            try:
                # ---------------- SENSOR DATA ----------------
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

                # ---------------- APPLY BASE ----------------
                if BASE is not None:
                    delta = quat_mul(quat, quat_conjugate(BASE))
                else:
                    delta = quat

                world_forward = rotate_vector_by_quat(sensor_forward, delta)
                world_up      = rotate_vector_by_quat(sensor_up, delta)
                lat, lon = vector_to_latlon(world_forward)

                print("Corrected Quat:", tuple(round(c,4) for c in delta))
                print("Forward Vector:", tuple(round(f,4) for f in world_forward))
                print("Up Vector:", tuple(round(u,4) for u in world_up))
                if lat is not None:
                    print(f"Latitude: {lat:.3f}°, Longitude: {lon:.3f}°")
                else:
                    print("Latitude/Longitude: N/A")

                print("-"*40)
                time.sleep(0.1)

            except OSError:
                print("⚠️ I2C error — resetting sensor")
                global sensor
                sensor = init_sensor()
                time.sleep(0.2)
            except Exception as e:
                print("Unexpected error:", e)
                time.sleep(0.2)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

# ----------------------------
# Entry point
# ----------------------------
if __name__ == "__main__":
    main_loop()

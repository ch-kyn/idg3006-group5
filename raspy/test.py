import time
import math
import board
import busio

from adafruit_bno08x import (
    BNO_REPORT_ROTATION_VECTOR,
    BNO_REPORT_ACCELEROMETER,
    BNO_REPORT_GYROSCOPE
)
from adafruit_bno08x.i2c import BNO08X_I2C


# ------------------ INIT SENSOR ------------------

i2c = busio.I2C(board.SCL, board.SDA)
sensor = BNO08X_I2C(i2c, address=0x4A)

sensor.enable_feature(BNO_REPORT_ROTATION_VECTOR)
sensor.enable_feature(BNO_REPORT_ACCELEROMETER)
sensor.enable_feature(BNO_REPORT_GYROSCOPE)

time.sleep(1)

print("\nSensor ready.\n")


# ------------------ QUATERNION MATH ------------------

def quat_conjugate(q):
    w, x, y, z = q
    return (w, -x, -y, -z)


def quat_multiply(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2

    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 - x1*z2 + y1*w2 + z1*x2
    z = w1*z2 + x1*y2 - y1*x2 + z1*w2

    return (w, x, y, z)


def quat_to_euler(q):
    w, x, y, z = q

    # roll (X)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    # pitch (Y)
    sinp = 2 * (w * y - z * x)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)
    else:
        pitch = math.asin(sinp)

    # yaw (Z)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw


def rad_to_deg(rad):
    return rad * 180.0 / math.pi


# ------------------ AUTO CONFIG (START BUTTON) ------------------

print("Pek toppen av globen mot ønsket sted.")
input("Trykk ENTER for å sette START-posisjon...")

BASE = sensor.quaternion
print("\nBASE quaternion satt:", BASE)
print("Denne posisjonen er nå 0° lat / 0° long\n")


# ------------------ MAIN LOOP ------------------

while True:

    current = sensor.quaternion

    delta = quat_multiply(
        current,
        quat_conjugate(BASE)
    )

    roll, pitch, yaw = quat_to_euler(delta)

    # MAP TIL GLOBE
    latitude = rad_to_deg(pitch)
    longitude = rad_to_deg(roll)

    # Begrensninger
    latitude = max(min(latitude, 90), -90)
    if longitude > 180:
        longitude -= 360
    if longitude < -180:
        longitude += 360

    # ---------------- SENSOR PRINTS ----------------

    try:
        print("Accel:", sensor.acceleration)
    except:
        print("Accel: N/A")

    try:
        print("Gyro:", sensor.gyro)
    except:
        print("Gyro: N/A")

    print("Quat:", sensor.quaternion)

    print(f"Latitude: {latitude:6.2f}°, Longitude: {longitude:7.2f}°")
    print("-" * 40)

    time.sleep(0.1)

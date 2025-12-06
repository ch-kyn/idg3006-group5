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
    BNO_REPORT_GYROSCOPE,
    BNO_REPORT_MAGNETOMETER,
    BNO_REPORT_GEOMAGNETIC_ROTATION_VECTOR
)

# ----------------------------
# Reset + I2C
# ----------------------------
reset_pin = digitalio.DigitalInOut(board.D17)
reset_pin.direction = digitalio.Direction.OUTPUT
i2c = busio.I2C(board.SCL, board.SDA)

def init_sensor():
    print("Initializing BNO08X...")
    reset_pin.value = False
    time.sleep(0.01)
    reset_pin.value = True
    time.sleep(0.25)

    sensor = BNO08X_I2C(i2c, address=0x4A)

    sensor.enable_feature(BNO_REPORT_ACCELEROMETER)
    sensor.enable_feature(BNO_REPORT_GYROSCOPE)
    sensor.enable_feature(BNO_REPORT_MAGNETOMETER)

    # THIS is the important one: Earth referenced quaternion
    sensor.enable_feature(BNO_REPORT_GEOMAGNETIC_ROTATION_VECTOR)

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
        w1*w2 - x1*x2 - y1*y2 - z1*z2
    )

def rotate_vector_by_quat(v, q):
    qn = quat_norm(q)
    vx, vy, vz = v
    vq = (vx, vy, vz, 0.0)
    qc = quat_conjugate(qn)
    r = quat_mul(quat_mul(qn, vq), qc)
    return r[:3]

def normalize(v):
    norm = math.sqrt(sum([c*c for c in v]))
    if norm == 0:
        return (0.0, 0.0, 1.0)
    return tuple(c/norm for c in v)

# ----------------------------
# Latitude / Longitude
# ----------------------------
def vector_to_latlon(forward, up):
    ux, uy, uz = normalize(up)
    fx, fy, fz = normalize(forward)

    # Latitude = gravity
    lat = math.degrees(math.asin(uz))

    # Project forward onto horizontal
    hx = fx - (fx*ux + fy*uy + fz*uz) * ux
    hy = fy - (fx*ux + fy*uy + fz*uz) * uy

    # TRUE longitude (Earth locked now)
    lon = math.degrees(math.atan2(hy, hx))

    if lon > 180:
        lon -= 360
    elif lon < -180:
        lon += 360

    return lat, lon

# ----------------------------
# Special locations
# ----------------------------
def check_special_locations(lat, lon):
    if lat >= 89:
        print("📍 North Pole detected!")
    elif lat <= -89:
        print("📍 South Pole detected!")
    elif abs(lat) < 1 and abs(lon) < 1:
        print("📍 Null Island detected!")
    elif abs(lat) < 1:
        print("📍 Equator detected!")

# ----------------------------
# World vectors
# ----------------------------
sensor_forward = (1.0, 0.0, 0.0)
sensor_up = (0.0, 0.0, 1.0)

def main_loop():
    print("Using TRUE geomagnetic frame (real North & longitude)")

    while True:
        try:
            # THIS IS THE MAGIC LINE
            quat = quat_norm(sensor.geomagnetic_quaternion)

            world_forward = rotate_vector_by_quat(sensor_forward, quat)
            world_up = rotate_vector_by_quat(sensor_up, quat)

            lat, lon = vector_to_latlon(world_forward, world_up)

            print(f"Latitude: {lat:.2f}°, Longitude: {lon:.2f}°")
            check_special_locations(lat, lon)

            time.sleep(0.1)

        except Exception as e:
            print("Error:", e)
            time.sleep(0.2)

# ----------------------------
# Entry
# ----------------------------
if __name__ == "__main__":
    main_loop()

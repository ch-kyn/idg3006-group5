import math
import time
import board
import busio
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR

# ----------------------------
# Setup I2C and sensor
# ----------------------------
i2c = busio.I2C(board.SCL, board.SDA)
bno = BNO08X_I2C(i2c)

# Enable rotation vector (quaternion)
bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)

# ----------------------------
# Helper: rotate any vector by quaternion
# ----------------------------
def rotate_vector(quat, v):
    w, x, y, z = quat
    vx, vy, vz = v
    # Quaternion rotation: v' = q * v * q^-1
    rx = (1 - 2*(y*y + z*z))*vx + 2*(x*y - w*z)*vy + 2*(x*z + w*y)*vz
    ry = 2*(x*y + w*z)*vx + (1 - 2*(x*x + z*z))*vy + 2*(y*z - w*x)*vz
    rz = 2*(x*z - w*y)*vx + 2*(y*z + w*x)*vy + (1 - 2*(x*x + y*y))*vz
    return rx, ry, rz

# ----------------------------
# Convert rotated vectors to latitude and longitude
# ----------------------------
def vectors_to_lat_lon(up, forward):
    ux, uy, uz = up
    fx, fy, fz = forward

    # Clamp uz to [-1,1] to avoid math domain errors
    uz = max(-1.0, min(1.0, uz))
    
    # Latitude: angle from equator plane (XY-plane)
    latitude = math.degrees(math.asin(uz))

    # Longitude: projection of forward vector onto XY-plane
    lon_rad = math.atan2(fy, fx)
    longitude = math.degrees(lon_rad)

    # Normalize longitude to -180..180
    if longitude > 180:
        longitude -= 360
    elif longitude < -180:
        longitude += 360

    return latitude, longitude

# ----------------------------
# Main loop
# ----------------------------
# Define device-space reference vectors
UP_VEC = (0, 1, 0)       # points "up" on device
FORWARD_VEC = (0, 0, 1)  # points "forward" on device

while True:
    quat = bno.quaternion  # (w, x, y, z)

    # Rotate reference vectors into world coordinates
    up_world = rotate_vector(quat, UP_VEC)
    forward_world = rotate_vector(quat, FORWARD_VEC)

    # Compute latitude and longitude
    lat, lon = vectors_to_lat_lon(up_world, forward_world)

    print(f"Lat: {lat:6.2f}°, Lon: {lon:7.2f}°")
    time.sleep(1)

import math
import board
import busio
from adafruit_bno08x import BNO08X_I2C

# ------------------------------------------
# Setup I2C and sensor
# ------------------------------------------
i2c = busio.I2C(board.SCL, board.SDA)
bno = BNO08X_I2C(i2c)

# Enable rotation vector (quaternion)
bno.enable_feature(BNO08X_I2C.FEATURE_ROTATION_VECTOR)

# ------------------------------------------
# Helper: rotate UP vector (0,0,1) by quaternion
# This produces the device's UP direction in world coordinates
# ------------------------------------------
def rotate_up(quat):
    qw, qx, qy, qz = quat

    # Rotated UP vector (0,0,1)
    ux = 2 * (qx*qz + qw*qy)
    uy = 2 * (qy*qz - qw*qx)
    uz = qw*qw - qx*qx - qy*qy + qz*qz

    return (ux, uy, uz)

# ------------------------------------------
# Main loop
# ------------------------------------------
while True:
    quat = bno.quaternion  # (w, x, y, z)

    # 1. Get sensor UP vector in world space
    ux, uy, uz = rotate_up(quat)

    # 2. Latitude = tilt relative to vertical (gravity)
    latitude = math.degrees(math.asin(uz))

    # 3. Longitude = rotation around vertical axis
    longitude = math.degrees(math.atan2(ux, uy))

    # Normalize longitude to -180..180
    if longitude > 180:
        longitude -= 360
    if longitude < -180:
        longitude += 360

    print(f"Lat: {latitude:6.2f}°,   Lon: {longitude:7.2f}°")

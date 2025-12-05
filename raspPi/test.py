import time
import board
import busio
from adafruit_bno08x import BNO08X_I2C, BNO_REPORT_ROTATION_VECTOR, BNO_REPORT_LINEAR_ACCELERATION
from pyquaternion import Quaternion
import numpy as np

# ----------------------------
# I2C and sensor setup
# ----------------------------
i2c = busio.I2C(board.SCL, board.SDA)
sensor = BNO08X_I2C(i2c)

# Enable reports
sensor.enable_feature(BNO_REPORT_ROTATION_VECTOR)
sensor.enable_feature(BNO_REPORT_LINEAR_ACCELERATION)

# ----------------------------
# Calibration quaternion
# ----------------------------
cal_quat = Quaternion(0, 0, 0, 1)  # identity (no rotation yet)

# ----------------------------
# Initialize position & velocity
# ----------------------------
position = np.array([0.0, 0.0, 0.0])  # x, y, z in meters
velocity = np.array([0.0, 0.0, 0.0])  # m/s

prev_time = time.time()

# ----------------------------
# Main loop
# ----------------------------
while True:
    # Get current time
    now = time.time()
    dt = now - prev_time
    prev_time = now

    # ----------------------------
    # Read rotation vector (quaternion)
    # ----------------------------
    if sensor.quaternion is not None:
        q = Quaternion(sensor.quaternion)  # x, y, z, w
        # Apply calibration: relative orientation
        q_rel = cal_quat.inverse * q

    # ----------------------------
    # Read linear acceleration
    # ----------------------------
    if sensor.linear_acceleration is not None:
        acc = np.array(sensor.linear_acceleration)  # [ax, ay, az] in m/s²
        # Rotate acceleration to world frame
        acc_world = q_rel.rotate(acc)

        # Integrate acceleration → velocity
        velocity += acc_world * dt
        # Integrate velocity → position
        position += velocity * dt

    print(f"Position: x={position[0]:.3f}, y={position[1]:.3f}, z={position[2]:.3f}")
    
    time.sleep(1)  # 100 Hz update
# ----------------------------
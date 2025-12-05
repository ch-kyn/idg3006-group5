import time
import board
import busio
import numpy as np
from pyquaternion import Quaternion

# Correct import for the sensor driver:
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import (
    BNO_REPORT_ROTATION_VECTOR,
    BNO_REPORT_LINEAR_ACCELERATION
)

# ----------------------------
# I2C Setup
# ----------------------------
i2c = busio.I2C(board.SCL, board.SDA)
sensor = BNO08X_I2C(i2c)

# Enable sensor features
sensor.enable_feature(BNO_REPORT_ROTATION_VECTOR)
sensor.enable_feature(BNO_REPORT_LINEAR_ACCELERATION)

# ----------------------------
# Calibration quaternion (identity for now)
# ----------------------------
cal_quat = Quaternion(0, 0, 0, 1)

# ----------------------------
# State variables
# ----------------------------
position = np.array([0.0, 0.0, 0.0])
velocity = np.array([0.0, 0.0, 0.0])
prev_time = time.time()

print("Starting coordinate tracking...")
print("Move the sensor gently to test.\n")

# ----------------------------
# Main loop
# ----------------------------
while True:
    now = time.time()
    dt = now - prev_time
    prev_time = now

    # Read orientation quaternion
    quat_raw = sensor.quaternion
    if quat_raw is not None:
        q = Quaternion(quat_raw[0], quat_raw[1], quat_raw[2], quat_raw[3])
        q_rel = cal_quat.inverse * q
    else:
        continue  # No quaternion yet

    # Read linear acceleration (gravity removed)
    acc_raw = sensor.linear_acceleration
    if acc_raw is not None:
        acc = np.array(acc_raw)

        # Rotate acceleration into world frame
        acc_world = q_rel.rotate(acc)

        # Integrate acceleration → velocity
        velocity += acc_world * dt

        # Integrate velocity → position
        position += velocity * dt

        # Print coordinates
        print(
            f"Position: "
            f"X={position[0]:.3f} m, "
            f"Y={position[1]:.3f} m, "
            f"Z={position[2]:.3f} m"
        )

    time.sleep(0.01)  # ~100 Hz

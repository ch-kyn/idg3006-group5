import numpy as np
import math

def normalize(v):
    n = np.linalg.norm(v)
    return v if n == 0 else v / n

# --- 1. Build rotation to map v1 -> v2 --- #
def rotation_between(v1, v2):
    v1 = normalize(v1)
    v2 = normalize(v2)
    cross = np.cross(v1, v2)
    dot = np.dot(v1, v2)

    if dot < -0.999999:
        # 180° flip around ANY perpendicular axis
        axis = normalize(np.cross(v1, [1,0,0]))
        if np.linalg.norm(axis) < 0.001:
            axis = normalize(np.cross(v1, [0,1,0]))
        return rot_matrix(axis, math.pi)

    k = 1 / (1 + dot)
    vx, vy, vz = cross

    return np.array([
        [1 + k*(vx*vx-1),     k*vx*vy - vz,      k*vx*vz + vy],
        [k*vy*vx + vz,        1 + k*(vy*vy-1),   k*vy*vz - vx],
        [k*vz*vx - vy,        k*vz*vy + vx,      1 + k*(vz*vz-1)]
    ])


def rot_matrix(axis, angle):
    x,y,z = normalize(axis)
    c = math.cos(angle)
    s = math.sin(angle)
    C = 1 - c
    return np.array([
        [c + x*x*C,   x*y*C - z*s, x*z*C + y*s],
        [y*x*C + z*s, c + y*y*C,   y*z*C - x*s],
        [z*x*C - y*s, z*y*C + x*s, c + z*z*C  ]
    ])

# --- 2. Convert unit vector to latitude/longitude --- #
def vector_to_latlon(v):
    vx, vy, vz = normalize(v)
    lat = math.degrees(math.asin(vz))
    lon = math.degrees(math.atan2(vy, vx))
    lon = (lon + 180) % 360 - 180
    return lat, lon


# === EXAMPLE === #
# Step 1: You calibrate while pointing at Null Island
v_calib = np.array([0.22, -0.91, 0.36])  # example IMU reading
target_null = np.array([1, 0, 0])
R_calib = rotation_between(v_calib, target_null)

# Step 2: Later IMU reading (globe rotated)
v_now = np.array([0.15, -0.88, 0.44])
v_corrected = R_calib @ v_now
lat, lon = vector_to_latlon(v_corrected)

print(lat, lon)

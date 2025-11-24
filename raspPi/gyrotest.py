import time
import math
import board
import busio
import digitalio

from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR


# ----------------------------
#  RESET PIN (REQUIRED)
# ----------------------------
reset_pin = digitalio.DigitalInOut(board.D7)
reset_pin.direction = digitalio.Direction.OUTPUT



# ----------------------------
#  I2C INIT
# ----------------------------
i2c = busio.I2C(board.SCL, board.SDA)

def init_sensor():
    """Initialize sensor with reset."""
    print("Initializing BNO08X...")
    sensor = BNO08X_I2C(i2c, address=0x4A, debug=False)
    sensor.enable_feature(BNO_REPORT_ROTATION_VECTOR)
    return sensor

sensor = init_sensor()


# ----------------------------
# Quaternion + vector helpers
# ----------------------------
def quat_conjugate(q):
    x, y, z, w = q
    return (-x, -y, -z, w)

def quat_mul(q1, q2):
    x1,y1,z1,w1 = q1
    x2,y2,z2,w2 = q2
    return (
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
        w1*w2 - x1*x2 - y1*y2 - z1*z2
    )

def rotate_vector_by_quat(v, q):
    vx, vy, vz = v
    vq = (vx, vy, vz, 0.0)
    qc = quat_conjugate(q)
    return quat_mul(quat_mul(q, vq), qc)[:3]

def vector_to_latlon(v):
    vx, vy, vz = v
    mag = math.sqrt(vx*vx + vy*vy + vz*vz)
    if mag == 0:
        return None, None
    vx /= mag; vy /= mag; vz /= mag
    lat = math.degrees(math.asin(vz))
    lon = math.degrees(math.atan2(vy, vx))
    if lon >= 180: lon -= 360
    if lon < -180: lon += 360
    return lat, lon


# ----------------------------
# CONFIG
# ----------------------------
sensor_axis = (1.0, 0.0, 0.0)   # use +X as pointing direction
calib_quat  = (0.0, 0.0, 0.0, 1.0)  # no calibration rotation

STABLE_THRESHOLD_DEG = 2.0       # must stay within ±1° window
STABLE_TIME_SEC = 3.0            # must remain stable for 3 seconds
stable = False

# ----------------------------
# STABILITY TRACKING
# ----------------------------
last_latlon = None
stable_start = None


# ----------------------------
# MAIN LOOP
# ----------------------------
while True:
    try:
        # Read quaternion
        x, y, z, w = sensor.quaternion
        if (x, y, z, w) == (0.0, 0.0, 0.0, 0.0):
            continue

        q = (x, y, z, w)

        # Rotate sensor axis → world vector
        world_vec = rotate_vector_by_quat(sensor_axis, q)

        # Convert to lat/lon
        lat, lon = vector_to_latlon(world_vec)
        if lat is None:
            continue

        current = (lat, lon)

        # If this is first reading, initialize stability tracking
        if last_latlon is None:
            last_latlon = current
            stable_start = time.time()
            continue

        # Check if movement is small
        lat_diff = abs(lat - last_latlon[0])
        lon_diff = abs(lon - last_latlon[1])

        if lat_diff < STABLE_THRESHOLD_DEG and lon_diff < STABLE_THRESHOLD_DEG:
            # Still stable → check timer
            if time.time() - stable_start >= STABLE_TIME_SEC:
                if stable == False:
                    print(f"Stable position reached:")
                    print(f"→ Latitude:  {lat:.2f}°")
                    print(f"→ Longitude: {lon:.2f}°")
                    print("---------------------------")

                    # Reset so it must become stable AGAIN
                    stable_start = time.time()
                    stable = True
                    last_latlon = current
        else:
            # Movement too large → reset stabilization timer
            stable_start = time.time()
            last_latlon = current
            stable = False

        time.sleep(0.05)

    except OSError:
        # I²C glitch — reinitialize sensor
        print("\n⚠️  I2C hiccup — resetting sensor...")
        time.sleep(0.2)
        sensor = init_sensor()

    except Exception as e:
        print("Unexpected error:", e)
        time.sleep(0.2)

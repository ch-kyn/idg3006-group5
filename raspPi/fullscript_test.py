import time
import math
import board
import busio
import digitalio
import requests

from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR

# ----------------------------
# CONFIG
# ----------------------------
SENSOR_AXIS = (1.0, 0.0, 0.0)       # +X as pointing direction
CALIB_QUAT  = (0.0, 0.0, 0.0, 1.0)  # no calibration rotation
STABLE_THRESHOLD_DEG = 1.0          # ±1° window
STABLE_TIME_SEC = 3.0               # must remain stable for 3 seconds

SERVER_URL = "http://www.example.com"
TOKEN = "YOUR_TOKEN_HERE"

# ----------------------------
# RESET PIN & I2C INIT
# ----------------------------
reset_pin = digitalio.DigitalInOut(board.D17)
reset_pin.direction = digitalio.Direction.OUTPUT
i2c = busio.I2C(board.SCL, board.SDA)

def init_sensor():
    print("Initializing BNO08X...")
    sensor = BNO08X_I2C(i2c, reset_pin=reset_pin, address=0x4A, debug=False)
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
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
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
# Send coordinates to server
# ----------------------------
def send_coords(lat, lon, token):
    payload = {"lat": lat, "lon": lon, "token": token}
    try:
        response = requests.post(SERVER_URL, json=payload, timeout=5)
        response.raise_for_status()
        try:
            return response.json()
        except requests.JSONDecodeError:
            return response.text
    except requests.RequestException as e:
        print("Error sending coordinates:", e)
        return None

# ----------------------------
# STABILITY TRACKING
# ----------------------------
last_latlon = None
stable_start = None
stable_sent = False  # <-- Track if we already sent coords

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
        world_vec = rotate_vector_by_quat(SENSOR_AXIS, q)

        # Convert to lat/lon
        lat, lon = vector_to_latlon(world_vec)
        if lat is None:
            continue
        current = (lat, lon)

        # First reading → initialize
        if last_latlon is None:
            last_latlon = current
            stable_start = time.time()
            stable_sent = False
            continue

        # Compute movement
        lat_diff = abs(lat - last_latlon[0])
        lon_diff = abs(lon - last_latlon[1])

        if lat_diff < STABLE_THRESHOLD_DEG and lon_diff < STABLE_THRESHOLD_DEG:
            # Still stable → check timer
            if stable_start is None:
                stable_start = time.time()
                stable_sent = False

            if time.time() - stable_start >= STABLE_TIME_SEC and not stable_sent:
                print(f"Stable position reached:")
                print(f"→ Latitude:  {lat:.2f}°")
                print(f"→ Longitude: {lon:.2f}°")
                print("---------------------------")

                # Send coordinates once
                send_coords(lat, lon, TOKEN)
                stable_sent = True
        else:
            # Movement too large → reset
            stable_start = time.time()
            last_latlon = current
            stable_sent = False

        time.sleep(0.05)

    except OSError:
        print("\n⚠️  I2C hiccup — resetting sensor...")
        time.sleep(0.2)
        sensor = init_sensor()

    except Exception as e:
        print("Unexpected error:", e)
        time.sleep(0.2)

import asyncio
import socketio
import time
import math
import board
import busio
import digitalio
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR

WS_URI = "http://192.168.166.154:8765"
sio = socketio.AsyncClient()

# Sensor setup (same as before)
reset_pin = digitalio.DigitalInOut(board.D17)
reset_pin.direction = digitalio.Direction.OUTPUT
i2c = busio.I2C(board.SCL, board.SDA)

def init_sensor():
    reset_pin.value = False
    time.sleep(0.01)
    reset_pin.value = True
    time.sleep(0.25)
    sensor = BNO08X_I2C(i2c, address=0x4A)
    sensor.enable_feature(BNO_REPORT_ROTATION_VECTOR)
    return sensor

sensor = init_sensor()

# Helpers (quaternions, rotate_vector_by_quat, vector_to_latlon) omitted for brevity

calibration_quat = (0,0,0,1)
sensor_axis = (1,0,0)

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
    vx /= mag
    vy /= mag
    vz /= mag
    lat = math.degrees(math.asin(vz))
    lon = math.degrees(math.atan2(vy, vx))
    if lon >= 180: lon -= 360
    if lon < -180: lon += 360
    return lat, lon

def invert_quat(q):
    return quat_conjugate(q)

def calibrate(q):
    global calibration_quat
    calibration_quat = invert_quat(q)
    print("Calibration set")

@sio.event
async def connect():
    print("✅ Connected to server!")

@sio.event
async def disconnect():
    print("❌ Disconnected from server")

async def main_loop():
    global sensor
    while True:
        try:
            x, y, z, w = sensor.quaternion
            if (x, y, z, w) == (0,0,0,0):
                await asyncio.sleep(0.01)
                continue

            raw_q = (x, y, z, w)
            corrected_q = quat_mul(calibration_quat, raw_q)
            world_vec = rotate_vector_by_quat(sensor_axis, corrected_q)
            lat, lon = vector_to_latlon(world_vec)
            if lat is None:
                await asyncio.sleep(0.1)
                continue

            await sio.emit("coords", {"lat": round(lat,3), "lon": round(lon,3)})
            print(f"Sent: lat={lat:.3f}, lon={lon:.3f}")
            await asyncio.sleep(0.1)

        except Exception as e:
            print("Error:", e)
            await asyncio.sleep(0.5)

async def runner():
    await sio.connect(WS_URI)
    await main_loop()  # run continuously

if __name__ == "__main__":
    asyncio.run(runner())

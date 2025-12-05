import asyncio
import websockets
import json
import time
import math
import board
import busio
import digitalio
import sys
import select

from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR


# ----------------------------
# WebSocket config
# ----------------------------
WS_URI = "ws://192.168.166.154:8765"


# ----------------------------
# RESET PIN
# ----------------------------
reset_pin = digitalio.DigitalInOut(board.D17)
reset_pin.direction = digitalio.Direction.OUTPUT


# ----------------------------
# I2C INIT
# ----------------------------
i2c = busio.I2C(board.SCL, board.SDA)


def init_sensor():
    print("Initializing BNO08X...")

    reset_pin.value = False
    time.sleep(0.01)
    reset_pin.value = True
    time.sleep(0.25)

    sensor = BNO08X_I2C(i2c, address=0x4A)
    sensor.enable_feature(BNO_REPORT_ROTATION_VECTOR)
    return sensor


sensor = init_sensor()


# ----------------------------------------
# CALIBRATION OFFSETS (pitch, yaw)
# ----------------------------------------
cal_pitch = 0.0
cal_yaw = 0.0


# ----------------------------------------
# Keyboard helper
# ----------------------------------------
def key_pressed():
    dr, dw, de = select.select([sys.stdin], [], [], 0)
    return dr != []


# ----------------------------------------
# Quaternion → Euler angles
#
# yaw   = heading (longitude)
# pitch = tilt up/down (latitude)
# roll  = tilt sideways
#
# This avoids gimbal lock because BNO08X orientation
# is already fused and stable.
# ----------------------------------------
def quat_to_euler(x, y, z, w):
    # yaw (Z axis)
    yaw = math.atan2(
        2.0 * (w*z + x*y),
        1.0 - 2.0 * (y*y + z*z)
    )

    # pitch (X axis)
    sinp = 2.0 * (w*x - y*z)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi/2, sinp)   # 90° clamp
    else:
        pitch = math.asin(sinp)

    # roll (Y axis) - not used for lat/lon
    roll = math.atan2(
        2.0 * (w*y + z*x),
        1.0 - 2.0 * (x*x + y*y)
    )

    return pitch, yaw, roll


# ----------------------------------------
# Calibration
# ----------------------------------------
def calibrate(pitch, yaw):
    global cal_pitch, cal_yaw
    cal_pitch = -pitch
    cal_yaw   = -yaw
    print("\n🎯 Calibration saved! Orientation → (0,0)\n")


# ----------------------------------------
# Main loop
# ----------------------------------------
async def send_coordinates():
    global sensor

    async with websockets.connect(WS_URI) as websocket:
        print("Connected to WebSocket server!")

        while True:

            # Keyboard calibration
            if key_pressed():
                ch = sys.stdin.read(1)
                if ch.lower() == "c":
                    x, y, z, w = sensor.quaternion
                    pitch, yaw, _ = quat_to_euler(x, y, z, w)
                    calibrate(pitch, yaw)

            try:
                x, y, z, w = sensor.quaternion
                if (x, y, z, w) == (0, 0, 0, 0):
                    await asyncio.sleep(0.01)
                    continue

                pitch, yaw, roll = quat_to_euler(x, y, z, w)

                # Apply calibration
                pitch += cal_pitch
                yaw   += cal_yaw

                # Convert to degrees
                lat = math.degrees(pitch)   # -90..+90
                lon = math.degrees(yaw)     # -180..+180

                msg = json.dumps({
                    "lat": round(lat, 3),
                    "lon": round(lon, 3),
                })

                await websocket.send(msg)
                print("Sent:", msg)

                await asyncio.sleep(0.1)

            except OSError:
                print("\n⚠️ I2C error — resetting sensor…")
                sensor = init_sensor()
                await asyncio.sleep(0.2)

            except Exception as e:
                print("Unexpected error:", e)
                await asyncio.sleep(0.2)


# ----------------------------------------
# Entry
# ----------------------------------------
if __name__ == "__main__":
    import tty, termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        asyncio.run(send_coordinates())
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

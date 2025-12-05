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
from adafruit_bno08x import BNO_REPORT_GRAVITY


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
    sensor.enable_feature(BNO_REPORT_GRAVITY)
    return sensor


sensor = init_sensor()


# ----------------------------
# GLOBAL CALIBRATION OFFSETS
# ----------------------------
cal_offset_lat = 0.0
cal_offset_lon = 0.0


# ----------------------------
# Keyboard helper
# ----------------------------
def key_pressed():
    dr, dw, de = select.select([sys.stdin], [], [], 0)
    return dr != []


# ----------------------------
# Lat/lon from gravity vector
# ----------------------------
def gravity_to_latlon(gx, gy, gz):
    mag = math.sqrt(gx*gx + gy*gy + gz*gz)
    if mag == 0:
        return None, None

    gx /= mag
    gy /= mag
    gz /= mag

    # Gravity vector points DOWN, invert Z
    gz = -gz

    lat = math.degrees(math.asin(gz))          # -90..90
    lon = math.degrees(math.atan2(gy, gx))      # -180..180

    return lat, lon


# ----------------------------
# Calibration function
# ----------------------------
def calibrate(lat, lon):
    global cal_offset_lat, cal_offset_lon
    cal_offset_lat = -lat
    cal_offset_lon = -lon
    print("\n🎯 Calibration saved! Current orientation → (0,0)\n")


# ----------------------------
# Main loop
# ----------------------------
async def send_coordinates():
    global sensor
    async with websockets.connect(WS_URI) as websocket:
        print("Connected to WebSocket server!")

        while True:

            # Calibration key
            if key_pressed():
                ch = sys.stdin.read(1)
                if ch.lower() == "c":
                    try:
                        gx, gy, gz = sensor.gravity
                        lat, lon = gravity_to_latlon(gx, gy, gz)
                        if lat is not None:
                            calibrate(lat, lon)
                    except:
                        pass

            try:
                gx, gy, gz = sensor.gravity
                lat, lon = gravity_to_latlon(gx, gy, gz)

                if lat is None:
                    await asyncio.sleep(0.01)
                    continue

                # Apply calibration offsets
                lat += cal_offset_lat
                lon += cal_offset_lon

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


# ----------------------------
# Entry
# ----------------------------
if __name__ == "__main__":
    import tty, termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        asyncio.run(send_coordinates())
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

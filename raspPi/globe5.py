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
WS_URI = "ws://10.22.62.39:8765"

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

# ----------------------------
# Quaternion helpers
# ----------------------------
def quat_conjugate(q):
    x, y, z, w = q
    return (-x, -y, -z, w)

def invert_quat(q):
    # For unit quaternions inverse == conjugate
    return quat_conjugate(q)

def quat_mul(q1, q2):
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return (
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
    )

def rotate_vector_by_quat(v, q):
    vx, vy, vz = v
    vq = (vx, vy, vz, 0.0)
    qc = quat_conjugate(q)
    rx, ry, rz, rw = quat_mul(quat_mul(q, vq), qc)
    return (rx, ry, rz)

def normalize(v):
    x, y, z = v
    m = math.sqrt(x*x + y*y + z*z)
    if m == 0:
        return (0.0, 0.0, 0.0)
    return (x/m, y/m, z/m)

# ----------------------------
# CONFIG
# ----------------------------
# Local sensor axes (used for rotating into world space each frame)
local_x = (1.0, 0.0, 0.0)
local_y = (0.0, 1.0, 0.0)
local_z = (0.0, 0.0, 1.0)

calibration_quat = (0.0, 0.0, 0.0, 1.0)  # identity

# ----------------------------
# Calibration
# ----------------------------
def calibrate(q_current):
    """
    Press 'c' while pointing at the globe's reference (0°,0°).
    We set calibration so that current orientation becomes identity.
    """
    global calibration_quat
    q_target = (0.0, 0.0, 0.0, 1.0)
    calibration_quat = quat_mul(invert_quat(q_current), q_target)
    print("\n🎯 Calibration set! Orientation aligned to 0° lat / 0° lon.\n")

# ----------------------------
# Keyboard helper
# ----------------------------
def key_pressed():
    dr, dw, de = select.select([sys.stdin], [], [], 0)
    return dr != []

# ----------------------------
# Main loop
# ----------------------------
async def send_coordinates():
    global sensor
    async with websockets.connect(WS_URI) as websocket:
        print("Connected to WebSocket server!")

        while True:
            # allow calibration via 'c'
            if key_pressed():
                ch = sys.stdin.read(1)
                if ch.lower() == "c":
                    calibrate(sensor.quaternion)

            try:
                # Read quaternion from sensor
                x, y, z, w = sensor.quaternion
                if (x, y, z, w) == (0, 0, 0, 0):
                    await asyncio.sleep(0.01)
                    continue

                raw_q = (x, y, z, w)

                # Apply calibration correction
                corrected_q = quat_mul(calibration_quat, raw_q)

                # Rotate all local axes into world space
                world_x = normalize(rotate_vector_by_quat(local_x, corrected_q))
                world_y = normalize(rotate_vector_by_quat(local_y, corrected_q))
                world_z = normalize(rotate_vector_by_quat(local_z, corrected_q))

                # --- Optionally enable these debug prints temporarily ---
                # print("world_x:", world_x, "world_y:", world_y, "world_z:", world_z)

                # Choose which axis is closest to world vertical (largest abs Z)
                axes = [world_x, world_y, world_z]
                abs_z_vals = [abs(a[2]) for a in axes]
                up_index = abs_z_vals.index(max(abs_z_vals))
                world_up = axes[up_index]

                # The other two axes are heading candidates
                heading_candidates = [axes[i] for i in range(3) if i != up_index]

                # --- Latitude (Option A: tilt angle from horizontal) ---
                ux, uy, uz = world_up
                horiz_mag = math.sqrt(ux*ux + uy*uy)
                lat = math.degrees(math.atan2(uz, horiz_mag))  # -90..+90 robust

                # --- Longitude / Heading (choose best horizontal candidate) ---
                best = None
                best_proj = -1.0
                for cand in heading_candidates:
                    cx, cy, cz = cand
                    proj = math.sqrt(cx*cx + cy*cy)
                    if proj > best_proj:
                        best_proj = proj
                        best = cand

                if best_proj > 1e-6:
                    cx, cy, cz = best
                    lon = math.degrees(math.atan2(cy, cx))
                else:
                    # Degenerate: both candidates nearly vertical. Use cross product fallback.
                    f = heading_candidates[0]
                    rx = f[1]*world_up[2] - f[2]*world_up[1]
                    ry = f[2]*world_up[0] - f[0]*world_up[2]
                    rz = f[0]*world_up[1] - f[1]*world_up[0]
                    r = normalize((rx, ry, rz))

                    # if still degenerate, project global X onto plane orthogonal to world_up
                    if abs(r[0]) < 1e-6 and abs(r[1]) < 1e-6:
                        ux, uy, uz = world_up
                        dot = 1.0*ux + 0.0*uy + 0.0*uz
                        vx = 1.0 - dot*ux
                        vy = 0.0 - dot*uy
                        # vz = 0.0 - dot*uz  # we intentionally zero vz for pure horizontal
                        r = normalize((vx, vy, 0.0))

                    lon = math.degrees(math.atan2(r[1], r[0]))

                # Normalize longitude into -180..180
                if lon > 180:
                    lon -= 360
                elif lon < -180:
                    lon += 360

                # --- Optional debug: print chosen up axis and heading candidate ---
                # print("up_index:", up_index, "world_up:", world_up, "lat:", lat, "lon:", lon)

                msg = json.dumps({
                    "lat": round(lat, 3),
                    "lon": round(lon, 3),
                })

                await websocket.send(msg)
                print("Sent:", msg)

                await asyncio.sleep(0.05)  # ~20 Hz

            except OSError:
                print("\n⚠️ I2C error — resetting sensor…")
                sensor = init_sensor()
                await asyncio.sleep(0.3)

            except Exception as e:
                print("Unexpected error:", e)
                await asyncio.sleep(0.3)

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

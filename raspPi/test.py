#!/usr/bin/env python3
"""
BNO08X diagnostic + robust mapping script

- Press 'c' to calibrate (capture current orientation as lat=0,lon=0 reference).
- Press 'v' to toggle verbose diagnostic output (rotation matrix, vectors).
- Press 's' to toggle smoothing for lat/lon.
- Press 'q' to quit.

This prints diagnostics so you can verify axes, quaternions and mapping before streaming.
"""
import asyncio
import time
import math
import sys
import select
import board
import busio
import digitalio

# adafruit library
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR, BNO_REPORT_GRAVITY

# ----------------------------
# Configuration / mappings
# ----------------------------
I2C_ADDRESS = 0x4A
RESET_PIN = board.D17

# Which sensor axes correspond to "aim" (forward) and "up"?
# By default assume sensor X=forward, Z=up: forward=(1,0,0), up=(0,0,1)
SENSOR_FORWARD = (1.0, 0.0, 0.0)
SENSOR_UP = (0.0, 0.0, 1.0)

# smoothing alpha for exponential smoothing (0 = off, 1 = instant)
SMOOTH_ALPHA = 0.25  # default smoothing factor (can toggle)

# ----------------------------
# I2C + sensor init
# ----------------------------
reset_pin = digitalio.DigitalInOut(RESET_PIN)
reset_pin.direction = digitalio.Direction.OUTPUT

i2c = busio.I2C(board.SCL, board.SDA)

def init_sensor(enable_gravity=True):
    print("Initializing BNO08X...")
    reset_pin.value = False
    time.sleep(0.01)
    reset_pin.value = True
    time.sleep(0.25)
    sensor = BNO08X_I2C(i2c, address=I2C_ADDRESS)
    sensor.enable_feature(BNO_REPORT_ROTATION_VECTOR)
    if enable_gravity:
        try:
            sensor.enable_feature(BNO_REPORT_GRAVITY)
        except Exception:
            # some versions may not support gravity; it's optional
            pass
    return sensor

sensor = init_sensor()

# ----------------------------
# Quaternion helpers
# ----------------------------
def quat_normalize(q):
    x,y,z,w = q
    mag = math.sqrt(x*x + y*y + z*z + w*w)
    if mag == 0:
        return (0.0,0.0,0.0,1.0)
    return (x/mag, y/mag, z/mag, w/mag)

def quat_conjugate(q):
    x,y,z,w = q
    return (-x, -y, -z, w)

def quat_inverse(q):
    # For unit quaternions inverse == conjugate
    return quat_conjugate(quat_normalize(q))

def quat_mul(a, b):
    ax,ay,az,aw = a
    bx,by,bz,bw = b
    return (
        aw*bx + ax*bw + ay*bz - az*by,
        aw*by - ax*bz + ay*bw + az*bx,
        aw*bz + ax*by - ay*bx + az*bw,
        aw*bw - ax*bx - ay*by - az*bz,
    )

def quat_to_matrix(q):
    # Returns 3x3 rotation matrix (row-major as tuple of tuples)
    x,y,z,w = quat_normalize(q)
    # compute terms
    xx = x*x; yy = y*y; zz = z*z
    xy = x*y; xz = x*z; yz = y*z
    wx = w*x; wy = w*y; wz = w*z

    # Rotation matrix that maps sensor-frame vectors into world-frame:
    # R = [[1-2yy-2zz, 2xy-2wz, 2xz+2wy],
    #      [2xy+2wz, 1-2xx-2zz, 2yz-2wx],
    #      [2xz-2wy, 2yz+2wx, 1-2xx-2yy]]
    r00 = 1 - 2*(yy + zz)
    r01 = 2*(xy - wz)
    r02 = 2*(xz + wy)

    r10 = 2*(xy + wz)
    r11 = 1 - 2*(xx + zz)
    r12 = 2*(yz - wx)

    r20 = 2*(xz - wy)
    r21 = 2*(yz + wx)
    r22 = 1 - 2*(xx + yy)

    return ((r00, r01, r02),
            (r10, r11, r12),
            (r20, r21, r22))

def mat_mul_vec(m, v):
    return (
        m[0][0]*v[0] + m[0][1]*v[1] + m[0][2]*v[2],
        m[1][0]*v[0] + m[1][1]*v[1] + m[1][2]*v[2],
        m[2][0]*v[0] + m[2][1]*v[1] + m[2][2]*v[2],
    )

# ----------------------------
# Lat/Lon math
# ----------------------------
def clamp(x, a, b):
    return max(a, min(b, x))

def vector_to_latlon(v):
    vx,vy,vz = v
    mag = math.sqrt(vx*vx + vy*vy + vz*vz)
    if mag == 0:
        return None, None
    vx /= mag; vy /= mag; vz /= mag
    # latitude: asin(z)
    lat_rad = math.asin(clamp(vz, -1.0, 1.0))
    lon_rad = math.atan2(vy, vx)
    lat = math.degrees(lat_rad)
    lon = math.degrees(lon_rad)
    lon = ((lon + 180.0) % 360.0) - 180.0
    return lat, lon

# ----------------------------
# Globals / state
# ----------------------------
cal_quat = (0.0, 0.0, 0.0, 1.0)  # identity (no calibration)
verbose = True
smoothing_on = False
smooth_alpha = SMOOTH_ALPHA
smoothed_lat = None
smoothed_lon = None
last_lon = 0.0

# ----------------------------
# Input helper
# ----------------------------
def key_pressed():
    dr,_,_ = select.select([sys.stdin], [], [], 0)
    return dr != []

# ----------------------------
# Utility: pretty print matrix
# ----------------------------
def pretty_mat(m):
    return ("\n".join([
        f"[{m[0][0]: .4f} {m[0][1]: .4f} {m[0][2]: .4f}]",
        f"[{m[1][0]: .4f} {m[1][1]: .4f} {m[1][2]: .4f}]",
        f"[{m[2][0]: .4f} {m[2][1]: .4f} {m[2][2]: .4f}]",
    ]))

# ----------------------------
# Calibration function
# ----------------------------
def calibrate(current_q):
    global cal_quat
    # We want corrected_q = cal_quat * raw_q, and during calibration we want corrected_q == identity
    # So cal_quat = inverse(raw_q)
    cal_quat = quat_inverse(current_q)
    print("CALIBRATION saved (cal_quat = inverse of captured quaternion)")

# ----------------------------
# Pole handling helper
# ----------------------------
def handle_pole(lat, lon, f_w_z):
    # If forward vector z is extremely close to +/-1, longitude is ambiguous.
    # We keep previous lon to avoid wild jumps; mark ambiguous.
    ambiguous = False
    if abs(abs(f_w_z) - 1.0) < 1e-3:  # very near pole
        ambiguous = True
    return ambiguous

# ----------------------------
# Main diagnostic loop
# ----------------------------
async def diagnostic_loop():
    global sensor, verbose, smoothing_on, smoothed_lat, smoothed_lon, last_lon

    print("Starting diagnostic loop. Keys: c=calibrate, v=toggle verbose, s=toggle smoothing, q=quit")
    # set non-blocking stdin
    import tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while True:
            # read quaternion
            try:
                raw_q = sensor.quaternion  # (x,y,z,w)
            except Exception as e:
                print("Sensor read error:", e)
                raw_q = (0.0,0.0,0.0,1.0)

            raw_q = quat_normalize(raw_q)
            # apply calibration: corrected_q = cal_quat * raw_q
            corrected_q = quat_mul(cal_quat, raw_q)
            corrected_q = quat_normalize(corrected_q)

            # rotation matrix mapping sensor-frame -> world-frame
            R = quat_to_matrix(corrected_q)

            # rotate sensor axes to world
            f_w = mat_mul_vec(R, SENSOR_FORWARD)
            u_w = mat_mul_vec(R, SENSOR_UP)

            # compute lat/lon from forward vector in world coords
            lat, lon = vector_to_latlon(f_w)
            if lat is None:
                await asyncio.sleep(0.05)
                continue

            # pole handling / ambiguity
            f_w_z = f_w[2]
            ambiguous = handle_pole(lat, lon, f_w_z)
            if ambiguous:
                lon_display = f"{lon:.3f} (ambiguous near pole)"
            else:
                lon_display = f"{lon:.3f}"

            # smoothing
            if smoothing_on:
                if smoothed_lat is None:
                    smoothed_lat = lat
                    smoothed_lon = lon
                else:
                    # careful with longitude wrap crossing
                    # convert lon difference into [-180,180] delta
                    dlon = ((lon - smoothed_lon + 180) % 360) - 180
                    smoothed_lat = (1.0 - smooth_alpha)*smoothed_lat + smooth_alpha*lat
                    smoothed_lon = (smoothed_lon + smooth_alpha*dlon)
                    # normalize smoothed_lon into [-180,180]
                    smoothed_lon = ((smoothed_lon + 180.0) % 360.0) - 180.0
                lat_out = smoothed_lat
                lon_out = smoothed_lon
            else:
                lat_out = lat
                lon_out = lon

            # print diagnostic
            print("------------------------------------------------------------")
            print(f"raw_q (norm)   = ({raw_q[0]:.4f}, {raw_q[1]:.4f}, {raw_q[2]:.4f}, {raw_q[3]:.4f})")
            print(f"cal_quat       = ({cal_quat[0]:.4f}, {cal_quat[1]:.4f}, {cal_quat[2]:.4f}, {cal_quat[3]:.4f})")
            print(f"corrected_q    = ({corrected_q[0]:.4f}, {corrected_q[1]:.4f}, {corrected_q[2]:.4f}, {corrected_q[3]:.4f})")
            print(f"f_w (world fwd)= ({f_w[0]:.4f}, {f_w[1]:.4f}, {f_w[2]:.4f})")
            print(f"u_w (world up) = ({u_w[0]:.4f}, {u_w[1]:.4f}, {u_w[2]:.4f})")

            if verbose:
                print("Rotation matrix R (sensor->world):")
                print(pretty_mat(R))

            # gravity if available
            grav = None
            try:
                grav = sensor.gravity
            except Exception:
                grav = None
            if grav is not None:
                gx,gy,gz = grav
                print(f"gravity (raw)   = ({gx:.4f}, {gy:.4f}, {gz:.4f})")
            else:
                print("gravity         = (not available)")

            print(f"lat, lon (raw)  = {lat:.6f}, {lon_display}")
            print(f"lat, lon (out)  = {lat_out:.6f}, {lon_out:.6f}")
            if ambiguous:
                print("NOTE: near-pole ambiguity detected — longitude is unreliable here.")
            print("Controls: c=calibrate, v=toggle verbose, s=toggle smoothing, q=quit")
            sys.stdout.flush()

            # small sleep while checking for keypresses
            t0 = time.time()
            while time.time() - t0 < 0.12:
                if key_pressed():
                    ch = sys.stdin.read(1)
                    if ch.lower() == 'c':
                        print("Calibrating to current orientation (will set lat=0,lon=0 reference).")
                        calibrate(raw_q)  # use raw_q as captured orientation
                    elif ch.lower() == 'v':
                        verbose = not verbose
                        print("Verbose:", verbose)
                    elif ch.lower() == 's':
                        smoothing_on = not smoothing_on
                        smoothed_lat = None
                        smoothed_lon = None
                        print("Smoothing:", smoothing_on)
                    elif ch.lower() == 'q':
                        print("Quitting...")
                        return
                await asyncio.sleep(0.01)

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

# ----------------------------
# Entry
# ----------------------------
if __name__ == "__main__":
    try:
        asyncio.run(diagnostic_loop())
    except KeyboardInterrupt:
        print("\nInterrupted by user, exiting.")

import time, board, busio, digitalio
from adafruit_bno08x.i2c import BNO08X_I2C

# ---- Hardware reset pin ----
reset_pin = digitalio.DigitalInOut(board.D17)
reset_pin.direction = digitalio.Direction.OUTPUT

# ---- Hardware reset ----
print("Hardware reset...")
reset_pin.value = False
time.sleep(0.5)
reset_pin.value = True
time.sleep(1.5)

# ---- Bring up I2C ----
i2c = busio.I2C(board.SCL, board.SDA)
sensor = BNO08X_I2C(i2c, address=0x4A)

print("Sending SHTP reset packet...")

# -------------------------------
# LOW-LEVEL SH2 RESET COMMAND
# -------------------------------
# Channel 2 = Control Channel
# Report ID 1 = Reset
#
# Format:
#   Byte 0-1: payload length
#   Byte 2: channel number
#   Byte 3: sequence number
#   Byte 4: Report ID (0x01)
# -------------------------------

# Build packet
channel = 2
seq = sensor.sequence_numbers[channel]
packet = bytearray([0x01])  # Report ID: RESET

sensor._send_shtp_packet(channel, packet)
sensor.sequence_numbers[channel] = (seq + 1) & 0xFF

print("Reset command sent. Waiting...")
time.sleep(2)

print("Try running tiny_test.py again.")

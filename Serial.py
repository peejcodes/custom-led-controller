# """import serial
# import time
#
# # COM port is the one your ESP32 shows in Device Manager
# ser = serial.Serial("/dev/ttyACM0", 115200, timeout=1)
# #time.sleep(2)  # ESP32 resets on serial connection
#
# # Send predefined colors
# '''
# for color in ["red", "green", "blue","red", "green", "blue","red", "green", "blue"]:
#     ser.write((color + "\n").encode())
#     time.sleep(1)
# '''
#
# # Send custom RGB
# ser.write(b"0,0,10\n")
# """
#
# import serial
# import time
#
# class SerialManager:
#     def __init__(self, port="/dev/ttyACM0", baudrate=115200, timeout=1):
#         """
#         Initialize the serial connection to the ESP32.
#         """
#         self.port = port
#         self.baudrate = baudrate
#         self.timeout = timeout
#         self.ser = None
#
#     def connect(self):
#         """
#         Open the serial connection.
#         """
#         try:
#             self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
#             time.sleep(2)  # Give the ESP32 time to reset
#             print(f"Connected to {self.port} at {self.baudrate} baud.")
#         except serial.SerialException as e:
#             print(f"Failed to connect to {self.port}: {e}")
#
#     def disconnect(self):
#         """
#         Close the serial connection.
#         """
#         if self.ser and self.ser.is_open:
#             self.ser.close()
#             print("Serial connection closed.")
#
#     def send_color(self, pin, led, r, g, b):
#         """
#         Send an RGB color command for a specific pin and LED.
#         Example format sent: "12,5,255,100,50\n"
#         """
#         if not self.ser or not self.ser.is_open:
#             print("Serial connection not open.")
#             return
#
#         # Construct and send the message
#         command = f"{pin},{led},{r},{g},{b}\n"
#         self.ser.write(command.encode())
#
#     def send_predefined(self, color_name):
#         """
#         Send a predefined color name to the ESP32 (if your ESP32 code supports it).
#         Example: 'red', 'green', 'blue'
#         """
#         if not self.ser or not self.ser.is_open:
#             print("Serial connection not open.")
#             return
#
#         command = f"{color_name}\n"
#         self.ser.write(command.encode())
#
#     def read_line(self):
#         """
#         Read a single line of response from the ESP32.
#         """
#         if self.ser and self.ser.in_waiting:
#             return self.ser.readline().decode().strip()
#         return None
#
#
# colors = [
#     # Whites
#     "white", "bright_white", "soft_white", "dim_white", "warm_white", "cool_white",
#     # Reds
#     "red", "bright_red", "soft_red", "dim_red", "rose_red",
#     # Greens
#     "green", "bright_green", "soft_green", "dim_green", "mint_green", "forest_green",
#     # Blues
#     "blue", "bright_blue", "soft_blue", "dim_blue", "sky_blue", "deep_blue",
#     # Yellows and Oranges
#     "yellow", "warm_yellow", "amber", "orange", "gold", "dim_amber",
#     # Purples / Pinks
#     "purple", "soft_purple", "violet", "magenta", "pink", "hot_pink", "lavender",
#     # Cyans / Aquas
#     "cyan", "bright_cyan", "aqua", "teal", "seafoam",
#     # Browns and Earth tones
#     "brown", "tan", "chocolate", "sienna",
#     # Grays (brightness-based)
#     "very_dim_white", "soft_gray", "bright_gray",
#     # Novel / effect tones
#     "flame", "sunset", "ice", "mint", "turquoise", "aqua_white"
# ]
#
#
#
# sm = SerialManager("/dev/ttyACM0", 115200)
# sm.connect()
#
# # Send to pin 12, LED 0 with color (255, 0, 100)
#
# sm.send_color(48, 0, 150, 0, 150)
# time.sleep(1)
# #sm.send_predefined("teal")
# time.sleep(1)
# # Optional predefined color
# #sm.send_predefined("red")
# '''print(len(colors))
# for i in range(len(colors)):
#     sm.send_predefined(colors[i])
#     time.sleep(0.5)
#
# '''
# # Read any incoming data
# response = sm.read_line()
# if response:
#     print("ESP32 says:", response)
#
# sm.disconnect()

"""
#------------V1---------------
# serial_test.py (PC)
import serial
import time

PORT = "/dev/ttyACM0"
BAUD = 115200
PIN = 48
LED = 0

def open_serial():
    ser = serial.Serial(PORT, BAUD, timeout=1)
    # Some ESP32 auto-reset circuits toggle via DTR/RTS; keep stable after open:
    try:
        ser.dtr = False
        ser.rts = False
    except Exception:
        pass
    time.sleep(0.5)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    return ser

def wait_ready(ser, timeout_s=5.0):
    ser.write(b"PING\n")
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        line = ser.readline().decode(errors="replace").strip()
        if line == "#READY":
            return True
    return False

def send_packet(ser, seq, pin, led, r, g, b):
    msg = f"{seq},{pin},{led},{r},{g},{b}\n"
    ser.write(msg.encode())

def read_ack(ser, timeout_s=1.0):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        line = ser.readline().decode(errors="replace").strip()
        if not line:
            continue
        # Expect: ACK,seq,ok   or ERR,....
        return line
    return None

def main():
    ser = open_serial()
    try:
        if not wait_ready(ser, 6.0):
            raise RuntimeError("Did not see #READY from ESP32 (script not running / wrong port / reset loop).")

        errors = 0

        for seq in range(256):
            v = seq  # r=g=b=v
            send_packet(ser, seq, PIN, LED, v, v, v)

            resp = read_ack(ser, 1.5)
            if resp is None:
                print(f"NO_ACK for seq={seq}")
                errors += 1
                continue

            if resp.startswith("ACK,"):
                parts = resp.split(",")
                if len(parts) >= 3 and parts[1].isdigit():
                    ack_seq = int(parts[1])
                    if ack_seq != seq:
                        print(f"ACK_MISMATCH sent={seq} got={resp}")
                        errors += 1
                else:
                    print(f"BAD_ACK_FORMAT: {resp}")
                    errors += 1
            elif resp.startswith("ERR,"):
                print(f"ESP_ERR for seq={seq}: {resp}")
                errors += 1
            else:
                # unexpected line (boot noise, etc.)
                print(f"UNEXPECTED: {resp}")
                errors += 1

            # small pacing if you want
            # time.sleep(0.01)

        # Ask ESP to print status + last packets
        ser.write(b"DUMP\n")
        t0 = time.time()
        while time.time() - t0 < 2.0:
            line = ser.readline().decode(errors="replace").strip()
            if line:
                print(line)

        print(f"Done. errors={errors}")

    finally:
        ser.close()

if __name__ == "__main__":
    main()
"""

import serial
import time

PORT = "/dev/ttyACM0"
BAUD = 921600
PIN = 48
LED = 0

RUN_FUNCTIONAL_256 = True
RUN_BENCH_UNACKED = True
RUN_BENCH_ACKED = True

UNACKED_N = 2000
ACKED_N = 1000


def open_serial():
    ser = serial.Serial(PORT, BAUD, timeout=1)
    try:
        ser.dtr = False
        ser.rts = False
    except Exception:
        pass
    time.sleep(0.5)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    return ser


def send_cmd(ser, cmd):
    ser.write((cmd.strip() + "\n").encode())


def read_line(ser, timeout_s=1.0):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            line = ser.readline().decode(errors="replace").strip()
        except serial.SerialException as e:
            raise RuntimeError(f"Serial error while reading: {e}")
        if line:
            return line
    return None


def read_until_prefix(ser, prefix, timeout_s=2.0):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        line = read_line(ser, timeout_s=timeout_s)
        if not line:
            continue
        if line.startswith(prefix):
            return line
        # ignore unrelated lines (old ACKs, etc.)
    return None


def wait_ready(ser, timeout_s=5.0):
    send_cmd(ser, "PING")
    line = read_until_prefix(ser, "#READY", timeout_s=timeout_s)
    return line is not None


def send_packet(ser, seq, pin, led, r, g, b):
    ser.write(f"{seq},{pin},{led},{r},{g},{b}\n".encode())


def esp_rate(ser):
    ser.reset_input_buffer()
    send_cmd(ser, "RATE")
    line = read_until_prefix(ser, "RATE,", timeout_s=2.0)
    if line:
        print(line)


def drain(ser, seconds=0.5):
    t0 = time.time()
    while time.time() - t0 < seconds:
        line = read_line(ser, timeout_s=0.1)
        if line:
            print(line)


def functional_256(ser):
    errors = 0
    for seq in range(256):
        v = seq
        send_packet(ser, seq, PIN, LED, v, v, v)

        resp = read_until_prefix(ser, "ACK,", timeout_s=2.0)
        if resp is None:
            print(f"NO_ACK for seq={seq}")
            errors += 1
            continue

        parts = resp.split(",")
        if len(parts) >= 3 and parts[1].isdigit():
            ack_seq = int(parts[1])
            if ack_seq != seq:
                print(f"ACK_MISMATCH sent={seq} got={resp}")
                errors += 1
        else:
            print(f"BAD_ACK_FORMAT: {resp}")
            errors += 1

    print(f"Functional 0..255 done. errors={errors}")


def bench_unacked(ser, n):
    # Disable output from ESP so we don't flood host RX and stall USB CDC
    ser.reset_input_buffer()
    send_cmd(ser, "LOGOFF")
    read_until_prefix(ser, "ACK,", timeout_s=1.0)  # ack for logoff

    send_cmd(ser, "ACKOFF")
    read_until_prefix(ser, "ACK,", timeout_s=1.0)  # ack for ackoff

    # now ESP is quiet while receiving packets
    t0 = time.perf_counter()
    for seq in range(n):
        v = seq & 0xFF
        send_packet(ser, seq, PIN, LED, v, v, v)
    ser.flush()
    dt = time.perf_counter() - t0
    print(f"UNACKED: {n/dt:.1f} msg/s   ({n} msgs in {dt:.3f}s)")

    # Turn ACK back on for queries / next phases
    send_cmd(ser, "ACKON")
    read_until_prefix(ser, "ACK,", timeout_s=1.0)

    esp_rate(ser)


def bench_acked(ser, n):
    # Keep logging off for speed, keep ACKs on
    ser.reset_input_buffer()
    send_cmd(ser, "LOGOFF")
    read_until_prefix(ser, "ACK,", timeout_s=1.0)

    send_cmd(ser, "ACKON")
    read_until_prefix(ser, "ACK,", timeout_s=1.0)

    errors = 0
    t0 = time.perf_counter()
    for seq in range(n):
        v = seq & 0xFF
        send_packet(ser, seq, PIN, LED, v, v, v)

        resp = read_until_prefix(ser, "ACK,", timeout_s=2.0)
        if resp is None:
            errors += 1
            continue

        parts = resp.split(",")
        if len(parts) >= 3 and parts[1].lstrip("-").isdigit():
            ack_seq = int(parts[1])
            if ack_seq != seq:
                errors += 1
        else:
            errors += 1

    dt = time.perf_counter() - t0
    print(f"ACKED:   {n/dt:.1f} msg/s   ({n} msgs in {dt:.3f}s)  errors={errors}")

    esp_rate(ser)


def main():
    ser = open_serial()
    try:
        if not wait_ready(ser, 6.0):
            raise RuntimeError("Did not see #READY from ESP32.")

        send_cmd(ser, "RESET")
        read_until_prefix(ser, "ACK,", timeout_s=2.0)

        esp_rate(ser)

        if RUN_FUNCTIONAL_256:
            send_cmd(ser, "ACKON")
            read_until_prefix(ser, "ACK,", timeout_s=1.0)
            send_cmd(ser, "LOGON")
            read_until_prefix(ser, "ACK,", timeout_s=1.0)

            functional_256(ser)
            esp_rate(ser)

        if RUN_BENCH_UNACKED:
            bench_unacked(ser, UNACKED_N)

        if RUN_BENCH_ACKED:
            bench_acked(ser, ACKED_N)

        # restore logging if you want logs after benches
        send_cmd(ser, "LOGON")
        read_until_prefix(ser, "ACK,", timeout_s=1.0)

        send_cmd(ser, "DUMP")
        drain(ser, 2.0)

    finally:
        ser.close()


if __name__ == "__main__":
    main()

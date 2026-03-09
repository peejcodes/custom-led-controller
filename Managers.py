# -------------------
# Library Imports
# -------------------
import json
import os
import serial
import time


# -------------------
# Class Imports
# -------------------


# -----------------------------
# Theme Manager
# -----------------------------
class ThemeManager:
    def __init__(self, theme_file="theme.json"):
        self.theme_file = theme_file
        # default theme structure (simple example)
        self.theme = {
            "Button": {"color_normal": (50, 50, 50), "color_hover": (70, 70, 70),
                       "color_pressed": (30, 30, 30)},  "Label": {"text_color": (255, 255, 255)}
        }
        self.load_theme()

    def load_theme(self):
        if os.path.exists(self.theme_file):
            with open(self.theme_file, "r") as f:
                user_theme = json.load(f)
                for widget_type, settings in user_theme.items():
                    if widget_type in self.theme:
                        self.theme[widget_type].update(settings)
        else:
            with open(self.theme_file, "w") as f:
                json.dump(self.theme, f, indent=4)

    def get(self, widget_type, key, fallback=None):
        return self.theme.get(widget_type, {}).get(key, fallback)


# -----------------------------
# Page Manager
# -----------------------------
class PageManager:
    def __init__(self):
        self.pages = {}
        self.current = None
        self.active_color_picker = None

    def add_page(self, page):
        self.pages[page.name] = page
        if self.current is None:
            self.current = page.name

    def set_page(self, name):
        if name in self.pages:
            self.current = name

    def get_current(self):
        return self.pages.get(self.current, None)

    def draw(self, screen):
        page = self.get_current()
        if page:
            page.draw(screen)

    def handle_event(self, event):
        page = self.get_current()
        if page:
            page.handle_event(event)

    def update(self, dt):
        page = self.get_current()
        if page:
            page.update(dt)



# -----------------------------
# Serial Manager
# -----------------------------
import serial
import struct
import time

START_BYTE = 0xAA
END_BYTE = 0x55

class SerialManager:
    def __init__(self, port="/dev/ttyACM0", baud=115200):
        self.ser = serial.Serial(port, baud, timeout=1)
        print("[SerialManager] Connected")

    def _read_ack(self):
        line = self.ser.readline().decode().strip()
        return line == "ACK"

    # -------------------------
    # Setup strip (16-bit LED count)
    # -------------------------
    def setup_strip(self, strip_id, segment_id, pin, led_count):
        # Pack: 0x01, strip_id, segment_id, pin, led_count_hi, led_count_lo
        frame = struct.pack(">BBBBH", 0x01, strip_id, segment_id, pin, led_count)
        packet = bytes([START_BYTE]) + frame + bytes([END_BYTE])
        self.ser.write(packet)
        time.sleep(0.05)
        if not self._read_ack():
            print("Setup failed")
        else:
            print("Setup ACK received")

    # -------------------------
    # LED updates (16-bit index)
    # -------------------------
    def send_led_updates(self, updates):
        """
        updates = [(strip_id, segment_id, led_index, r, g, b), ...]
        """
        count = len(updates)
        payload = b''.join(struct.pack(">BBHBBB", *u) for u in updates)  # 16-bit index
        packet = bytes([START_BYTE, count]) + payload + bytes([END_BYTE])
        self.ser.write(packet)
        time.sleep(0.01)
        if not self._read_ack():
            print("Packet failed")
        else:
            print("ACK OK")

    def close(self):
        self.ser.close()


# -------------------------
# Example Usage
# -------------------------
if __name__ == "__main__":
    sm = SerialManager()
    sm.setup_strip(0, 0, 48, 500)  # 500 LEDs example

    # send first 5 LEDs red gradient
    for i in range(5):
        sm.send_led_updates([(0, 0, i, 50 * i % 255, 0, 0)])
        time.sleep(0.2)

    sm.close()

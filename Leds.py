# -------------------
# Library Imports
# -------------------
import pygame


# -------------------
# Class Imports
# -------------------
from Variables import SCALE

# =========================
# Controller Class
# =========================
class Controller:
    """
    Top-level controller for managing multiple strips of LEDs.
    """

    def __init__(self):
        self.strips = []

    def add_strip(self, led_qty, max_mA):
        """Add a new LED strip."""
        strip = Strip(led_qty, max_mA)
        self.strips.append(strip)
        return strip

    def set_global_brightness(self, brightness):
        """Set brightness for all LEDs in all strips."""
        for strip in self.strips:
            for led in strip.leds:
                led.set_brightness(brightness)
            strip.calc_mA()

    def set_all_color(self, r, g, b):
        """Set all LEDs in all strips to the same color."""
        for strip in self.strips:
            for led in strip.leds:
                led.color = Color(r, g, b)
                led.update()
            strip.calc_mA()

    def set_led(self, strip_index, led_index, r, g, b):
        """Set a specific LED to a color by strip and index."""
        try:
            led = self.strips[strip_index].leds[led_index]
            led.color = Color(r, g, b)
            led.update()
            self.strips[strip_index].calc_mA()
        except IndexError:
            print("Invalid LED or strip index")

    def print_status(self):
        """Print strip and LED status: colors, brightness, current."""
        for idx, strip in enumerate(self.strips):
            print(f"Strip {idx}: {strip.calc_mA():.2f} mA total")
            for i, led in enumerate(strip.leds):
                c = led.color
                print(f"  LED {i}: RGB=({c.r},{c.g},{c.b}) "
                      f"Brightness={led.brightness:.2f} mA={led.mA:.2f}")


# -------------------
# LED Visualizer CLASS
# -------------------
class Led():
    """
    Represents a single LED rectangle on screen.
    Each LED has a position, size, and color.
    """

    def __init__(self, position_x, position_y, surface, color=(255, 0, 0)):
        self.color = Color(color)
        self.position_x = position_x #
        self.position_y = position_y
        self.surface = surface
        # Width and height are scaled so the LEDs look correct on any screen scaling
        self.width = int(11*SCALE)
        self.height = int(40*SCALE)
        self.update()

    def change_color(self, new_color):
        """Change the color of this LED."""
        self.color = new_color

    def draw_led(self, screen):
        """Draw this LED as a filled rectangle with a black outline."""
        rect = (self.position_x, self.position_y, self.width, self.height)
        pygame.draw.rect(screen, self.color, rect, width=0)  # Fill
        pygame.draw.rect(screen, (0, 0, 0), rect, width=2)  # Outline

    def update(self):
        """Recalculate brightness (0.0–1.0) and estimated current draw (mA)."""
        self.brightness = (self.color.r + self.color.g + self.color.b) / (255 * 3)
        self.mA = 60 * self.brightness  # assume max 60mA per LED

    def set_brightness(self, target_brightness):
        """
        Adjust RGB values to achieve target brightness (0.0–1.0),
        preserving color ratios.
        """
        current_brightness = (self.color.r + self.color.g + self.color.b) / (255 * 3)
        if current_brightness == 0:
            # If off, just scale uniformly to target brightness
            values = int(target_brightness * 255)
            self.color.r = values
            self.color.g = values
            self.color.b = values
            return

        scale = target_brightness / current_brightness
        self.color.r = min(int(self.color.r * scale), 255)
        self.color.g = min(int(self.color.g * scale), 255)
        self.color.b = min(int(self.color.b * scale), 255)
        self.update()


# =========================
# Segment Class
# =========================
class Segment:
    """
    A segment is a group of LEDs within a strip,
    with a maximum current allowance.
    """

    def __init__(self, led_qty, max_mA):
        self.led_qty = led_qty
        self.max_mA = max_mA
        self.led_array = []
        self.actual_mA = 0
        self.build_leds()

    def build_leds(self):
        """Populate the segment with default LEDs (dim white)."""
        self.led_array = []
        self.actual_mA = 0
        for _ in range(self.led_qty):
            pixel = Led(100, 100, 100)
            self.led_array.append(pixel)
            self.actual_mA += pixel.mA

    def calc_mA(self):
        """Recalculate current draw of all LEDs in the segment."""
        self.actual_mA = 0
        for led in self.led_array:
            led.update()
            self.actual_mA += led.mA
        return self.actual_mA


# =========================
# Strip Class
# =========================
class Strip:
    """
    A strip is a collection of segments. Typically one long LED strip.
    """

    def __init__(self, led_qty, max_mA):
        self.led_qty = led_qty
        self.max_mA = max_mA
        self.segments = []
        # By default, create one segment covering the entire strip
        self.add_segment(led_qty, max_mA)

    def add_segment(self, led_qty, max_mA):
        """Add a segment with given LED count and current limit."""
        seg = Segment(led_qty, max_mA)
        self.segments.append(seg)
        return seg

    def calc_mA(self):
        """Return total current draw across all segments."""
        return sum(seg.calc_mA() for seg in self.segments)

    @property
    def leds(self):
        """Flattened list of all LEDs in all segments."""
        leds = []
        for seg in self.segments:
            leds.extend(seg.led_array)
        return leds


# =========================
# Extended Color Class
# =========================
class Color(pygame.Color):
    """
    Extended pygame.Color with extra helpers for HSV (0–1 range),
    blending, and inversion.
    """

    # ---- Normalized HSV (0.0–1.0 instead of deg/% for convenience) ----
    @property
    def hsv01(self):
        """Get HSV as (h, s, v) normalized to 0.0–1.0 instead of degrees/percent."""
        h, s, v, a = self.hsva
        return h / 360.0, s / 100.0, v / 100.0

    @hsv01.setter
    def hsv01(self, hsv):
        """Set color using normalized (h, s, v) values in 0.0–1.0 range."""
        h, s, v = hsv
        self.hsva = (h * 360.0, s * 100.0, v * 100.0, 100)

    # ---- Blending ----
    def blend(self, other, ratio=0.5):
        """
        Blend this color with another Color.
        ratio=0.0 returns self, ratio=1.0 returns other.
        """
        r = int(self.r * (1 - ratio) + other.r * ratio)
        g = int(self.g * (1 - ratio) + other.g * ratio)
        b = int(self.b * (1 - ratio) + other.b * ratio)
        a = int(self.a * (1 - ratio) + other.a * ratio)
        return Color(r, g, b, a)

    # ---- Inversion ----
    def invert(self):
        """Return the inverse (complementary) color."""
        return Color(255 - self.r, 255 - self.g, 255 - self.b, self.a)

# =========================
# Palette Class
# =========================
class Palette:
    """
    A palette stores up to 3 colors that can be combined
    into gradients or used by patterns.
    """

    def __init__(self):
        self.primary_color = (0, 0, 0)
        self.secondary_color = (0, 0, 0)
        self.tertiary_color = (0, 0, 0)
        self.palettes = ["default", "color_1", "gradient", "color_1+2", "color_1+2+3"]

    def set_primary(self, r, g, b):
        self.primary_color = Color(r, g, b)

    def set_secondary(self, r, g, b):
        self.secondary_color = Color(r, g, b)

    def set_tertiary(self, r, g, b):
        self.tertiary_color = Color(r, g, b)


# =========================
# Pattern Class
# =========================
class Pattern:
    """
    A pattern defines how colors are animated/applied
    to LEDs using a palette.
    """

    def __init__(self):
        self.palette = Palette()
        # Available effect patterns (placeholder list)
        self.patterns = [
            "1_color", "2_color_gradient", "3_color_gradient", "blend", "blink", "blink_rainbow",
            "bouncing_balls", "candle", "chase", "rainbow_cycle", "dj_light", "dissolve",
            "dissolve_random", "rain", "dynamic", "dynamic_smooth", "fade", "fairy",
            "fill_noise", "fireworks", "flow", "glitter", "grav_center", "grav_centric",
            "grav_freq", "grav_meter", "heartbeat", "juggle", "juggles", "lake",
            "lighthouse", "lightning", "loading", "matrix", "meteor", "meteor_smooth",
            "mid_noise", "noise_1", "noise_2", "noise_3", "noise_4", "noise_pal",
            "pacifica", "palette", "phased", "phased_noise", "pixels", "pixelwave",
            "plasma", "plasmoid", "popcorn", "pride_cycle", "puddles", "railway",
            "random_solid", "ripple_peak", "rocktaves", "running", "running_dual",
            "saw", "scan", "scan_dual", "sine", "sinelon", "solid_glitter",
            "solid_pattern", "solid_pattern_tri", "sparkle", "sparkle_dark", "sparkle+"
        ]
        self.current_pattern = "1_color"


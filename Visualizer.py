# -------------------
# Library Imports
# -------------------
import pygame
import math

# -------------------
# Class Imports
# -------------------
from Variables import SCALE, SCREEN_WIDTH, SCREEN_HEIGHT
from Widgets import Label, Button
from Leds import Led


# -------------------
# VISUALIZER
# -------------------
class LedVisualizer():
    """
    Controls and manages an array of LED objects.
    Handles patterns, speed, and drawing logic.
    """

    def __init__(self, screen, num_leds=80, speed=1, pattern_index=3):
        # Available pattern names (index-based navigation)
        self.pattern_list = ['solid', 'chase', 'pulse', 'wave', 'rainbow', 'strobe', 'fire', 'bounce']
        self.num_leds = num_leds  # Total number of LEDs
        self.speed = speed  # Speed modifier for patterns
        self.leds = []  # List that will store Led() objects
        self.pattern_index = pattern_index
        self.screen = screen
        self.set_leds()  # Initialize LEDs immediately

    @property
    def pattern(self):
        """Convenience property to get the current pattern name."""
        return self.pattern_list[self.pattern_index]

    def set_leds(self):
        """Position and create all LED objects in a row near the bottom of the screen."""
        self.leds.clear()
        for i in range(self.num_leds):
            # Space LEDs horizontally with spacing of 11px each, offset 120px from left
            x = int((i * ((SCREEN_WIDTH-160)/self.num_leds)+155)*SCALE)
            print(SCREEN_WIDTH)
            print(x)
            y = int(SCREEN_HEIGHT-50*SCALE)  # Fixed vertical position
            self.leds.append(Led(x, y, self.screen))

    def draw_leds(self):
        """Draw all LEDs on the screen."""
        for led in self.leds:
            led.draw_led(self.screen)

    def set_solid(self, color):
        """Set all LEDs to the same solid color."""
        for led in self.leds:
            led.change_color(color)

    def speed_up(self):
        """Increase animation speed."""
        self.speed += 1

    def speed_down(self):
        """Decrease animation speed but not below zero."""
        self.speed = max(0, self.speed - 1)

    # -------------------
    # PATTERN FUNCTIONS
    # -------------------
    # Each pattern takes elapsed_time and updates LEDs accordingly.

    def pattern_solid(self, elapsed_time):
        """All LEDs are set to solid green, regardless of time."""
        self.set_solid((0, 255, 0))

    def pattern_chase(self, elapsed_time):
        """A single green LED chases across blue LEDs."""
        index = int((elapsed_time * self.speed) % self.num_leds)
        for i, led in enumerate(self.leds):
            if i == index:
                led.change_color((0, 255, 0))  # Active LED
            else:
                led.change_color((0, 0, 255))  # Inactive LEDs

    def pattern_pulse(self, elapsed_time):
        """All LEDs pulse red, brightness modulated by a sine wave."""
        brightness = (math.sin(elapsed_time * self.speed) + 1) / 2
        color = (int(255 * brightness), 0, 0)
        for led in self.leds:
            led.change_color(color)

    def pattern_wave(self, elapsed_time):
        """Creates a moving sine wave pattern across LEDs with cyan-magenta blending."""
        for i, led in enumerate(self.leds):
            brightness = (math.sin((i / 5.0) + elapsed_time * self.speed) + 1) / 2
            color = (0, int(255 * brightness), 255 - int(255 * brightness))
            led.change_color(color)

    def pattern_rainbow(self, elapsed_time):
        """Cycle through rainbow colors smoothly across LEDs."""
        for i, led in enumerate(self.leds):
            hue = (i / self.num_leds + elapsed_time * self.speed * 0.1) % 1.0
            color = pygame.Color(0)
            color.hsva = (hue * 360, 100, 100, 100)
            led.change_color(color)

    def pattern_strobe(self, elapsed_time):
        """All LEDs strobe between white and black at the set speed."""
        phase = int(elapsed_time * self.speed) % 2
        color = (255, 255, 255) if phase == 0 else (0, 0, 0)
        for led in self.leds:
            led.change_color(color)

    def pattern_fire(self, elapsed_time):
        """Random flickering fire effect using red/yellow/orange hues."""
        import random
        for led in self.leds:
            r = random.randint(180, 255)
            g = random.randint(50, 150)
            b = random.randint(0, 50)
            led.change_color((r, g, b))

    def pattern_bounce(self, elapsed_time):
        """Single LED bounces back and forth across the strip."""
        cycle = int((elapsed_time * self.speed) % ((self.num_leds - 1) * 2))
        index = cycle if cycle < self.num_leds else (2 * self.num_leds - cycle - 2)
        for i, led in enumerate(self.leds):
            if i == index:
                led.change_color((255, 0, 0))  # Active bouncing LED
            else:
                led.change_color((0, 0, 0))

    # -------------------
    # DISPATCHER
    # -------------------
    def run_pattern(self, elapsed_time):
        """Run the currently selected pattern."""
        if self.pattern == 'solid':
            self.pattern_solid(elapsed_time)
        elif self.pattern == 'chase':
            self.pattern_chase(elapsed_time)
        elif self.pattern == 'pulse':
            self.pattern_pulse(elapsed_time)
        elif self.pattern == 'wave':
            self.pattern_wave(elapsed_time)
        elif self.pattern == 'rainbow':
            self.pattern_rainbow(elapsed_time)
        elif self.pattern == 'strobe':
            self.pattern_strobe(elapsed_time)
        elif self.pattern == 'fire':
            self.pattern_fire(elapsed_time)
        elif self.pattern == 'bounce':
            self.pattern_bounce(elapsed_time)
        else:
            self.set_solid((128, 128, 128))  # Fallback gray if pattern not found


# -----------------------------
# Visualizer Controls
# -----------------------------
class VisualizerControls:
    def __init__(self, font, visualizer, manager):
        self.visualizer = visualizer
        self.font = font
        self.manager = manager

        # Pattern label
        self.pattern_label = Label(
            rect=(int(325/800*SCREEN_WIDTH*SCALE), int(400/480*SCREEN_HEIGHT*SCALE), int(300/800*SCREEN_WIDTH*SCALE), int(40/480*SCREEN_HEIGHT*SCALE)),
            text=f"Pattern: {self.visualizer.pattern}",
            font=font,
            text_color=(255, 255, 255),
            bg_color=(0, 0, 0),
            border_radius=int(2*SCALE)
        )

        # Buttons
        self.buttons = [
            Button(rect=(int((175 + 55)/800*SCREEN_WIDTH*SCALE)-25, int(400/480*SCREEN_HEIGHT*SCALE), int(50/800*SCREEN_WIDTH*SCALE), int(40/480*SCREEN_HEIGHT*SCALE)),
                   text="-", font=font,
                   command=self.visualizer.speed_down, border_radius=2),
            Button(rect=(int(670/800*SCREEN_WIDTH*SCALE), int(400/480*SCREEN_HEIGHT*SCALE), int(50/800*SCREEN_WIDTH*SCALE), int(40/480*SCREEN_HEIGHT*SCALE)),
                   text="+", font=font,
                   command=self.visualizer.speed_up, border_radius=2),
            Button(rect=(int(175/800*SCREEN_WIDTH*SCALE)-25, int(400/480*SCREEN_HEIGHT*SCALE), int(50/800*SCREEN_WIDTH*SCALE), int(40/480*SCREEN_HEIGHT*SCALE)),
                   text="<", font=font,
                   command=self.prev_pattern, border_radius=2),
            Button(rect=(int((775 - 50)/800*SCREEN_WIDTH*SCALE), int(400/480*SCREEN_HEIGHT*SCALE), int(50/800*SCREEN_WIDTH*SCALE), int(40/480*SCREEN_HEIGHT*SCALE)),
                   text=">", font=font,
                   command=self.next_pattern, border_radius=2),
        ]

    def prev_pattern(self):
        self.visualizer.pattern_index = (self.visualizer.pattern_index - 1) % len(self.visualizer.pattern_list)
        self.update_label()

    def next_pattern(self):
        self.visualizer.pattern_index = (self.visualizer.pattern_index + 1) % len(self.visualizer.pattern_list)
        self.update_label()

    def update_label(self):
        self.pattern_label.text = f"Pattern: {self.visualizer.pattern}"
        self.pattern_label.text_surf = self.font.render(
            self.pattern_label.text, True, self.pattern_label.text_color
        )

    def handle_event(self, event):
        self.pattern_label.handle_event(event)
        for b in self.buttons:
            b.handle_event(event)

    def update(self, dt):
        self.pattern_label.update(dt)
        for b in self.buttons:
            b.update(dt)

    def draw(self, screen):
        self.pattern_label.draw(screen)
        for b in self.buttons:
            b.draw(screen)
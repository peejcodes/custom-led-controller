"""A large grab bag of LED strip and LED grid patterns.

This module is intentionally standalone so you can drop it into an existing
controller project without dragging in big dependencies.

Design assumptions:
    - 1D patterns return a list of RGB tuples, one tuple per LED.
    - 2D patterns return a grid of RGB tuples as ``grid[y][x]``.
    - Time ``t`` is expressed in seconds and can come from ``time.time()``
      or from your animation loop's running timer.
    - Colors use 8-bit RGB integers in the range 0-255.

The patterns below are inspired by classic LED effects seen in projects like
WLED, FastLED demos, arcade marquees, stage lighting, and decorative holiday
installs, but the implementations here are written as a fresh Python module
with a simple API.
"""

from __future__ import annotations

from dataclasses import dataclass
import colorsys
import math
from typing import Callable, Sequence


Color = tuple[int, int, int]
Frame1D = list[Color]
Frame2D = list[list[Color]]
Palette = Sequence[Color]

TAU = math.tau
BLACK: Color = (0, 0, 0)
WHITE: Color = (255, 255, 255)

SUNSET_PALETTE: tuple[Color, ...] = (
    (6, 11, 28),
    (33, 41, 77),
    (135, 56, 62),
    (234, 120, 76),
    (255, 205, 120),
    (255, 245, 220),
)
FIRE_PALETTE: tuple[Color, ...] = (
    (0, 0, 0),
    (40, 0, 0),
    (120, 10, 0),
    (220, 40, 0),
    (255, 140, 0),
    (255, 230, 130),
    (255, 255, 255),
)
LAVA_PALETTE: tuple[Color, ...] = (
    (18, 0, 0),
    (70, 4, 0),
    (145, 15, 0),
    (220, 50, 0),
    (255, 120, 10),
    (255, 215, 80),
)
OCEAN_PALETTE: tuple[Color, ...] = (
    (0, 8, 25),
    (0, 34, 70),
    (0, 82, 125),
    (0, 148, 180),
    (80, 220, 210),
    (220, 255, 250),
)
AURORA_PALETTE: tuple[Color, ...] = (
    (0, 6, 18),
    (0, 35, 50),
    (0, 120, 90),
    (60, 220, 135),
    (130, 255, 200),
    (160, 110, 255),
)
PARTY_PALETTE: tuple[Color, ...] = (
    (255, 0, 102),
    (255, 110, 0),
    (255, 235, 0),
    (0, 210, 120),
    (0, 160, 255),
    (175, 90, 255),
)
ICE_PALETTE: tuple[Color, ...] = (
    (0, 0, 20),
    (0, 40, 90),
    (30, 140, 210),
    (120, 220, 255),
    (235, 255, 255),
)
NEON_PALETTE: tuple[Color, ...] = (
    (255, 30, 130),
    (20, 255, 220),
    (255, 250, 60),
    (110, 90, 255),
)
STORM_PALETTE: tuple[Color, ...] = (
    (3, 6, 14),
    (18, 28, 50),
    (40, 58, 90),
    (100, 125, 155),
    (220, 235, 255),
)
FOREST_PALETTE: tuple[Color, ...] = (
    (5, 18, 8),
    (15, 45, 15),
    (45, 95, 35),
    (110, 150, 70),
    (220, 235, 190),
)
TERRAIN_PALETTE: tuple[Color, ...] = (
    (0, 25, 65),
    (0, 90, 120),
    (40, 135, 65),
    (95, 165, 80),
    (170, 150, 95),
    (230, 230, 230),
)


@dataclass(frozen=True)
class PatternInfo:
    """Metadata that makes pattern discovery easier in a UI or controller."""

    name: str
    dimension: str
    summary: str
    function: Callable[..., object]


PATTERNS_1D: dict[str, PatternInfo] = {}
PATTERNS_2D: dict[str, PatternInfo] = {}


def register_1d(summary: str) -> Callable[[Callable[..., Frame1D]], Callable[..., Frame1D]]:
    """Store a 1D pattern in the registry as soon as it is defined."""

    def decorator(function: Callable[..., Frame1D]) -> Callable[..., Frame1D]:
        PATTERNS_1D[function.__name__] = PatternInfo(
            name=function.__name__,
            dimension="1d",
            summary=summary,
            function=function,
        )
        return function

    return decorator


def register_2d(summary: str) -> Callable[[Callable[..., Frame2D]], Callable[..., Frame2D]]:
    """Store a 2D pattern in the registry as soon as it is defined."""

    def decorator(function: Callable[..., Frame2D]) -> Callable[..., Frame2D]:
        PATTERNS_2D[function.__name__] = PatternInfo(
            name=function.__name__,
            dimension="2d",
            summary=summary,
            function=function,
        )
        return function

    return decorator


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Keep a number inside a fixed range."""

    return max(minimum, min(maximum, value))


def clamp01(value: float) -> float:
    """Shortcut for clamping a value to the common 0.0 - 1.0 range."""

    return clamp(value, 0.0, 1.0)


def fract(value: float) -> float:
    """Return only the fractional part of a number."""

    return value - math.floor(value)


def smoothstep(value: float) -> float:
    """Ease a 0-1 value so movement looks softer and less robotic."""

    value = clamp01(value)
    return value * value * (3.0 - 2.0 * value)


def ping_pong(value: float, length: float) -> float:
    """Bounce a value back and forth between 0 and ``length``."""

    if length <= 0:
        return 0.0
    wrapped = value % (2.0 * length)
    return length - abs(wrapped - length)


def triangle_wave(value: float) -> float:
    """Produce a repeating 0-1-0 shape used for marching or pulsing motion."""

    return 1.0 - abs((value % 2.0) - 1.0)


def normalize_index(index: int, size: int) -> float:
    """Convert an LED index into a 0.0 - 1.0 position."""

    if size <= 1:
        return 0.0
    return index / float(size - 1)


def centered_coord(index: int, size: int) -> float:
    """Convert an index into a -1.0 to 1.0 position around the center."""

    return normalize_index(index, size) * 2.0 - 1.0


def clamp_channel(value: float) -> int:
    """Clamp a single color channel to a valid 8-bit integer."""

    return int(round(clamp(value, 0.0, 255.0)))


def clamp_color(color: Sequence[float]) -> Color:
    """Clamp a full RGB color into a tuple of 8-bit integers."""

    return (
        clamp_channel(color[0]),
        clamp_channel(color[1]),
        clamp_channel(color[2]),
    )


def add_colors(*colors: Color) -> Color:
    """Add several colors together and clamp the result to a valid RGB color."""

    red = sum(color[0] for color in colors)
    green = sum(color[1] for color in colors)
    blue = sum(color[2] for color in colors)
    return clamp_color((red, green, blue))


def scale_color(color: Color, amount: float) -> Color:
    """Dim or brighten a color by multiplying its intensity."""

    amount = max(0.0, amount)
    return clamp_color((color[0] * amount, color[1] * amount, color[2] * amount))


def blend_colors(color_a: Color, color_b: Color, amount: float) -> Color:
    """Blend two colors together with ``amount`` between 0 and 1."""

    amount = clamp01(amount)
    return clamp_color(
        (
            color_a[0] + (color_b[0] - color_a[0]) * amount,
            color_a[1] + (color_b[1] - color_a[1]) * amount,
            color_a[2] + (color_b[2] - color_a[2]) * amount,
        )
    )


def hsv_color(hue: float, saturation: float = 1.0, value: float = 1.0) -> Color:
    """Convert the more animation-friendly HSV color model into RGB."""

    red, green, blue = colorsys.hsv_to_rgb(fract(hue), clamp01(saturation), clamp01(value))
    return clamp_color((red * 255.0, green * 255.0, blue * 255.0))


def sample_palette(palette: Palette, position: float) -> Color:
    """Pick a color from a palette and smoothly blend between entries."""

    if not palette:
        return BLACK
    if len(palette) == 1:
        return clamp_color(palette[0])

    scaled = fract(position) * len(palette)
    index = int(math.floor(scaled)) % len(palette)
    next_index = (index + 1) % len(palette)
    amount = scaled - math.floor(scaled)
    return blend_colors(clamp_color(palette[index]), clamp_color(palette[next_index]), amount)


def hash01(*coords: float, seed: int = 0) -> float:
    """Generate a repeatable pseudo-random value without keeping state."""

    total = seed * 17.0 + 0.123456789
    for offset, coord in enumerate(coords):
        total += coord * (12.9898 + offset * 78.233)
    return fract(math.sin(total) * 43758.5453123)


def value_noise_1d(x: float, seed: int = 0) -> float:
    """Smooth random noise along a line."""

    left = math.floor(x)
    right = left + 1
    blend = smoothstep(fract(x))
    return hash01(left, seed=seed) * (1.0 - blend) + hash01(right, seed=seed) * blend


def value_noise_2d(x: float, y: float, seed: int = 0) -> float:
    """Smooth random noise on a 2D surface."""

    x0 = math.floor(x)
    y0 = math.floor(y)
    x1 = x0 + 1
    y1 = y0 + 1
    tx = smoothstep(fract(x))
    ty = smoothstep(fract(y))

    n00 = hash01(x0, y0, seed=seed)
    n10 = hash01(x1, y0, seed=seed)
    n01 = hash01(x0, y1, seed=seed)
    n11 = hash01(x1, y1, seed=seed)

    nx0 = n00 * (1.0 - tx) + n10 * tx
    nx1 = n01 * (1.0 - tx) + n11 * tx
    return nx0 * (1.0 - ty) + nx1 * ty


def fbm_1d(x: float, octaves: int = 4, seed: int = 0) -> float:
    """Fractal noise: layered smooth noise that feels more organic."""

    value = 0.0
    amplitude = 0.5
    frequency = 1.0
    total_amplitude = 0.0
    for octave in range(octaves):
        value += value_noise_1d(x * frequency, seed=seed + octave * 17) * amplitude
        total_amplitude += amplitude
        frequency *= 2.0
        amplitude *= 0.5
    return value / total_amplitude if total_amplitude else 0.0


def fbm_2d(x: float, y: float, octaves: int = 4, seed: int = 0) -> float:
    """2D fractal noise used for clouds, fire, water, and aurora-like movement."""

    value = 0.0
    amplitude = 0.5
    frequency = 1.0
    total_amplitude = 0.0
    for octave in range(octaves):
        value += value_noise_2d(x * frequency, y * frequency, seed=seed + octave * 23) * amplitude
        total_amplitude += amplitude
        frequency *= 2.0
        amplitude *= 0.5
    return value / total_amplitude if total_amplitude else 0.0


def gaussian(distance: float, radius: float) -> float:
    """Soft falloff curve that makes dots and blobs look smoother."""

    radius = max(radius, 0.0001)
    return math.exp(-((distance / radius) ** 2))


def build_strip(length: int, painter: Callable[[int, float], Color]) -> Frame1D:
    """Create a 1D frame by asking ``painter`` what each LED should show."""

    if length <= 0:
        return []
    return [clamp_color(painter(index, normalize_index(index, length))) for index in range(length)]


def build_grid(width: int, height: int, painter: Callable[[int, int, float, float], Color]) -> Frame2D:
    """Create a 2D frame by asking ``painter`` for each pixel color."""

    if width <= 0 or height <= 0:
        return []
    return [
        [
            clamp_color(painter(x, y, normalize_index(x, width), normalize_index(y, height)))
            for x in range(width)
        ]
        for y in range(height)
    ]


def border_index(x: int, y: int, width: int, height: int) -> int | None:
    """Map a border pixel to a single loop index for perimeter chases."""

    if width <= 0 or height <= 0:
        return None
    if width == 1:
        return y
    if height == 1:
        return x
    if y == 0:
        return x
    if x == width - 1:
        return (width - 1) + y
    if y == height - 1:
        return (width - 1) + (height - 1) + (width - 1 - x)
    if x == 0:
        return (width - 1) + (height - 1) + (width - 1) + (height - 1 - y)
    return None


def border_length(width: int, height: int) -> int:
    """Return how many pixels are in the outer ring of a grid."""

    if width <= 0 or height <= 0:
        return 0
    if width == 1:
        return height
    if height == 1:
        return width
    return (width * 2) + (height * 2) - 4


def flatten_grid(grid: Frame2D, serpentine: bool = False) -> Frame1D:
    """Flatten a 2D frame for controllers that actually store LEDs in one line."""

    flattened: Frame1D = []
    for row_index, row in enumerate(grid):
        if serpentine and row_index % 2 == 1:
            flattened.extend(reversed(row))
        else:
            flattened.extend(row)
    return flattened


def list_patterns(dimension: str | None = None) -> list[PatternInfo]:
    """Return all known patterns, optionally filtered to 1D or 2D."""

    if dimension == "1d":
        return [PATTERNS_1D[name] for name in sorted(PATTERNS_1D)]
    if dimension == "2d":
        return [PATTERNS_2D[name] for name in sorted(PATTERNS_2D)]
    return [*list_patterns("1d"), *list_patterns("2d")]


@register_1d("Every LED stays the same color, like dipping the whole strip in one paint bucket.")
def solid_color(length: int, t: float, color: Color = WHITE) -> Frame1D:
    """Solid color strip.

    Layperson description:
        This is the simplest pattern possible. Every light is exactly the same
        color, so the whole strip looks like one continuous glowing bar.

    How it works:
        The function ignores time and repeats the same RGB value for each LED.
    """

    return [clamp_color(color) for _ in range(max(0, length))]


@register_1d("Spinning red and white stripes, like a candy cane or barber pole.")
def candy_cane(
    length: int,
    t: float,
    color_a: Color = (255, 20, 20),
    color_b: Color = (255, 255, 255),
    stripe_size: int = 4,
    speed: float = 1.0,
) -> Frame1D:
    """Candy cane stripes.

    Layperson description:
        Alternating stripes slide along the strip so it feels like a festive
        candy cane twisting in place.

    How it works:
        We divide the strip into chunks and alternate between two colors while
        shifting those chunks forward over time.
    """

    stripe_size = max(1, stripe_size)
    offset = int(t * speed * stripe_size * 2.0)

    def paint(index: int, _: float) -> Color:
        stripe = ((index + offset) // stripe_size) % 2
        return color_a if stripe == 0 else color_b

    return build_strip(length, paint)


@register_1d("A full rainbow stretched across the strip so every LED gets its own color band.")
def rainbow_gradient(length: int, t: float, bands: float = 1.0, saturation: float = 1.0) -> Frame1D:
    """Static rainbow gradient.

    Layperson description:
        The strip becomes a full rainbow from one end to the other, which is
        handy for testing colors or showing off all LEDs at once.

    How it works:
        Each LED gets a hue based on its position from left to right.
    """

    def paint(_: int, position: float) -> Color:
        return hsv_color(position * bands, saturation, 1.0)

    return build_strip(length, paint)


@register_1d("A full rainbow that rotates down the strip like a moving color wheel.")
def rainbow_cycle(length: int, t: float, bands: float = 2.0, speed: float = 0.18) -> Frame1D:
    """Animated rainbow cycle.

    Layperson description:
        The strip shows multiple rainbow bands that slowly drift along, which
        feels like the LEDs are wrapped in a moving color wheel.

    How it works:
        Position chooses the base hue, then time shifts the hue forward.
    """

    def paint(_: int, position: float) -> Color:
        return hsv_color(position * bands + t * speed, 1.0, 1.0)

    return build_strip(length, paint)


@register_1d("One color sweeps across the strip from end to end like someone painting it live.")
def color_wipe(
    length: int,
    t: float,
    color: Color = (0, 180, 255),
    background: Color = BLACK,
    speed: float = 1.0,
) -> Frame1D:
    """Color wipe.

    Layperson description:
        A colored bar fills the strip one LED at a time, then restarts, which
        feels like someone is drawing light across the strip.

    How it works:
        We compute a moving head position and light every LED behind it.
    """

    if length <= 0:
        return []
    head = int((t * speed * length) % (length + 1))

    def paint(index: int, _: float) -> Color:
        return color if index < head else background

    return build_strip(length, paint)


@register_1d("Small lit dots march in lockstep like a theater marquee.")
def theater_chase(
    length: int,
    t: float,
    color: Color = (255, 180, 30),
    background: Color = (8, 8, 8),
    spacing: int = 3,
    speed: float = 8.0,
) -> Frame1D:
    """Theater chase.

    Layperson description:
        This recreates the classic marching-bulb look from old movie theaters
        and carnival signs.

    How it works:
        One LED in each small repeating group is lit, and the lit slot shifts
        over time.
    """

    spacing = max(1, spacing)
    phase = int(t * speed) % spacing

    def paint(index: int, _: float) -> Color:
        return color if (index + phase) % spacing == 0 else background

    return build_strip(length, paint)


@register_1d("A bright eye bounces back and forth with a soft tail behind it.")
def scanner(length: int, t: float, color: Color = (255, 30, 30), speed: float = 12.0, tail: float = 8.0) -> Frame1D:
    """Single scanner.

    Layperson description:
        This is the classic red scanner eye: one bright point sweeps from side
        to side and leaves a fading trail.

    How it works:
        A bouncing head position is calculated, then nearby LEDs fade based on
        distance from that head.
    """

    if length <= 0:
        return []
    head = ping_pong(t * speed, max(1, length - 1))

    def paint(index: int, _: float) -> Color:
        brightness = gaussian(index - head, tail)
        return scale_color(color, brightness)

    return build_strip(length, paint)


@register_1d("Two scanner eyes start at opposite ends and cross in the middle.")
def dual_scanner(
    length: int,
    t: float,
    color_a: Color = (255, 40, 40),
    color_b: Color = (40, 80, 255),
    speed: float = 10.0,
    tail: float = 7.0,
) -> Frame1D:
    """Dual scanner.

    Layperson description:
        Two glowing eyes sweep toward each other, cross, and bounce apart again.

    How it works:
        We calculate one bouncing head, mirror it, and add the two colors.
    """

    if length <= 0:
        return []
    head_a = ping_pong(t * speed, max(1, length - 1))
    head_b = (length - 1) - head_a

    def paint(index: int, _: float) -> Color:
        first = scale_color(color_a, gaussian(index - head_a, tail))
        second = scale_color(color_b, gaussian(index - head_b, tail))
        return add_colors(first, second)

    return build_strip(length, paint)


@register_1d("A bright comet circles the strip with a glowing tail that slowly fades away.")
def comet_trail(length: int, t: float, color: Color = (110, 220, 255), speed: float = 18.0, tail: int = 16) -> Frame1D:
    """Single comet.

    Layperson description:
        A bright point races around the strip while a tail stretches behind it,
        like a tiny comet made out of LEDs.

    How it works:
        We wrap the head around the strip and only light LEDs behind the head.
    """

    if length <= 0:
        return []
    tail = max(1, tail)
    head = (t * speed) % length

    def paint(index: int, _: float) -> Color:
        distance_behind = (head - index) % length
        if distance_behind > tail:
            return BLACK
        brightness = (1.0 - distance_behind / tail) ** 2
        return scale_color(color, brightness)

    return build_strip(length, paint)


@register_1d("Several meteors race around the strip at once, each with a fading tail.")
def meteor_rain(length: int, t: float, speed: float = 15.0, count: int = 4, tail: int = 14, palette: Palette = PARTY_PALETTE) -> Frame1D:
    """Multiple meteors.

    Layperson description:
        Instead of one comet, this launches several colorful meteors around the
        strip at slightly different speeds.

    How it works:
        Each meteor gets its own head position and color, then we add them
        together on the same frame.
    """

    if length <= 0:
        return []
    count = max(1, count)
    tail = max(1, tail)

    def paint(index: int, _: float) -> Color:
        color = BLACK
        for meteor in range(count):
            local_speed = speed * (1.0 + meteor * 0.12)
            head = (t * local_speed + meteor * length / count) % length
            distance_behind = (head - index) % length
            if distance_behind <= tail:
                brightness = (1.0 - distance_behind / tail) ** 2
                meteor_color = sample_palette(palette, meteor / count)
                color = add_colors(color, scale_color(meteor_color, brightness))
        return color

    return build_strip(length, paint)


@register_1d("Small stars gently blink on and off all across the strip.")
def twinkle_stars(length: int, t: float, background: Color = (3, 3, 10), sparkle: Color = WHITE, speed: float = 0.8, seed: int = 0) -> Frame1D:
    """Twinkling stars.

    Layperson description:
        The strip becomes a night sky where each LED has its own little sparkle
        rhythm, so the lights blink naturally instead of all together.

    How it works:
        Each LED gets a personal pulse phase from a repeatable pseudo-random
        number, then that phase drives a soft sparkle curve.
    """

    def paint(index: int, _: float) -> Color:
        phase = fract(t * speed + hash01(index, seed=seed) * 3.0)
        blink = max(0.0, math.sin(phase * math.pi)) ** (7 + int(hash01(index, seed=seed + 1) * 5))
        return blend_colors(background, sparkle, blink)

    return build_strip(length, paint)


@register_1d("Fast white sparkles pop on top of a darker background, like glitter catching light.")
def sparkle_pop(
    length: int,
    t: float,
    base_color: Color = (0, 25, 60),
    sparkle_color: Color = WHITE,
    density: float = 0.12,
    speed: float = 18.0,
    seed: int = 0,
) -> Frame1D:
    """Glitter-style sparkles.

    Layperson description:
        Short bright flashes appear randomly over a background color, similar to
        glitter or snow catching a spotlight.

    How it works:
        We create a new pseudo-random sparkle map several times per second and
        brighten only the pixels that land above a threshold.
    """

    frame = math.floor(t * speed)
    threshold = 1.0 - clamp01(density)

    def paint(index: int, _: float) -> Color:
        trigger = hash01(index, frame, seed=seed)
        sparkle_amount = smoothstep((trigger - threshold) / max(0.0001, 1.0 - threshold))
        return blend_colors(base_color, sparkle_color, sparkle_amount)

    return build_strip(length, paint)


@register_1d("Confetti-like speckles burst across the strip in lots of random colors.")
def confetti_burst(length: int, t: float, background: Color = (5, 5, 12), density: float = 0.2, speed: float = 14.0, seed: int = 0) -> Frame1D:
    """Confetti burst.

    Layperson description:
        This pattern sprays little colored dots over a dark background, giving a
        lively party or fireworks afterglow feel.

    How it works:
        Random tests decide where each speckle appears, and each speckle gets a
        different hue from the color wheel.
    """

    frame = math.floor(t * speed)
    threshold = 1.0 - clamp01(density)

    def paint(index: int, _: float) -> Color:
        chance = hash01(index * 1.7, frame, seed=seed)
        if chance < threshold:
            return background
        hue = hash01(index * 2.3, frame, seed=seed + 9)
        color = hsv_color(hue, 0.85, 1.0)
        amount = smoothstep((chance - threshold) / max(0.0001, 1.0 - threshold))
        return blend_colors(background, color, amount)

    return build_strip(length, paint)


@register_1d("The whole strip gently brightens and dims like breathing.")
def breathe(length: int, t: float, color: Color = (90, 180, 255), speed: float = 0.7, floor: float = 0.08) -> Frame1D:
    """Breathing pulse.

    Layperson description:
        All LEDs fade in and out together with a slow, soft rhythm like an idle
        power light or a sleeping robot.

    How it works:
        A cosine wave makes the brightness rise and fall smoothly.
    """

    inhale = 0.5 - 0.5 * math.cos(t * speed * TAU)
    brightness = floor + (1.0 - floor) * (inhale ** 2)
    return [scale_color(color, brightness) for _ in range(max(0, length))]


@register_1d("A double thump pulse that looks like a cartoon heartbeat monitor.")
def heartbeat(length: int, t: float, color: Color = (255, 25, 60), speed: float = 1.0, floor: float = 0.05) -> Frame1D:
    """Heartbeat pulse.

    Layperson description:
        Instead of a perfectly even pulse, this does a quick double beat and
        then rests, which feels much more like a real heartbeat.

    How it works:
        Two narrow pulse curves are added together inside each one-second cycle.
    """

    phase = fract(t * speed)
    first = math.exp(-((phase - 0.17) / 0.045) ** 2)
    second = 0.8 * math.exp(-((phase - 0.31) / 0.06) ** 2)
    brightness = clamp01(floor + first + second)
    return [scale_color(color, brightness) for _ in range(max(0, length))]


@register_1d("One glowing dot glides side to side like the classic FastLED sinelon effect.")
def sinelon(length: int, t: float, color: Color = (255, 70, 200), speed: float = 1.4, tail: float = 10.0) -> Frame1D:
    """Sinelon sweep.

    Layperson description:
        A single dot drifts smoothly back and forth with a long elegant trail.

    How it works:
        A sine wave chooses the dot's center point, then nearby LEDs are dimmed
        based on their distance from that moving center.
    """

    if length <= 0:
        return []
    head = (math.sin(t * speed * TAU) * 0.5 + 0.5) * (length - 1)

    def paint(index: int, _: float) -> Color:
        return scale_color(color, gaussian(index - head, tail))

    return build_strip(length, paint)


@register_1d("Several colored dots weave through each other like juggling balls.")
def juggle_balls(length: int, t: float, count: int = 5, speed: float = 1.0, tail: float = 7.0, palette: Palette = PARTY_PALETTE) -> Frame1D:
    """Juggling dots.

    Layperson description:
        Multiple bright dots move with different rhythms, cross paths, and make
        the strip feel busy and playful.

    How it works:
        Each dot gets a slightly different sine wave and color, then we add the
        dots together.
    """

    if length <= 0:
        return []
    count = max(1, count)

    def paint(index: int, _: float) -> Color:
        color = BLACK
        for ball in range(count):
            frequency = speed * (0.7 + ball * 0.17)
            phase = ball * 0.9
            head = (math.sin(t * frequency * TAU + phase) * 0.5 + 0.5) * (length - 1)
            ball_color = sample_palette(palette, ball / count)
            color = add_colors(color, scale_color(ball_color, gaussian(index - head, tail)))
        return color

    return build_strip(length, paint)


@register_1d("Striped bands pulse with a musical beat, even without any audio input.")
def bpm_stripes(length: int, t: float, bpm: float = 120.0, palette: Palette = PARTY_PALETTE, bands: float = 6.0) -> Frame1D:
    """Beat-synced stripes.

    Layperson description:
        This feels like club lighting: bold stripes breathe in and out to a
        fixed beat.

    How it works:
        A pretend metronome drives the brightness while LED position chooses a
        palette color band.
    """

    beat = 0.5 - 0.5 * math.cos(t * bpm / 60.0 * TAU)

    def paint(_: int, position: float) -> Color:
        palette_position = position * bands + beat * 0.18
        brightness = 0.2 + 0.8 * triangle_wave(position * bands - beat * bands)
        return scale_color(sample_palette(palette, palette_position), brightness)

    return build_strip(length, paint)


@register_1d("A fiery strip full of hot flickers, like looking at a row of flames.")
def fire_strip(length: int, t: float, speed: float = 1.0, palette: Palette = FIRE_PALETTE, seed: int = 0) -> Frame1D:
    """Linear fire.

    Layperson description:
        This gives a strip a campfire-like feel with bright hot patches and dark
        ember gaps moving around.

    How it works:
        Layered noise creates uneven heat values, and those heat values are
        turned into warm colors through a fire palette.
    """

    def paint(index: int, position: float) -> Color:
        noise = fbm_1d(position * 6.0 - t * speed * 1.8, seed=seed)
        fine = fbm_1d(position * 19.0 + t * speed * 3.4, seed=seed + 50)
        heat = clamp01(noise * 0.72 + fine * 0.35)
        return sample_palette(palette, heat ** 1.15)

    return build_strip(length, paint)


@register_1d("Molten blobs drift down the strip like glowing lava in a lamp.")
def lava_flow(length: int, t: float, speed: float = 0.7, palette: Palette = LAVA_PALETTE, seed: int = 0) -> Frame1D:
    """Lava flow.

    Layperson description:
        Thick warm blobs slide around slowly so the strip looks heavy and molten.

    How it works:
        Slow-moving noise shapes the blobs and a warm palette sells the lava
        look.
    """

    def paint(_: int, position: float) -> Color:
        blobs = fbm_1d(position * 3.6 + t * speed * 0.7, seed=seed)
        curls = 0.25 * math.sin(position * 18.0 - t * speed * 3.0)
        heat = clamp01(blobs + curls)
        return sample_palette(palette, heat)

    return build_strip(length, paint)


@register_1d("Rolling blue-green waves that feel like moonlight reflecting on water.")
def ocean_current(length: int, t: float, speed: float = 1.0, palette: Palette = OCEAN_PALETTE, seed: int = 0) -> Frame1D:
    """Ocean current.

    Layperson description:
        Long smooth blue waves slide along the strip, giving a calm underwater
        or shoreline feel.

    How it works:
        Several wave shapes are layered together so the motion feels fluid
        instead of perfectly mechanical.
    """

    def paint(_: int, position: float) -> Color:
        wave_a = 0.5 + 0.5 * math.sin(position * 10.0 + t * speed * 1.8)
        wave_b = 0.5 + 0.5 * math.sin(position * 25.0 - t * speed * 2.7)
        shimmer = fbm_1d(position * 8.0 - t * speed * 0.6, seed=seed)
        level = clamp01(wave_a * 0.45 + wave_b * 0.25 + shimmer * 0.5)
        return sample_palette(palette, level)

    return build_strip(length, paint)


@register_1d("Green and purple ribbons slide around like a miniature aurora.")
def aurora_ribbon(length: int, t: float, speed: float = 0.6, palette: Palette = AURORA_PALETTE, seed: int = 0) -> Frame1D:
    """Aurora ribbon.

    Layperson description:
        Soft curtains of color bend across the strip the way northern lights do
        across the sky.

    How it works:
        Noise provides organic movement, and the palette supplies the aurora
        colors.
    """

    def paint(_: int, position: float) -> Color:
        curtain = fbm_1d(position * 4.0 + t * speed * 0.5, seed=seed)
        wave = 0.5 + 0.5 * math.sin(position * 14.0 - t * speed * 2.0)
        glow = clamp01(curtain * 0.7 + wave * 0.5)
        return scale_color(sample_palette(palette, glow * 0.85), glow)

    return build_strip(length, paint)


@register_1d("Ripples spread outward from a changing center point like pebbles dropped in water.")
def ripple_ring(
    length: int,
    t: float,
    color: Color = (100, 190, 255),
    background: Color = (0, 5, 20),
    speed: float = 1.0,
    frequency: float = 0.8,
) -> Frame1D:
    """Ripples along a strip.

    Layperson description:
        This makes the strip feel like a pond surface where ring waves move
        outward from the middle.

    How it works:
        A moving source point emits a cosine wave, and distance from that source
        determines which LEDs sit on the bright part of the ripple.
    """

    if length <= 0:
        return []
    source = (0.5 + 0.25 * math.sin(t * speed * 0.6)) * (length - 1)

    def paint(index: int, _: float) -> Color:
        distance = abs(index - source)
        ripple = 0.5 + 0.5 * math.cos(distance * frequency - t * speed * TAU * 1.4)
        fade = 1.0 / (1.0 + distance * 0.12)
        return blend_colors(background, color, clamp01(ripple * fade * 1.7))

    return build_strip(length, paint)


@register_1d("Smooth blended colors bubble and morph like a classic plasma screen saver.")
def plasma_band(length: int, t: float, speed: float = 1.0, saturation: float = 0.9) -> Frame1D:
    """Plasma line.

    Layperson description:
        Colors ooze into each other in smooth waves that never settle into a
        simple repeating stripe.

    How it works:
        Several sine waves are added together, and the combined value is used as
        a color-wheel position.
    """

    def paint(_: int, position: float) -> Color:
        value = (
            math.sin(position * 12.0 + t * speed * 1.8)
            + math.sin(position * 23.0 - t * speed * 1.3)
            + math.sin(position * 7.0 + t * speed * 2.1)
        ) / 3.0
        hue = 0.5 + value * 0.35
        return hsv_color(hue, saturation, 1.0)

    return build_strip(length, paint)


@register_1d("A shimmering palette wash that feels organic instead of stripy.")
def noise_shimmer(length: int, t: float, speed: float = 0.8, palette: Palette = NEON_PALETTE, seed: int = 0) -> Frame1D:
    """Noise shimmer.

    Layperson description:
        Instead of obvious stripes, this creates softly moving zones of color
        with a gentle shimmery texture.

    How it works:
        Fractal noise chooses both the hue position and the brightness.
    """

    def paint(_: int, position: float) -> Color:
        hue_position = fbm_1d(position * 5.0 + t * speed * 0.5, seed=seed)
        brightness = 0.3 + 0.7 * fbm_1d(position * 13.0 - t * speed * 1.8, seed=seed + 30)
        return scale_color(sample_palette(palette, hue_position), brightness)

    return build_strip(length, paint)


@register_1d("Alternating red and blue emergency flashes split across the strip.")
def police_lights(length: int, t: float, speed: float = 2.0) -> Frame1D:
    """Red and blue police lights.

    Layperson description:
        One half of the strip flashes red and the other half flashes blue with
        a quick emergency-vehicle rhythm.

    How it works:
        Time is divided into short flash windows, and each side uses a different
        color.
    """

    phase = fract(t * speed)
    flash_a = 1.0 if phase < 0.15 or 0.28 < phase < 0.43 else 0.05
    flash_b = 1.0 if 0.5 < phase < 0.65 or 0.78 < phase < 0.93 else 0.05
    midpoint = max(1, length // 2)

    def paint(index: int, _: float) -> Color:
        if index < midpoint:
            return scale_color((255, 0, 0), flash_a)
        return scale_color((0, 70, 255), flash_b)

    return build_strip(length, paint)


@register_1d("The strip gradually turns from deep night into warm daylight.")
def sunrise(length: int, t: float, speed: float = 0.08) -> Frame1D:
    """Sunrise fade.

    Layperson description:
        This slowly transitions through nighttime blue, dawn orange, and pale
        daylight.

    How it works:
        A slow progress value drives both the overall sky color and a bright
        glowing sun spot.
    """

    phase = fract(t * speed)
    sky = sample_palette(SUNSET_PALETTE, phase * 0.9)
    sun_center = phase

    def paint(_: int, position: float) -> Color:
        sun_glow = math.exp(-((position - sun_center) / 0.11) ** 2)
        return add_colors(scale_color(sky, 0.85), scale_color((255, 220, 140), sun_glow))

    return build_strip(length, paint)


@register_1d("Chunky blocks run around the strip like a retro marquee or loading bar.")
def runner_blocks(length: int, t: float, block_size: int = 6, gap: int = 3, speed: float = 10.0, palette: Palette = PARTY_PALETTE) -> Frame1D:
    """Running blocks.

    Layperson description:
        Groups of LEDs move together instead of single dots, giving the strip a
        strong chunky arcade feel.

    How it works:
        We repeat a block-plus-gap pattern and scroll it along the strip.
    """

    block_size = max(1, block_size)
    gap = max(0, gap)
    cycle = block_size + gap
    offset = int(t * speed)

    def paint(index: int, _: float) -> Color:
        slot = (index + offset) % max(1, cycle * len(palette))
        palette_slot = (slot // cycle) % len(palette)
        if slot % cycle < block_size:
            return sample_palette(palette, palette_slot / max(1, len(palette)))
        return BLACK

    return build_strip(length, paint)


@register_1d("A smooth gradient with little glitter flashes sprinkled over it.")
def glitter_gradient(length: int, t: float, palette: Palette = SUNSET_PALETTE, speed: float = 0.15, sparkle_density: float = 0.08, seed: int = 0) -> Frame1D:
    """Gradient plus glitter.

    Layperson description:
        A soft color wash covers the strip, and bright sparkles briefly appear
        on top to make it feel more alive.

    How it works:
        The base layer is a slowly moving palette gradient, then a second
        sparkle layer brightens only a few LEDs at a time.
    """

    frame = math.floor(t * 18.0)
    threshold = 1.0 - clamp01(sparkle_density)

    def paint(index: int, position: float) -> Color:
        base = sample_palette(palette, position + t * speed)
        trigger = hash01(index, frame, seed=seed)
        sparkle = smoothstep((trigger - threshold) / max(0.0001, 1.0 - threshold))
        return add_colors(base, scale_color(WHITE, sparkle))

    return build_strip(length, paint)


@register_1d("A crisp strobe that slams between dark and bright like a stage light.")
def strobe(length: int, t: float, color: Color = WHITE, speed: float = 12.0, duty_cycle: float = 0.15) -> Frame1D:
    """Strobe flash.

    Layperson description:
        The whole strip flashes rapidly on and off, which is useful for dramatic
        stage-light energy.

    How it works:
        Each cycle spends a short time fully on and the rest nearly off.
    """

    phase = fract(t * speed)
    brightness = 1.0 if phase < clamp01(duty_cycle) else 0.02
    return [scale_color(color, brightness) for _ in range(max(0, length))]


@register_1d("Several neon wave lines twist through each other like glowing snakes.")
def neon_snakes(length: int, t: float, speed: float = 1.0, palette: Palette = NEON_PALETTE) -> Frame1D:
    """Interwoven neon waves.

    Layperson description:
        Colorful glowing lanes weave across the strip in a smooth futuristic
        pattern.

    How it works:
        Multiple moving wave crests are layered together using different colors.
    """

    def paint(_: int, position: float) -> Color:
        color = BLACK
        for lane in range(4):
            center = fract(t * speed * (0.14 + lane * 0.03) + lane * 0.21)
            distance = min(abs(position - center), 1.0 - abs(position - center))
            lane_color = sample_palette(palette, lane / 4.0)
            color = add_colors(color, scale_color(lane_color, gaussian(distance, 0.07 + lane * 0.01)))
        return color

    return build_strip(length, paint)


@register_1d("Dark storm clouds roll by, with occasional lightning flashes ripping through them.")
def storm_clouds_strip(length: int, t: float, speed: float = 0.5, seed: int = 0) -> Frame1D:
    """Storm clouds with lightning.

    Layperson description:
        The strip mostly shows moody blue-gray clouds, but now and then a bright
        lightning bolt flashes through one area.

    How it works:
        Noise creates the cloudy base, and a separate time-based trigger adds a
        narrow bright flash region.
    """

    flash_strength = smoothstep((value_noise_1d(t * speed * 0.9, seed=seed) - 0.82) / 0.18)
    bolt_center = hash01(math.floor(t * speed * 2.0), seed=seed + 99)

    def paint(index: int, position: float) -> Color:
        clouds = sample_palette(STORM_PALETTE, fbm_1d(position * 4.0 + t * speed * 0.3, seed=seed))
        lightning = gaussian(position - bolt_center, 0.06) * flash_strength
        return add_colors(scale_color(clouds, 0.8), scale_color(WHITE, lightning * 1.4))

    return build_strip(length, paint)


@register_1d("Deep red embers glow and occasionally flare brighter like a dying fire bed.")
def ember_bed(length: int, t: float, speed: float = 0.7, seed: int = 0) -> Frame1D:
    """Glowing ember bed.

    Layperson description:
        This is less like open flame and more like a bed of coals that slowly
        breathe and spark.

    How it works:
        Slow noise creates hot and cool pockets, then rare spark spikes add
        brighter orange flares.
    """

    frame = math.floor(t * 10.0)

    def paint(index: int, position: float) -> Color:
        base_heat = fbm_1d(position * 8.0 - t * speed * 0.4, seed=seed)
        spark = smoothstep((hash01(index, frame, seed=seed + 7) - 0.93) / 0.07)
        ember = blend_colors((30, 0, 0), (210, 60, 0), base_heat)
        return add_colors(ember, scale_color((255, 180, 50), spark))

    return build_strip(length, paint)


@register_1d("A stripy candy-store look where multiple bright colors rotate in repeating bands.")
def carousel_stripes(length: int, t: float, speed: float = 1.2, bands: int = 10, palette: Palette = PARTY_PALETTE) -> Frame1D:
    """Carousel stripes.

    Layperson description:
        Bold repeating color slices spin around the strip like a carnival ride
        canopy.

    How it works:
        LED position picks which band it belongs to, then time rotates the band
        assignment.
    """

    bands = max(1, bands)

    def paint(_: int, position: float) -> Color:
        band_position = position * bands + t * speed
        return sample_palette(palette, band_position / bands)

    return build_strip(length, paint)


@register_2d("Every pixel stays the same color, useful as a baseline or test pattern.")
def solid_grid(width: int, height: int, t: float, color: Color = WHITE) -> Frame2D:
    """Solid color grid.

    Layperson description:
        The whole panel glows one single color, which is useful for testing and
        for simple room-light scenes.

    How it works:
        We ignore time and repeat the same RGB value for every pixel.
    """

    color = clamp_color(color)
    return [[color for _ in range(max(0, width))] for _ in range(max(0, height))]


@register_2d("A drifting checkerboard that looks like glowing floor tiles sliding past each other.")
def checkerboard_drift(
    width: int,
    height: int,
    t: float,
    color_a: Color = (255, 170, 60),
    color_b: Color = (25, 15, 5),
    tile_size: int = 3,
    speed: float = 2.0,
) -> Frame2D:
    """Drifting checkerboard.

    Layperson description:
        This turns a panel into a moving checkerboard or glowing tiled floor.

    How it works:
        Pixel coordinates are grouped into tiles, and those tile boundaries are
        shifted over time.
    """

    tile_size = max(1, tile_size)
    shift = int(t * speed * tile_size)

    def paint(x: int, y: int, _: float, __: float) -> Color:
        tile = ((x + shift) // tile_size + (y + shift // 2) // tile_size) % 2
        return color_a if tile == 0 else color_b

    return build_grid(width, height, paint)


@register_2d("A rainbow field where both x and y position influence the color.")
def rainbow_field(width: int, height: int, t: float, x_bands: float = 1.5, y_bands: float = 0.6, speed: float = 0.15) -> Frame2D:
    """2D rainbow field.

    Layperson description:
        The grid shows a rainbow that bends across both directions, so it feels
        more like a colorful map than a simple left-to-right gradient.

    How it works:
        Horizontal and vertical positions both contribute to the hue.
    """

    def paint(_: int, __: int, nx: float, ny: float) -> Color:
        hue = nx * x_bands + ny * y_bands + t * speed
        return hsv_color(hue, 1.0, 1.0)

    return build_grid(width, height, paint)


@register_2d("A classic plasma effect with smooth lava-lamp color movement over the whole grid.")
def plasma_2d(width: int, height: int, t: float, speed: float = 1.0, saturation: float = 0.9) -> Frame2D:
    """2D plasma.

    Layperson description:
        Colors ooze and swirl in big smooth blobs, like an old-school screensaver
        or a sci-fi energy wall.

    How it works:
        Multiple wave equations based on position and distance from center are
        added together to create a smoothly changing field.
    """

    def paint(x: int, y: int, _: float, __: float) -> Color:
        cx = centered_coord(x, width)
        cy = centered_coord(y, height)
        radius = math.hypot(cx, cy)
        value = (
            math.sin(cx * 6.0 + t * speed * 1.5)
            + math.sin(cy * 7.0 - t * speed * 1.2)
            + math.sin((cx + cy) * 4.0 + t * speed * 0.9)
            + math.sin(radius * 12.0 - t * speed * 2.0)
        ) / 4.0
        return hsv_color(0.5 + value * 0.35, saturation, 1.0)

    return build_grid(width, height, paint)


@register_2d("Overlapping waves from multiple sources make water-like interference patterns.")
def wave_interference(width: int, height: int, t: float, speed: float = 1.0, color: Color = (80, 170, 255), background: Color = (0, 8, 22)) -> Frame2D:
    """Wave interference.

    Layperson description:
        This looks like several pebbles were dropped into a pond at once and the
        waves are crossing over each other.

    How it works:
        We measure each pixel's distance from moving wave sources and add the
        resulting ripple values together.
    """

    sources = (
        (
            0.5 + 0.28 * math.sin(t * speed * 0.9),
            0.5 + 0.28 * math.cos(t * speed * 0.7),
        ),
        (
            0.5 + 0.33 * math.cos(t * speed * 0.6 + 1.2),
            0.5 + 0.25 * math.sin(t * speed * 0.85 + 0.7),
        ),
        (
            0.5 + 0.20 * math.sin(t * speed * 0.5 + 2.0),
            0.5 + 0.32 * math.cos(t * speed * 0.75 + 2.5),
        ),
    )

    def paint(_: int, __: int, nx: float, ny: float) -> Color:
        ripple_sum = 0.0
        for sx, sy in sources:
            distance = math.hypot(nx - sx, ny - sy)
            ripple_sum += math.cos(distance * 24.0 - t * speed * 7.0)
        ripple = clamp01(0.5 + ripple_sum / (2.0 * len(sources)))
        return blend_colors(background, color, ripple)

    return build_grid(width, height, paint)


@register_2d("Light rays burst from the center like a spinning sun or star.")
def radial_sunburst(width: int, height: int, t: float, speed: float = 0.7, palette: Palette = SUNSET_PALETTE, rays: int = 12) -> Frame2D:
    """Radial sunburst.

    Layperson description:
        Bright spokes radiate from the center and slowly rotate like a stylized
        sun or carnival star.

    How it works:
        The angle from the center decides which ray a pixel belongs to, while
        distance controls how much it fades.
    """

    rays = max(1, rays)

    def paint(x: int, y: int, _: float, __: float) -> Color:
        cx = centered_coord(x, width)
        cy = centered_coord(y, height)
        angle = math.atan2(cy, cx)
        radius = math.hypot(cx, cy)
        beam = 0.5 + 0.5 * math.cos(angle * rays + t * speed * TAU)
        glow = clamp01((beam ** 4) * (1.2 - radius * 0.9))
        return scale_color(sample_palette(palette, beam * 0.4 + 0.05), glow)

    return build_grid(width, height, paint)


@register_2d("A twisting whirlpool of color spirals around the center.")
def vortex_swirl(width: int, height: int, t: float, speed: float = 1.0, palette: Palette = PARTY_PALETTE) -> Frame2D:
    """Vortex swirl.

    Layperson description:
        Colors wrap around the center in a spinning whirlpool or portal shape.

    How it works:
        We convert pixel positions into radius and angle, then twist the angle
        based on radius so the colors spiral.
    """

    def paint(x: int, y: int, _: float, __: float) -> Color:
        cx = centered_coord(x, width)
        cy = centered_coord(y, height)
        angle = math.atan2(cy, cx)
        radius = math.hypot(cx, cy)
        spiral = angle / TAU + radius * 1.3 - t * speed * 0.18
        brightness = clamp01(1.1 - radius * 0.85)
        return scale_color(sample_palette(palette, spiral), brightness)

    return build_grid(width, height, paint)


@register_2d("Falling green code columns inspired by the classic Matrix look.")
def matrix_rain(width: int, height: int, t: float, speed: float = 8.0, tail: int = 8, seed: int = 0) -> Frame2D:
    """Matrix rain.

    Layperson description:
        Each column has glowing green drops falling downward with bright heads
        and fading tails.

    How it works:
        Every column gets its own falling head position and brightness profile.
    """

    tail = max(1, tail)

    def paint(x: int, y: int, _: float, __: float) -> Color:
        column_speed = speed * (0.55 + hash01(x, seed=seed) * 0.9)
        offset = hash01(x, seed=seed + 21) * (height + tail)
        head = (t * column_speed + offset) % (height + tail) - tail
        distance = head - y
        if 0.0 <= distance <= tail:
            brightness = (1.0 - distance / tail) ** 2
            green = blend_colors((0, 20, 0), (0, 255, 90), brightness)
            if distance < 1.0:
                return add_colors(green, (140, 255, 180))
            return green
        ambient = 0.04 * value_noise_2d(x * 0.4, y * 0.2 + t * 0.3, seed=seed)
        return scale_color((0, 120, 30), ambient)

    return build_grid(width, height, paint)


@register_2d("A night-sky grid with stars that twinkle at different rhythms.")
def twinkle_sky(width: int, height: int, t: float, speed: float = 0.6, seed: int = 0) -> Frame2D:
    """Twinkling sky.

    Layperson description:
        The panel becomes a dark sky where stars gently brighten and dim at
        different times.

    How it works:
        Pixel coordinates decide whether a star exists there, and if it does,
        the star gets its own personal blink phase.
    """

    background = (2, 3, 12)

    def paint(x: int, y: int, _: float, __: float) -> Color:
        star_chance = hash01(x, y, seed=seed)
        if star_chance < 0.92:
            nebula = 0.08 * fbm_2d(x * 0.15 + t * 0.03, y * 0.15, seed=seed + 11)
            return add_colors(background, scale_color((30, 60, 120), nebula))
        phase = fract(t * speed + hash01(x, y, seed=seed + 31) * 3.0)
        sparkle = max(0.0, math.sin(phase * math.pi)) ** 8
        star_color = blend_colors((180, 200, 255), WHITE, hash01(x, y, seed=seed + 51))
        return add_colors(background, scale_color(star_color, sparkle))

    return build_grid(width, height, paint)


@register_2d("A vertical fire effect with bright flames at the bottom and dimmer smoke-like heat above.")
def fire_2d(width: int, height: int, t: float, speed: float = 1.0, palette: Palette = FIRE_PALETTE, seed: int = 0) -> Frame2D:
    """2D fire.

    Layperson description:
        The bottom of the panel burns brightest, and the heat breaks up into
        flickering tongues as it rises.

    How it works:
        Noise creates the flicker, while vertical position controls how hot or
        cool the fire should be.
    """

    def paint(x: int, y: int, _: float, ny: float) -> Color:
        bottomness = ny
        turbulence = fbm_2d(x * 0.22, y * 0.15 - t * speed * 2.2, seed=seed)
        tongues = 0.18 * math.sin(x * 0.45 + (1.0 - ny) * 8.0 + t * speed * 3.0)
        heat = clamp01(turbulence * 0.8 + bottomness * 1.1 + tongues - (1.0 - bottomness) * 0.8)
        return sample_palette(palette, heat)

    return build_grid(width, height, paint)


@register_2d("Soft green and purple curtains drift downward like northern lights.")
def aurora_grid(width: int, height: int, t: float, speed: float = 0.5, palette: Palette = AURORA_PALETTE, seed: int = 0) -> Frame2D:
    """Aurora on a grid.

    Layperson description:
        The panel shows long glowing curtains that sway and shimmer the way
        northern lights do.

    How it works:
        Horizontal noise shapes the curtain folds and brightness varies with
        height so the effect feels airy.
    """

    def paint(x: int, y: int, _: float, ny: float) -> Color:
        curtain = fbm_2d(x * 0.18 + t * speed * 0.4, y * 0.08, seed=seed)
        ribbon = 0.5 + 0.5 * math.sin(x * 0.25 - t * speed * 1.7)
        glow = clamp01(curtain * 0.7 + ribbon * 0.45 - abs(ny - 0.45) * 0.5)
        return scale_color(sample_palette(palette, curtain * 0.8 + ribbon * 0.2), glow)

    return build_grid(width, height, paint)


@register_2d("Warm blobby shapes drift around like a real lava lamp.")
def lava_lamp(width: int, height: int, t: float, speed: float = 0.45, palette: Palette = LAVA_PALETTE) -> Frame2D:
    """Lava lamp blobs.

    Layperson description:
        Big rounded warm blobs slowly merge and separate, which feels like a
        classic glass lava lamp.

    How it works:
        Several moving blob centers each contribute a soft field, and the
        combined field is mapped through a lava palette.
    """

    centers = (
        (-0.45 + 0.35 * math.sin(t * speed * 0.8), -0.3 + 0.35 * math.cos(t * speed * 0.7), 0.42),
        (0.35 + 0.28 * math.cos(t * speed * 0.6 + 1.7), 0.25 + 0.32 * math.sin(t * speed * 0.8 + 0.9), 0.36),
        (0.00 + 0.22 * math.sin(t * speed * 0.9 + 2.3), -0.15 + 0.40 * math.cos(t * speed * 0.5 + 0.5), 0.33),
    )

    def paint(x: int, y: int, _: float, __: float) -> Color:
        cx = centered_coord(x, width)
        cy = centered_coord(y, height)
        field = 0.0
        for ox, oy, radius in centers:
            field += gaussian(math.hypot(cx - ox, cy - oy), radius)
        field = clamp01(field * 0.8)
        return sample_palette(palette, field)

    return build_grid(width, height, paint)


@register_2d("Mirrored slices of color make a kaleidoscope pattern that shifts over time.")
def kaleidoscope(width: int, height: int, t: float, speed: float = 0.7, arms: int = 8, palette: Palette = PARTY_PALETTE) -> Frame2D:
    """Kaleidoscope.

    Layperson description:
        A kaleidoscope takes one shape and mirrors it many times; this does the
        same thing with color wedges.

    How it works:
        We split the circle into mirrored angular slices and color them based on
        the mirrored angle plus the distance from center.
    """

    arms = max(1, arms)
    sector = TAU / arms

    def paint(x: int, y: int, _: float, __: float) -> Color:
        cx = centered_coord(x, width)
        cy = centered_coord(y, height)
        angle = math.atan2(cy, cx) + t * speed
        radius = math.hypot(cx, cy)
        local = abs(((angle % sector) / sector) - 0.5) * 2.0
        palette_position = local * 0.6 + radius * 0.4
        brightness = clamp01(1.15 - radius * 0.85)
        return scale_color(sample_palette(palette, palette_position), brightness)

    return build_grid(width, height, paint)


@register_2d("A horizontal and vertical scanner sweep through the grid and cross at the center.")
def scanner_cross(
    width: int,
    height: int,
    t: float,
    color_h: Color = (255, 50, 50),
    color_v: Color = (40, 180, 255),
    speed: float = 6.0,
    thickness: float = 1.7,
) -> Frame2D:
    """Crossed scanners.

    Layperson description:
        A horizontal bar and a vertical bar sweep across the panel and create a
        bright cross wherever they meet.

    How it works:
        The x and y scan positions bounce independently and each bar fades away
        from its center line.
    """

    x_head = ping_pong(t * speed, max(1, width - 1))
    y_head = ping_pong(t * speed * 0.92, max(1, height - 1))

    def paint(x: int, y: int, _: float, __: float) -> Color:
        horizontal = scale_color(color_h, gaussian(y - y_head, thickness))
        vertical = scale_color(color_v, gaussian(x - x_head, thickness))
        return add_colors(horizontal, vertical)

    return build_grid(width, height, paint)


@register_2d("Lights race around just the outer edge of the panel.")
def perimeter_chase(width: int, height: int, t: float, speed: float = 10.0, tail: int = 14, palette: Palette = PARTY_PALETTE) -> Frame2D:
    """Perimeter chase.

    Layperson description:
        Only the border LEDs light up, and the color chase runs around the edge
        like a sign frame or cabinet trim.

    How it works:
        The outer border is treated like one long loop, and a moving head lights
        pixels behind it.
    """

    loop = border_length(width, height)
    if loop <= 0:
        return []
    tail = max(1, tail)
    head = (t * speed) % loop

    def paint(x: int, y: int, _: float, __: float) -> Color:
        index = border_index(x, y, width, height)
        if index is None:
            return BLACK
        distance_behind = (head - index) % loop
        if distance_behind > tail:
            return BLACK
        brightness = (1.0 - distance_behind / tail) ** 2
        return scale_color(sample_palette(palette, index / max(1, loop)), brightness)

    return build_grid(width, height, paint)


@register_2d("Circular ripples spread across a watery surface from moving droplets.")
def ripple_pool(width: int, height: int, t: float, speed: float = 1.0, palette: Palette = OCEAN_PALETTE) -> Frame2D:
    """Rippling pool.

    Layperson description:
        The panel looks like water disturbed by occasional droplets that create
        expanding rings.

    How it works:
        We use one or more moving droplet sources and convert each pixel's
        distance from those sources into ring brightness.
    """

    droplets = (
        (0.5 + 0.25 * math.sin(t * speed * 0.7), 0.55 + 0.18 * math.cos(t * speed * 0.8)),
        (0.5 + 0.20 * math.cos(t * speed * 0.5 + 1.5), 0.4 + 0.22 * math.sin(t * speed * 0.6 + 0.8)),
    )

    def paint(_: int, __: int, nx: float, ny: float) -> Color:
        rings = 0.0
        for dx, dy in droplets:
            distance = math.hypot(nx - dx, ny - dy)
            rings += 0.5 + 0.5 * math.cos(distance * 30.0 - t * speed * 6.5)
        level = clamp01(rings / len(droplets))
        return sample_palette(palette, 0.15 + level * 0.55)

    return build_grid(width, height, paint)


@register_2d("Soft blobs of color merge into each other like liquid bubbles.")
def metaballs(width: int, height: int, t: float, speed: float = 0.5, palette: Palette = NEON_PALETTE) -> Frame2D:
    """Colorful metaballs.

    Layperson description:
        Rounded blobs wander around and merge into larger shapes when they get
        close, like liquid bubbles made of light.

    How it works:
        Each blob contributes a soft field; where fields overlap, the color gets
        stronger and changes.
    """

    balls = (
        (-0.5 + 0.35 * math.sin(t * speed * 0.7), -0.35 + 0.25 * math.cos(t * speed * 0.9), 0.30),
        (0.45 + 0.20 * math.cos(t * speed * 0.5 + 0.8), -0.05 + 0.35 * math.sin(t * speed * 0.8 + 0.6), 0.28),
        (0.00 + 0.40 * math.sin(t * speed * 0.6 + 1.7), 0.35 + 0.22 * math.cos(t * speed * 0.7 + 1.5), 0.34),
    )

    def paint(x: int, y: int, _: float, __: float) -> Color:
        cx = centered_coord(x, width)
        cy = centered_coord(y, height)
        field = 0.0
        tint = 0.0
        for index, (bx, by, radius) in enumerate(balls):
            strength = gaussian(math.hypot(cx - bx, cy - by), radius)
            field += strength
            tint += strength * (index / max(1, len(balls) - 1))
        field = clamp01(field * 0.95)
        return scale_color(sample_palette(palette, tint), field)

    return build_grid(width, height, paint)


@register_2d("Large soft cloud banks roll across the panel.")
def noise_clouds(width: int, height: int, t: float, speed: float = 0.25, palette: Palette = STORM_PALETTE, seed: int = 0) -> Frame2D:
    """Soft noise clouds.

    Layperson description:
        This makes the panel look like a sky full of slowly drifting cloud
        layers.

    How it works:
        Fractal noise provides large and small cloud details, and a muted palette
        keeps the look soft.
    """

    def paint(x: int, y: int, _: float, __: float) -> Color:
        density = fbm_2d(x * 0.12 + t * speed * 0.5, y * 0.12, seed=seed)
        detail = fbm_2d(x * 0.26 - t * speed * 0.7, y * 0.26, seed=seed + 40)
        cloud = clamp01(density * 0.7 + detail * 0.35)
        return sample_palette(palette, cloud * 0.85)

    return build_grid(width, height, paint)


@register_2d("Layered blue-green waves inspired by the Pacifica-style ocean effect.")
def pacifica_grid(width: int, height: int, t: float, speed: float = 0.6, palette: Palette = OCEAN_PALETTE) -> Frame2D:
    """Layered ocean waves.

    Layperson description:
        Gentle ocean-like bands roll diagonally across the panel with a rich
        layered water look.

    How it works:
        Several wave layers with different directions and speeds are combined,
        then mapped into an ocean palette.
    """

    def paint(x: int, y: int, nx: float, ny: float) -> Color:
        layer_a = 0.5 + 0.5 * math.sin(nx * 11.0 + ny * 3.0 + t * speed * 1.5)
        layer_b = 0.5 + 0.5 * math.sin(nx * 4.5 - ny * 8.0 - t * speed * 1.1)
        layer_c = 0.5 + 0.5 * math.sin((nx + ny) * 9.0 + t * speed * 2.0)
        surf = clamp01(layer_a * 0.34 + layer_b * 0.33 + layer_c * 0.33)
        foam = (layer_a * layer_b) ** 3
        return add_colors(sample_palette(palette, surf * 0.7), scale_color((180, 255, 250), foam * 0.35))

    return build_grid(width, height, paint)


@register_2d("A rotating spiral galaxy with a bright glowing core and starry arms.")
def spiral_galaxy(width: int, height: int, t: float, speed: float = 0.35, arms: int = 4, seed: int = 0) -> Frame2D:
    """Spiral galaxy.

    Layperson description:
        The center glows brightly while sweeping spiral arms curl around it like
        a galaxy viewed from above.

    How it works:
        The angle and distance from center decide whether a pixel lands inside a
        spiral arm, while noise adds scattered stars.
    """

    arms = max(1, arms)

    def paint(x: int, y: int, _: float, __: float) -> Color:
        cx = centered_coord(x, width)
        cy = centered_coord(y, height)
        angle = math.atan2(cy, cx)
        radius = math.hypot(cx, cy)
        arm_value = 0.5 + 0.5 * math.cos(angle * arms - radius * 10.0 + t * speed * TAU * 2.0)
        arm_glow = (arm_value ** 6) * clamp01(1.1 - radius)
        core = gaussian(radius, 0.18)
        stars = smoothstep((hash01(x, y, math.floor(t * 2.0), seed=seed) - 0.985) / 0.015)
        return add_colors(
            scale_color((255, 220, 170), core * 1.2),
            scale_color((110, 140, 255), arm_glow),
            scale_color(WHITE, stars),
        )

    return build_grid(width, height, paint)


@register_2d("Concentric rings zoom toward or away from the center like a tunnel.")
def tunnel_vision(width: int, height: int, t: float, speed: float = 1.0, palette: Palette = PARTY_PALETTE) -> Frame2D:
    """Tunnel rings.

    Layperson description:
        Bright rings move through the panel as if you are flying through a
        colorful tunnel.

    How it works:
        Distance from center produces ring spacing, and time shifts those rings
        forward.
    """

    def paint(x: int, y: int, _: float, __: float) -> Color:
        radius = math.hypot(centered_coord(x, width), centered_coord(y, height))
        ring = 0.5 + 0.5 * math.cos(radius * 22.0 - t * speed * 6.0)
        return scale_color(sample_palette(palette, radius - t * speed * 0.1), ring)

    return build_grid(width, height, paint)


@register_2d("A fan-like pinwheel spins from the center with bold color wedges.")
def pinwheel(width: int, height: int, t: float, speed: float = 0.8, blades: int = 6, palette: Palette = PARTY_PALETTE) -> Frame2D:
    """Spinning pinwheel.

    Layperson description:
        The panel becomes a spinning toy pinwheel or carnival spinner with bold
        triangular blades.

    How it works:
        The angle around center chooses a blade, while the blade pattern rotates
        over time.
    """

    blades = max(1, blades)

    def paint(x: int, y: int, _: float, __: float) -> Color:
        cx = centered_coord(x, width)
        cy = centered_coord(y, height)
        angle = math.atan2(cy, cx) / TAU + t * speed * 0.12
        radius = math.hypot(cx, cy)
        blade = fract(angle * blades)
        brightness = clamp01(1.1 - radius * 0.75)
        return scale_color(sample_palette(palette, blade), brightness)

    return build_grid(width, height, paint)


@register_2d("Large colored tiles drift and change like a glowing digital mosaic.")
def mosaic_shift(width: int, height: int, t: float, speed: float = 1.0, tile_size: int = 3, palette: Palette = PARTY_PALETTE, seed: int = 0) -> Frame2D:
    """Shifting mosaic.

    Layperson description:
        The panel is divided into big blocks, and those blocks drift through
        changing colors like animated stained glass.

    How it works:
        We color each tile instead of each pixel and scroll the tile coordinates
        over time.
    """

    tile_size = max(1, tile_size)

    def paint(x: int, y: int, _: float, __: float) -> Color:
        tile_x = math.floor((x + t * speed * tile_size) / tile_size)
        tile_y = math.floor((y - t * speed * tile_size * 0.6) / tile_size)
        tone = hash01(tile_x, tile_y, seed=seed) + t * speed * 0.03
        brightness = 0.5 + 0.5 * hash01(tile_x, tile_y, seed=seed + 14)
        return scale_color(sample_palette(palette, tone), brightness)

    return build_grid(width, height, paint)


@register_2d("Diamond-shaped pulses expand from the center using city-block distance.")
def diamond_pulse(width: int, height: int, t: float, speed: float = 1.0, palette: Palette = ICE_PALETTE) -> Frame2D:
    """Diamond pulses.

    Layperson description:
        Instead of round rings, this creates pulses with sharp diamond edges.

    How it works:
        We use horizontal-plus-vertical distance from center instead of round
        distance, then animate waves through that measurement.
    """

    def paint(x: int, y: int, _: float, __: float) -> Color:
        distance = abs(centered_coord(x, width)) + abs(centered_coord(y, height))
        pulse = 0.5 + 0.5 * math.cos(distance * 16.0 - t * speed * 6.0)
        return scale_color(sample_palette(palette, distance * 0.4 - t * speed * 0.07), pulse)

    return build_grid(width, height, paint)


@register_2d("Stars streak outward from the center like a spaceship jump effect.")
def starfield_grid(width: int, height: int, t: float, speed: float = 0.6, stars: int = 28, seed: int = 0) -> Frame2D:
    """Warp-speed starfield.

    Layperson description:
        Bright stars shoot away from the center, giving a hyperspace or warp
        tunnel feeling.

    How it works:
        Each star gets a direction and a looping depth value that determines how
        far it has traveled from the center.
    """

    stars = max(1, stars)
    max_radius = math.hypot(1.0, 1.0)

    def paint(x: int, y: int, _: float, __: float) -> Color:
        cx = centered_coord(x, width)
        cy = centered_coord(y, height)
        color = BLACK
        for star in range(stars):
            angle = hash01(star, seed=seed) * TAU
            depth = fract(hash01(star, seed=seed + 31) + t * speed * (0.3 + hash01(star, seed=seed + 47) * 1.1))
            radius = (depth ** 2) * max_radius
            sx = math.cos(angle) * radius
            sy = math.sin(angle) * radius
            brightness = gaussian(math.hypot(cx - sx, cy - sy), 0.05 + depth * 0.03) * depth
            color = add_colors(color, scale_color(WHITE, brightness * 1.6))
        return color

    return build_grid(width, height, paint)


@register_2d("Contour-map style bands sweep across the panel like animated terrain.")
def terrain_topography(width: int, height: int, t: float, speed: float = 0.15, seed: int = 0) -> Frame2D:
    """Animated terrain lines.

    Layperson description:
        This looks like a colorful topographic map where elevation bands shift
        and crawl over time.

    How it works:
        Noise acts like fake height data, then contour lines are drawn wherever
        that height crosses band boundaries.
    """

    def paint(x: int, y: int, _: float, __: float) -> Color:
        height_value = fbm_2d(x * 0.12 + t * speed * 0.4, y * 0.12 - t * speed * 0.2, seed=seed)
        base = sample_palette(TERRAIN_PALETTE, height_value * 0.88)
        contour = abs(fract(height_value * 10.0) - 0.5)
        line = clamp01(1.0 - contour * 18.0)
        return add_colors(scale_color(base, 0.9), scale_color(WHITE, line * 0.25))

    return build_grid(width, height, paint)


@register_2d("A warm sunset scene with a bright sun near the horizon and glowing clouds.")
def sunset_horizon(width: int, height: int, t: float, speed: float = 0.04, seed: int = 0) -> Frame2D:
    """Animated sunset horizon.

    Layperson description:
        The bottom of the panel glows like a horizon while a sun and cloud haze
        slowly drift across the sky.

    How it works:
        Vertical position chooses the sky gradient and a moving circular glow
        provides the sun.
    """

    sun_x = 0.5 + 0.22 * math.sin(t * speed * TAU)
    sun_y = 0.72 + 0.05 * math.cos(t * speed * TAU * 0.8)

    def paint(x: int, y: int, nx: float, ny: float) -> Color:
        sky = sample_palette(SUNSET_PALETTE, (1.0 - ny) * 0.6 + 0.08)
        cloud = fbm_2d(x * 0.16 + t * speed * 1.2, y * 0.10, seed=seed)
        haze = scale_color((255, 140, 80), cloud * 0.18)
        sun = gaussian(math.hypot(nx - sun_x, ny - sun_y), 0.16)
        return add_colors(scale_color(sky, 0.92), haze, scale_color((255, 215, 120), sun))

    return build_grid(width, height, paint)


@register_2d("A frosty field of cool cyan waves and bright icy highlights.")
def ice_waves(width: int, height: int, t: float, speed: float = 0.7, palette: Palette = ICE_PALETTE) -> Frame2D:
    """Frozen wave field.

    Layperson description:
        The panel feels cold and crystalline, with blue-white ridges moving like
        wind over snow or ice.

    How it works:
        Layered wave shapes produce ridges, and a cool palette gives the frosty
        color scheme.
    """

    def paint(_: int, __: int, nx: float, ny: float) -> Color:
        ridges = 0.5 + 0.5 * math.sin(nx * 12.0 + t * speed * 1.8)
        ridges *= 0.5 + 0.5 * math.sin(ny * 10.0 - t * speed * 1.2)
        sparkle = (ridges ** 4) * 0.7
        base = sample_palette(palette, ridges * 0.75)
        return add_colors(base, scale_color(WHITE, sparkle))

    return build_grid(width, height, paint)


@register_2d("A patchwork ember field with hot sparks dancing through dark ash.")
def ember_field(width: int, height: int, t: float, speed: float = 0.6, seed: int = 0) -> Frame2D:
    """Ember field.

    Layperson description:
        This looks like glowing coal patches across a fire pit, with occasional
        sparks flickering brighter.

    How it works:
        Noise creates the hot patches while a faster random layer adds brief
        spark bursts.
    """

    frame = math.floor(t * 14.0)

    def paint(x: int, y: int, _: float, __: float) -> Color:
        heat = fbm_2d(x * 0.20 - t * speed * 0.3, y * 0.20, seed=seed)
        base = sample_palette(LAVA_PALETTE, heat * 0.8)
        spark = smoothstep((hash01(x, y, frame, seed=seed + 17) - 0.97) / 0.03)
        return add_colors(scale_color(base, 0.65), scale_color((255, 210, 80), spark))

    return build_grid(width, height, paint)


__all__ = [
    "BLACK",
    "WHITE",
    "AURORA_PALETTE",
    "Color",
    "FIRE_PALETTE",
    "Frame1D",
    "Frame2D",
    "ICE_PALETTE",
    "LAVA_PALETTE",
    "NEON_PALETTE",
    "OCEAN_PALETTE",
    "PARTY_PALETTE",
    "PATTERNS_1D",
    "PATTERNS_2D",
    "PatternInfo",
    "SUNSET_PALETTE",
    "TERRAIN_PALETTE",
    "build_grid",
    "build_strip",
    "flatten_grid",
    "list_patterns",
    *sorted(PATTERNS_1D),
    *sorted(PATTERNS_2D),
]

from __future__ import annotations

from dataclasses import dataclass
import inspect
import math
from typing import Callable

from . import pattern_library as lib
from .models import PaletteSlot, PatternDescriptor, PlaybackSettings, RGBColor

PatternRenderer = Callable[[int, float, list[PaletteSlot], PlaybackSettings], list[RGBColor]]


@dataclass(frozen=True)
class PatternSpec:
    id: str
    label: str
    summary: str
    category: str
    renderer: PatternRenderer
    legacy: bool = False


def _palette_color(palette: list[PaletteSlot], index: int) -> RGBColor:
    if not palette:
        return RGBColor(r=255, g=255, b=255)
    return palette[index % len(palette)].color


def _mix(a: RGBColor, b: RGBColor, t: float) -> RGBColor:
    t = max(0.0, min(1.0, t))
    return RGBColor(
        r=int(a.r + (b.r - a.r) * t),
        g=int(a.g + (b.g - a.g) * t),
        b=int(a.b + (b.b - a.b) * t),
    )


def _wheel(position: float) -> RGBColor:
    position = position % 1.0
    if position < 1 / 3:
        x = position * 3
        return RGBColor(r=int(255 * (1 - x)), g=int(255 * x), b=0)
    if position < 2 / 3:
        x = (position - 1 / 3) * 3
        return RGBColor(r=0, g=int(255 * (1 - x)), b=int(255 * x))
    x = (position - 2 / 3) * 3
    return RGBColor(r=int(255 * x), g=0, b=int(255 * (1 - x)))


def _to_tuple(color: RGBColor | None) -> tuple[int, int, int]:
    if color is None:
        return (255, 255, 255)
    return (color.r, color.g, color.b)


def _dim_tuple(color: RGBColor, factor: float) -> tuple[int, int, int]:
    scaled = color.scaled(factor)
    return (scaled.r, scaled.g, scaled.b)


def _palette_tuples(palette: list[PaletteSlot]) -> tuple[tuple[int, int, int], ...]:
    if len(palette) >= 2:
        return tuple(slot.color.clamp_tuple() for slot in palette)
    if len(palette) == 1:
        return (palette[0].color.clamp_tuple(),)
    return tuple()


def _brightness_scale(colors: list[tuple[int, int, int]], brightness: float) -> list[RGBColor]:
    factor = max(0.0, min(1.0, brightness))
    return [
        RGBColor(
            r=max(0, min(255, int(round(r * factor)))),
            g=max(0, min(255, int(round(g * factor)))),
            b=max(0, min(255, int(round(b * factor)))),
        )
        for r, g, b in colors
    ]


def _float(default: object, fallback: float) -> float:
    return float(default) if isinstance(default, (int, float)) else fallback


def _int(default: object, fallback: int) -> int:
    return int(default) if isinstance(default, (int, float)) else fallback


def _intensity_factor(playback: PlaybackSettings) -> float:
    return 0.55 + max(0.0, min(2.0, playback.intensity)) * 0.75


def _pattern_kwargs(pattern_id: str, palette: list[PaletteSlot], playback: PlaybackSettings, signature: inspect.Signature) -> dict[str, object]:
    palette_tuples = _palette_tuples(palette)
    primary = _palette_color(palette, 0)
    secondary = _palette_color(palette, 1)
    accent = _palette_color(palette, 2)
    shadow = _palette_color(palette, 3 if len(palette) > 3 else 1)
    intensity = _intensity_factor(playback)

    kwargs: dict[str, object] = {}
    for name, parameter in signature.parameters.items():
        if name in {"length", "t"}:
            continue

        default = parameter.default
        if name == "color":
            kwargs[name] = _to_tuple(primary)
        elif name == "color_a":
            kwargs[name] = _to_tuple(primary)
        elif name == "color_b":
            kwargs[name] = _to_tuple(secondary)
        elif name == "base_color":
            kwargs[name] = _to_tuple(shadow)
        elif name == "sparkle_color":
            kwargs[name] = _to_tuple(accent)
        elif name == "sparkle":
            kwargs[name] = _to_tuple(accent)
        elif name == "background":
            kwargs[name] = _dim_tuple(shadow, 0.12)
        elif name == "palette":
            if len(palette_tuples) >= 2:
                kwargs[name] = palette_tuples
        elif name == "seed":
            kwargs[name] = playback.seed
        elif name == "speed":
            kwargs[name] = _float(default, 1.0) * max(0.05, playback.speed)
        elif name == "bpm":
            kwargs[name] = _float(default, 120.0) * max(0.05, playback.speed)
        elif name in {"tail", "block_size", "bands", "count"}:
            kwargs[name] = max(1, int(round(_float(default, 1.0) * intensity)))
        elif name == "spacing":
            base = _float(default, 3.0)
            kwargs[name] = max(1, int(round(base / max(0.6, min(1.8, intensity)))))
        elif name == "gap":
            kwargs[name] = max(1, int(round(_float(default, 2.0) * (0.8 + playback.intensity * 0.4))))
        elif name in {"density", "sparkle_density"}:
            kwargs[name] = max(0.01, min(0.9, _float(default, 0.1) * (0.5 + playback.intensity)))
        elif name == "frequency":
            kwargs[name] = max(0.1, _float(default, 1.0) * (0.7 + playback.intensity * 0.5))
        elif name == "stripe_size":
            kwargs[name] = max(1, int(round(_float(default, 4.0) * (0.7 + playback.intensity * 0.5))))
        elif name == "duty_cycle":
            kwargs[name] = max(0.02, min(0.6, _float(default, 0.15) * (0.7 + playback.intensity * 0.4)))
        elif name == "floor":
            kwargs[name] = max(0.01, min(0.3, _float(default, 0.08) * (1.1 - min(playback.intensity, 1.5) * 0.25)))
        elif name == "saturation":
            kwargs[name] = max(0.35, min(1.0, 0.6 + playback.intensity * 0.2))
    if pattern_id in {"fire", "fire_strip", "lava_flow", "ember_bed"} and len(palette_tuples) < 3:
        kwargs.pop("palette", None)
    if pattern_id in {"ocean_current", "aurora_ribbon", "noise_shimmer", "glitter_gradient", "runner_blocks", "carousel_stripes"} and len(palette_tuples) < 2:
        kwargs.pop("palette", None)
    return kwargs


def _render_library(pattern_id: str) -> PatternRenderer:
    info = lib.PATTERNS_1D[pattern_id]
    signature = inspect.signature(info.function)

    def render(length: int, t: float, palette: list[PaletteSlot], playback: PlaybackSettings) -> list[RGBColor]:
        kwargs = _pattern_kwargs(pattern_id, palette, playback, signature)
        frame = info.function(length, t, **kwargs)
        return _brightness_scale(frame, playback.brightness)

    return render


def _render_wave(length: int, t: float, palette: list[PaletteSlot], playback: PlaybackSettings) -> list[RGBColor]:
    colors: list[RGBColor] = []
    primary = _palette_color(palette, 0)
    secondary = _palette_color(palette, 1)
    tertiary = _palette_color(palette, 2)
    depth = 0.5 + min(2.0, playback.intensity) * 0.35
    speed = playback.speed
    for index in range(max(0, length)):
        position = index / max(length - 1, 1)
        wave_a = 0.5 + 0.5 * math.sin(position * math.tau * 1.0 + t * speed * 1.4)
        wave_b = 0.5 + 0.5 * math.sin(position * math.tau * 3.0 - t * speed * 2.1)
        crest = max(0.0, min(1.0, wave_a * 0.65 + wave_b * 0.35 * depth))
        base = _mix(secondary, primary, crest)
        shimmer = _mix(base, tertiary, max(0.0, min(1.0, (crest ** 2) * 0.35)))
        colors.append(shimmer.scaled(playback.brightness))
    return colors


def _render_rain(length: int, t: float, palette: list[PaletteSlot], playback: PlaybackSettings) -> list[RGBColor]:
    colors: list[RGBColor] = []
    drop_color = _palette_color(palette, 0)
    splash_color = _palette_color(palette, 2)
    background = _palette_color(palette, 3 if len(palette) > 3 else 1).scaled(0.08 * playback.brightness)
    lanes = max(2, int(2 + playback.intensity * 4))
    velocity = 6.0 + playback.speed * 7.0
    for index in range(max(0, length)):
        position = index / max(length - 1, 1)
        brightness = 0.0
        color = drop_color
        for lane in range(lanes):
            seeded = (lane * 0.173 + playback.seed * 0.013) % 1.0
            head = (t * velocity * (1.0 + lane * 0.07) + seeded) % 1.15
            distance = abs(position - (head % 1.0))
            wrap_distance = min(distance, abs((position + 1.0) - (head % 1.0)))
            if wrap_distance < 0.09:
                lane_strength = 1.0 - (wrap_distance / 0.09)
                brightness = max(brightness, lane_strength)
                color = _mix(drop_color, splash_color, max(0.0, min(1.0, lane_strength * 0.6)))
        colors.append(color.scaled(max(0.06, brightness) * playback.brightness) if brightness > 0 else background)
    return colors


def _register(specs: list[PatternSpec], spec: PatternSpec) -> None:
    specs.append(spec)


_PATTERN_SPECS: list[PatternSpec] = []

core_summaries = {
    "solid": "Single color hold using the first palette slot.",
    "chase": "Classic theatre-style chase tuned to the active palette.",
    "pulse": "Smooth breathing fade driven by the first palette slot.",
    "wave": "Palette-based travelling wave with soft shimmer on the crests.",
    "rainbow": "Full-spectrum rainbow sweep independent of the palette.",
    "strobe": "Fast hard flashes with duty-cycle driven punch.",
    "fire": "Organic warm flicker with palette-aware heat zones.",
    "rain": "Layered droplet streaks moving through each segment.",
}

_register(_PATTERN_SPECS, PatternSpec("solid", "Solid", core_summaries["solid"], "Core", _render_library("solid_color"), True))
_register(_PATTERN_SPECS, PatternSpec("chase", "Chase", core_summaries["chase"], "Core", _render_library("theater_chase"), True))
_register(_PATTERN_SPECS, PatternSpec("pulse", "Pulse", core_summaries["pulse"], "Core", _render_library("breathe"), True))
_register(_PATTERN_SPECS, PatternSpec("wave", "Wave", core_summaries["wave"], "Core", _render_wave, True))
_register(_PATTERN_SPECS, PatternSpec("rainbow", "Rainbow", core_summaries["rainbow"], "Core", _render_library("rainbow_cycle"), True))
_register(_PATTERN_SPECS, PatternSpec("strobe", "Strobe", core_summaries["strobe"], "Core", _render_library("strobe"), True))
_register(_PATTERN_SPECS, PatternSpec("fire", "Fire", core_summaries["fire"], "Core", _render_library("fire_strip"), True))
_register(_PATTERN_SPECS, PatternSpec("rain", "Rain", core_summaries["rain"], "Core", _render_rain, True))

pattern_categories = {
    "solid_color": "Essentials",
    "candy_cane": "Stripes",
    "rainbow_gradient": "Color Fields",
    "rainbow_cycle": "Color Fields",
    "color_wipe": "Motion",
    "theater_chase": "Motion",
    "scanner": "Motion",
    "dual_scanner": "Motion",
    "comet_trail": "Motion",
    "meteor_rain": "Motion",
    "twinkle_stars": "Atmosphere",
    "sparkle_pop": "Atmosphere",
    "confetti_burst": "Atmosphere",
    "breathe": "Essentials",
    "heartbeat": "Energy",
    "sinelon": "Motion",
    "juggle_balls": "Energy",
    "bpm_stripes": "Energy",
    "fire_strip": "Atmosphere",
    "lava_flow": "Atmosphere",
    "ocean_current": "Atmosphere",
    "aurora_ribbon": "Atmosphere",
    "ripple_ring": "Energy",
    "plasma_band": "Color Fields",
    "noise_shimmer": "Atmosphere",
    "police_lights": "Alerts",
    "sunrise": "Atmosphere",
    "runner_blocks": "Stripes",
    "glitter_gradient": "Atmosphere",
    "neon_snakes": "Energy",
    "storm_clouds_strip": "Atmosphere",
    "ember_bed": "Atmosphere",
    "carousel_stripes": "Stripes",
}

friendly_labels = {
    "solid_color": "Solid Color",
    "rainbow_gradient": "Rainbow Gradient",
    "rainbow_cycle": "Rainbow Cycle",
    "color_wipe": "Color Wipe",
    "theater_chase": "Theater Chase",
    "dual_scanner": "Dual Scanner",
    "comet_trail": "Comet Trail",
    "meteor_rain": "Meteor Rain",
    "twinkle_stars": "Twinkle Stars",
    "sparkle_pop": "Sparkle Pop",
    "confetti_burst": "Confetti Burst",
    "bpm_stripes": "BPM Stripes",
    "fire_strip": "Fire Strip",
    "lava_flow": "Lava Flow",
    "ocean_current": "Ocean Current",
    "aurora_ribbon": "Aurora Ribbon",
    "ripple_ring": "Ripple Ring",
    "plasma_band": "Plasma Band",
    "noise_shimmer": "Noise Shimmer",
    "police_lights": "Police Lights",
    "runner_blocks": "Runner Blocks",
    "glitter_gradient": "Glitter Gradient",
    "storm_clouds_strip": "Storm Clouds",
    "ember_bed": "Ember Bed",
    "carousel_stripes": "Carousel Stripes",
}

for pattern_id, info in lib.PATTERNS_1D.items():
    if pattern_id in {"solid_color", "theater_chase", "breathe", "rainbow_cycle", "strobe", "fire_strip"}:
        continue
    label = friendly_labels.get(pattern_id, pattern_id.replace("_", " ").title())
    category = pattern_categories.get(pattern_id, "Library")
    _register(
        _PATTERN_SPECS,
        PatternSpec(
            id=pattern_id,
            label=label,
            summary=info.summary,
            category=category,
            renderer=_render_library(pattern_id),
            legacy=False,
        ),
    )

AVAILABLE_PATTERNS: list[PatternSpec] = list(_PATTERN_SPECS)
PATTERN_MAP: dict[str, PatternRenderer] = {spec.id: spec.renderer for spec in AVAILABLE_PATTERNS}
PATTERN_DESCRIPTORS: list[PatternDescriptor] = [
    PatternDescriptor(id=spec.id, label=spec.label, summary=spec.summary, category=spec.category, legacy=spec.legacy)
    for spec in AVAILABLE_PATTERNS
]
PATTERN_CHOICES: set[str] = set(PATTERN_MAP)


def resolve_pattern(pattern_id: str) -> PatternRenderer:
    return PATTERN_MAP.get(pattern_id, PATTERN_MAP["rainbow"])

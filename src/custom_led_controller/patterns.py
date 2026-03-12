from __future__ import annotations

import math
import random
from typing import Callable, Iterable
from .models import PatternKind, RGBColor, PaletteSlot, PlaybackSettings


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


def pattern_solid(length: int, t: float, palette: list[PaletteSlot], playback: PlaybackSettings) -> list[RGBColor]:
    color = _palette_color(palette, 0).scaled(playback.brightness)
    return [color for _ in range(length)]


def pattern_chase(length: int, t: float, palette: list[PaletteSlot], playback: PlaybackSettings) -> list[RGBColor]:
    colors = []
    head = int(t * 10 * playback.speed) % max(length, 1)
    for i in range(length):
        distance = min((i - head) % max(length, 1), 8)
        if distance < 4:
            factor = max(0.15, 1.0 - distance / 4)
            colors.append(_palette_color(palette, 0).scaled(factor * playback.brightness))
        else:
            colors.append(_palette_color(palette, 1).scaled(0.06 * playback.brightness))
    return colors


def pattern_pulse(length: int, t: float, palette: list[PaletteSlot], playback: PlaybackSettings) -> list[RGBColor]:
    factor = (math.sin(t * playback.speed * 2 * math.pi) + 1) / 2
    base = _palette_color(palette, 0).scaled(max(0.05, factor * playback.brightness))
    return [base for _ in range(length)]


def pattern_wave(length: int, t: float, palette: list[PaletteSlot], playback: PlaybackSettings) -> list[RGBColor]:
    colors: list[RGBColor] = []
    primary = _palette_color(palette, 0)
    secondary = _palette_color(palette, 1)
    for i in range(length):
        phase = (i / max(length, 1)) * 2 * math.pi
        factor = (math.sin((phase + t * playback.speed * 3)) + 1) / 2
        color = _mix(secondary, primary, factor).scaled(playback.brightness)
        colors.append(color)
    return colors


def pattern_rainbow(length: int, t: float, palette: list[PaletteSlot], playback: PlaybackSettings) -> list[RGBColor]:
    return [
        _wheel((i / max(length, 1)) + (t * playback.speed * 0.1)).scaled(playback.brightness)
        for i in range(length)
    ]


def pattern_strobe(length: int, t: float, palette: list[PaletteSlot], playback: PlaybackSettings) -> list[RGBColor]:
    on = int(t * playback.speed * 8) % 2 == 0
    color = _palette_color(palette, 0).scaled(playback.brightness if on else 0.0)
    return [color for _ in range(length)]


def pattern_fire(length: int, t: float, palette: list[PaletteSlot], playback: PlaybackSettings) -> list[RGBColor]:
    rng = random.Random(int(t * 20 * playback.speed) + playback.seed)
    hot = _palette_color(palette, 0)
    warm = _palette_color(palette, 1)
    cool = _palette_color(palette, 2 if len(palette) > 2 else 1)
    colors = []
    for _ in range(length):
        flicker = rng.random()
        if flicker > 0.75:
            colors.append(_mix(warm, hot, rng.random()).scaled(playback.brightness))
        elif flicker > 0.35:
            colors.append(_mix(cool, warm, rng.random()).scaled(playback.brightness))
        else:
            colors.append(_mix(RGBColor(r=0, g=0, b=0), cool, rng.random()).scaled(playback.brightness))
    return colors


def pattern_rain(length: int, t: float, palette: list[PaletteSlot], playback: PlaybackSettings) -> list[RGBColor]:
    colors: list[RGBColor] = []
    drop_color = _palette_color(palette, 0)
    background = _palette_color(palette, 1).scaled(0.05 * playback.brightness)
    for i in range(length):
        lane = (i * 17) % 23
        y = (t * playback.speed * 12 + lane) % max(length, 1)
        if abs(y - i) < 2:
            factor = 1.0 - (abs(y - i) / 2)
            colors.append(drop_color.scaled(factor * playback.brightness))
        else:
            colors.append(background)
    return colors


PATTERN_MAP: dict[PatternKind, Callable[[int, float, list[PaletteSlot], PlaybackSettings], list[RGBColor]]] = {
    PatternKind.SOLID: pattern_solid,
    PatternKind.CHASE: pattern_chase,
    PatternKind.PULSE: pattern_pulse,
    PatternKind.WAVE: pattern_wave,
    PatternKind.RAINBOW: pattern_rainbow,
    PatternKind.STROBE: pattern_strobe,
    PatternKind.FIRE: pattern_fire,
    PatternKind.RAIN: pattern_rain,
}

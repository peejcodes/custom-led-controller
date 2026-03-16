from __future__ import annotations

from enum import Enum
from typing import List, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class TransportMode(str, Enum):
    MOCK = "mock"
    SERIAL = "serial"


class RGBColor(BaseModel):
    r: int = Field(ge=0, le=255)
    g: int = Field(ge=0, le=255)
    b: int = Field(ge=0, le=255)

    def clamp_tuple(self) -> tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def scaled(self, factor: float) -> "RGBColor":
        factor = max(0.0, min(1.0, factor))
        return RGBColor(
            r=int(self.r * factor),
            g=int(self.g * factor),
            b=int(self.b * factor),
        )


class PaletteSlot(BaseModel):
    id: str
    name: str
    color: RGBColor


class PlaybackSettings(BaseModel):
    pattern: str = "rainbow"
    fps: int = Field(default=30, ge=1, le=120)
    speed: float = Field(default=1.0, ge=0.01, le=20.0)
    brightness: float = Field(default=0.75, ge=0.0, le=1.0)
    intensity: float = Field(default=1.0, ge=0.0, le=2.0)
    seed: int = 42

    @field_validator("pattern")
    @classmethod
    def normalize_pattern(cls, value: str) -> str:
        value = str(value or "").strip()
        return value or "rainbow"


class OutputConfig(BaseModel):
    id: str
    name: str
    pin: int = Field(ge=0)
    led_count: int = Field(ge=1, le=4096)
    enabled: bool = True


class ControllerConfig(BaseModel):
    id: str
    name: str
    mode: Literal["mock", "serial"] = "mock"
    port: str = "mock"
    baudrate: int = 921600
    enabled: bool = True
    outputs: List[OutputConfig] = Field(default_factory=list)

    @field_validator("outputs")
    @classmethod
    def validate_output_ids_unique(cls, outputs: List[OutputConfig]) -> List[OutputConfig]:
        ids = [output.id for output in outputs]
        if len(ids) != len(set(ids)):
            raise ValueError("Output IDs must be unique per controller.")
        return outputs

    def total_leds(self) -> int:
        return sum(output.led_count for output in self.outputs if output.enabled)


class SegmentConfig(BaseModel):
    id: str
    name: str
    controller_id: str
    output_id: str
    start: int = Field(ge=0)
    length: int = Field(ge=1)
    reversed: bool = False

    @property
    def end_exclusive(self) -> int:
        return self.start + self.length


class ZoneConfig(BaseModel):
    id: str
    name: str
    segment_ids: List[str] = Field(default_factory=list)


class ProjectConfig(BaseModel):
    name: str = "Custom LED Controller"
    controllers: List[ControllerConfig] = Field(default_factory=list)
    segments: List[SegmentConfig] = Field(default_factory=list)
    zones: List[ZoneConfig] = Field(default_factory=list)
    palette: List[PaletteSlot] = Field(default_factory=list)
    playback: PlaybackSettings = Field(default_factory=PlaybackSettings)

    @model_validator(mode="after")
    def validate_references(self) -> "ProjectConfig":
        controller_ids = {controller.id for controller in self.controllers}
        segment_ids = {segment.id for segment in self.segments}
        output_index = {
            (controller.id, output.id): output
            for controller in self.controllers
            for output in controller.outputs
        }

        for segment in self.segments:
            if segment.controller_id not in controller_ids:
                raise ValueError(f"Unknown controller_id on segment {segment.id}: {segment.controller_id}")
            key = (segment.controller_id, segment.output_id)
            if key not in output_index:
                raise ValueError(f"Unknown output reference on segment {segment.id}: {key}")
            output = output_index[key]
            if segment.end_exclusive > output.led_count:
                raise ValueError(
                    f"Segment {segment.id} exceeds output length "
                    f"({segment.end_exclusive} > {output.led_count})"
                )

        for zone in self.zones:
            for segment_id in zone.segment_ids:
                if segment_id not in segment_ids:
                    raise ValueError(f"Unknown segment_id on zone {zone.id}: {segment_id}")

        return self


class ControllerStatus(BaseModel):
    controller_id: str
    connected: bool
    mode: Literal["mock", "serial"]
    detail: str = "idle"
    last_frame_at: float | None = None


class OutputFrame(BaseModel):
    output_id: str
    colors: List[RGBColor]


class ControllerFrame(BaseModel):
    controller_id: str
    outputs: List[OutputFrame]


class ProjectSnapshot(BaseModel):
    project: ProjectConfig
    controller_status: List[ControllerStatus]
    server_time: float


class PreviewResponse(BaseModel):
    project_name: str
    server_time: float
    frames: List[ControllerFrame]


class PatternDescriptor(BaseModel):
    id: str
    label: str
    summary: str
    category: str
    legacy: bool = False

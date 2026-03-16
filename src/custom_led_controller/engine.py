from __future__ import annotations

import time
from .models import ControllerFrame, OutputFrame, ProjectConfig, RGBColor
from .patterns import resolve_pattern


def _blank_output(length: int) -> list[RGBColor]:
    return [RGBColor(r=0, g=0, b=0) for _ in range(length)]


class FrameRenderer:
    def render_project(self, project: ProjectConfig, seconds: float | None = None) -> list[ControllerFrame]:
        t = time.monotonic() if seconds is None else seconds
        pattern_fn = resolve_pattern(project.playback.pattern)
        frames: list[ControllerFrame] = []

        for controller in project.controllers:
            controller_outputs: dict[str, list[RGBColor]] = {
                output.id: _blank_output(output.led_count)
                for output in controller.outputs
                if output.enabled
            }

            for segment in [s for s in project.segments if s.controller_id == controller.id]:
                colors = pattern_fn(segment.length, t, project.palette, project.playback)
                if segment.reversed:
                    colors = list(reversed(colors))

                target = controller_outputs[segment.output_id]
                for offset, color in enumerate(colors):
                    idx = segment.start + offset
                    if 0 <= idx < len(target):
                        target[idx] = color

            frames.append(
                ControllerFrame(
                    controller_id=controller.id,
                    outputs=[
                        OutputFrame(output_id=output_id, colors=colors)
                        for output_id, colors in controller_outputs.items()
                    ],
                )
            )
        return frames

    def flatten_bytes(self, controller_frame: ControllerFrame) -> dict[str, bytes]:
        payloads: dict[str, bytes] = {}
        for output_frame in controller_frame.outputs:
            buffer = bytearray()
            for color in output_frame.colors:
                buffer.extend((color.r, color.g, color.b))
            payloads[output_frame.output_id] = bytes(buffer)
        return payloads

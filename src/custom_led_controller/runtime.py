from __future__ import annotations

import asyncio
import time
from typing import Dict, List

from .config import AppSettings
from .engine import FrameRenderer
from .models import ControllerConfig, ControllerStatus, PreviewResponse, ProjectConfig, ProjectSnapshot, TransportMode
from .storage import ProjectStore
from .transports.base import BaseTransport
from .transports.mock import MockTransport
from .transports.serial_transport import SerialTransport


def default_project() -> ProjectConfig:
    from .models import (
        ControllerConfig,
        OutputConfig,
        PaletteSlot,
        PlaybackSettings,
        ProjectConfig,
        RGBColor,
        SegmentConfig,
        TransportMode,
        ZoneConfig,
    )

    return ProjectConfig(
        name="Custom LED Controller",
        controllers=[
            ControllerConfig(
                id="ctrl-alpha",
                name="Controller Alpha",
                mode=TransportMode.MOCK,
                port="mock",
                outputs=[
                    OutputConfig(id="out-a1", name="Left Rail", pin=2, led_count=60),
                    OutputConfig(id="out-a2", name="Dash", pin=3, led_count=90),
                    OutputConfig(id="out-a3", name="Rear Accent", pin=4, led_count=48),
                ],
            ),
            ControllerConfig(
                id="ctrl-bravo",
                name="Controller Bravo",
                mode=TransportMode.MOCK,
                port="mock",
                outputs=[
                    OutputConfig(id="out-b1", name="Cargo", pin=5, led_count=120),
                    OutputConfig(id="out-b2", name="Door Pair", pin=6, led_count=40),
                ],
            ),
        ],
        segments=[
            SegmentConfig(id="seg-left-1", name="Front Left", controller_id="ctrl-alpha", output_id="out-a1", start=0, length=30),
            SegmentConfig(id="seg-left-2", name="Rear Left", controller_id="ctrl-alpha", output_id="out-a1", start=30, length=30),
            SegmentConfig(id="seg-dash", name="Main Dash", controller_id="ctrl-alpha", output_id="out-a2", start=0, length=90),
            SegmentConfig(id="seg-rear", name="Rear Accent", controller_id="ctrl-alpha", output_id="out-a3", start=0, length=48),
            SegmentConfig(id="seg-cargo", name="Cargo Floor", controller_id="ctrl-bravo", output_id="out-b1", start=0, length=120),
            SegmentConfig(id="seg-door-l", name="Door Left", controller_id="ctrl-bravo", output_id="out-b2", start=0, length=20),
            SegmentConfig(id="seg-door-r", name="Door Right", controller_id="ctrl-bravo", output_id="out-b2", start=20, length=20, reversed=True),
        ],
        zones=[
            ZoneConfig(id="zone-cabin", name="Cabin Glow", segment_ids=["seg-left-1", "seg-dash", "seg-door-l", "seg-door-r"]),
            ZoneConfig(id="zone-rear", name="Rear Area", segment_ids=["seg-left-2", "seg-rear", "seg-cargo"]),
        ],
        palette=[
            PaletteSlot(id="p1", name="Hot", color=RGBColor(r=255, g=96, b=24)),
            PaletteSlot(id="p2", name="Cool", color=RGBColor(r=40, g=120, b=255)),
            PaletteSlot(id="p3", name="Accent", color=RGBColor(r=255, g=255, b=255)),
            PaletteSlot(id="p4", name="Shadow", color=RGBColor(r=18, g=18, b=28)),
        ],
        playback=PlaybackSettings(pattern="rainbow", fps=30, speed=1.0, brightness=0.75, intensity=1.0, seed=42),
    )


class RuntimeState:
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.renderer = FrameRenderer()
        self.store = ProjectStore(settings.project_path)
        self.project = self.store.load() or default_project()
        self.store.save(self.project)
        self.transports: dict[str, BaseTransport] = {}
        self._stream_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    def snapshot(self) -> ProjectSnapshot:
        return ProjectSnapshot(
            project=self.project,
            controller_status=self.controller_status(),
            server_time=time.time(),
        )

    def controller_status(self) -> list[ControllerStatus]:
        statuses = []
        for controller in self.project.controllers:
            transport = self.transports.get(controller.id)
            if transport is None:
                statuses.append(
                    ControllerStatus(
                        controller_id=controller.id,
                        connected=False,
                        mode=controller.mode,
                        detail="not connected",
                        last_frame_at=None,
                    )
                )
            else:
                statuses.append(transport.status())
        return statuses

    def preview(self, seconds: float | None = None) -> PreviewResponse:
        frames = self.renderer.render_project(self.project, seconds=seconds)
        return PreviewResponse(
            project_name=self.project.name,
            server_time=time.time(),
            frames=frames,
        )

    def replace_project(self, project: ProjectConfig) -> ProjectConfig:
        self.project = project
        self.store.save(project)
        return project

    async def connect_controller(self, controller_id: str) -> ControllerStatus:
        controller = self._controller_or_raise(controller_id)
        transport = self._build_transport(controller)
        await transport.connect()
        self.transports[controller_id] = transport
        return transport.status()

    async def disconnect_controller(self, controller_id: str) -> ControllerStatus:
        transport = self.transports.get(controller_id)
        controller = self._controller_or_raise(controller_id)
        if transport is not None:
            await transport.disconnect()
            del self.transports[controller_id]
        return ControllerStatus(
            controller_id=controller_id,
            connected=False,
            mode=controller.mode,
            detail="not connected",
            last_frame_at=None,
        )

    def _controller_or_raise(self, controller_id: str) -> ControllerConfig:
        for controller in self.project.controllers:
            if controller.id == controller_id:
                return controller
        raise KeyError(f"Unknown controller: {controller_id}")

    def _build_transport(self, controller: ControllerConfig) -> BaseTransport:
        if controller.mode == TransportMode.MOCK or controller.port == "mock":
            return MockTransport(controller)
        return SerialTransport(controller)

    async def start(self) -> None:
        if self._stream_task is None or self._stream_task.done():
            self._stream_task = asyncio.create_task(self._stream_loop(), name="frame-stream-loop")

    async def stop(self) -> None:
        if self._stream_task is not None:
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass
        for transport in list(self.transports.values()):
            await transport.disconnect()
        self.transports.clear()

    async def _stream_loop(self) -> None:
        while True:
            fps = max(1, self.project.playback.fps)
            frame_period = 1.0 / fps
            started = time.perf_counter()
            frames = self.renderer.render_project(self.project)
            frame_index = {frame.controller_id: frame for frame in frames}
            for controller_id, transport in list(self.transports.items()):
                frame = frame_index.get(controller_id)
                if frame is None or not transport.connected:
                    continue
                payloads = self.renderer.flatten_bytes(frame)
                await transport.send_frame(payloads)
            elapsed = time.perf_counter() - started
            await asyncio.sleep(max(0.0, frame_period - elapsed))

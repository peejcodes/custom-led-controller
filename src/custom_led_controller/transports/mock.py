from __future__ import annotations

import asyncio
import time
from .base import BaseTransport
from ..models import TransportMode


class MockTransport(BaseTransport):
    @property
    def mode(self) -> TransportMode:
        return TransportMode.MOCK

    async def connect(self) -> None:
        await asyncio.sleep(0)
        self.connected = True
        self.detail = "mock connected"

    async def disconnect(self) -> None:
        await asyncio.sleep(0)
        self.connected = False
        self.detail = "mock disconnected"

    async def send_frame(self, payloads: dict[str, bytes]) -> None:
        await asyncio.sleep(0)
        if not self.connected:
            return
        self.last_frame_at = time.time()
        total = sum(len(buffer) for buffer in payloads.values())
        self.detail = f"mock frame ok ({total} bytes)"

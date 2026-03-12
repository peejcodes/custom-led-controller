from __future__ import annotations

import asyncio
import struct
import time


from .base import BaseTransport
from ..models import TransportMode


MAGIC = b"LEDC"
VERSION = 1
PACKET_FRAME = 0x10
PACKET_PING = 0x01


class SerialTransport(BaseTransport):
    """
    Serial transport scaffold.

    This class is intentionally conservative and minimal until the matching
    ESP32-S3 firmware is implemented. It already does useful things:

    - opens the configured serial port
    - can send a small ping packet
    - can stream frame packets per output

    The packet format used here should be finalized together with the firmware.

    Proposed packet header:

    magic[4] | version[1] | type[1] | output_id_len[1] | payload_len[4]

    followed by:
    - output_id bytes (utf-8)
    - payload bytes (raw RGB triplets)
    """

    def __init__(self, controller):
        super().__init__(controller)
        self._serial = None

    @property
    def mode(self) -> TransportMode:
        return TransportMode.SERIAL

    async def connect(self) -> None:
        import importlib
        serial = importlib.import_module("serial")
        loop = asyncio.get_running_loop()
        self._serial = await loop.run_in_executor(
            None,
            lambda: serial.Serial(
                self.controller.port,
                self.controller.baudrate,
                timeout=0.25,
                write_timeout=0.25,
            ),
        )
        self.connected = True
        self.detail = f"serial connected @ {self.controller.port}"
        await self._send_ping()

    async def disconnect(self) -> None:
        if self._serial is not None and self._serial.is_open:
            await asyncio.get_running_loop().run_in_executor(None, self._serial.close)
        self.connected = False
        self.detail = "serial disconnected"

    async def _send_ping(self) -> None:
        if not self._serial:
            return
        packet = MAGIC + bytes([VERSION, PACKET_PING, 0]) + struct.pack(">I", 0)
        await asyncio.get_running_loop().run_in_executor(None, self._serial.write, packet)

    async def send_frame(self, payloads: dict[str, bytes]) -> None:
        if not self._serial or not self.connected:
            return
        loop = asyncio.get_running_loop()
        for output_id, payload in payloads.items():
            output_bytes = output_id.encode("utf-8")
            packet = (
                MAGIC
                + bytes([VERSION, PACKET_FRAME, len(output_bytes)])
                + struct.pack(">I", len(payload))
                + output_bytes
                + payload
            )
            await loop.run_in_executor(None, self._serial.write, packet)
        self.last_frame_at = time.time()
        total = sum(len(chunk) for chunk in payloads.values())
        self.detail = f"serial frame ok ({total} rgb bytes)"

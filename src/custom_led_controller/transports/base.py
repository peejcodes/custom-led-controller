from __future__ import annotations

from abc import ABC, abstractmethod
from ..models import ControllerConfig, ControllerStatus, TransportMode


class BaseTransport(ABC):
    def __init__(self, controller: ControllerConfig):
        self.controller = controller
        self.connected = False
        self.last_frame_at: float | None = None
        self.detail = "idle"

    @property
    @abstractmethod
    def mode(self) -> TransportMode:
        raise NotImplementedError

    @abstractmethod
    async def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def send_frame(self, payloads: dict[str, bytes]) -> None:
        raise NotImplementedError

    def status(self) -> ControllerStatus:
        return ControllerStatus(
            controller_id=self.controller.id,
            connected=self.connected,
            mode=self.mode,
            detail=self.detail,
            last_frame_at=self.last_frame_at,
        )

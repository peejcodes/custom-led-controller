from pathlib import Path
from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8787
    data_dir: Path = Field(default_factory=lambda: Path("data"))
    project_file: str = "project.json"
    websocket_preview_fps: int = 10

    @property
    def project_path(self) -> Path:
        return self.data_dir / self.project_file

from __future__ import annotations

import json
from pathlib import Path
from .models import ProjectConfig


class ProjectStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> ProjectConfig | None:
        if not self.path.exists():
            return None
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return ProjectConfig.model_validate(payload)

    def save(self, project: ProjectConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(project.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )

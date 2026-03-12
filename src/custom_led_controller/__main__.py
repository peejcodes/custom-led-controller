from __future__ import annotations

import uvicorn
from .api import create_app
from .config import AppSettings


def main() -> None:
    settings = AppSettings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    app = create_app(settings)
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()

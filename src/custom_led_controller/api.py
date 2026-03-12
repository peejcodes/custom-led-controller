from __future__ import annotations

from pathlib import Path
import time

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import AppSettings
from .models import ControllerStatus, PreviewResponse, ProjectConfig, ProjectSnapshot
from .runtime import RuntimeState


def create_app(settings: AppSettings | None = None) -> FastAPI:
    settings = settings or AppSettings()
    runtime = RuntimeState(settings)
    app = FastAPI(title="Custom LED Controller", version="0.1.0")
    app.state.runtime = runtime

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.on_event("startup")
    async def startup() -> None:
        await runtime.start()

    @app.on_event("shutdown")
    async def shutdown() -> None:
        await runtime.stop()

    @app.get("/api/health")
    async def health() -> dict:
        return {"ok": True, "time": time.time()}

    @app.get("/api/project", response_model=ProjectSnapshot)
    async def get_project() -> ProjectSnapshot:
        return runtime.snapshot()

    @app.put("/api/project", response_model=ProjectSnapshot)
    async def put_project(project: ProjectConfig) -> ProjectSnapshot:
        runtime.replace_project(project)
        return runtime.snapshot()

    @app.post("/api/project/reset", response_model=ProjectSnapshot)
    async def reset_project() -> ProjectSnapshot:
        from .runtime import default_project
        runtime.replace_project(default_project())
        return runtime.snapshot()

    @app.get("/api/preview", response_model=PreviewResponse)
    async def get_preview(seconds: float | None = Query(default=None)) -> PreviewResponse:
        return runtime.preview(seconds=seconds)

    @app.post("/api/controllers/{controller_id}/connect", response_model=ControllerStatus)
    async def connect_controller(controller_id: str) -> ControllerStatus:
        try:
            return await runtime.connect_controller(controller_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Connect failed: {exc}") from exc

    @app.post("/api/controllers/{controller_id}/disconnect", response_model=ControllerStatus)
    async def disconnect_controller(controller_id: str) -> ControllerStatus:
        try:
            return await runtime.disconnect_controller(controller_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Disconnect failed: {exc}") from exc

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(static_dir / "index.html", headers={"Cache-Control": "no-store"})

    return app

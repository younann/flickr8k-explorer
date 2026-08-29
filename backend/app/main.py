from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import default_data_dir
from app.models import HealthResponse
from app.repository import DatasetRepository
from app.routes import dataset_router


def create_app(data_dir: Path | None = None) -> FastAPI:
    resolved_data_dir = data_dir or default_data_dir()
    app = FastAPI(title="Flickr8k Explorer API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=[],
    )
    repository = DatasetRepository(resolved_data_dir)
    app.include_router(dataset_router(repository))

    @app.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(**{
            "status": "ok",
            "dataset_ready": repository.ready,
        })

    return app


app = create_app()

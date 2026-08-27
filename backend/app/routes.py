from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.repository import DatasetRepository


def dataset_router(repository: DatasetRepository) -> APIRouter:
    router = APIRouter(prefix="/api")

    def require_data() -> None:
        if not repository.ready:
            raise HTTPException(status_code=409, detail="Dataset is not imported. Run python scripts/import_dataset.py --download.")

    @router.get("/overview")
    def overview() -> dict:
        require_data()
        return repository.overview()

    @router.get("/samples")
    def samples(q: str = "", split: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100)) -> dict:
        require_data()
        return repository.samples(query=q, split=split, page=page, page_size=page_size)

    @router.get("/samples/{sample_id}")
    def sample_detail(sample_id: str) -> dict:
        require_data()
        sample = repository.detail(sample_id)
        if sample is None:
            raise HTTPException(status_code=404, detail="Sample not found")
        return {"sample": sample, "neighbors": {"previous_id": None, "next_id": None}}

    @router.get("/samples/{sample_id}/image")
    def sample_image(sample_id: str) -> FileResponse:
        require_data()
        image = repository.image(sample_id)
        if image is None:
            raise HTTPException(status_code=404, detail="Image not found")
        path, media_type = image
        return FileResponse(path, media_type=media_type)

    return router

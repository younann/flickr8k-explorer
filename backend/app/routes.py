from __future__ import annotations

import csv
from io import StringIO
import json
import re
import sqlite3
from collections.abc import Iterator
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BeforeValidator

from app.repository import DatasetRepository
from app.models import (
    CollectionExportResponse,
    CollectionListResponse,
    CollectionResponse,
    CreateCollectionRequest,
    CreateFindingRequest,
    ErrorResponse,
    ExportFinding,
    FindingResponse,
    FindingsResponse,
    OverviewResponse,
    RadarResponse,
    SampleAnalysisResponse,
    SampleDetailResponse,
    SamplePage,
    SimilarSamplesResponse,
)

ANALYSIS_BACKFILL_REQUIRED = "Analysis backfill is required. Run python scripts/import_dataset.py --download."


def _strict_radar_boolean(value: object) -> bool:
    if value is True or value == "true":
        return True
    if value is False or value == "false":
        return False
    raise ValueError("near_duplicates_only must be true or false")


RadarBoolean = Annotated[bool, BeforeValidator(_strict_radar_boolean)]


def dataset_router(repository: DatasetRepository) -> APIRouter:
    router = APIRouter(prefix="/api")

    def require_data() -> None:
        if not repository.ready:
            raise HTTPException(status_code=409, detail="Dataset is not imported. Run python scripts/import_dataset.py --download.")

    def require_analysis() -> None:
        if not repository.analysis_ready:
            raise HTTPException(status_code=409, detail=ANALYSIS_BACKFILL_REQUIRED)

    errors = {409: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
    @router.get("/overview", response_model=OverviewResponse, responses=errors)
    def overview() -> OverviewResponse:
        require_data()
        return OverviewResponse(**repository.overview())

    @router.get("/samples", response_model=SamplePage, responses=errors)
    def samples(
        q: str = "", split: str | None = None, sort: Literal["default", "disagreement"] = "default",
        page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100),
    ) -> SamplePage:
        require_data()
        if sort == "disagreement":
            require_analysis()
        return SamplePage(**repository.samples(query=q, split=split, sort=sort, page=page, page_size=page_size))

    @router.get("/samples/{sample_id}", response_model=SampleDetailResponse, responses=errors)
    def sample_detail(sample_id: str) -> SampleDetailResponse:
        require_data()
        sample = repository.detail(sample_id)
        if sample is None:
            raise HTTPException(status_code=404, detail="Sample not found")
        return SampleDetailResponse(sample=sample, neighbors={"previous_id": None, "next_id": None})

    @router.get("/samples/{sample_id}/image", responses=errors)
    def sample_image(sample_id: str) -> FileResponse:
        require_data()
        image = repository.image(sample_id)
        if image is None:
            raise HTTPException(status_code=404, detail="Image not found")
        path, media_type = image
        return FileResponse(path, media_type=media_type)

    @router.get("/radar", response_model=RadarResponse, responses=errors)
    def radar(
        split: Literal["train", "validation", "test"] | None = None,
        min_score: int = Query(0, ge=0, le=100),
        max_score: int = Query(100, ge=0, le=100),
        near_duplicates_only: RadarBoolean = False,
    ) -> RadarResponse:
        require_data()
        require_analysis()
        if min_score > max_score:
            raise HTTPException(status_code=422, detail="min_score must not exceed max_score")
        return RadarResponse(**repository.radar(
            split=split, min_score=min_score, max_score=max_score, near_duplicates_only=near_duplicates_only,
        ))

    @router.get("/samples/{sample_id}/analysis", response_model=SampleAnalysisResponse, responses=errors)
    def sample_analysis(sample_id: str) -> SampleAnalysisResponse:
        require_data()
        require_analysis()
        analysis = repository.analysis(sample_id)
        if analysis is None:
            raise HTTPException(status_code=404, detail="Sample not found")
        return SampleAnalysisResponse(**analysis)

    @router.get("/samples/{sample_id}/similar", response_model=SimilarSamplesResponse, responses=errors)
    def similar_samples(sample_id: str, limit: int = Query(6, ge=1, le=6)) -> SimilarSamplesResponse:
        require_data()
        require_analysis()
        if repository.detail(sample_id) is None:
            raise HTTPException(status_code=404, detail="Sample not found")
        return SimilarSamplesResponse(items=repository.similar(sample_id, limit))

    @router.get("/collections", response_model=CollectionListResponse, responses=errors)
    def collections() -> CollectionListResponse:
        require_data()
        return CollectionListResponse(items=repository.collections())

    @router.post("/collections", status_code=201, response_model=CollectionResponse, responses={**errors, 409: {"model": ErrorResponse}})
    def create_collection(request: CreateCollectionRequest) -> CollectionResponse:
        require_data()
        try:
            return CollectionResponse(**repository.create_collection(request.name))
        except sqlite3.IntegrityError as error:
            raise HTTPException(status_code=409, detail="Collection name already exists") from error

    @router.delete("/collections/{collection_id}", status_code=204, responses=errors)
    def delete_collection(collection_id: int) -> Response:
        require_data()
        if not repository.delete_collection(collection_id):
            raise HTTPException(status_code=404, detail="Collection not found")
        return Response(status_code=204)

    @router.get("/collections/{collection_id}/findings", response_model=FindingsResponse, responses=errors)
    def collection_findings(collection_id: int) -> FindingsResponse:
        require_data()
        if repository.collection(collection_id) is None:
            raise HTTPException(status_code=404, detail="Collection not found")
        return FindingsResponse(items=repository.findings(collection_id))

    @router.post("/collections/{collection_id}/findings", status_code=201, response_model=FindingResponse, responses=errors)
    def create_finding(collection_id: int, request: CreateFindingRequest) -> FindingResponse:
        require_data()
        if repository.collection(collection_id) is None:
            raise HTTPException(status_code=404, detail="Collection not found")
        if repository.detail(request.sample_id) is None:
            raise HTTPException(status_code=404, detail="Sample not found")
        return FindingResponse(**repository.create_finding(
            collection_id, request.sample_id, json.dumps(request.tags), request.note
        ))

    @router.delete("/findings/{finding_id}", status_code=204, responses=errors)
    def delete_finding(finding_id: int) -> Response:
        require_data()
        if not repository.delete_finding(finding_id):
            raise HTTPException(status_code=404, detail="Finding not found")
        return Response(status_code=204)

    @router.get("/collections/{collection_id}/export", response_model=CollectionExportResponse, responses=errors)
    def export_collection(collection_id: int, format: Literal["csv", "json"] = "csv") -> StreamingResponse | JSONResponse:
        require_data()
        collection = repository.collection(collection_id)
        if collection is None:
            raise HTTPException(status_code=404, detail="Collection not found")
        export = CollectionExportResponse(
            collection=collection,
            findings=[ExportFinding(**finding) for finding in repository.collection_export(collection_id)],
        )
        filename = _export_filename(collection["name"])
        if format == "json":
            return JSONResponse(
                content=export.model_dump(),
                headers={"Content-Disposition": f'attachment; filename="{filename}.json"'},
            )
        return StreamingResponse(
            _csv_rows(export), media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
        )

    return router


def _export_filename(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return normalized or "collection"


def _csv_rows(export: CollectionExportResponse) -> Iterator[str]:
    fields = [
        "finding_id", "collection_id", "collection_name", "collection_created_at", "collection_updated_at",
        "sample_id", "tags", "note", "created_at", "updated_at",
        "split", "width", "height", "captions", "disagreement_score", "token_disagreement", "vocabulary_diversity",
        "mean_caption_length", "caption_length_spread", "perceptual_hash",
    ]
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    yield buffer.getvalue()
    for finding in export.findings:
        buffer.seek(0)
        buffer.truncate(0)
        writer.writerow({
            "finding_id": finding.id, "collection_id": finding.collection_id, "collection_name": export.collection.name,
            "collection_created_at": export.collection.created_at, "collection_updated_at": export.collection.updated_at,
            "sample_id": finding.sample_id, "tags": json.dumps(finding.tags), "note": finding.note,
            "created_at": finding.created_at, "updated_at": finding.updated_at, "split": finding.split,
            "width": finding.width, "height": finding.height, "captions": json.dumps(finding.captions),
            "disagreement_score": finding.disagreement_score, "token_disagreement": finding.token_disagreement,
            "vocabulary_diversity": finding.vocabulary_diversity, "mean_caption_length": finding.mean_caption_length,
            "caption_length_spread": finding.caption_length_spread, "perceptual_hash": finding.perceptual_hash,
        })
        yield buffer.getvalue()

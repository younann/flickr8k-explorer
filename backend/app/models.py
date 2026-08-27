from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str
    dataset_ready: bool


class OverviewResponse(BaseModel):
    splits: list[dict]
    captions: dict


class SampleSummary(BaseModel):
    id: str
    split: str
    width: int
    height: int
    caption_preview: str
    image_url: str


class SamplePage(BaseModel):
    items: list[SampleSummary]
    page: int
    page_size: int
    total: int


class SampleDetail(BaseModel):
    id: str
    split: str
    width: int
    height: int
    aspect_ratio: float
    captions: list[str]
    image_url: str


class SampleDetailResponse(BaseModel):
    sample: SampleDetail
    neighbors: dict[str, str | None]

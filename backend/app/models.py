from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str
    dataset_ready: bool


class OverviewResponse(BaseModel):
    splits: list["SplitSummary"]
    captions: "CaptionStats"


class SplitSummary(BaseModel):
    name: str
    sample_count: int


class TermCount(BaseModel):
    term: str
    count: int


class CaptionStats(BaseModel):
    total: int
    mean_word_count: float
    top_terms: list[TermCount]


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
    neighbors: "Neighbors"


class Neighbors(BaseModel):
    previous_id: str | None
    next_id: str | None

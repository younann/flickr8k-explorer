from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str
    dataset_ready: bool
    analysis_ready: bool


class OverviewResponse(BaseModel):
    splits: list["SplitSummary"]
    captions: "CaptionStats"
    aspect_ratio_bins: list["AspectRatioBin"]


class SplitSummary(BaseModel):
    name: str
    sample_count: int


class AspectRatioBin(BaseModel):
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


class ScoreBucket(BaseModel):
    name: str
    sample_count: int


class RadarSummary(BaseModel):
    sample_count: int
    mean_disagreement_score: float
    mean_token_disagreement: float
    mean_vocabulary_diversity: float


class RadarOutlier(BaseModel):
    id: str
    split: str
    width: int
    height: int
    caption_preview: str
    image_url: str
    disagreement_score: int
    token_disagreement: float
    vocabulary_diversity: float


class RadarResponse(BaseModel):
    distribution: list[ScoreBucket]
    summary: RadarSummary
    outliers: list[RadarOutlier]
    split_composition: list[SplitSummary]


class SampleAnalysisResponse(BaseModel):
    sample_id: str
    disagreement_score: int
    token_disagreement: float
    vocabulary_diversity: float
    mean_caption_length: float
    caption_length_spread: float
    differing_tokens: list[str]


class SimilarSample(BaseModel):
    id: str
    split: str
    width: int
    height: int
    caption_preview: str
    image_url: str
    distance: int


class SimilarSamplesResponse(BaseModel):
    items: list[SimilarSample]


class CreateCollectionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class CreateFindingRequest(BaseModel):
    sample_id: str
    tags: list[str] = Field(default_factory=list, max_length=8)
    note: str = Field(default="", max_length=1000)


class CollectionResponse(BaseModel):
    id: int
    name: str
    created_at: str
    updated_at: str
    finding_count: int = 0


class CollectionListResponse(BaseModel):
    items: list[CollectionResponse]


class FindingResponse(BaseModel):
    id: int
    collection_id: int
    sample_id: str
    tags: list[str]
    note: str
    created_at: str
    updated_at: str


class FindingsResponse(BaseModel):
    items: list[FindingResponse]


class ExportFinding(BaseModel):
    id: int
    collection_id: int
    sample_id: str
    tags: list[str]
    note: str
    created_at: str
    updated_at: str
    split: str
    width: int
    height: int
    captions: list[str]
    disagreement_score: int | None
    token_disagreement: float | None
    vocabulary_diversity: float | None
    mean_caption_length: float | None
    caption_length_spread: float | None
    perceptual_hash: str | None


class CollectionExportResponse(BaseModel):
    collection: CollectionResponse
    findings: list[ExportFinding]

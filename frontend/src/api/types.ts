export type SplitSummary = {
  name: string;
  sample_count: number;
};

export type AspectRatioBin = {
  name: string;
  sample_count: number;
};

export type TermCount = {
  term: string;
  count: number;
};

export type OverviewResponse = {
  splits: SplitSummary[];
  captions: {
    total: number;
    mean_word_count: number;
    top_terms: TermCount[];
  };
  aspect_ratio_bins: AspectRatioBin[];
};

export type ScoreBucket = {
  name: string;
  sample_count: number;
};

export type RadarSummary = {
  sample_count: number;
  mean_disagreement_score: number;
  mean_token_disagreement: number;
  mean_vocabulary_diversity: number;
};

export type RadarOutlier = {
  id: string;
  split: string;
  width: number;
  height: number;
  caption_preview: string;
  image_url: string;
  disagreement_score: number;
  token_disagreement: number;
  vocabulary_diversity: number;
};

export type RadarResponse = {
  distribution: ScoreBucket[];
  summary: RadarSummary;
  outliers: RadarOutlier[];
};

export type Sample = {
  id: string;
  split: string;
  width: number;
  height: number;
  caption_preview: string;
  image_url: string;
};

export type SamplePage = {
  items: Sample[];
  total: number;
  page: number;
  page_size: number;
};

export type SampleDetail = Sample & {
  aspect_ratio: number;
  captions: string[];
};

export type SampleAnalysis = {
  sample_id: string;
  disagreement_score: number;
  token_disagreement: number;
  vocabulary_diversity: number;
  mean_caption_length: number;
  caption_length_spread: number;
  differing_tokens: string[];
};

export type SimilarSample = Sample & {
  distance: number;
};

export type SimilarSamplesResponse = { items: SimilarSample[] };

export type Collection = {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
  finding_count: number;
};

export type CollectionListResponse = { items: Collection[] };

export type Finding = {
  id: number;
  collection_id: number;
  sample_id: string;
  tags: string[];
  note: string;
  created_at: string;
  updated_at: string;
};

export type FindingsResponse = { items: Finding[] };

export type CreateFinding = {
  sample_id: string;
  tags: string[];
  note: string;
};

type SampleDetailResponse = {
  sample: SampleDetail;
};

export type { SampleDetailResponse };

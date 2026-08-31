import { Link, useLocation, useNavigate } from "react-router-dom";
import type { RadarOutlier, ScoreBucket } from "../../api/types";
import { Feedback } from "../../components/Feedback";
import { useRadar } from "./useRadar";

const RADAR_SPLITS = ["train", "validation", "test"] as const;
type RadarSplit = typeof RADAR_SPLITS[number];

type RadarFilters = {
  split: RadarSplit | "";
  minScore: number;
  maxScore: number;
  nearDuplicatesOnly: boolean;
};

function normalizeScore(value: string | number | null, fallback: number): number {
  if (value === null || value === "") return fallback;
  const score = Number(value);
  return Number.isInteger(score) && score >= 0 && score <= 100 ? score : fallback;
}

function normalizedRadarFilters(params: URLSearchParams): RadarFilters {
  const split = params.get("split");
  const minScore = normalizeScore(params.get("min_score"), 0);
  const maxScore = normalizeScore(params.get("max_score"), 100);
  return {
    split: RADAR_SPLITS.includes(split as RadarSplit) ? split as RadarSplit : "",
    minScore: Math.min(minScore, maxScore),
    maxScore: Math.max(minScore, maxScore),
    nearDuplicatesOnly: params.get("near_duplicates_only") === "true",
  };
}

function radarParams(filters: RadarFilters): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.split) params.set("split", filters.split);
  if (filters.minScore) params.set("min_score", String(filters.minScore));
  if (filters.maxScore !== 100) params.set("max_score", String(filters.maxScore));
  if (filters.nearDuplicatesOnly) params.set("near_duplicates_only", "true");
  return params;
}

function Distribution({ buckets, total }: { buckets: ScoreBucket[]; total: number }) {
  return <section className="radar-distribution" aria-labelledby="radar-distribution-title">
    <div><p className="eyebrow">Score distribution</p><h2 id="radar-distribution-title">Where caption variation falls</h2></div>
    <div className="radar-buckets">{buckets.map(bucket => <div className="radar-bucket" key={bucket.name}>
      <span>{bucket.name}</span><i style={{ width: `${total ? (bucket.sample_count / total) * 100 : 0}%` }} />
      <b>{bucket.sample_count.toLocaleString()}</b>
    </div>)}</div>
  </section>;
}

function OutlierCard({ outlier, search }: { outlier: RadarOutlier; search: string }) {
  return <Link className="radar-card" to={`/samples/${outlier.id}?${search}`}>
    <img loading="lazy" src={outlier.image_url} alt={outlier.caption_preview} />
    <span className="split-label">{outlier.split}</span>
    <div><p>{outlier.caption_preview}</p><small>Disagreement score <b>{outlier.disagreement_score}</b> / 100</small></div>
  </Link>;
}

export function RadarPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const filters = normalizedRadarFilters(new URLSearchParams(location.search));
  const { split, minScore, maxScore, nearDuplicatesOnly } = filters;
  const { data, error, isLoading } = useRadar(radarParams(filters));
  const galleryContext = new URLSearchParams();
  if (split) galleryContext.set("split", split);
  galleryContext.set("sort", "disagreement");

  function update(updates: Partial<RadarFilters>) {
    const next = new URLSearchParams(location.search);
    const nextMin = normalizeScore(updates.minScore ?? minScore, minScore);
    const nextMax = normalizeScore(updates.maxScore ?? maxScore, maxScore);
    const safeMin = Math.min(nextMin, nextMax);
    const safeMax = Math.max(nextMin, nextMax);
    const nextSplit = updates.split ?? split;
    if (nextSplit) next.set("split", nextSplit); else next.delete("split");
    if (safeMin) next.set("min_score", String(safeMin)); else next.delete("min_score");
    if (safeMax !== 100) next.set("max_score", String(safeMax)); else next.delete("max_score");
    if (updates.nearDuplicatesOnly ?? nearDuplicatesOnly) next.set("near_duplicates_only", "true"); else next.delete("near_duplicates_only");
    navigate(`/radar${next.toString() ? `?${next}` : ""}`);
  }

  return <main className="radar">
    <div className="page-title"><p className="eyebrow">Research Radar / local heuristics</p><h1>Research Radar</h1><p>Scan locally computed caption variation, then inspect the examples where captions differ most.</p></div>
    <p className="radar-note">Scores are local, transparent heuristics based on caption token variation and vocabulary diversity. They do not measure annotation quality or semantic similarity.</p>
    {isLoading && <p className="status">Loading local Radar…</p>}
    {error && <Feedback error={error} />}
    {data && <>
      <section className="radar-composition" aria-labelledby="radar-composition-title"><p className="eyebrow">Dataset composition</p><h2 id="radar-composition-title">Samples by split</h2><ul>{data.split_composition.map(item => <li key={item.name}><b>{item.sample_count.toLocaleString()}</b> {item.name}</li>)}</ul></section>
      <form className="radar-filters" onSubmit={event => event.preventDefault()}>
        <label>Split<select value={split} onChange={event => update({ split: event.target.value as RadarSplit | "" })}><option value="">All splits</option>{data.split_composition.map(item => <option key={item.name} value={item.name}>{item.name}</option>)}</select></label>
        <label>Minimum disagreement<input type="number" min="0" max="100" value={minScore} onChange={event => update({ minScore: Number(event.target.value) })} /></label>
        <label>Maximum disagreement<input type="number" min="0" max="100" value={maxScore} onChange={event => update({ maxScore: Number(event.target.value) })} /></label>
        <label className="radar-check"><input type="checkbox" checked={nearDuplicatesOnly} onChange={event => update({ nearDuplicatesOnly: event.target.checked })} />Near-duplicate signal only</label>
      </form>
      <section className="radar-metrics" aria-label="Radar summary">
        <p><b>{data.summary.mean_disagreement_score.toFixed(1)}</b><span>average disagreement score</span></p>
        <p><b>{data.summary.mean_token_disagreement.toFixed(2)}</b><span>average token variation</span></p>
        <p><b>{data.summary.mean_vocabulary_diversity.toFixed(2)}</b><span>average vocabulary diversity</span></p>
      </section>
      <Distribution buckets={data.distribution} total={data.summary.sample_count} />
      <section className="radar-outliers" aria-labelledby="radar-outliers-title">
        <div><p className="eyebrow">Ranked local outliers</p><h2 id="radar-outliers-title">Start with the strongest variation</h2><p>{data.summary.sample_count.toLocaleString()} locally analysed samples. Opening an example keeps disagreement sorting for the gallery return path.</p></div>
        <div className="radar-grid">{data.outliers.map(outlier => <OutlierCard key={outlier.id} outlier={outlier} search={galleryContext.toString()} />)}</div>
        {data.outliers.length === 0 && <p className="status">No locally analysed samples are available for this Radar view.</p>}
      </section>
    </>}
  </main>;
}

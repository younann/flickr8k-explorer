import { Link, useLocation } from "react-router-dom";
import type { RadarOutlier, ScoreBucket } from "../../api/types";
import { Feedback } from "../../components/Feedback";
import { useRadar } from "./useRadar";

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
  const params = new URLSearchParams(location.search);
  const { data, error, isLoading } = useRadar(params);
  const galleryContext = new URLSearchParams(location.search);
  galleryContext.set("sort", "disagreement");

  return <main className="radar">
    <div className="page-title"><p className="eyebrow">Research Radar / local heuristics</p><h1>Research Radar</h1><p>Scan locally computed caption variation, then inspect the examples where captions differ most.</p></div>
    <p className="radar-note">Scores are local, transparent heuristics based on caption token variation and length spread. They do not measure annotation quality or semantic similarity.</p>
    {isLoading && <p className="status">Loading local Radar…</p>}
    {error && <Feedback error={error} />}
    {data && <>
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

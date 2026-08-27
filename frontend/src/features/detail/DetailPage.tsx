import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { getSample } from "../../api/client";
import type { SampleDetail } from "../../api/types";
import { Feedback } from "../../components/Feedback";

export function DetailPage() {
  const { id = "" } = useParams();
  const location = useLocation();
  const [sample, setSample] = useState<SampleDetail | null>(null);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => { getSample(id).then(setSample).catch(setError); }, [id]);

  if (error) return <main><Feedback error={error} /></main>;
  if (!sample) return <main><p className="status">Loading sample…</p></main>;
  return <main className="detail"><Link className="back" to={`/gallery${location.search}`}>← Back to results</Link><div className="inspection"><div className="image-panel"><img src={sample.image_url} alt={sample.captions[0]}/><p>{sample.width} × {sample.height} px <span>·</span> {sample.aspect_ratio.toFixed(2)} ratio <span>·</span> {sample.split}</p></div><section className="captions"><p className="eyebrow">Five human captions</p><h1>Read the annotation set</h1><ol>{sample.captions.map((caption, index) => <li key={caption}><b>{String(index + 1).padStart(2, "0")}</b>{caption}</li>)}</ol></section></div></main>;
}

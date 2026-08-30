import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { getCollections, getSample, getSampleAnalysis, getSimilarSamples } from "../../api/client";
import type { Collection, SampleAnalysis, SampleDetail, SimilarSample } from "../../api/types";
import { Feedback } from "../../components/Feedback";
import { AnalysisPanel } from "./AnalysisPanel";
import { SaveFindingForm } from "./SaveFindingForm";

export function DetailPage() {
  const { id = "" } = useParams();
  const location = useLocation();
  const [sample, setSample] = useState<SampleDetail | null>(null);
  const [analysis, setAnalysis] = useState<SampleAnalysis | null>(null);
  const [neighbors, setNeighbors] = useState<SimilarSample[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([getSample(id), getSampleAnalysis(id), getSimilarSamples(id), getCollections()])
      .then(([nextSample, nextAnalysis, similar, collectionList]) => {
        if (!active) return;
        setSample(nextSample);
        setAnalysis(nextAnalysis);
        setNeighbors(similar.items);
        setCollections(collectionList.items);
      })
      .catch(error => { if (active) setError(error); });
    return () => { active = false; };
  }, [id]);

  if (error) return <main><Feedback error={error} /></main>;
  if (!sample || !analysis) return <main><p className="status">Loading sample evidence…</p></main>;
  return <main className="detail">
    <Link className="back" to={`/gallery${location.search}`}>← Back to results</Link>
    <div className="inspection">
      <div className="image-panel"><img src={sample.image_url} alt={sample.captions[0]} /><p>{sample.width} × {sample.height} px <span>·</span> {sample.aspect_ratio.toFixed(2)} ratio <span>·</span> {sample.split}</p></div>
      <section className="captions"><p className="eyebrow">Five human captions</p><h1>Read the annotation set</h1><p>Use the local evidence below to distinguish wording variation from image-level near-duplicates.</p></section>
    </div>
    <AnalysisPanel analysis={analysis} captions={sample.captions} neighbors={neighbors} />
    <SaveFindingForm sampleId={sample.id} collections={collections} onCollectionCreated={collection => setCollections(current => [...current, collection])} />
  </main>;
}

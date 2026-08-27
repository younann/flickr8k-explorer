import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getOverview } from "../../api/client";
import type { OverviewResponse, SplitSummary } from "../../api/types";
import { Feedback } from "../../components/Feedback";
import "./OverviewPage.css";

export function useOverview(): UseQueryResult<OverviewResponse> {
  return useQuery({ queryKey: ["overview"], queryFn: getOverview, staleTime: 60_000 });
}

function titleCase(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function splitClass(name: string) {
  return ["train", "validation", "test"].includes(name) ? name : "";
}

function SplitStrip({ splits, total }: { splits: SplitSummary[]; total: number }) {
  return <div className="split-strip" aria-label="Dataset splits">
    {splits.map(split => <span className={splitClass(split.name)} key={split.name} style={{ width: `${total ? (split.sample_count / total) * 100 : 0}%` }}>
      {titleCase(split.name)} {split.sample_count.toLocaleString()} samples
    </span>)}
  </div>;
}

export function OverviewPage() {
  const { data, error, isLoading } = useOverview();
  const totalSamples = data?.splits.reduce((sum, split) => sum + split.sample_count, 0) ?? 0;

  return <main className="overview">
    <p className="eyebrow">Computer vision dataset explorer / 08K</p>
    <h1>Flickr8k Explorer</h1>
    <p className="lede">A local contact sheet for studying image-caption pairs: search language, scan the collection, and read every annotation in context.</p>
    {isLoading && <p className="status">Loading local index…</p>}
    {error && <Feedback error={error} />}
    {data && <>
      <SplitStrip splits={data.splits} total={totalSamples} />
      <section className="overview-metrics" aria-label="Dataset metrics">
        <p><b>{data.captions.total.toLocaleString()} captions</b><span>{data.captions.mean_word_count.toFixed(1)} words on average</span></p>
        <div><h2>Frequent terms</h2><ul>{data.captions.top_terms.map(term => <li key={term.term}><Link to={`/gallery?q=${encodeURIComponent(term.term)}`}>{term.term} {term.count.toLocaleString()}</Link></li>)}</ul></div>
      </section>
      <section className="aspect-ratios" aria-label="Aspect ratio distribution">
        <h2>Image shapes</h2>
        {data.aspect_ratio_bins.map(bin => <div className="aspect-ratio" key={bin.name}><span>{titleCase(bin.name)} {bin.sample_count.toLocaleString()} samples</span><i style={{ width: `${totalSamples ? (bin.sample_count / totalSamples) * 100 : 0}%` }} /></div>)}
      </section>
    </>}
    <section className="workflow"><article><b>01</b><h2>Describe the corpus</h2><p>Start with split-aware statistics and caption distributions after import.</p></article><article><b>02</b><h2>Find a pattern</h2><p>Use local full-text search and image dimensions to isolate a cohort.</p></article><article><b>03</b><h2>Inspect agreement</h2><p>Read all five captions alongside the source image.</p></article></section>
    <Link className="action" to="/gallery">Browse samples <span>→</span></Link>
  </main>;
}

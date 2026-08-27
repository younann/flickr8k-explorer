import { useEffect, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Link, Route, Routes, useLocation, useNavigate, useParams } from "react-router-dom";
import { getSample, getSamples, type Sample, type SampleDetail } from "../api";
import "../styles.css";

function Header() {
  return <header className="masthead"><Link className="wordmark" to="/">FLICKR8K <span>LOCAL</span></Link><nav aria-label="Primary"><Link to="/">Overview</Link><Link to="/gallery">Browse samples</Link></nav></header>;
}

function Overview() {
  return <main className="overview"><p className="eyebrow">Computer vision dataset explorer / 08K</p><h1>Flickr8k Explorer</h1><p className="lede">A local contact sheet for studying image-caption pairs: search language, scan the collection, and read every annotation in context.</p><div className="split-strip" aria-label="Dataset splits"><span className="train">TRAIN</span><span className="validation">VALIDATION</span><span className="test">TEST</span></div><section className="workflow"><article><b>01</b><h2>Describe the corpus</h2><p>Start with split-aware statistics and caption distributions after import.</p></article><article><b>02</b><h2>Find a pattern</h2><p>Use local full-text search and image dimensions to isolate a cohort.</p></article><article><b>03</b><h2>Inspect agreement</h2><p>Read all five captions alongside the source image.</p></article></section><Link className="action" to="/gallery">Browse samples <span>→</span></Link></main>;
}

function Gallery() {
  const location = useLocation(); const navigate = useNavigate();
  const query = new URLSearchParams(location.search); const q = query.get("q") ?? ""; const split = query.get("split") ?? "";
  const [input, setInput] = useState(q);
  useEffect(() => { setInput(q); }, [q]);
  useEffect(() => { const timer = window.setTimeout(() => { if (input !== q) { const next = new URLSearchParams(location.search); input ? next.set("q", input) : next.delete("q"); navigate(`/gallery?${next}`, { replace: true }); } }, 300); return () => window.clearTimeout(timer); }, [input, q, location.search, navigate]);
  const { data, error, isLoading, isFetching } = useQuery({ queryKey: ["samples", location.search], queryFn: () => getSamples(new URLSearchParams(location.search)), staleTime: 60_000, placeholderData: keepPreviousData });
  function update(key: string, value: string) { const next = new URLSearchParams(location.search); value ? next.set(key, value) : next.delete(key); navigate(`/gallery?${next}`); }
  return <main><div className="page-title"><p className="eyebrow">Browse / local index</p><h1>Contact sheet</h1><p>Search any of the five human captions. Results stay on this machine.</p></div><div className="filters"><label>Caption search<input name="q" value={input} onChange={event => setInput(event.target.value)} placeholder="dog, snow, bicycle…" /></label><label>Split<select value={split} onChange={e => update("split", e.target.value)}><option value="">All splits</option><option value="train">Train</option><option value="validation">Validation</option><option value="test">Test</option></select></label><button type="button" onClick={() => setInput("")}>Clear</button></div>{error && <p className="notice" role="alert">{error.message}</p>}{isLoading && <p className="status">Loading local index…</p>}{data && <><p className="result-count">{data.total.toLocaleString()} samples {isFetching && "· updating"}</p><div className="sample-grid">{data.items.map(sample => <Link className="sample-card" key={sample.id} to={`/samples/${sample.id}${location.search}`}><img loading="lazy" src={sample.image_url} alt={sample.caption_preview}/><span className="split-label">{sample.split}</span><p>{sample.caption_preview}</p><small>{sample.width} × {sample.height}</small></Link>)}</div>{data.items.length === 0 && <p className="status">No local samples match this query. Try fewer words or clear the split.</p>}</>}</main>;
}

function Detail() {
  const { id = "" } = useParams(); const location = useLocation(); const [sample, setSample] = useState<SampleDetail | null>(null); const [error, setError] = useState("");
  useEffect(() => { getSample(id).then(setSample).catch(e => setError(e.message)); }, [id]);
  if (error) return <main><p className="notice" role="alert">{error}</p></main>;
  if (!sample) return <main><p className="status">Loading sample…</p></main>;
  return <main className="detail"><Link className="back" to={`/gallery${location.search}`}>← Back to results</Link><div className="inspection"><div className="image-panel"><img src={sample.image_url} alt={sample.captions[0]}/><p>{sample.width} × {sample.height} px <span>·</span> {sample.aspect_ratio.toFixed(2)} ratio <span>·</span> {sample.split}</p></div><section className="captions"><p className="eyebrow">Five human captions</p><h1>Read the annotation set</h1><ol>{sample.captions.map((caption, index) => <li key={caption}><b>{String(index + 1).padStart(2, "0")}</b>{caption}</li>)}</ol></section></div></main>;
}

export function App() { return <><Header/><Routes><Route path="/" element={<Overview/>}/><Route path="/gallery" element={<Gallery/>}/><Route path="/samples/:id" element={<Detail/>}/></Routes></>; }

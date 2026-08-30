import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Feedback } from "../../components/Feedback";
import { parseGalleryQuery, withGalleryQuery } from "./query";
import { useSamples } from "./useSamples";

export function GalleryPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const galleryQuery = parseGalleryQuery(location.search);
  const [input, setInput] = useState(galleryQuery.q);
  const isDebouncing = input !== galleryQuery.q;
  const { data, error, isLoading, isFetching } = useSamples(new URLSearchParams(location.search));

  useEffect(() => { setInput(galleryQuery.q); }, [galleryQuery.q]);
  useEffect(() => {
    if (!isDebouncing) return;
    const timer = window.setTimeout(() => {
      navigate(`/gallery${withGalleryQuery(location.search, { q: input, page: 1 })}`, { replace: true });
    }, 300);
    return () => window.clearTimeout(timer);
  }, [input, isDebouncing, location.search, navigate]);

  function update(updates: Parameters<typeof withGalleryQuery>[1]) {
    navigate(`/gallery${withGalleryQuery(location.search, updates)}`);
  }
  function clearFilters() {
    setInput("");
    update({ q: "", split: "", page: 1 });
  }

  return <main><div className="page-title"><p className="eyebrow">Browse / local index</p><h1>Contact sheet</h1><p>Search any of the five human captions. Results stay on this machine.</p></div><div className="filters"><label>Caption search<input name="q" value={input} onChange={event => setInput(event.target.value)} placeholder="dog, snow, bicycle…" /></label><label>Split<select value={galleryQuery.split} onChange={e => update({ split: e.target.value, page: 1 })}><option value="">All splits</option><option value="train">Train</option><option value="validation">Validation</option><option value="test">Test</option></select></label><label>Sort samples<select value={galleryQuery.sort} onChange={e => update({ sort: e.target.value as typeof galleryQuery.sort, page: 1 })}><option value="default">Default order</option><option value="disagreement">Highest disagreement</option></select></label><button type="button" onClick={clearFilters}>Clear</button></div>{isDebouncing && <p className="status" aria-live="polite">Waiting to update search…</p>}{error && <Feedback error={error} />}{isLoading && <p className="status">Loading local index…</p>}{data && <><p className="result-count">{data.total.toLocaleString()} samples {isFetching && "· updating"}</p><div className="sample-grid">{data.items.map(sample => <Link className="sample-card" key={sample.id} to={`/samples/${sample.id}${location.search}`}><img loading="lazy" src={sample.image_url} alt={sample.caption_preview}/><span className="split-label">{sample.split}</span><p>{sample.caption_preview}</p><small>{sample.width} × {sample.height}</small></Link>)}</div>{data.items.length === 0 && <p className="status">No local samples match this query. Try fewer words or clear the split.</p>}<nav className="pagination" aria-label="Pagination"><button type="button" onClick={() => update({ page: data.page - 1 })} disabled={data.page <= 1}>Previous page</button><span>Page {data.page}</span><button type="button" onClick={() => update({ page: data.page + 1 })} disabled={data.page * data.page_size >= data.total}>Next page</button></nav></>}</main>;
}

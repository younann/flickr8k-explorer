import { Link } from "react-router-dom";
import type { SampleAnalysis, SimilarSample } from "../../api/types";

type AnalysisPanelProps = { analysis: SampleAnalysis; captions: string[]; neighbors: SimilarSample[] };

function strictSubsetTokens(captions: string[], candidates: string[]) {
  const counts = new Map<string, number>();
  for (const caption of captions) {
    for (const token of new Set(caption.toLowerCase().match(/[a-z]+/g) ?? [])) {
      counts.set(token, (counts.get(token) ?? 0) + 1);
    }
  }
  return new Set(candidates.filter(token => {
    const count = counts.get(token.toLowerCase()) ?? 0;
    return count > 0 && count < captions.length;
  }).map(token => token.toLowerCase()));
}

function HighlightedCaption({ caption, tokens }: { caption: string; tokens: Set<string> }) {
  return <>{caption.split(/([a-z]+)/gi).map((part, index) =>
    tokens.has(part.toLowerCase()) ? <mark key={`${part}-${index}`}>{part}</mark> : part,
  )}</>;
}

export function AnalysisPanel({ analysis, captions, neighbors }: AnalysisPanelProps) {
  const tokens = strictSubsetTokens(captions, analysis.differing_tokens);
  return <section className="analysis-panel" aria-labelledby="evidence-title">
    <div className="analysis-heading">
      <p className="eyebrow">Evidence triage / local signals</p>
      <h2 id="evidence-title">Read why these captions diverge</h2>
      <p>The score combines observable wording variation and caption-length spread. It is a local triage aid, not a judgement of caption quality or meaning.</p>
    </div>
    <dl className="evidence-metrics">
      <div><dt>Disagreement score</dt><dd>{analysis.disagreement_score}<small>/ 100</small></dd><p>Combined local signal used to rank caption variation.</p></div>
      <div><dt>Token disagreement</dt><dd>{analysis.token_disagreement.toFixed(2)}</dd><p>How often captions use different word tokens.</p></div>
      <div><dt>Vocabulary diversity</dt><dd>{analysis.vocabulary_diversity.toFixed(2)}</dd><p>How varied the caption vocabulary is across the set.</p></div>
      <div><dt>Caption-length spread</dt><dd>{analysis.caption_length_spread.toFixed(1)}</dd><p>Difference in caption word counts; mean {analysis.mean_caption_length.toFixed(1)} words.</p></div>
    </dl>
    <p className="token-key"><mark>Highlighted words</mark> appear in a strict subset of these captions, so the original wording remains readable in context.</p>
    <ol className="evidence-captions" aria-label="Captions with differing tokens highlighted">
      {captions.map((caption, index) => <li key={`${index}-${caption}`}><b>{String(index + 1).padStart(2, "0")}</b><HighlightedCaption caption={caption} tokens={tokens} /></li>)}
    </ol>
    <section className="near-duplicates" aria-labelledby="near-duplicates-title">
      <p className="eyebrow">Image hash neighbours</p>
      <h3 id="near-duplicates-title">Visually close candidates</h3>
      <p>These are near-duplicate candidates ranked by local perceptual-hash distance, not semantic similarity.</p>
      <div className="near-duplicate-grid">{neighbors.map(neighbor => <Link key={neighbor.id} className="near-duplicate-card" to={`/samples/${neighbor.id}`}>
        <img src={neighbor.image_url} alt={neighbor.caption_preview} />
        <span>Visually close · hash distance {neighbor.distance}</span>
      </Link>)}</div>
      {neighbors.length === 0 && <p className="status">No visually close near-duplicate candidates are available.</p>}
    </section>
  </section>;
}

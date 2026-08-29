# Research Radar design

## Goal

Evolve Flickr8k Explorer from a local caption browser into a local-first
research instrument for finding, explaining, saving, and exporting examples
of visual-language ambiguity. The product remains usable without hosted
services, accounts, or model downloads.

## User workflow

1. A researcher opens **Research Radar** and sees local dataset composition,
   caption-disagreement distribution, and ranked outliers.
2. They filter by split, disagreement range, or near-duplicate signal, then
   select a sample.
3. The sample inspection page explains the score, shows all five captions,
   highlights their differing terms, and lists visually close samples.
4. The researcher saves the sample to a named local collection with optional
   tags and a note.
5. The collection can be exported as CSV or JSON for reproducible analysis.

## Scope

### Caption disagreement

Import computes a transparent analysis row for each sample. It includes:

- the mean caption length and length spread;
- vocabulary diversity across the five captions;
- average pairwise token-set disagreement; and
- a normalized 0–100 disagreement score combining the latter two signals.

The UI shows the supporting values alongside the score. It must not imply
that the score is a learned model or an objective measure of annotation
quality.

### Lightweight visual similarity

Import stores a 64-bit perceptual image hash for every sample. The API ranks
other hashes by Hamming distance and returns the closest candidates. The UI
labels these as “visually close / near-duplicate candidates”, not semantic
similarity. This avoids an ML runtime and any weight download while still
supporting dataset-audit use cases.

### Local findings

Collections and findings live in the same local SQLite database. A collection
has a name and timestamps. A finding references one collection and one sample
and has optional tags and a text note. Deleting a collection deletes its
findings; deleting a finding leaves its sample untouched.

## Data model

Migration files add the following tables:

- `sample_analysis(sample_id PRIMARY KEY, disagreement_score,
  token_disagreement, vocabulary_diversity, mean_caption_length,
  caption_length_spread, perceptual_hash)`;
- `collections(id PRIMARY KEY, name UNIQUE, created_at, updated_at)`; and
- `findings(id PRIMARY KEY, collection_id REFERENCES collections,
  sample_id REFERENCES samples, tags, note, created_at, updated_at)`.

Indexes cover the analysis score, collection membership, and finding sample
lookup. Import recomputes analysis rows without modifying user-created
collections or findings.

## API

The existing read-only dataset router grows into focused route groups with
Pydantic request and response models.

- `GET /api/radar` returns distribution buckets, summary metrics, and ranked
  outlier previews; accepts split and ranking controls.
- `GET /api/samples` accepts analysis-aware filtering and sorting while
  preserving current caption search and split behavior.
- `GET /api/samples/{sample_id}/analysis` returns score explanation and
  differing caption tokens.
- `GET /api/samples/{sample_id}/similar` returns a bounded, deterministic
  list of perceptual-hash neighbours.
- `GET /api/collections`, `POST /api/collections`, and
  `DELETE /api/collections/{id}` manage collections.
- `GET /api/collections/{id}/findings`, `POST /api/collections/{id}/findings`,
  and `DELETE /api/findings/{id}` manage saved evidence.
- `GET /api/collections/{id}/export?format=csv|json` downloads an export that
  includes collection metadata, finding notes/tags, sample dimensions, all
  captions, and analysis fields.

All invalid IDs return the existing typed 404 error shape. Invalid write
payloads use FastAPI's validation response. Exports reject unsupported formats
with a typed 422 response.

## Frontend

`OverviewPage` becomes the Research Radar while retaining the concise local
dataset summary. It adds disagreement distribution, high-disagreement examples,
and a direct path to filtered gallery results.

`GalleryPage` gains sort and filter controls for analysis signals. It preserves
all filter state in the URL.

`DetailPage` becomes evidence triage: an analysis explanation, highlighted
caption variation, visually-close candidates, and a compact save-to-collection
form. A Collections page provides finding review and CSV/JSON exports.

Each feature owns its route component, query hook, typed client calls, and
tests. Shared UI remains in the existing component area.

## Import and migration behavior

The importer analyzes newly accepted samples and can rebuild analysis records
for an already imported database. The process is idempotent. It reports any
corrupt/unreadable image with a sample identifier and leaves existing committed
data intact. Migrations remain forward-only and run during startup.

## Verification

- Unit tests cover score inputs, token highlighting, perceptual-hash distance,
  export serializers, migrations, and repository filters.
- API tests cover valid flows plus empty, missing, invalid, and unavailable
  dataset states.
- Frontend tests cover sorting, explanations, saving/removing findings, and
  URL preservation.
- Browser tests cover the end-to-end Radar → sample → finding → export flow at
  desktop and mobile widths.
- Accessibility tests cover new controls, dialog/form labels, keyboard use,
  and status/error messaging.

## Non-goals

This release does not add cloud sync, user accounts, shared collections,
embedding models, semantic search, training/evaluation pipelines, or claims
about semantic similarity. Those can be introduced later behind the persisted
analysis and collection boundaries.

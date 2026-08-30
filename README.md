# Flickr8k Explorer

A local-first visual inspection tool for the Flickr8k image-caption dataset. It is designed for the research loop of finding examples, checking caption coverage, and assessing visual-language ambiguity without a hosted database or search service.

## What it does

- Imports Flickr8k Parquet shards into local SQLite and writes images to the local `data/images/` cache.
- Searches all five human captions with SQLite FTS5 and filters by dataset split.
- Shows a responsive contact sheet with URL-shareable caption, split, sort, page, and page-size filters, plus a focused image inspector with all five captions, original dimensions, and aspect ratio.
- Displays an overview of local split totals, caption length and frequent terms, and portrait/square/landscape image distribution.
- Includes Research Radar: a local ranking of caption disagreement that helps researchers locate annotation sets worth inspecting, then return to a disagreement-sorted gallery.
- Lets researchers save evidence-backed annotations to local collections and export those collections as CSV or JSON.
- Runs entirely on one machine after the initial dataset import. The browser application only calls the local FastAPI server; it makes no Hugging Face, cloud database, hosted-search, or model-inference requests at runtime.

## Requirements

- Python 3.11+ and [uv](https://docs.astral.sh/uv/)
- Node.js 22+ and npm
- Approximately 2.5 GB free disk space for the source shards, extracted images, SQLite index, and development dependencies

## Run from a fresh clone

```bash
git clone <your-repository-url> flickr8k-explorer
cd flickr8k-explorer
cd backend && uv sync && cd ..
cd frontend && npm install && cd ..
cd backend && uv run python -m scripts.import_dataset --download && cd ..
bash ./scripts/dev.sh
```

Open `http://localhost:5173`. The initial import is the only operation that contacts Hugging Face. It downloads the manifest-pinned dataset shards once into `data/raw/`; later application runs use only local files. Set `FLICKR8K_DATA_DIR=/absolute/path` before import and backend startup to place all dataset files elsewhere.

`scripts/dev.sh` starts the local FastAPI server and Vite development server together. Stop it with `Ctrl-C`; it shuts down both child processes. A fresh checkout needs the import above before the API can serve dataset endpoints.

## Dataset manifest

`backend/dataset_manifest.json` is the single checked-in source for the Hugging Face repository, immutable revision, and Parquet files assigned to each split. The importer downloads only those declared files and passes the manifest revision to Hugging Face; the API and browser never contact Hugging Face after an import.

To update the dataset, change the manifest in one review: choose an immutable repository revision, list every required Parquet filename under its split, and keep each filename unique within that split. Validate the change before importing it into a new local data directory:

```bash
cd backend && uv run pytest tests/test_manifest.py -v
FLICKR8K_DATA_DIR=/absolute/path/to/new-data uv run python -m scripts.import_dataset --download
```

Use `uv run python -m scripts.import_dataset --help` to inspect the command without downloading any data.

## SQLite migrations

The local database schema is managed by numbered SQL files in `backend/app/migrations/`. On startup, the backend records successfully applied versions in `schema_migrations` and applies every new migration once. Migrations are forward-only and idempotent, so an existing local import remains usable when the application is updated.

For a data-model change, add the next numbered SQL migration, keep it safe for an existing database, and verify it before release:

```bash
cd backend && uv run pytest tests/test_migrations.py -v
```

To run in two terminals instead:

```bash
cd backend && uv run uvicorn app.main:app --reload
cd frontend && npm run dev
```

## Architecture

```text
Hugging Face (one-time download) -> data/raw/*.parquet -> importer -> data/flickr8k.sqlite + data/images/*
                                                                    |
React/Vite SPA <--- local HTTP JSON/image bytes <--- FastAPI <-------+
```

`backend/app/importer.py` owns Parquet ingestion; `repository.py` owns parameterized SQLite reads; `routes.py` owns HTTP behavior. The React client is intentionally a small feature-oriented UI that consumes those local endpoints.

## Research Radar and local findings

Research Radar ranks examples by transparent, locally computed caption-token variation and caption-length spread. Choose **Highest disagreement** in the contact-sheet sort control to make the same analysis order shareable in the URL. The score is a triage signal, not a measure of annotation quality, image semantics, or ground truth.

The detail view also lists visually close candidates using perceptual-hash distance. Perceptual hashes are useful for finding near-duplicate images, but they do not understand image content: a small hash distance is not semantic similarity, and a large distance does not prove two images are unrelated. Review the image and its five captions before drawing a conclusion.

Save a finding with optional tags and a note to a local collection. The collection view exports the saved evidence as CSV or JSON; exports stay on the local API and contain the collection metadata and finding fields needed for a later analysis step.

## 90-second demo flow

1. Open **Research Radar** and choose one of the high-disagreement outliers.
2. Inspect its five captions, local score breakdown, and visually close candidates.
3. Choose a local collection, add a concise ambiguity note or tags, then select **Save finding**.
4. Open **Collections** from the saved confirmation and select **Export CSV** (or JSON) to carry the finding into the next analysis step.

## Local quality gates

```bash
cd backend && uv run pytest -v
cd frontend && npm test -- --run
cd frontend && npm run build
```

Browser checks use a generated 31-sample fixture dataset and never download Flickr8k. Install the Playwright browser once, then run the local E2E and accessibility gates:

```bash
cd frontend
npx playwright install chromium
npm run test:e2e
npm run test:a11y
```

Each command creates `frontend/e2e/fixtures/data/` through the existing importer, starts a fixture-only FastAPI server and Vite, and runs at desktop and 375px viewport widths.

For a release-style check from a clean checkout, run all five commands in order after installing dependencies and Chromium:

```bash
cd backend && uv run pytest -v
cd frontend && npm test -- --run
cd frontend && npm run build
cd frontend && npm run test:e2e
cd frontend && npm run test:a11y
```

## Scope and trade-offs

The first version favors transparent, dependable retrieval: SQLite FTS5 searches the human captions locally and produces explainable results. It intentionally does not include embeddings, semantic/image similarity, model inference, accounts, or cloud infrastructure. Local annotations and collection exports are included; richer capabilities can be added behind the existing sample IDs and repository boundary without changing the local data contract.

## Troubleshooting

- **API responds `409 Dataset is not imported`:** run the import command with `--download` and restart the API.
- **Port is busy:** run Uvicorn with `--port 8001`, then update the `/api` proxy target in `frontend/vite.config.ts`.
- **Import has no space:** choose another local cache location with `FLICKR8K_DATA_DIR` before importing.

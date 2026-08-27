# Flickr8k Explorer

A local-first visual inspection tool for the Flickr8k image-caption dataset. It is designed for the research loop of finding examples, checking caption coverage, and assessing visual-language ambiguity without a hosted database or search service.

## What it does

- Imports Flickr8k Parquet shards into local SQLite and writes images to the local `data/images/` cache.
- Searches all five human captions with SQLite FTS5 and filters by dataset split.
- Shows a responsive contact sheet and a focused image inspector with all five captions, original dimensions, and aspect ratio.
- Runs entirely on one machine after the initial dataset import. The browser application only calls the local FastAPI server.

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

Open `http://localhost:5173`. The initial import is the only operation that contacts Hugging Face. It downloads the current dataset shards once into `data/raw/`; later runs use only local files. Set `FLICKR8K_DATA_DIR=/absolute/path` before import and backend startup to place all dataset files elsewhere.

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

## Test and build

```bash
cd backend && uv run pytest -v
cd frontend && npm test -- --run && npm run build
```

## Scope and trade-offs

The first version favors transparent, dependable retrieval: SQLite FTS5 searches the human captions locally and produces explainable results. It does not include embeddings, semantic/image similarity, model inference, accounts, annotations, or cloud infrastructure. Those capabilities can be added behind the existing sample IDs and repository boundary without changing the local data contract.

## Troubleshooting

- **API responds `409 Dataset is not imported`:** run the import command with `--download` and restart the API.
- **Port is busy:** run Uvicorn with `--port 8001`, then update the `/api` proxy target in `frontend/vite.config.ts`.
- **Import has no space:** choose another local cache location with `FLICKR8K_DATA_DIR` before importing.

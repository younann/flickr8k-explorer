# Flickr8k Dataset Visualization Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a locally runnable React and Python application that lets computer-vision researchers explore Flickr8k, search its captions, browse samples, and inspect individual image-caption examples.

**Architecture:** A FastAPI service imports the downloaded Hugging Face Parquet shards into a local SQLite index and exposes a small, paginated JSON API plus image-byte endpoints. A React/Vite TypeScript SPA consumes that API: an overview reports dataset health and distributions, a gallery supports filters and full-text caption search, and a detail route presents the image with all five captions and inspection metadata. The source Parquet files and SQLite database remain local under a gitignored `data/` directory; no service is needed after the initial download/import.

**Tech Stack:** Python 3.11, FastAPI, Uvicorn, SQLite FTS5, PyArrow, Pillow, Hugging Face Hub; React 18, TypeScript, Vite, React Router, TanStack Query, Recharts, Vitest, pytest.

**Spec:** `/Users/younan.nwesre/Downloads/HomeAssignment.pdf`

## Global Constraints

- Use a React frontend and a Python backend.
- The entire solution must run locally on a single developer machine.
- Do not use cloud services, managed databases, external vector/search databases, hosted search, or paid APIs.
- Store and process all application data locally; SQLite is the only database and the downloaded dataset is cached on disk.
- Use standard open-source libraries and keep the feature set deliberately small and useful.
- The current `jxie/flickr8k` dataset is Parquet, has train/validation/test splits, stores image data plus five caption columns, and totals about 1.1 GB; download it once with the Hugging Face Hub and reuse local files.
- A reviewer must be able to clone the repository, follow `README.md`, import the data, and run the whole system locally without undocumented manual steps.
- Prefer thoughtful, well-integrated capabilities over a larger feature count; every included feature must support browsing, inspecting, or understanding the dataset.

---

## Product decisions

### Included

- An import command that downloads the four Parquet shards to `data/raw/`, validates their expected columns, extracts image metadata, and creates a reproducible SQLite index.
- Dataset overview: split counts, image dimensions/aspect-ratio distribution, caption-length distribution, and most frequent normalized caption terms.
- Gallery: server-side paginated image cards, split filter, free-text caption search, minimum/maximum image width/height, and sorting by source order or caption length.
- Detail view: full-resolution image, all captions, split, original dimensions, aspect ratio, average caption length, and adjacent previous/next samples within the active gallery query.
- Clear empty, loading, and error states; keyboard-accessible navigation; responsive desktop-first layout.

### Explicitly deferred

- CLIP embeddings, image-to-image similarity, semantic search, automatic labeling, annotations, accounts, saved collections, and background job infrastructure. These are useful extensions, but they increase download size, startup time, and implementation risk without being required by the assignment.

## Assignment coverage matrix

| Assignment need / evaluation criterion | Concrete plan response | Evidence before delivery |
| --- | --- | --- |
| Local single-machine runtime | React runs locally through Vite; FastAPI runs locally through Uvicorn; SQLite, images, raw Parquet, and statistics live under repository-local `data/`. The running application makes no remote calls. | Start both processes with network access disabled after import; browse overview, gallery, detail, and image endpoints successfully. |
| Clone, setup, and run locally | `README.md`, pinned Python/Node dependencies, an idempotent importer, a data-path environment variable, and `scripts/dev.sh` give one supported happy path plus portable two-terminal commands. | Perform a clean-directory rehearsal using only commands copied from `README.md`; retain the exact command/output transcript in delivery notes. |
| Reasonable, thoughtful scope | The product concentrates on the three core research workflows: describe dataset composition, retrieve samples by concrete text/metadata predicates, and inspect image/caption agreement. It intentionally excludes embeddings, accounts, annotations, and operational infrastructure. | README has a “Scope and trade-offs” section that explains the deferments and why SQLite FTS is the appropriate first retrieval layer. |
| Useful to CV researchers | Overview reveals split balance and image/caption distributions; gallery enables finding visual-language examples; detail exposes all five annotations and source metadata needed to assess ambiguity or coverage. | Fixture integration test plus manual scenarios: find all captions mentioning a term, constrain by split/dimensions, and inspect the five captions of a selected sample. |
| UX and usability | URL-shareable filters, server pagination, responsive card grid, useful loading/empty/error states, accessible labels/focus styles, keyboard image dialog controls, and query-preserving back/next navigation. | Component tests for navigation and states; manual desktop and 375px viewport checklist; browser accessibility audit with zero serious violations. |
| Frontend and backend design | Frontend features own their views and API hooks; the backend separates configuration, import, persistence/query, schemas, routes, and media streaming. The API is typed, validated, and pagination occurs server-side. | API tests cover validation and query semantics; a short architecture section in README describes module boundaries and data flow. |
| Generic, modular, expandable code quality | Stable sample IDs, normalized image/caption tables, a repository boundary around SQL, Pydantic/TypeScript contracts, migration/schema version checks, and fixture-based tests make later search/embedding modules additive. | Full backend/frontend test suites and production frontend build pass; README names extension seams without claiming unbuilt capabilities. |

## Planned repository structure

| Path | Responsibility |
| --- | --- |
| `backend/app/main.py` | FastAPI application, CORS for the Vite dev server, router registration, static health endpoint. |
| `backend/app/config.py` | Environment-driven paths and limits; resolves the repository-local `data/` directory. |
| `backend/app/db.py` | SQLite connection lifecycle, read-only query helpers, and schema-version check. |
| `backend/app/models.py` | Pydantic request/query/response models shared by API routes. |
| `backend/app/repository.py` | Parameterized SQL for overview, gallery, samples, captions, and FTS search. |
| `backend/app/routes/dataset.py` | `GET /api/overview`, `GET /api/samples`, and `GET /api/samples/{id}`. |
| `backend/app/routes/media.py` | `GET /api/samples/{id}/image`, streaming locally stored image bytes with a safe media type. |
| `backend/scripts/import_dataset.py` | Idempotent CLI: download, validate, import, compute aggregate tables, and report progress. |
| `backend/schema.sql` | SQLite tables, indexes, FTS5 virtual table/triggers, and schema version. |
| `backend/tests/` | API, repository, and importer tests built around a tiny generated Parquet fixture. |
| `frontend/src/api/client.ts` | Typed API request functions and query-string serializer. |
| `frontend/src/api/types.ts` | TypeScript representations of API payloads. |
| `frontend/src/app/App.tsx` | Routes, global shell, and error boundary. |
| `frontend/src/features/overview/` | Metric cards and two distribution charts. |
| `frontend/src/features/gallery/` | Filter state, query sync, result grid, pagination, and sample cards. |
| `frontend/src/features/detail/` | Image inspector, captions panel, metadata, and query-preserving navigation. |
| `frontend/src/components/` | Reusable accessible controls and feedback states. |
| `frontend/src/test/` | MSW-backed component and navigation tests. |
| `README.md` | Prerequisites, import/start commands, screenshots/GIF if available, data footprint, and architecture notes. |
| `.gitignore` | Excludes raw shards, SQLite database, downloaded images, Python/Node environments, and build output. |

## API contract

All responses are JSON except the image endpoint. `SampleSummary.id` is a stable SHA-256 digest of the original image bytes; it is generated during import, never derived from a row offset.

```text
GET /api/health
  -> { "status": "ok", "dataset_ready": boolean }

GET /api/overview
  -> { splits: [{name, sample_count}], image_dimensions: {width_bins, height_bins, aspect_ratio_bins},
       captions: {length_bins, top_terms: [{term, count}]} }

GET /api/samples?split=train&q=dog&min_width=300&max_width=1000&sort=source&page=1&page_size=30
  -> { items: SampleSummary[], page, page_size, total, query: AppliedQuery }

GET /api/samples/{id}
  -> { sample: SampleDetail, neighbors: {previous_id: string | null, next_id: string | null} }

GET /api/samples/{id}/image
  -> image/jpeg | image/png
```

`SampleSummary` contains `id`, `split`, `width`, `height`, `caption_preview`, and `image_url`. `SampleDetail` adds `captions: string[5]`, `caption_length_mean`, and the source shard/row for reproducibility. The detail endpoint receives the active gallery parameters too, so its neighbor IDs honor the current filter and sort.

## Implementation tasks

### Task 1: Scaffold the local application and document the developer contract

**Files:**
- Create: `backend/pyproject.toml`, `backend/app/__init__.py`, `backend/app/main.py`, `frontend/package.json`, `frontend/vite.config.ts`, `frontend/src/main.tsx`, `frontend/src/app/App.tsx`, `.gitignore`, `README.md`
- Test: `backend/tests/test_health.py`, `frontend/src/app/App.test.tsx`

**Interfaces:**
- Produces `GET /api/health` and a React shell rendering `Flickr8k Explorer`.

- [ ] Write a failing pytest that creates the app with a temporary empty data directory and expects `GET /api/health` to return HTTP 200 with `{"status":"ok","dataset_ready":false}`.
- [ ] Run `cd backend && uv run pytest tests/test_health.py -v`; confirm the route is absent.
- [ ] Create the FastAPI app with a `/api/health` route, CORS allowing `http://localhost:5173`, and configuration read from `FLICKR8K_DATA_DIR`.
- [ ] Write a failing Vitest/Testing Library test that renders `App` and expects one level-one heading, `Flickr8k Explorer`.
- [ ] Create the Vite React/TypeScript shell and route placeholder; run `cd frontend && npm test -- --run` and `npm run build`.
- [ ] Write the initial README with exact prerequisites, `uv sync`, `npm install`, and the later import/start commands; add `data/`, `.venv/`, `node_modules/`, and build artifacts to `.gitignore`.

### Task 2: Build the reproducible local dataset importer and SQLite schema

**Files:**
- Create: `backend/schema.sql`, `backend/scripts/import_dataset.py`, `backend/app/config.py`, `backend/app/db.py`
- Test: `backend/tests/test_import_dataset.py`, `backend/tests/fixtures.py`

**Interfaces:**
- Consumes: the four local Parquet shards or Hub files from repo `jxie/flickr8k`.
- Produces: `data/flickr8k.sqlite` containing `samples`, `captions`, `caption_search`, and `dataset_stats`; image bytes are stored in `data/images/{sample_id}.{extension}`.

- [ ] Write a generated two-row Parquet fixture with an `image` struct and five `caption_0` through `caption_4` fields, plus tests for dimension extraction, five-caption insertion, duplicate-safe re-import, and rejection of missing caption columns.
- [ ] Run `cd backend && uv run pytest tests/test_import_dataset.py -v`; confirm the importer cannot yet be imported.
- [ ] Define the schema: `samples(id TEXT PRIMARY KEY, split TEXT NOT NULL, source_shard TEXT NOT NULL, source_row INTEGER NOT NULL, image_path TEXT NOT NULL, media_type TEXT NOT NULL, width INTEGER NOT NULL, height INTEGER NOT NULL, aspect_ratio REAL NOT NULL)`, `captions(sample_id, position, text, word_count, PRIMARY KEY(sample_id, position))`, and an FTS5 table indexed from captions. Add indexes for split, dimensions, and caption word count.
- [ ] Implement an idempotent `python scripts/import_dataset.py [--data-dir PATH] [--download] [--force]`: download only when local shards are absent, iterate Parquet in record batches, normalize and validate image/caption values, write image bytes atomically, populate SQLite in transactions, then rebuild aggregate statistics. Never load a full shard into memory.
- [ ] Run importer tests and a manual fixture import; verify SQLite has two samples, ten captions, valid stored media files, and unchanged row counts after a second run.

### Task 3: Implement the query layer and stable API endpoints

**Files:**
- Create: `backend/app/models.py`, `backend/app/repository.py`, `backend/app/routes/__init__.py`, `backend/app/routes/dataset.py`, `backend/app/routes/media.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_dataset_routes.py`, `backend/tests/test_repository.py`

**Interfaces:**
- Consumes: the Task 2 SQLite schema.
- Produces: the API contract above, with all query values validated before SQL execution.

- [ ] Write repository tests for split filtering, multi-caption FTS match (one sample appears once even if two captions match), min/max dimension filtering, stable sort, page totals, and `previous_id`/`next_id` constrained to the same query.
- [ ] Write FastAPI tests for 400 responses on unknown sort, a negative page, page size over 100, malformed dimensions, and a 404 for unknown sample or missing image file.
- [ ] Implement Pydantic models and parameterized repository methods; use a whitelist mapping for sort modes rather than interpolating client input into SQL. Define `q` as an AND-token FTS query after escaping FTS operators, to make user-entered prose safe and predictable.
- [ ] Add `GET /api/overview`, `GET /api/samples`, detail, and image streaming routes. Return `dataset_ready:false`/HTTP 409 with a helpful import command for data-dependent requests when the database does not exist.
- [ ] Run `cd backend && uv run pytest -v`; run the service and verify the health and fixture-backed gallery responses with `curl`.

### Task 4: Create the overview that makes dataset composition legible

**Files:**
- Create: `frontend/src/api/types.ts`, `frontend/src/api/client.ts`, `frontend/src/features/overview/OverviewPage.tsx`, `frontend/src/features/overview/MetricCard.tsx`, `frontend/src/features/overview/DistributionChart.tsx`
- Modify: `frontend/src/app/App.tsx`
- Test: `frontend/src/features/overview/OverviewPage.test.tsx`

**Interfaces:**
- Consumes: `GET /api/overview`.
- Produces: route `/` with split totals, image-dimension/aspect-ratio distribution, caption-length distribution, and top caption terms.

- [ ] Create an MSW handler returning a deliberately uneven split distribution and known histogram values; write a test for all three split totals, a chart title, the top-term list, and an accessible loading state.
- [ ] Run `cd frontend && npm test -- --run OverviewPage.test.tsx`; confirm the component is missing.
- [ ] Implement a typed API client and TanStack Query provider with 30-second stale time. Render concise metric cards plus two Recharts bar charts: aspect ratio and caption word count. Render top terms as buttons that link to `/gallery?q=<term>`.
- [ ] Display a data-not-imported callout when the backend returns 409 and a retryable error state on network failure.
- [ ] Run all frontend tests and `npm run build`; inspect the route at desktop and 375px width without horizontal overflow.

### Task 5: Build the filterable, paginated image gallery

**Files:**
- Create: `frontend/src/features/gallery/GalleryPage.tsx`, `frontend/src/features/gallery/GalleryFilters.tsx`, `frontend/src/features/gallery/SampleGrid.tsx`, `frontend/src/features/gallery/SampleCard.tsx`, `frontend/src/features/gallery/galleryQuery.ts`
- Modify: `frontend/src/app/App.tsx`
- Test: `frontend/src/features/gallery/GalleryPage.test.tsx`, `frontend/src/features/gallery/galleryQuery.test.ts`

**Interfaces:**
- Consumes: `GET /api/samples` and URL query values `split`, `q`, `min_width`, `max_width`, `sort`, `page`.
- Produces: route `/gallery` whose controls and pagination are shareable through the URL.

- [ ] Write pure-function tests showing that valid URL parameters serialize deterministically, blank values are omitted, page resets to `1` when any filter changes, and invalid client-side dimension bounds show `Minimum must not exceed maximum` without fetching.
- [ ] Write an MSW-backed UI test that searches `dog`, chooses `train`, verifies the request URL, renders 30 result cards with meaningful image `alt` text from `caption_preview`, and preserves the filters in each detail link.
- [ ] Implement a debounced text search, split select, numeric dimensions, sort select, clear-filters button, total count, cards, and previous/next pagination. Disable controls while a new query is in flight but leave old results visible with an updating indicator.
- [ ] Use native lazy-loaded `<img>` elements with fixed aspect-ratio containers to prevent layout shift; show a textual fallback if an individual image fails.
- [ ] Run targeted and full frontend tests, `npm run build`, and manually verify a copied gallery URL restores the same search and page.

### Task 6: Deliver a focused image-and-caption inspection view

**Files:**
- Create: `frontend/src/features/detail/SampleDetailPage.tsx`, `frontend/src/features/detail/ImageInspector.tsx`, `frontend/src/features/detail/CaptionList.tsx`, `frontend/src/features/detail/SampleMetadata.tsx`
- Modify: `frontend/src/app/App.tsx`
- Test: `frontend/src/features/detail/SampleDetailPage.test.tsx`

**Interfaces:**
- Consumes: `GET /api/samples/{id}` plus the active gallery query string.
- Produces: `/samples/:id` with all captions, metadata, image, and query-aware neighbors.

- [ ] Write an MSW-backed test that verifies all five numbered captions, natural image dimensions/ratio, a back-to-results link retaining the query, disabled previous control when `previous_id` is null, and a next link that retains the query.
- [ ] Run the test and confirm the route is absent.
- [ ] Implement the page with a contained image that can expand to its natural size in a modal/dialog, an ordered caption list, compact metadata, and buttons for previous/next sample. Use an error boundary/not-found view for a 404.
- [ ] Add keyboard focus management and Escape-to-close for the image dialog; ensure visible focus styles and no color-only state indicators.
- [ ] Run all frontend tests/build and manually test gallery-to-detail-to-next-to-back navigation.

### Task 7: Final integration, local-run ergonomics, and acceptance verification

**Files:**
- Modify: `README.md`, `backend/pyproject.toml`, `frontend/package.json`
- Create: `scripts/dev.sh`, `backend/tests/test_full_fixture_flow.py`
- Test: all backend and frontend suites.

**Interfaces:**
- Consumes: completed importer, API, and SPA.
- Produces: one documented local workflow from clone to usable explorer.

- [ ] Write a fixture-flow integration test: import the tiny Parquet fixture into a temporary data directory, call overview, search a known caption, retrieve its detail, and retrieve image bytes with the expected media type.
- [ ] Add `scripts/dev.sh` that starts the backend and frontend together, forwards Ctrl-C to both child processes, and fails fast if either executable is missing. Keep a separate two-terminal command path in the README for portability.
- [ ] Complete README sections: project purpose, architecture diagram in text, exact setup/import/run commands, first-import disk/time expectations, API endpoint table, test commands, troubleshooting for missing data or an occupied port, and “Scope and trade-offs.” State that the initial Hugging Face download is the only external network dependency and subsequent operation is local.
- [ ] Run `cd backend && uv run pytest -v`, `cd frontend && npm test -- --run`, and `cd frontend && npm run build`; record the commands and outcomes in the delivery notes.
- [ ] In a clean temporary clone (or clean directory containing only the tracked project files), execute every README setup/import/start command verbatim. Confirm no data is written outside the selected `FLICKR8K_DATA_DIR`, the default path is repository-local `data/`, and every command succeeds without an undocumented prerequisite.
- [ ] After the import completes, disable network access (or block outbound traffic for the app processes), start the application, and confirm overview, filtered gallery, detail, images, empty results, and missing-data guidance behave as documented. Record this result as proof that normal application operation is fully local.
- [ ] Run an automated browser accessibility audit on overview, gallery, and detail at desktop width and repeat a manual check at 375px width: no horizontal scrolling, all controls have labels, focus is visible, the image dialog closes with Escape, and result navigation is keyboard reachable. Fix any serious/critical audit finding before delivery.

## Acceptance checklist

- [ ] A fresh clone can install, import, and run the application using only README commands.
- [ ] All downloaded data, extracted images, and indexes reside under local `data/` and are excluded from git.
- [ ] The UI is useful without guessing: overview explains composition, gallery supports concrete investigative questions, and details expose all five captions.
- [ ] No API depends on remote runtime calls; stopping the network after import does not prevent browsing.
- [ ] Backend validation, tests, typed responses, and modular feature directories make future additions (e.g. visual embeddings) possible without reworking the core.

## Plan review notes

- The data importer intentionally accepts the cost of a roughly 1.1 GB local first download because it meets the stated local-data constraint and avoids a brittle runtime dependency on hosted dataset APIs.
- Caption FTS is selected over embeddings for this submission: it delivers immediately useful, explainable retrieval with SQLite alone. A future `similarity` module can add local embeddings without changing sample IDs or gallery routes.
- The plan avoids storing image blobs inside SQLite so image delivery remains straightforward and database backup/query work stays light; SQLite stores stable paths and metadata only.

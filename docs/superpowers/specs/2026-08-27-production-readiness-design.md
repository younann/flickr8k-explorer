# Production Readiness Design

## Goal

Make the local-only Flickr8k Explorer maintainable, testable, and robust while preserving its single-developer-machine runtime model.

## Constraints

- All application data, search, and processing remain local after the one-time dataset import.
- No cloud services, managed databases, paid APIs, hosted search, or user accounts are introduced.
- Existing local import data remains usable; migrations are forward-only and idempotent.
- The gallery remains URL-shareable and responsive while searching.

## Stage 1: Complete the researcher workflow

The gallery filter model becomes a single URL-backed object: `q`, `split`, `page`, and `page_size`. Clear resets all filter keys and returns to page one. Previous/next controls use the server-returned `page`, `page_size`, and `total`; all existing filters remain intact.

The overview consumes `GET /api/overview` and renders actual split totals, mean caption length, frequent terms, and dimension/aspect-ratio distributions. The API adds those histogram values from local SQLite queries. The gallery exposes an `isDebouncing` state during the 300 ms input delay, then TanStack Query keeps the previous page visible while fresh data arrives.

## Stage 2: Frontend boundaries and typed contracts

`App.tsx` becomes route composition only. `features/overview`, `features/gallery`, and `features/detail` own their page components, API hooks, and focused view components. `components/` contains only shared layout and feedback UI.

`api/types.ts` declares every successful response and structured API error. `api/client.ts` validates an HTTP response before returning data and throws `ApiError { status, message }`. TanStack Query hooks are named by resource, such as `useSamples(query)` and `useOverview()`.

## Stage 3: Backend contracts and database lifecycle

Pydantic models define health, overview, sample summary/detail, pagination, and error payloads. Routes use `response_model` so the OpenAPI document and actual responses stay aligned.

Routes move into `app/routes/`: `dataset.py` handles overview/sample JSON and `media.py` streams images. The repository remains the only location with SQL.

`schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)` records applied migrations. `db.initialize()` applies ordered SQL migrations inside one transaction, skipping versions already recorded. The existing schema becomes migration `001_initial.sql`; later changes are new files, never edited historical migrations.

## Stage 4: Resilient dataset ingestion

Replace implicit hard-coded filenames with a checked-in `dataset_manifest.json` containing dataset repository, revision, split, filename, and expected SHA-256 when known. The importer reads this manifest, downloads only missing files, and reports a clear error if a listed file cannot be fetched. Updating to a future dataset revision is one reviewed manifest change, not an importer code change.

## Stage 5: Quality gates

Playwright runs against a fixture-backed local server. It covers imported gallery search, pagination, detail navigation back to the same query, and empty/missing-data states. Axe checks run on overview, gallery, and detail. Unit/API tests cover schema migration idempotency, typed error payloads, manifest validation, overview distributions, and URL filter behavior.

## Acceptance criteria

- A user can clear all filters, paginate results, and return from an inspected sample without losing context.
- Overview values are derived from the locally indexed dataset, not static copy.
- Every documented JSON endpoint has a Pydantic response model and a TypeScript consumer type.
- Re-running migrations and imports never duplicates data or corrupts an existing local database.
- The importer reads an explicit versioned manifest.
- Automated unit, API, browser-flow, and accessibility tests pass locally with documented commands.

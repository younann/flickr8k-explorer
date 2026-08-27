# Production Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the usability backlog and make the local-only application modular, typed, migration-safe, and browser-testable.

**Architecture:** Preserve FastAPI + SQLite + React/Vite. Introduce versioned SQLite migrations and typed backend/frontend contracts at the API boundary; keep feature UI, data hooks, and shared components separate. Quality gates run only local fixture servers and browsers.

**Tech Stack:** FastAPI/Pydantic, SQLite, PyArrow, React/TypeScript, TanStack Query, Vitest, Playwright, axe-core.

**Spec:** `docs/superpowers/specs/2026-08-27-production-readiness-design.md`

## Global Constraints

- All data/search/processing remain local after the one-time import.
- No cloud, managed database, paid API, hosted search, or user accounts.
- Migrations are forward-only and idempotent; existing local imports remain usable.
- Gallery state is URL-shareable through `q`, `split`, `page`, and `page_size`.

---

## File structure

| Path | Responsibility |
| --- | --- |
| `backend/app/migrations/001_initial.sql` | Initial versioned SQLite schema. |
| `backend/app/models.py` | Pydantic API responses and error payload. |
| `backend/app/routes/dataset.py`, `media.py` | Typed JSON and media endpoint groups. |
| `backend/dataset_manifest.json` | Versioned Flickr8k shard description. |
| `frontend/src/api/{client,types}.ts` | Typed HTTP boundary and `ApiError`. |
| `frontend/src/features/{overview,gallery,detail}/` | Feature routes, hooks, and view components. |
| `frontend/e2e/` | Playwright and axe accessibility coverage. |

### Task 1: Add SQLite migrations and typed API models

**Files:** Create `backend/app/migrations/001_initial.sql`, `backend/app/models.py`, `backend/tests/test_migrations.py`; modify `backend/app/db.py`, `backend/app/main.py`.

**Interfaces:** `initialize(connection) -> None` applies each numbered SQL file exactly once; `HealthResponse`, `OverviewResponse`, `SamplePage`, `SampleDetailResponse`, and `ErrorResponse` are Pydantic models used by routes.

- [ ] Write a failing test that initializes a temporary database twice and asserts `schema_migrations` contains only version `1`, and `samples` exists after each call.
- [ ] Run `cd backend && uv run pytest tests/test_migrations.py -v`; expect failure because no migration table exists.
- [ ] Move the current schema into `migrations/001_initial.sql`; make `initialize()` create `schema_migrations`, detect numeric migration filenames, execute unapplied SQL in a transaction, and insert the version/timestamp only after success.
- [ ] Write failing route tests expecting typed health and missing-data responses, then define Pydantic models and attach `response_model=` to endpoints.
- [ ] Run `cd backend && uv run pytest -v`; expect all importer, API, and migration tests to pass.

### Task 2: Make ingestion manifest-driven

**Files:** Create `backend/dataset_manifest.json`, `backend/tests/test_manifest.py`; modify `backend/scripts/import_dataset.py`, `README.md`.

**Interfaces:** `load_manifest(path: Path) -> DatasetManifest` returns `{repository, revision, splits}`; `download_shards(manifest, raw_dir) -> dict[str, list[Path]]` downloads only declared files.

- [ ] Write failing tests for a valid two-split manifest, missing required manifest fields, and invalid duplicate `(split, filename)` entries.
- [ ] Run `cd backend && uv run pytest tests/test_manifest.py -v`; expect import/validation failure.
- [ ] Implement Pydantic manifest validation; replace the `SHARDS` constant with `dataset_manifest.json`, pin the existing dataset revision, and pass `revision=` to `hf_hub_download`.
- [ ] Document the manifest update procedure and verify `uv run python -m scripts.import_dataset --help` succeeds without downloading data.

### Task 3: Finish gallery navigation and overview API data

**Files:** Modify `backend/app/repository.py`, `backend/app/routes/dataset.py`, `backend/tests/test_dataset_routes.py`; create `frontend/src/features/gallery/query.ts`, `frontend/src/features/gallery/GalleryPage.test.tsx`.

**Interfaces:** `GET /api/samples` accepts `q`, `split`, `page`, `page_size` and returns `{items,page,page_size,total}`; `GET /api/overview` returns split totals, mean caption length, top terms, and `aspect_ratio_bins`.

- [ ] Write failing backend tests for page two returning a different slice and overview `aspect_ratio_bins` totaling the sample count.
- [ ] Implement parameterized limit/offset and bins (`portrait`, `square`, `landscape`) in repository SQL; validate page values through Pydantic/FastAPI constraints.
- [ ] Write failing frontend tests: Clear removes `q` and `split`; Next updates only `page`; a debounce indicator appears before the new request.
- [ ] Implement pure URL helpers `parseGalleryQuery` and `withGalleryQuery`; wire clear, previous/next controls, and `isDebouncing` into the gallery.
- [ ] Run backend and focused gallery tests; verify copied page-two URLs restore the same results.

### Task 4: Split the frontend and add typed client/hooks

**Files:** Create `frontend/src/api/{client,types}.ts`, `frontend/src/features/overview/OverviewPage.tsx`, `frontend/src/features/gallery/{GalleryPage,useSamples}.ts`, `frontend/src/features/detail/DetailPage.tsx`, `frontend/src/components/{AppShell,Feedback}.tsx`; modify `frontend/src/app/App.tsx`, `frontend/src/main.tsx`.

**Interfaces:** `ApiError(status:number,message:string)`, `getOverview(): Promise<OverviewResponse>`, `useSamples(query): UseQueryResult<SamplePage>`, `useOverview(): UseQueryResult<OverviewResponse>`.

- [ ] Write failing component tests for rendering real split totals/top terms from an overview fixture and rendering a 409 as import guidance.
- [ ] Implement the typed client so non-OK responses parse `{detail}` and throw `ApiError`; create resource hooks with 60-second stale time and prior-data retention.
- [ ] Move each existing page to its feature module; leave `App.tsx` with only `AppShell` and route declarations.
- [ ] Render overview metrics and aspect-ratio bars from `useOverview`; make terms navigate to `/gallery?q=<term>`.
- [ ] Run `cd frontend && npm test -- --run && npm run build`; confirm no import from legacy `App.tsx` page implementations remains.

### Task 5: Add local end-to-end and accessibility gates

**Files:** Create `frontend/playwright.config.ts`, `frontend/e2e/{gallery.spec.ts,accessibility.spec.ts}`, `frontend/e2e/fixtures/`; modify `frontend/package.json`, `README.md`.

**Interfaces:** `npm run test:e2e` starts fixture backend/Vite, then runs Playwright; `npm run test:a11y` runs axe checks on overview, gallery, and detail.

- [ ] Write a failing Playwright test that searches a fixture dataset, opens a result, returns to the same query, moves to next page, and sees an empty state for a missing term.
- [ ] Add Playwright, `@axe-core/playwright`, and scripts; configure a fixture data directory created through the existing importer before tests start.
- [ ] Add axe assertions for serious/critical violations at desktop and 375px viewports, including keyboard-reachable gallery controls.
- [ ] Run `npm run test:e2e` and `npm run test:a11y`; fix only observed failures and rerun both commands.

### Task 6: Documentation and delivery verification

**Files:** Modify `README.md`, `docs/backlog.md`; test all suites.

- [ ] Document migrations, manifest updates, local quality-gate commands, pagination, overview, and the guarantee that post-import runtime stays local.
- [ ] Mark each completed backlog item and retain only deliberately deferred scope.
- [ ] Run `cd backend && uv run pytest -v`, `cd frontend && npm test -- --run && npm run build && npm run test:e2e && npm run test:a11y`.
- [ ] Confirm the developer launcher, dataset import, and test commands work from a clean local checkout; record any required browser-install command in README.

## Coverage review

- Stage 1 is Tasks 3 and 4.
- Stage 2 is Task 4.
- Stage 3 is Task 1.
- Stage 4 is Task 2.
- Stage 5 is Task 5.
- Delivery acceptance and documentation are Task 6.

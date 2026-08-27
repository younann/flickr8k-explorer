# Deferred improvements

## UX and usability

- [ ] Make the gallery **Clear** action reset both the caption search and selected split, or rename it to **Clear search** if it intentionally affects only text.
- [ ] Add visible previous/next pagination controls and retain the current filters while moving between pages.
- [ ] Replace the overview landing-page placeholders with the local split, caption-length, and image-distribution statistics already available from `GET /api/overview`.
- [ ] Show a brief **Searching…** state during the 300 ms debounce interval, before the cached/updated results request begins.

## Frontend and backend design

- [ ] Split `frontend/src/app/App.tsx` into focused overview, gallery, detail, layout, and shared-component modules as the UI grows.
- [ ] Add explicit Pydantic response models for API payloads instead of returning untyped dictionaries from route handlers.
- [ ] Move `backend/app/routes.py` into a `backend/app/routes/` package when additional endpoint groups are introduced.
- [ ] Add SQLite schema versioning and forward migrations before making future data-model changes.

## Code quality and extensibility

- [ ] Replace hard-coded Flickr8k shard filenames with a dataset-manifest discovery step or a documented versioned manifest, so upstream file changes are easier to accommodate.
- [ ] Add end-to-end browser tests for import-ready gallery search, sample inspection, query-preserving navigation, and empty/error states.
- [ ] Add automated accessibility checks for overview, gallery, and detail pages, including keyboard navigation and responsive layouts.
- [ ] Expand typed frontend API contracts to cover overview and error payloads, then validate those contracts in component tests.

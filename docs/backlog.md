# Backlog status

The production-readiness scope is complete. The finished items remain recorded below; only the route-package extraction is deliberately deferred because the application still has a single small API endpoint group.

## Completed in the production-readiness delivery

- [x] Make the gallery **Clear** action reset both the caption search and selected split.
- [x] Add visible previous/next pagination controls and retain the current filters while moving between pages.
- [x] Replace overview placeholders with local split, caption-length, frequent-term, and image-distribution statistics from `GET /api/overview`.
- [x] Show a brief search-update state during the 300 ms debounce interval.
- [x] Split the frontend into focused overview, gallery, detail, layout, and shared-component modules.
- [x] Add explicit Pydantic response models for API payloads.
- [x] Add SQLite schema versioning and forward migrations for future data-model changes.
- [x] Replace hard-coded Flickr8k shard filenames with the documented, versioned dataset manifest.
- [x] Add local end-to-end browser coverage for search, sample inspection, query-preserving navigation, pagination, and empty states.
- [x] Add automated accessibility checks for overview, gallery, detail, keyboard navigation, and responsive layouts.
- [x] Expand typed frontend API contracts to cover overview and error payloads, with component coverage.

## Deliberately deferred scope

- [ ] Move `backend/app/routes.py` into a `backend/app/routes/` package when additional endpoint groups are introduced.

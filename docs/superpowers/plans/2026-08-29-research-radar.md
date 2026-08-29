# Research Radar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-first Research Radar that explains caption disagreement, surfaces perceptual-hash neighbours, and lets researchers save and export findings.

**Architecture:** SQLite stores transparent per-sample analysis plus local collections and findings. The importer derives analysis deterministically from existing Flickr8k images and captions; FastAPI exposes typed, focused read/write endpoints; React feature modules render the Radar, evidence triage, and collections workflow.

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, SQLite, Pillow, pytest/httpx, React, TypeScript, TanStack Query, React Router, Vitest, Playwright, axe-core.

**Spec:** `docs/superpowers/specs/2026-08-29-research-radar-design.md`

## Global Constraints

- The product remains fully local-first: no hosted service, account, embedding model, or model-weight download.
- Similarity copy must say “visually close” or “near-duplicate candidate”; it must not claim semantic similarity.
- Caption-disagreement scores must show their transparent supporting signals and must not claim annotation quality.
- Existing caption search, split filtering, pagination, URL preservation, and local import behavior must continue to work.
- Import analysis must be idempotent and must never remove user-created collections or findings.
- New APIs use explicit Pydantic request/response models and parameterized SQLite queries.
- Every implementation task follows red → green → refactor and commits only its own files.

---

## File structure

- `backend/app/analysis.py` — pure caption-token, score, perceptual-hash, and Hamming-distance functions.
- `backend/app/migrations/002_research_radar.sql` — analysis, collection, and finding tables plus indexes.
- `backend/app/importer.py` — invokes pure analysis while importing and rebuilds analysis for existing imports.
- `backend/app/models.py` — typed Radar, analysis, similarity, collection, finding, and export models.
- `backend/app/repository.py` — parameterized reads/writes for research data.
- `backend/app/routes.py` — typed API routes and CSV/JSON export response creation.
- `backend/tests/test_analysis.py` — deterministic pure-function tests.
- `backend/tests/test_research_routes.py` — migration/repository/API integration tests.
- `frontend/src/api/types.ts` and `frontend/src/api/client.ts` — frontend contracts and requests.
- `frontend/src/features/radar/*` — Radar page, query hook, and tests.
- `frontend/src/features/detail/*` — analysis explanation, similarity list, and save-finding controls.
- `frontend/src/features/collections/*` — collection review and export controls.
- `frontend/src/app/App.tsx`, `frontend/src/components/AppShell.tsx`, and `frontend/src/styles.css` — routes, navigation, and shared layout rules.
- `frontend/e2e/research-radar.spec.ts` and `frontend/e2e/accessibility.spec.ts` — end-to-end and accessibility coverage.
- `README.md` — demo workflow and local-first research capabilities.

### Task 1: Deterministic analysis primitives

**Files:**
- Create: `backend/app/analysis.py`
- Create: `backend/tests/test_analysis.py`
- Modify: `backend/pyproject.toml`

**Interfaces:**
- Produces: `caption_analysis(captions: list[str]) -> CaptionAnalysis`.
- Produces: `perceptual_hash(image: PIL.Image.Image) -> int`.
- Produces: `hamming_distance(left: int, right: int) -> int`.
- Consumed by: importer and repository similarity ranking.

- [ ] **Step 1: Write the failing tests**

```python
from app.analysis import caption_analysis, hamming_distance

def test_caption_analysis_rewards_different_caption_vocabularies():
    repeated = caption_analysis(["a dog runs"] * 5)
    varied = caption_analysis([
        "a dog runs through grass", "a puppy chases a ball",
        "an animal plays outdoors", "a brown dog leaps", "a pet runs fast",
    ])
    assert repeated.disagreement_score == 0
    assert varied.disagreement_score > repeated.disagreement_score

def test_hamming_distance_counts_changed_bits():
    assert hamming_distance(0b1010, 0b1111) == 2
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend && uv run pytest tests/test_analysis.py -v`

Expected: FAIL because `app.analysis` does not exist.

- [ ] **Step 3: Implement the minimal pure analysis module**

```python
@dataclass(frozen=True)
class CaptionAnalysis:
    disagreement_score: int
    token_disagreement: float
    vocabulary_diversity: float
    mean_caption_length: float
    caption_length_spread: float

def hamming_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()
```

Normalize lowercase alphabetic tokens, calculate pairwise Jaccard distance for the five token sets, calculate population standard deviation of caption word counts, and clamp the rounded composite score to `0..100`. Implement an average-hash Pillow algorithm by converting to grayscale, resizing to `8x8`, and setting a bit for each pixel at or above the mean.

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd backend && uv run pytest tests/test_analysis.py -v`

Expected: PASS with two tests.

- [ ] **Step 5: Commit**

```bash
git add backend/app/analysis.py backend/tests/test_analysis.py backend/pyproject.toml
git commit -m "feat: add local research analysis primitives"
```

### Task 2: Persist analysis, collections, and findings

**Files:**
- Create: `backend/app/migrations/002_research_radar.sql`
- Modify: `backend/app/importer.py`
- Modify: `backend/tests/test_import_dataset.py`
- Modify: `backend/tests/test_migrations.py`

**Interfaces:**
- Consumes: `caption_analysis()` and `perceptual_hash()` from Task 1.
- Produces: one `sample_analysis` row for every imported sample.
- Produces: SQLite `collections` and `findings` tables usable by Task 3.

- [ ] **Step 1: Write the failing migration/import tests**

```python
def test_import_persists_analysis_for_each_sample(imported_data_dir):
    with connect(imported_data_dir) as connection:
        row = connection.execute(
            "SELECT disagreement_score, perceptual_hash FROM sample_analysis"
        ).fetchone()
    assert row["disagreement_score"] >= 0
    assert row["perceptual_hash"] is not None

def test_research_migration_creates_finding_tables(data_dir):
    with connect(data_dir) as connection:
        initialize(connection)
        names = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )}
    assert {"sample_analysis", "collections", "findings"} <= names
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_import_dataset.py tests/test_migrations.py -v`

Expected: FAIL because `sample_analysis` and the research tables do not exist.

- [ ] **Step 3: Add the migration and importer writes**

```sql
CREATE TABLE sample_analysis (
    sample_id TEXT PRIMARY KEY REFERENCES samples(id) ON DELETE CASCADE,
    disagreement_score INTEGER NOT NULL,
    token_disagreement REAL NOT NULL,
    vocabulary_diversity REAL NOT NULL,
    mean_caption_length REAL NOT NULL,
    caption_length_spread REAL NOT NULL,
    perceptual_hash TEXT NOT NULL
);
CREATE INDEX sample_analysis_score_idx ON sample_analysis(disagreement_score DESC);
```

Add `collections` and `findings` with integer primary keys, UTC `CURRENT_TIMESTAMP` creation/update fields, a unique collection name, foreign keys, and indexes on `findings(collection_id)` and `findings(sample_id)`. Format the 64-bit hash as a zero-padded 16-character hexadecimal string before storing it. After reading every source row, compute analysis from its five captions and `INSERT OR REPLACE` it even when `samples.id` already exists; re-running the importer therefore backfills analysis for a pre-existing database without touching collections or findings. Keep the analysis write inside the existing import transaction.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_import_dataset.py tests/test_migrations.py -v`

Expected: PASS and repeat-import remains idempotent.

- [ ] **Step 5: Commit**

```bash
git add backend/app/migrations/002_research_radar.sql backend/app/importer.py backend/tests/test_import_dataset.py backend/tests/test_migrations.py
git commit -m "feat: persist research analysis and findings tables"
```

### Task 3: Typed repository and API contracts

**Files:**
- Modify: `backend/app/models.py`
- Modify: `backend/app/repository.py`
- Modify: `backend/app/routes.py`
- Create: `backend/tests/test_research_routes.py`

**Interfaces:**
- Produces: `radar(split: str | None) -> dict`, `analysis(sample_id: str) -> dict | None`, and `similar(sample_id: str, limit: int = 6) -> list[dict]`.
- Produces: `create_collection(name: str) -> dict`, `create_finding(collection_id: int, sample_id: str, tags: str, note: str) -> dict`, and `collection_export(collection_id: int) -> list[dict]`.
- Consumed by: Tasks 4–6 through typed HTTP endpoints.

- [ ] **Step 1: Write failing route tests**

```python
def test_radar_returns_ranked_outliers(client):
    response = client.get("/api/radar")
    assert response.status_code == 200
    assert response.json()["outliers"][0]["disagreement_score"] >= 0

def test_collection_finding_can_be_created_and_exported(client, sample_id):
    collection = client.post("/api/collections", json={"name": "Ambiguity"}).json()
    finding = client.post(
        f"/api/collections/{collection['id']}/findings",
        json={"sample_id": sample_id, "tags": ["action"], "note": "Different verbs"},
    )
    assert finding.status_code == 201
    exported = client.get(f"/api/collections/{collection['id']}/export?format=json")
    assert exported.status_code == 200
    assert exported.json()["findings"][0]["note"] == "Different verbs"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_research_routes.py -v`

Expected: FAIL with 404 routes or missing Pydantic models.

- [ ] **Step 3: Implement Pydantic models, repository methods, and routes**

```python
class CreateCollectionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)

class CreateFindingRequest(BaseModel):
    sample_id: str
    tags: list[str] = Field(default_factory=list, max_length=8)
    note: str = Field(default="", max_length=1000)
```

Use parameterized queries for every repository value. Convert stored hexadecimal hashes with `int(value, 16)` before calling Python `hamming_distance()`, exclude the selected sample, sort by `(distance, sample_id)`, and cap the result at `6`. Return `404` for nonexistent samples/collections/findings. Use `StreamingResponse` for CSV and `JSONResponse` with attachment headers for JSON export. Add `POST` and `DELETE` to CORS methods.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_research_routes.py tests/test_dataset_routes.py -v`

Expected: PASS, including typed 404 and validation cases.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models.py backend/app/repository.py backend/app/routes.py backend/tests/test_research_routes.py
git commit -m "feat: expose research radar and findings APIs"
```

### Task 4: Typed frontend client and Research Radar

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Create: `frontend/src/features/radar/RadarPage.tsx`
- Create: `frontend/src/features/radar/useRadar.ts`
- Create: `frontend/src/features/radar/RadarPage.test.tsx`
- Modify: `frontend/src/app/App.tsx`
- Modify: `frontend/src/components/AppShell.tsx`
- Modify: `frontend/src/styles.css`

**Interfaces:**
- Consumes: `GET /api/radar` response defined in Task 3.
- Produces: route `/radar` and `getRadar(params: URLSearchParams): Promise<RadarResponse>`.
- Consumed by: navigation and Task 6 browser coverage.

- [ ] **Step 1: Write the failing Radar component test**

```tsx
test("links a Radar outlier to a disagreement-filtered gallery", async () => {
  render(<App />, { wrapper: routerAt("/radar") });
  await userEvent.click(await screen.findByRole("link", { name: /Fixture dog 1/i }));
  expect(window.location.search).toContain("sort=disagreement");
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd frontend && npm test -- --run src/features/radar/RadarPage.test.tsx`

Expected: FAIL because the Radar route and client do not exist.

- [ ] **Step 3: Implement typed query and Radar page**

```tsx
export function useRadar(params: URLSearchParams) {
  return useQuery({ queryKey: ["radar", params.toString()], queryFn: () => getRadar(params) });
}
```

Render concise distribution buckets, three local summary metrics, and ranked outlier cards. Each card must display the disagreement score and link to `/samples/{id}` while retaining a `sort=disagreement` gallery context. Add a “Research Radar” navigation item and preserve the existing overview route.

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd frontend && npm test -- --run src/features/radar/RadarPage.test.tsx`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api frontend/src/features/radar frontend/src/app/App.tsx frontend/src/components/AppShell.tsx frontend/src/styles.css
git commit -m "feat: add research radar dashboard"
```

### Task 5: Evidence triage and local collections

**Files:**
- Modify: `frontend/src/features/detail/DetailPage.tsx`
- Create: `frontend/src/features/detail/AnalysisPanel.tsx`
- Create: `frontend/src/features/detail/SaveFindingForm.tsx`
- Create: `frontend/src/features/collections/CollectionsPage.tsx`
- Create: `frontend/src/features/collections/CollectionsPage.test.tsx`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/app/App.tsx`
- Modify: `frontend/src/styles.css`

**Interfaces:**
- Consumes: sample analysis, similar-sample, collection, and finding endpoints from Task 3.
- Produces: route `/collections`, a save-finding control, and download links for `/export?format=csv|json`.

- [ ] **Step 1: Write failing evidence and collection tests**

```tsx
test("saves a tagged finding from evidence triage", async () => {
  render(<DetailPage />, { wrapper: routerAt(`/samples/${fixtureSampleId}`) });
  await userEvent.selectOptions(await screen.findByLabelText("Collection"), "1");
  await userEvent.type(screen.getByLabelText("Tags"), "action, ambiguity");
  await userEvent.click(screen.getByRole("button", { name: "Save finding" }));
  expect(await screen.findByText("Saved to Action ambiguity examples")).toBeVisible();
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd frontend && npm test -- --run src/features/detail src/features/collections/CollectionsPage.test.tsx`

Expected: FAIL because analysis controls and collection routes do not exist.

- [ ] **Step 3: Implement evidence triage and collections UI**

Display score, token disagreement, vocabulary diversity, and caption-length spread with explanatory copy. Highlight only tokens that occur in a strict subset of captions; keep original captions readable. Render visually-close cards using the required near-duplicate wording. Add an accessible form with collection, tags, and note fields; show success/error status with `aria-live`. Collections must list findings with delete controls and plain anchor downloads for CSV/JSON exports.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd frontend && npm test -- --run src/features/detail src/features/collections/CollectionsPage.test.tsx`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api frontend/src/features/detail frontend/src/features/collections frontend/src/app/App.tsx frontend/src/styles.css
git commit -m "feat: add evidence triage and local collections"
```

### Task 6: Analysis-aware browse, browser verification, and delivery documentation

**Files:**
- Modify: `frontend/src/features/gallery/query.ts`
- Modify: `frontend/src/features/gallery/GalleryPage.tsx`
- Modify: `frontend/src/features/gallery/GalleryPage.test.tsx`
- Create: `frontend/e2e/research-radar.spec.ts`
- Modify: `frontend/e2e/accessibility.spec.ts`
- Modify: `README.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `sort=disagreement` and analysis-aware `/api/samples` behavior from Tasks 3–5.
- Produces: URL-shareable analysis browsing and a documented demo workflow.

- [ ] **Step 1: Write the failing gallery and browser tests**

```tsx
test("keeps disagreement sorting while changing gallery page", async () => {
  render(<GalleryPage />, { wrapper: routerAt("/gallery?sort=disagreement") });
  await userEvent.click(await screen.findByRole("button", { name: "Next page" }));
  expect(window.location.search).toBe("?sort=disagreement&page=2");
});
```

```ts
test("researcher saves and exports an ambiguity finding", async ({ page }) => {
  await page.goto("/radar");
  await page.getByRole("link", { name: /Fixture dog/i }).first().click();
  await page.getByRole("button", { name: "Save finding" }).click();
  await expect(page.getByText(/Saved to/i)).toBeVisible();
  await page.getByRole("link", { name: "Collections" }).click();
  await expect(page.getByRole("link", { name: "Export CSV" })).toBeVisible();
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd frontend && npm test -- --run src/features/gallery/GalleryPage.test.tsx`

Expected: FAIL because analysis sorting is not represented in query state.

- [ ] **Step 3: Implement URL sorting, browser coverage, and docs**

Extend `GalleryQuery` with `sort: "default" | "disagreement"` and set it through a labelled native select. Ensure pagination and detail back-links retain it. Add `.superpowers/` to `.gitignore`. Add README sections for Research Radar, the perceptual-hash limitation, annotations/exports, and a 90-second demo flow: open Radar, inspect outlier, save finding, export collection.

- [ ] **Step 4: Run full verification**

Run:

```bash
cd backend && uv run pytest -v
cd frontend && npm test -- --run
cd frontend && npm run build
cd frontend && npm run test:e2e
cd frontend && npm run test:a11y
```

Expected: every command exits `0`; browser tests pass at desktop and mobile widths.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/gallery frontend/e2e README.md .gitignore
git commit -m "feat: complete research radar workflow"
```

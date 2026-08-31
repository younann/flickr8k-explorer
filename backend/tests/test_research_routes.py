import csv
from io import StringIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import connect
from app.importer import import_shards
from app.main import create_app
from tests.fixtures import write_fixture_shard


def prepared_client(tmp_path: Path) -> TestClient:
    shard = write_fixture_shard(tmp_path / "train.parquet")
    data_dir = tmp_path / "data"
    import_shards({"train": [shard]}, data_dir)
    return TestClient(create_app(data_dir=data_dir))


@pytest.mark.parametrize(
    "path",
    [
        "/api/radar",
        "/api/samples?sort=disagreement",
        "/api/samples/{sample_id}/analysis",
        "/api/samples/{sample_id}/similar",
    ],
)
def test_analysis_dependent_reads_require_a_local_backfill(tmp_path: Path, path: str):
    shard = write_fixture_shard(tmp_path / "train.parquet")
    data_dir = tmp_path / "data"
    import_shards({"train": [shard]}, data_dir)
    with connect(data_dir) as connection:
        metadata_table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'analysis_metadata'"
        ).fetchone()
        if metadata_table is not None:
            connection.execute("DELETE FROM analysis_metadata WHERE key = 'analysis_version'")
            connection.commit()

    client = TestClient(create_app(data_dir=data_dir))
    sample_id = client.get("/api/samples").json()["items"][0]["id"]
    response = client.get(path.format(sample_id=sample_id))

    assert response.status_code == 409
    assert response.json() == {"detail": "Analysis backfill is required. Run python scripts/import_dataset.py --download."}


def test_radar_returns_ranked_outliers(tmp_path: Path):
    client = prepared_client(tmp_path)

    response = client.get("/api/radar")

    assert response.status_code == 200
    payload = response.json()
    assert payload["outliers"][0]["disagreement_score"] >= 0
    assert payload["summary"]["sample_count"] == 2
    assert sum(bucket["sample_count"] for bucket in payload["distribution"]) == 2
    assert payload["split_composition"] == [{"name": "train", "sample_count": 2}]


def test_radar_filters_by_score_and_exact_hash_near_duplicate_signal(tmp_path: Path):
    client = prepared_client(tmp_path)
    data_dir = tmp_path / "data"
    sample_ids = [item["id"] for item in client.get("/api/samples").json()["items"]]
    with connect(data_dir) as connection:
        connection.execute("UPDATE samples SET split = 'validation' WHERE id = ?", (sample_ids[1],))
        connection.execute("UPDATE sample_analysis SET disagreement_score = 25, perceptual_hash = '0000000000000000' WHERE sample_id = ?", (sample_ids[0],))
        connection.execute("UPDATE sample_analysis SET disagreement_score = 85, perceptual_hash = '0000000000000000' WHERE sample_id = ?", (sample_ids[1],))
        connection.execute(
            """INSERT INTO samples (id, split, source_shard, source_row, image_path, media_type, width, height, aspect_ratio)
            VALUES ('unpaired', 'validation', 'extra.parquet', 0, 'unused.png', 'image/png', 1, 1, 1)"""
        )
        connection.execute("INSERT INTO captions (sample_id, position, text, word_count) VALUES ('unpaired', 0, 'Unpaired sample', 2)")
        connection.execute(
            """INSERT INTO sample_analysis (sample_id, disagreement_score, token_disagreement, vocabulary_diversity,
            mean_caption_length, caption_length_spread, perceptual_hash) VALUES ('unpaired', 85, 0, 0, 0, 0, 'ffffffffffffffff')"""
        )
        connection.commit()

    response = client.get("/api/radar", params={"split": "validation", "min_score": 80, "max_score": 90, "near_duplicates_only": "true"})

    assert response.status_code == 200
    assert response.json()["summary"]["sample_count"] == 1
    assert [item["id"] for item in response.json()["outliers"]] == [sample_ids[1]]
    assert response.json()["split_composition"] == [
        {"name": "train", "sample_count": 1},
        {"name": "validation", "sample_count": 2},
    ]
    assert client.get("/api/radar", params={"min_score": 90, "max_score": 80}).status_code == 422


def test_analysis_and_visually_close_samples_use_local_hashes(tmp_path: Path):
    client = prepared_client(tmp_path)
    sample_id = client.get("/api/samples").json()["items"][0]["id"]

    analysis = client.get(f"/api/samples/{sample_id}/analysis")
    similar = client.get(f"/api/samples/{sample_id}/similar")

    assert analysis.status_code == 200
    assert analysis.json()["disagreement_score"] >= 0
    assert similar.status_code == 200
    assert all(item["id"] != sample_id for item in similar.json()["items"])
    assert [item["distance"] for item in similar.json()["items"]] == sorted(
        item["distance"] for item in similar.json()["items"]
    )


def test_similar_samples_caps_tied_hashes_and_uses_sample_id_as_tiebreaker(tmp_path: Path):
    client = prepared_client(tmp_path)
    data_dir = tmp_path / "data"
    existing_ids = [item["id"] for item in client.get("/api/samples").json()["items"]]
    selected_id, other_id = existing_ids
    with connect(data_dir) as connection:
        connection.execute("UPDATE sample_analysis SET perceptual_hash = ? WHERE sample_id = ?", ("0000000000000000", selected_id))
        connection.execute("UPDATE sample_analysis SET perceptual_hash = ? WHERE sample_id = ?", ("ffffffffffffffff", other_id))
        for index in range(7):
            sample_id = f"candidate-{index}"
            connection.execute(
                """INSERT INTO samples (id, split, source_shard, source_row, image_path, media_type, width, height, aspect_ratio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (sample_id, "train", "ties.parquet", index, "unused.png", "image/png", 4, 3, 4 / 3),
            )
            connection.execute(
                "INSERT INTO captions (sample_id, position, text, word_count) VALUES (?, ?, ?, ?)",
                (sample_id, 0, "A tied candidate.", 3),
            )
            connection.execute(
                """INSERT INTO sample_analysis
                    (sample_id, disagreement_score, token_disagreement, vocabulary_diversity,
                    mean_caption_length, caption_length_spread, perceptual_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (sample_id, 0, 0, 0, 0, 0, "0000000000000000"),
            )
        connection.commit()

    response = client.get(f"/api/samples/{selected_id}/similar?limit=6")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [f"candidate-{index}" for index in range(6)]
    assert all(item["distance"] == 0 for item in response.json()["items"])


def test_samples_can_sort_by_disagreement_without_changing_existing_filters(tmp_path: Path):
    client = prepared_client(tmp_path)
    data_dir = tmp_path / "data"
    source_order = [item["id"] for item in client.get("/api/samples", params={"q": "dog", "split": "train"}).json()["items"]]
    with connect(data_dir) as connection:
        connection.execute("UPDATE sample_analysis SET disagreement_score = ? WHERE sample_id = ?", (0, source_order[0]))
        connection.execute("UPDATE sample_analysis SET disagreement_score = ? WHERE sample_id = ?", (100, source_order[1]))
        connection.commit()

    response = client.get("/api/samples", params={"q": "dog", "split": "train", "sort": "disagreement"})

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert [item["id"] for item in response.json()["items"]] == list(reversed(source_order))


def test_collection_finding_can_be_created_and_exported(tmp_path: Path):
    client = prepared_client(tmp_path)
    sample_id = client.get("/api/samples").json()["items"][0]["id"]

    collection = client.post("/api/collections", json={"name": "Ambiguity"})
    assert collection.status_code == 201
    collection_id = collection.json()["id"]
    finding = client.post(
        f"/api/collections/{collection_id}/findings",
        json={"sample_id": sample_id, "tags": ["action"], "note": "Different verbs"},
    )
    exported = client.get(f"/api/collections/{collection_id}/export?format=json")
    csv_export = client.get(f"/api/collections/{collection_id}/export?format=csv")

    assert finding.status_code == 201
    assert exported.status_code == 200
    assert exported.headers["content-disposition"] == 'attachment; filename="ambiguity.json"'
    assert exported.json()["findings"][0]["note"] == "Different verbs"
    assert exported.json()["findings"][0]["captions"][0] == "A blue dog runs."
    assert exported.json()["collection"]["created_at"]
    assert exported.json()["collection"]["updated_at"]
    assert len(exported.json()["findings"][0]["perceptual_hash"]) == 16
    assert csv_export.status_code == 200
    assert csv_export.headers["content-disposition"] == 'attachment; filename="ambiguity.csv"'
    csv_row = next(csv.DictReader(StringIO(csv_export.text)))
    json_finding = exported.json()["findings"][0]
    assert csv_row["collection_created_at"] == exported.json()["collection"]["created_at"]
    assert csv_row["collection_updated_at"] == exported.json()["collection"]["updated_at"]
    assert csv_row["perceptual_hash"] == json_finding["perceptual_hash"]
    assert csv_row["caption_length_spread"] == str(json_finding["caption_length_spread"])


def test_collection_export_keeps_saved_findings_without_analysis_rows(tmp_path: Path):
    client = prepared_client(tmp_path)
    data_dir = tmp_path / "data"
    sample_id = client.get("/api/samples").json()["items"][0]["id"]
    collection = client.post("/api/collections", json={"name": "Legacy evidence"}).json()
    client.post(
        f"/api/collections/{collection['id']}/findings",
        json={"sample_id": sample_id, "tags": ["legacy"], "note": "Keep this note."},
    )
    with connect(data_dir) as connection:
        connection.execute("DELETE FROM sample_analysis WHERE sample_id = ?", (sample_id,))
        connection.commit()

    response = client.get(f"/api/collections/{collection['id']}/export?format=json")

    assert response.status_code == 200
    assert len(response.json()["findings"]) == 1
    assert response.json()["findings"][0]["sample_id"] == sample_id
    assert response.json()["findings"][0]["perceptual_hash"] is None


def test_missing_resources_and_invalid_write_payloads_use_http_errors(tmp_path: Path):
    client = prepared_client(tmp_path)

    missing_sample = client.get("/api/samples/missing/analysis")
    missing_collection = client.post(
        "/api/collections/999/findings",
        json={"sample_id": "missing", "tags": [], "note": ""},
    )
    missing_finding = client.delete("/api/findings/999")
    invalid_collection = client.post("/api/collections", json={"name": ""})
    invalid_finding = client.post(
        "/api/collections/1/findings",
        json={"sample_id": "sample", "tags": [str(index) for index in range(9)]},
    )

    assert missing_sample.status_code == 404
    assert missing_sample.json() == {"detail": "Sample not found"}
    assert missing_collection.status_code == 404
    assert missing_collection.json() == {"detail": "Collection not found"}
    assert missing_finding.status_code == 404
    assert missing_finding.json() == {"detail": "Finding not found"}
    assert invalid_collection.status_code == 422
    assert invalid_finding.status_code == 422


def test_research_routes_are_typed_and_cors_allows_writes(tmp_path: Path):
    client = TestClient(create_app(data_dir=tmp_path))

    openapi = client.get("/openapi.json").json()
    preflight = client.options(
        "/api/collections",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert openapi["paths"]["/api/radar"]["get"]["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/RadarResponse"
    }
    assert openapi["paths"]["/api/collections"]["post"]["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/CreateCollectionRequest"
    }
    assert preflight.status_code == 200
    assert "POST" in preflight.headers["access-control-allow-methods"]
    assert "DELETE" in preflight.headers["access-control-allow-methods"]

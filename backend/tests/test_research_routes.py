from pathlib import Path

from fastapi.testclient import TestClient

from app.importer import import_shards
from app.main import create_app
from tests.fixtures import write_fixture_shard


def prepared_client(tmp_path: Path) -> TestClient:
    shard = write_fixture_shard(tmp_path / "train.parquet")
    data_dir = tmp_path / "data"
    import_shards({"train": [shard]}, data_dir)
    return TestClient(create_app(data_dir=data_dir))


def test_radar_returns_ranked_outliers(tmp_path: Path):
    client = prepared_client(tmp_path)

    response = client.get("/api/radar")

    assert response.status_code == 200
    payload = response.json()
    assert payload["outliers"][0]["disagreement_score"] >= 0
    assert payload["summary"]["sample_count"] == 2
    assert sum(bucket["sample_count"] for bucket in payload["distribution"]) == 2


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
    assert csv_export.status_code == 200
    assert csv_export.headers["content-disposition"] == 'attachment; filename="ambiguity.csv"'
    assert "Different verbs" in csv_export.text


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

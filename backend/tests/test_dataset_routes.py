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


def test_samples_filters_by_caption_text_and_returns_a_paginated_summary(tmp_path: Path):
    client = prepared_client(tmp_path)

    response = client.get("/api/samples", params={"q": "rests", "split": "train"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["caption_preview"] == "A dog rests."
    assert payload["items"][0]["width"] == 6


def test_sample_detail_and_image_endpoint_return_local_imported_content(tmp_path: Path):
    client = prepared_client(tmp_path)
    sample_id = client.get("/api/samples", params={"q": "rests"}).json()["items"][0]["id"]

    detail = client.get(f"/api/samples/{sample_id}")
    image = client.get(f"/api/samples/{sample_id}/image")

    assert detail.status_code == 200
    assert detail.json()["sample"]["captions"][0] == "A dog rests."
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"


def test_overview_reports_local_split_and_caption_distribution(tmp_path: Path):
    client = prepared_client(tmp_path)

    response = client.get("/api/overview")

    assert response.status_code == 200
    assert response.json()["splits"] == [{"name": "train", "sample_count": 2}]
    assert response.json()["captions"]["total"] == 10

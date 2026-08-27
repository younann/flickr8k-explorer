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


def test_samples_page_two_returns_a_different_slice(tmp_path: Path):
    client = prepared_client(tmp_path)

    first_page = client.get("/api/samples", params={"page": 1, "page_size": 1})
    second_page = client.get("/api/samples", params={"page": 2, "page_size": 1})

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert first_page.json()["items"][0]["id"] != second_page.json()["items"][0]["id"]
    assert second_page.json()["page"] == 2
    assert second_page.json()["page_size"] == 1


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


def test_overview_reports_aspect_ratio_bins_that_total_all_samples(tmp_path: Path):
    client = prepared_client(tmp_path)

    response = client.get("/api/overview")

    assert response.status_code == 200
    bins = response.json()["aspect_ratio_bins"]
    assert [bin["name"] for bin in bins] == ["portrait", "square", "landscape"]
    assert sum(bin["sample_count"] for bin in bins) == 2
    assert bins == [
        {"name": "portrait", "sample_count": 0},
        {"name": "square", "sample_count": 0},
        {"name": "landscape", "sample_count": 2},
    ]


def test_missing_data_response_uses_the_documented_error_contract(tmp_path: Path):
    client = TestClient(create_app(data_dir=tmp_path))

    response = client.get("/api/overview")
    openapi = client.get("/openapi.json").json()

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Dataset is not imported. Run python scripts/import_dataset.py --download."
    }
    assert openapi["paths"]["/api/overview"]["get"]["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/OverviewResponse"
    }
    assert openapi["paths"]["/api/overview"]["get"]["responses"]["409"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorResponse"
    }


def test_sample_routes_declare_typed_response_models(tmp_path: Path):
    client = TestClient(create_app(data_dir=tmp_path))

    paths = client.get("/openapi.json").json()["paths"]

    assert paths["/api/samples"]["get"]["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SamplePage"
    }
    assert paths["/api/samples/{sample_id}"]["get"]["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SampleDetailResponse"
    }

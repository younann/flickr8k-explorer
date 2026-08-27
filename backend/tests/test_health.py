from fastapi.testclient import TestClient

from app.main import create_app


def test_health_reports_dataset_not_ready_for_an_empty_data_directory(tmp_path):
    client = TestClient(create_app(data_dir=tmp_path))

    response = client.get("/api/health")
    openapi = client.get("/openapi.json").json()

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "dataset_ready": False}
    assert openapi["paths"]["/api/health"]["get"]["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HealthResponse"
    }

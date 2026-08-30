from pathlib import Path

from fastapi.testclient import TestClient

from app.db import connect
from app.main import create_app


def test_health_reports_dataset_not_ready_for_an_empty_data_directory(tmp_path):
    client = TestClient(create_app(data_dir=tmp_path))

    response = client.get("/api/health")
    openapi = client.get("/openapi.json").json()

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "dataset_ready": False, "analysis_ready": False}
    assert openapi["paths"]["/api/health"]["get"]["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HealthResponse"
    }


def test_startup_migrates_a_v1_database_and_reports_analysis_backfill_needed(tmp_path):
    with connect(tmp_path) as connection:
        connection.executescript((Path(__file__).parents[1] / "app" / "migrations" / "001_initial.sql").read_text())
        connection.execute("CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
        connection.execute("INSERT INTO schema_migrations (version, applied_at) VALUES (1, CURRENT_TIMESTAMP)")
        connection.execute(
            """INSERT INTO samples (id, split, source_shard, source_row, image_path, media_type, width, height, aspect_ratio)
            VALUES ('legacy', 'train', 'legacy.parquet', 0, 'legacy.png', 'image/png', 1, 1, 1)"""
        )
        connection.execute("INSERT INTO captions (sample_id, position, text, word_count) VALUES ('legacy', 0, 'Legacy sample', 2)")
        connection.commit()

    client = TestClient(create_app(data_dir=tmp_path), raise_server_exceptions=False)

    assert client.get("/api/health").json() == {"status": "ok", "dataset_ready": True, "analysis_ready": False}
    radar = client.get("/api/radar")
    assert radar.status_code == 200
    assert radar.json()["summary"]["sample_count"] == 0

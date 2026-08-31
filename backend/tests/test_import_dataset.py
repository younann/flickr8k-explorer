from pathlib import Path

import pyarrow.parquet as pq

import app.analysis as analysis_module
import app.importer as importer_module
import app.repository as repository_module
from app.analysis import CURRENT_ANALYSIS_VERSION
from app.db import connect
from app.importer import import_shards
from app.repository import DatasetRepository
from tests.fixtures import write_fixture_shard


def test_import_creates_one_sample_per_parquet_row_and_five_captions(tmp_path: Path):
    shard = write_fixture_shard(tmp_path / "train.parquet")

    report = import_shards({"train": [shard]}, tmp_path / "data")

    assert report.samples_imported == 2
    assert report.captions_imported == 10
    assert (tmp_path / "data" / "flickr8k.sqlite").is_file()
    assert len(list((tmp_path / "data" / "images").glob("*.png"))) == 2


def test_second_import_of_the_same_shard_does_not_duplicate_rows(tmp_path: Path):
    shard = write_fixture_shard(tmp_path / "train.parquet")

    import_shards({"train": [shard]}, tmp_path / "data")
    report = import_shards({"train": [shard]}, tmp_path / "data")

    assert report.samples_imported == 0
    assert report.captions_imported == 0


def test_import_persists_analysis_for_each_sample(tmp_path: Path):
    shard = write_fixture_shard(tmp_path / "train.parquet")
    data_dir = tmp_path / "data"

    import_shards({"train": [shard]}, data_dir)

    with connect(data_dir) as connection:
        rows = connection.execute(
            "SELECT disagreement_score, perceptual_hash FROM sample_analysis ORDER BY sample_id"
        ).fetchall()

    assert len(rows) == 2
    assert all(row["disagreement_score"] >= 0 for row in rows)
    assert all(len(row["perceptual_hash"]) == 16 for row in rows)
    assert all(int(row["perceptual_hash"], 16) >= 0 for row in rows)


def test_reimport_backfills_analysis_without_touching_findings(tmp_path: Path):
    shard = write_fixture_shard(tmp_path / "train.parquet")
    data_dir = tmp_path / "data"
    import_shards({"train": [shard]}, data_dir)

    with connect(data_dir) as connection:
        sample_id = connection.execute("SELECT id FROM samples ORDER BY id LIMIT 1").fetchone()["id"]
        connection.execute("UPDATE sample_analysis SET disagreement_score = -1")
        collection_id = connection.execute(
            "INSERT INTO collections (name) VALUES ('Review queue')"
        ).lastrowid
        finding_id = connection.execute(
            "INSERT INTO findings (collection_id, sample_id, tags, note) VALUES (?, ?, ?, ?)",
            (collection_id, sample_id, '[\"review\"]', "Keep this finding."),
        ).lastrowid
        connection.commit()

    report = import_shards({"train": [shard]}, data_dir)

    with connect(data_dir) as connection:
        analysis = connection.execute(
            "SELECT disagreement_score FROM sample_analysis WHERE sample_id = ?", (sample_id,)
        ).fetchone()
        finding = connection.execute(
            "SELECT collection_id, sample_id, tags, note FROM findings WHERE id = ?", (finding_id,)
        ).fetchone()

    assert report.samples_imported == 0
    assert report.captions_imported == 0
    assert analysis["disagreement_score"] >= 0
    assert dict(finding) == {
        "collection_id": collection_id,
        "sample_id": sample_id,
        "tags": '["review"]',
        "note": "Keep this finding.",
    }


def test_reimport_records_the_current_analysis_version(tmp_path: Path):
    shard = write_fixture_shard(tmp_path / "train.parquet")
    data_dir = tmp_path / "data"
    import_shards({"train": [shard]}, data_dir)

    with connect(data_dir) as connection:
        metadata_table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'analysis_metadata'"
        ).fetchone()
        assert metadata_table is not None
        connection.execute("DELETE FROM analysis_metadata WHERE key = 'analysis_version'")
        connection.commit()

    import_shards({"train": [shard]}, data_dir)

    with connect(data_dir) as connection:
        version = connection.execute(
            "SELECT value FROM analysis_metadata WHERE key = 'analysis_version'"
        ).fetchone()

    assert version["value"] == CURRENT_ANALYSIS_VERSION


def test_partial_reimport_after_an_analysis_upgrade_keeps_dataset_stale(tmp_path: Path, monkeypatch):
    shard = write_fixture_shard(tmp_path / "train.parquet")
    partial_shard = tmp_path / "partial.parquet"
    pq.write_table(pq.read_table(shard).slice(0, 1), partial_shard)
    data_dir = tmp_path / "data"
    import_shards({"train": [shard]}, data_dir)

    upgraded_version = "2"
    monkeypatch.setattr(analysis_module, "CURRENT_ANALYSIS_VERSION", upgraded_version)
    monkeypatch.setattr(importer_module, "CURRENT_ANALYSIS_VERSION", upgraded_version)
    monkeypatch.setattr(repository_module, "CURRENT_ANALYSIS_VERSION", upgraded_version)

    import_shards({"train": [partial_shard]}, data_dir)

    assert DatasetRepository(data_dir).analysis_ready is False


def test_analysis_readiness_rejects_a_stale_metadata_marker(tmp_path: Path):
    shard = write_fixture_shard(tmp_path / "train.parquet")
    data_dir = tmp_path / "data"
    import_shards({"train": [shard]}, data_dir)

    with connect(data_dir) as connection:
        connection.execute("UPDATE analysis_metadata SET value = '0' WHERE key = 'analysis_version'")
        connection.commit()

    assert DatasetRepository(data_dir).analysis_ready is False

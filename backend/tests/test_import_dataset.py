from pathlib import Path

from app.importer import import_shards
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

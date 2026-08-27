import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.import_dataset import download_shards, load_manifest


def write_manifest(path: Path, content: dict[str, object]) -> Path:
    path.write_text(json.dumps(content))
    return path


def test_load_manifest_preserves_each_declared_split_and_filename(tmp_path: Path):
    manifest = load_manifest(
        write_manifest(
            tmp_path / "dataset_manifest.json",
            {
                "repository": "example/flickr8k",
                "revision": "a" * 40,
                "splits": {
                    "train": ["data/train-00000.parquet"],
                    "validation": ["data/validation-00000.parquet"],
                },
            },
        )
    )

    assert manifest.repository == "example/flickr8k"
    assert manifest.revision == "a" * 40
    assert manifest.splits == {
        "train": ["data/train-00000.parquet"],
        "validation": ["data/validation-00000.parquet"],
    }


@pytest.mark.parametrize(
    "manifest_content",
    [
        {"revision": "a" * 40, "splits": {"train": ["data/train.parquet"]}},
        {"repository": "example/flickr8k", "splits": {"train": ["data/train.parquet"]}},
        {"repository": "example/flickr8k", "revision": "a" * 40},
    ],
)
def test_load_manifest_rejects_missing_required_fields(tmp_path: Path, manifest_content: dict[str, object]):
    manifest_path = write_manifest(tmp_path / "dataset_manifest.json", manifest_content)

    with pytest.raises(ValidationError):
        load_manifest(manifest_path)


def test_load_manifest_rejects_duplicate_filename_within_a_split(tmp_path: Path):
    manifest_path = write_manifest(
        tmp_path / "dataset_manifest.json",
        {
            "repository": "example/flickr8k",
            "revision": "a" * 40,
            "splits": {"train": ["data/train-00000.parquet", "data/train-00000.parquet"]},
        },
    )

    with pytest.raises(ValidationError, match="duplicate"):
        load_manifest(manifest_path)


def test_download_shards_requests_only_manifest_files_at_manifest_revision(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    manifest = load_manifest(
        write_manifest(
            tmp_path / "dataset_manifest.json",
            {
                "repository": "example/flickr8k",
                "revision": "a" * 40,
                "splits": {
                    "train": ["data/train-00000.parquet"],
                    "test": ["data/test-00000.parquet"],
                },
            },
        )
    )
    requests: list[dict[str, object]] = []

    def fake_download(**kwargs: object) -> str:
        requests.append(kwargs)
        return str(tmp_path / str(kwargs["filename"]))

    monkeypatch.setattr("scripts.import_dataset.hf_hub_download", fake_download)

    downloaded = download_shards(manifest, tmp_path / "raw")

    assert downloaded == {
        "train": [tmp_path / "data/train-00000.parquet"],
        "test": [tmp_path / "data/test-00000.parquet"],
    }
    assert requests == [
        {
            "repo_id": "example/flickr8k",
            "repo_type": "dataset",
            "revision": "a" * 40,
            "filename": "data/train-00000.parquet",
            "local_dir": tmp_path / "raw",
        },
        {
            "repo_id": "example/flickr8k",
            "repo_type": "dataset",
            "revision": "a" * 40,
            "filename": "data/test-00000.parquet",
            "local_dir": tmp_path / "raw",
        },
    ]

from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import hf_hub_download
from pydantic import BaseModel, Field, field_validator

from app.config import default_data_dir
from app.importer import import_shards

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "dataset_manifest.json"


class DatasetManifest(BaseModel):
    repository: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    splits: dict[str, list[str]] = Field(min_length=1)

    @field_validator("splits")
    @classmethod
    def validate_unique_filenames(cls, splits: dict[str, list[str]]) -> dict[str, list[str]]:
        for split, filenames in splits.items():
            if not split:
                raise ValueError("split names must not be empty")
            if not filenames:
                raise ValueError(f"split {split!r} must declare at least one filename")
            duplicates = {filename for filename in filenames if filenames.count(filename) > 1}
            if duplicates:
                duplicate_list = ", ".join(sorted(duplicates))
                raise ValueError(f"duplicate filenames declared for split {split!r}: {duplicate_list}")
        return splits


def load_manifest(path: Path) -> DatasetManifest:
    return DatasetManifest.model_validate_json(path.read_text())


def download_shards(manifest: DatasetManifest, raw_dir: Path) -> dict[str, list[Path]]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, list[Path]] = {}
    for split, filenames in manifest.splits.items():
        result[split] = []
        for filename in filenames:
            downloaded = hf_hub_download(
                repo_id=manifest.repository,
                filename=filename,
                repo_type="dataset",
                revision=manifest.revision,
                local_dir=raw_dir,
            )
            result[split].append(Path(downloaded))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and index Flickr8k locally")
    parser.add_argument("--data-dir", type=Path, default=default_data_dir())
    parser.add_argument("--download", action="store_true", help="Download missing Parquet shards from Hugging Face")
    arguments = parser.parse_args()
    raw_dir = arguments.data_dir / "raw"
    if not arguments.download:
        raise SystemExit("Pass --download to fetch the dataset into the selected local data directory.")
    manifest = load_manifest(MANIFEST_PATH)
    report = import_shards(download_shards(manifest, raw_dir), arguments.data_dir)
    print(f"Imported {report.samples_imported} samples and {report.captions_imported} captions into {arguments.data_dir}")


if __name__ == "__main__":
    main()

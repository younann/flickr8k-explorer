from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import hf_hub_download

from app.config import default_data_dir
from app.importer import import_shards

SHARDS = {
    "train": ["data/train-00000-of-00002-2f8f6bfa852eac4b.parquet", "data/train-00001-of-00002-2173151d8cd6c7fb.parquet"],
    "validation": ["data/validation-00000-of-00001-7025a2b596f14b7b.parquet"],
    "test": ["data/test-00000-of-00001-42a2661d12c73e48.parquet"],
}


def download_shards(raw_dir: Path) -> dict[str, list[Path]]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, list[Path]] = {}
    for split, filenames in SHARDS.items():
        result[split] = []
        for filename in filenames:
            downloaded = hf_hub_download("jxie/flickr8k", filename=filename, repo_type="dataset", local_dir=raw_dir)
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
    report = import_shards(download_shards(raw_dir), arguments.data_dir)
    print(f"Imported {report.samples_imported} samples and {report.captions_imported} captions into {arguments.data_dir}")


if __name__ == "__main__":
    main()

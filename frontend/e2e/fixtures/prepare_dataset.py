from __future__ import annotations

import os
import sys
from io import BytesIO
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.importer import import_shards


def image_bytes(index: int) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (4 + index % 3, 3 + index % 2), color=(index * 7 % 255, index * 13 % 255, index * 17 % 255)).save(buffer, format="PNG")
    return buffer.getvalue()


def prepare_fixture_dataset(data_dir: Path) -> None:
    shard = data_dir / "fixture.parquet"
    data_dir.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist([
        {
            "image": {"bytes": image_bytes(index), "path": f"fixture-dog-{index}.png"},
            "caption_0": f"Fixture dog {index} runs.",
            "caption_1": f"A local dog number {index} moves.",
            "caption_2": f"Dog fixture {index}.",
            "caption_3": f"A test animal {index}.",
            "caption_4": f"Fixture sample {index}.",
        }
        for index in range(1, 32)
    ]), shard)
    import_shards({"train": [shard]}, data_dir)


if __name__ == "__main__":
    configured_dir = os.environ.get("FLICKR8K_DATA_DIR")
    if not configured_dir:
        raise SystemExit("FLICKR8K_DATA_DIR must point to the local E2E fixture directory")
    prepare_fixture_dataset(Path(configured_dir))

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from PIL import Image


def write_fixture_shard(path: Path, *, split: str = "train") -> Path:
    image_buffer = BytesIO()
    Image.new("RGB", (4, 3), color=(22, 66, 88)).save(image_buffer, format="PNG")
    image_bytes = image_buffer.getvalue()
    second_image_buffer = BytesIO()
    Image.new("RGB", (6, 4), color=(99, 44, 20)).save(second_image_buffer, format="PNG")
    records = [
        {
            "image": {"bytes": image_bytes, "path": "blue-dog.png"},
            "caption_0": "A blue dog runs.",
            "caption_1": "A dog moves quickly.",
            "caption_2": "The dog is blue.",
            "caption_3": "A bright animal runs.",
            "caption_4": "Dog outdoors.",
        },
        {
            "image": {"bytes": second_image_buffer.getvalue(), "path": "resting-dog.png"},
            "caption_0": "A dog rests.",
            "caption_1": "The animal is still.",
            "caption_2": "Blue dog waits.",
            "caption_3": "A quiet dog.",
            "caption_4": "An animal waits.",
        },
    ]
    table = pa.Table.from_pylist(records)
    pq.write_table(table, path)
    return path

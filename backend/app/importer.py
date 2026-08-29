from __future__ import annotations

import hashlib
import mimetypes
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable

import pyarrow.parquet as pq
from PIL import Image

from app.analysis import caption_analysis, perceptual_hash
from app.db import connect, initialize

CAPTION_COLUMNS = tuple(f"caption_{index}" for index in range(5))


@dataclass(frozen=True)
class ImportReport:
    samples_imported: int
    captions_imported: int


def _image_extension(image: Image.Image, original_path: str | None) -> str:
    if original_path:
        suffix = Path(original_path).suffix.lower()
        if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
            return suffix
    return {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}.get(image.format or "", ".bin")


def _read_image(value: object) -> tuple[bytes, str | None]:
    if not isinstance(value, dict) or not isinstance(value.get("bytes"), bytes):
        raise ValueError("image must be a struct containing bytes")
    path = value.get("path")
    return value["bytes"], path if isinstance(path, str) else None


def import_shards(shards_by_split: dict[str, Iterable[Path]], data_dir: Path) -> ImportReport:
    data_dir.mkdir(parents=True, exist_ok=True)
    images_dir = data_dir / "images"
    images_dir.mkdir(exist_ok=True)
    connection = connect(data_dir)
    initialize(connection)
    samples_imported = 0
    captions_imported = 0
    try:
        for split, shard_paths in shards_by_split.items():
            for shard_path in shard_paths:
                parquet = pq.ParquetFile(shard_path)
                expected = {"image", *CAPTION_COLUMNS}
                if not expected.issubset(parquet.schema_arrow.names):
                    missing = sorted(expected.difference(parquet.schema_arrow.names))
                    raise ValueError(f"{shard_path} is missing required columns: {', '.join(missing)}")
                source_row = 0
                for batch in parquet.iter_batches(batch_size=256):
                    for row in batch.to_pylist():
                        image_bytes, original_path = _read_image(row["image"])
                        sample_id = hashlib.sha256(image_bytes).hexdigest()
                        with Image.open(BytesIO(image_bytes)) as image:
                            image.load()
                            width, height = image.size
                            extension = _image_extension(image, original_path)
                            media_type = mimetypes.types_map.get(extension, "application/octet-stream")
                            image_hash = f"{perceptual_hash(image):016x}"
                        image_path = images_dir / f"{sample_id}{extension}"
                        if not image_path.exists():
                            image_path.write_bytes(image_bytes)
                        captions = [
                            (sample_id, position, str(row[column]).strip(), len(str(row[column]).split()))
                            for position, column in enumerate(CAPTION_COLUMNS)
                        ]
                        inserted = connection.execute(
                            """INSERT OR IGNORE INTO samples
                            (id, split, source_shard, source_row, image_path, media_type, width, height, aspect_ratio)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (sample_id, split, shard_path.name, source_row, image_path.name, media_type, width, height, width / height),
                        ).rowcount
                        if inserted:
                            samples_imported += 1
                            connection.executemany(
                                "INSERT INTO captions (sample_id, position, text, word_count) VALUES (?, ?, ?, ?)",
                                captions,
                            )
                            connection.executemany(
                                "INSERT INTO caption_search (sample_id, text) VALUES (?, ?)",
                                [(sample_id, caption[2]) for caption in captions],
                            )
                            captions_imported += len(captions)
                        analysis = caption_analysis([caption[2] for caption in captions])
                        connection.execute(
                            """INSERT OR REPLACE INTO sample_analysis
                            (sample_id, disagreement_score, token_disagreement, vocabulary_diversity,
                             mean_caption_length, caption_length_spread, perceptual_hash)
                            VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (
                                sample_id,
                                analysis.disagreement_score,
                                analysis.token_disagreement,
                                analysis.vocabulary_diversity,
                                analysis.mean_caption_length,
                                analysis.caption_length_spread,
                                image_hash,
                            ),
                        )
                        source_row += 1
        connection.commit()
    finally:
        connection.close()
    return ImportReport(samples_imported=samples_imported, captions_imported=captions_imported)

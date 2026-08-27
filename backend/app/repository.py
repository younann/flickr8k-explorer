from __future__ import annotations

from pathlib import Path

from app.db import connect, database_path


def _terms(query: str) -> str:
    return " AND ".join(f'"{term.replace(chr(34), "")}"' for term in query.split() if term)


class DatasetRepository:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    @property
    def ready(self) -> bool:
        return database_path(self.data_dir).is_file()

    def samples(self, *, query: str = "", split: str | None = None, page: int = 1, page_size: int = 30) -> dict:
        where = []
        parameters: list[object] = []
        join = ""
        if query.strip():
            join = " JOIN (SELECT DISTINCT sample_id FROM caption_search WHERE caption_search MATCH ?) search ON search.sample_id = samples.id"
            parameters.append(_terms(query))
        if split:
            where.append("samples.split = ?")
            parameters.append(split)
        condition = f" WHERE {' AND '.join(where)}" if where else ""
        with connect(self.data_dir) as connection:
            total = connection.execute(f"SELECT COUNT(*) FROM samples{join}{condition}", parameters).fetchone()[0]
            rows = connection.execute(
                f"""SELECT samples.id, samples.split, samples.width, samples.height, captions.text
                FROM samples{join} JOIN captions ON captions.sample_id = samples.id AND captions.position = 0
                {condition} ORDER BY samples.source_shard, samples.source_row LIMIT ? OFFSET ?""",
                [*parameters, page_size, (page - 1) * page_size],
            ).fetchall()
        return {
            "items": [
                {"id": row["id"], "split": row["split"], "width": row["width"], "height": row["height"], "caption_preview": row["text"], "image_url": f"/api/samples/{row['id']}/image"}
                for row in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    def overview(self) -> dict:
        with connect(self.data_dir) as connection:
            splits = connection.execute("SELECT split AS name, COUNT(*) AS sample_count FROM samples GROUP BY split ORDER BY name").fetchall()
            captions = connection.execute("SELECT COUNT(*) AS total, ROUND(AVG(word_count), 1) AS mean_word_count FROM captions").fetchone()
            terms = connection.execute("""SELECT lower(value) AS term, COUNT(*) AS count
                FROM captions, json_each('["' || replace(replace(lower(text), '"', ''), ' ', '","') || '"]')
                WHERE length(value) > 3 GROUP BY lower(value) ORDER BY count DESC, term LIMIT 10""").fetchall()
            aspect_ratio_bins = connection.execute("""
                SELECT 'portrait' AS name, COUNT(*) AS sample_count FROM samples WHERE aspect_ratio < 1
                UNION ALL
                SELECT 'square' AS name, COUNT(*) AS sample_count FROM samples WHERE aspect_ratio = 1
                UNION ALL
                SELECT 'landscape' AS name, COUNT(*) AS sample_count FROM samples WHERE aspect_ratio > 1
            """).fetchall()
        return {
            "splits": [dict(row) for row in splits],
            "captions": {"total": captions["total"], "mean_word_count": captions["mean_word_count"], "top_terms": [dict(row) for row in terms]},
            "aspect_ratio_bins": [dict(row) for row in aspect_ratio_bins],
        }

    def detail(self, sample_id: str) -> dict | None:
        with connect(self.data_dir) as connection:
            sample = connection.execute("SELECT * FROM samples WHERE id = ?", (sample_id,)).fetchone()
            if sample is None:
                return None
            captions = connection.execute("SELECT text FROM captions WHERE sample_id = ? ORDER BY position", (sample_id,)).fetchall()
        return {
            "id": sample["id"], "split": sample["split"], "width": sample["width"], "height": sample["height"],
            "aspect_ratio": sample["aspect_ratio"], "captions": [row["text"] for row in captions],
            "image_url": f"/api/samples/{sample_id}/image",
        }

    def image(self, sample_id: str) -> tuple[Path, str] | None:
        with connect(self.data_dir) as connection:
            row = connection.execute("SELECT image_path, media_type FROM samples WHERE id = ?", (sample_id,)).fetchone()
        if row is None:
            return None
        path = self.data_dir / "images" / row["image_path"]
        return (path, row["media_type"]) if path.is_file() else None

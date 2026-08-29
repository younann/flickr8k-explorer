from __future__ import annotations

import json
from pathlib import Path
import re

from app.analysis import hamming_distance
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

    def radar(self, split: str | None = None) -> dict:
        condition = " WHERE samples.split = ?" if split else ""
        parameters: tuple[object, ...] = (split,) if split else ()
        source = "FROM sample_analysis JOIN samples ON samples.id = sample_analysis.sample_id"
        buckets = {name: 0 for name in ("0-19", "20-39", "40-59", "60-79", "80-100")}
        with connect(self.data_dir) as connection:
            summary = connection.execute(
                f"""SELECT COUNT(*) AS sample_count,
                    COALESCE(AVG(disagreement_score), 0) AS mean_disagreement_score,
                    COALESCE(AVG(token_disagreement), 0) AS mean_token_disagreement,
                    COALESCE(AVG(vocabulary_diversity), 0) AS mean_vocabulary_diversity
                    {source}{condition}""",
                parameters,
            ).fetchone()
            rows = connection.execute(
                f"""SELECT CASE
                    WHEN disagreement_score < 20 THEN '0-19'
                    WHEN disagreement_score < 40 THEN '20-39'
                    WHEN disagreement_score < 60 THEN '40-59'
                    WHEN disagreement_score < 80 THEN '60-79'
                    ELSE '80-100' END AS name,
                    COUNT(*) AS sample_count
                    {source}{condition} GROUP BY name""",
                parameters,
            ).fetchall()
            buckets.update({row["name"]: row["sample_count"] for row in rows})
            outliers = connection.execute(
                f"""SELECT samples.id, samples.split, samples.width, samples.height, captions.text,
                    sample_analysis.disagreement_score, sample_analysis.token_disagreement,
                    sample_analysis.vocabulary_diversity
                    {source} JOIN captions ON captions.sample_id = samples.id AND captions.position = 0
                    {condition} ORDER BY sample_analysis.disagreement_score DESC, samples.id LIMIT 10""",
                parameters,
            ).fetchall()
        return {
            "distribution": [{"name": name, "sample_count": count} for name, count in buckets.items()],
            "summary": dict(summary),
            "outliers": [
                {
                    "id": row["id"], "split": row["split"], "width": row["width"], "height": row["height"],
                    "caption_preview": row["text"], "image_url": f"/api/samples/{row['id']}/image",
                    "disagreement_score": row["disagreement_score"], "token_disagreement": row["token_disagreement"],
                    "vocabulary_diversity": row["vocabulary_diversity"],
                }
                for row in outliers
            ],
        }

    def analysis(self, sample_id: str) -> dict | None:
        with connect(self.data_dir) as connection:
            row = connection.execute("SELECT * FROM sample_analysis WHERE sample_id = ?", (sample_id,)).fetchone()
            if row is None:
                return None
            captions = connection.execute(
                "SELECT text FROM captions WHERE sample_id = ? ORDER BY position", (sample_id,)
            ).fetchall()
        token_counts: dict[str, int] = {}
        for caption in captions:
            for token in set(re.findall(r"[a-z]+", caption["text"].lower())):
                token_counts[token] = token_counts.get(token, 0) + 1
        return {
            **dict(row),
            "differing_tokens": sorted(token for token, count in token_counts.items() if count < len(captions)),
        }

    def similar(self, sample_id: str, limit: int = 6) -> list[dict]:
        limit = max(0, min(limit, 6))
        with connect(self.data_dir) as connection:
            selected = connection.execute(
                "SELECT perceptual_hash FROM sample_analysis WHERE sample_id = ?", (sample_id,)
            ).fetchone()
            if selected is None:
                return []
            rows = connection.execute(
                """SELECT samples.id, samples.split, samples.width, samples.height, captions.text,
                    sample_analysis.perceptual_hash
                    FROM sample_analysis JOIN samples ON samples.id = sample_analysis.sample_id
                    JOIN captions ON captions.sample_id = samples.id AND captions.position = 0
                    WHERE sample_analysis.sample_id != ?""",
                (sample_id,),
            ).fetchall()
        selected_hash = int(selected["perceptual_hash"], 16)
        neighbors = [
            {
                "id": row["id"], "split": row["split"], "width": row["width"], "height": row["height"],
                "caption_preview": row["text"], "image_url": f"/api/samples/{row['id']}/image",
                "distance": hamming_distance(selected_hash, int(row["perceptual_hash"], 16)),
            }
            for row in rows
        ]
        return sorted(neighbors, key=lambda neighbor: (neighbor["distance"], neighbor["id"]))[:limit]

    def collections(self) -> list[dict]:
        with connect(self.data_dir) as connection:
            rows = connection.execute(
                """SELECT collections.*, COUNT(findings.id) AS finding_count FROM collections
                    LEFT JOIN findings ON findings.collection_id = collections.id
                    GROUP BY collections.id ORDER BY collections.created_at DESC, collections.id DESC"""
            ).fetchall()
        return [dict(row) for row in rows]

    def collection(self, collection_id: int) -> dict | None:
        with connect(self.data_dir) as connection:
            row = connection.execute(
                """SELECT collections.*, COUNT(findings.id) AS finding_count FROM collections
                    LEFT JOIN findings ON findings.collection_id = collections.id
                    WHERE collections.id = ? GROUP BY collections.id""",
                (collection_id,),
            ).fetchone()
        return dict(row) if row else None

    def create_collection(self, name: str) -> dict:
        with connect(self.data_dir) as connection:
            collection_id = connection.execute("INSERT INTO collections (name) VALUES (?)", (name,)).lastrowid
            connection.commit()
        collection = self.collection(collection_id)
        assert collection is not None
        return collection

    def findings(self, collection_id: int) -> list[dict]:
        with connect(self.data_dir) as connection:
            rows = connection.execute(
                "SELECT * FROM findings WHERE collection_id = ? ORDER BY created_at DESC, id DESC", (collection_id,)
            ).fetchall()
        return [self._finding_dict(row) for row in rows]

    def finding(self, finding_id: int) -> dict | None:
        with connect(self.data_dir) as connection:
            row = connection.execute("SELECT * FROM findings WHERE id = ?", (finding_id,)).fetchone()
        return self._finding_dict(row) if row else None

    def create_finding(self, collection_id: int, sample_id: str, tags: str, note: str) -> dict:
        with connect(self.data_dir) as connection:
            finding_id = connection.execute(
                "INSERT INTO findings (collection_id, sample_id, tags, note) VALUES (?, ?, ?, ?)",
                (collection_id, sample_id, tags, note),
            ).lastrowid
            connection.commit()
        finding = self.finding(finding_id)
        assert finding is not None
        return finding

    def delete_collection(self, collection_id: int) -> bool:
        with connect(self.data_dir) as connection:
            cursor = connection.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
            connection.commit()
        return cursor.rowcount == 1

    def delete_finding(self, finding_id: int) -> bool:
        with connect(self.data_dir) as connection:
            cursor = connection.execute("DELETE FROM findings WHERE id = ?", (finding_id,))
            connection.commit()
        return cursor.rowcount == 1

    def collection_export(self, collection_id: int) -> list[dict]:
        with connect(self.data_dir) as connection:
            rows = connection.execute(
                """SELECT findings.*, samples.split, samples.width, samples.height,
                    sample_analysis.disagreement_score, sample_analysis.token_disagreement,
                    sample_analysis.vocabulary_diversity, sample_analysis.mean_caption_length,
                    sample_analysis.caption_length_spread
                    FROM findings JOIN samples ON samples.id = findings.sample_id
                    JOIN sample_analysis ON sample_analysis.sample_id = findings.sample_id
                    WHERE findings.collection_id = ? ORDER BY findings.created_at DESC, findings.id DESC""",
                (collection_id,),
            ).fetchall()
            exported = []
            for row in rows:
                captions = connection.execute(
                    "SELECT text FROM captions WHERE sample_id = ? ORDER BY position", (row["sample_id"],)
                ).fetchall()
                exported.append({**self._finding_dict(row), **{
                    "split": row["split"], "width": row["width"], "height": row["height"],
                    "captions": [caption["text"] for caption in captions],
                    "disagreement_score": row["disagreement_score"], "token_disagreement": row["token_disagreement"],
                    "vocabulary_diversity": row["vocabulary_diversity"], "mean_caption_length": row["mean_caption_length"],
                    "caption_length_spread": row["caption_length_spread"],
                }})
        return exported

    @staticmethod
    def _finding_dict(row: object) -> dict:
        data = dict(row)
        data["tags"] = json.loads(data["tags"])
        return data

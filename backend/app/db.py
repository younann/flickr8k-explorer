from __future__ import annotations

import sqlite3
from pathlib import Path


def database_path(data_dir: Path) -> Path:
    return data_dir / "flickr8k.sqlite"


def connect(data_dir: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path(data_dir))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(connection: sqlite3.Connection) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"
    connection.executescript(schema_path.read_text())

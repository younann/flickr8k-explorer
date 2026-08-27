from __future__ import annotations

import sqlite3
from pathlib import Path
import re


def database_path(data_dir: Path) -> Path:
    return data_dir / "flickr8k.sqlite"


def connect(data_dir: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path(data_dir))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(connection: sqlite3.Connection) -> None:
    connection.execute(
        """CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        applied_at TEXT NOT NULL
        )"""
    )
    applied_versions = {
        row[0] for row in connection.execute("SELECT version FROM schema_migrations")
    }

    migrations: list[tuple[int, Path]] = []
    for path in (Path(__file__).parent / "migrations").glob("*.sql"):
        match = re.match(r"^(\d+)_.*\.sql$", path.name)
        if match:
            migrations.append((int(match.group(1)), path))
    migrations.sort(key=lambda migration: migration[0])

    for version, path in migrations:
        if version in applied_versions:
            continue
        savepoint = f"migration_{version}"
        connection.execute(f"SAVEPOINT {savepoint}")
        try:
            _execute_sql_script(connection, path.read_text())
            connection.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, CURRENT_TIMESTAMP)",
                (version,),
            )
        except Exception:
            connection.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
            connection.execute(f"RELEASE SAVEPOINT {savepoint}")
            raise
        else:
            connection.execute(f"RELEASE SAVEPOINT {savepoint}")


def _execute_sql_script(connection: sqlite3.Connection, script: str) -> None:
    statement = ""
    for line in script.splitlines(keepends=True):
        statement += line
        if sqlite3.complete_statement(statement):
            connection.execute(statement)
            statement = ""
    if statement.strip():
        connection.execute(statement)

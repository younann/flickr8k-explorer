from app.db import connect, initialize


def test_initialize_applies_each_schema_migration_once(tmp_path):
    connection = connect(tmp_path)
    initialize(connection)
    initialize(connection)

    versions = connection.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
    tables = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'samples'").fetchall()

    assert [row["version"] for row in versions] == [1]
    assert [row["name"] for row in tables] == ["samples"]

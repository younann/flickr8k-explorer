CREATE TABLE IF NOT EXISTS samples (
    id TEXT PRIMARY KEY,
    split TEXT NOT NULL,
    source_shard TEXT NOT NULL,
    source_row INTEGER NOT NULL,
    image_path TEXT NOT NULL,
    media_type TEXT NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    aspect_ratio REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS captions (
    sample_id TEXT NOT NULL REFERENCES samples(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    text TEXT NOT NULL,
    word_count INTEGER NOT NULL,
    PRIMARY KEY (sample_id, position)
);

CREATE INDEX IF NOT EXISTS samples_split_idx ON samples(split);
CREATE INDEX IF NOT EXISTS samples_dimensions_idx ON samples(width, height);
CREATE INDEX IF NOT EXISTS captions_word_count_idx ON captions(word_count);

CREATE VIRTUAL TABLE IF NOT EXISTS caption_search USING fts5(
    sample_id UNINDEXED,
    text
);

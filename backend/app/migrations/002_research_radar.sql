CREATE TABLE sample_analysis (
    sample_id TEXT PRIMARY KEY REFERENCES samples(id) ON DELETE CASCADE,
    disagreement_score INTEGER NOT NULL,
    token_disagreement REAL NOT NULL,
    vocabulary_diversity REAL NOT NULL,
    mean_caption_length REAL NOT NULL,
    caption_length_spread REAL NOT NULL,
    perceptual_hash TEXT NOT NULL
);

CREATE INDEX sample_analysis_score_idx ON sample_analysis(disagreement_score DESC);

CREATE TABLE collections (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE findings (
    id INTEGER PRIMARY KEY,
    collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    sample_id TEXT NOT NULL REFERENCES samples(id) ON DELETE CASCADE,
    tags TEXT NOT NULL DEFAULT '[]',
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX findings_collection_id_idx ON findings(collection_id);
CREATE INDEX findings_sample_id_idx ON findings(sample_id);

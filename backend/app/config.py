from __future__ import annotations

import os
from pathlib import Path


def default_data_dir() -> Path:
    configured_path = os.environ.get("FLICKR8K_DATA_DIR")
    if configured_path:
        return Path(configured_path).expanduser().resolve()
    return Path(__file__).resolve().parents[2] / "data"

"""JSON export helpers."""

from __future__ import annotations

import json
from pathlib import Path


def export_json_to_path(payload: dict, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return destination


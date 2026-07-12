"""
Append-only log of past `shai ask` requests, stored one JSON object per line
so it stays trivially greppable and never needs a rewrite to append to.
"""
import json
import os
from pathlib import Path
from typing import List, Optional

HISTORY_DIR = Path(os.getenv("SHAI_DATA_DIR", Path.home() / ".local" / "share" / "shai"))
HISTORY_FILE = HISTORY_DIR / "history.jsonl"


def append(entry: dict) -> None:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def load(limit: Optional[int] = None) -> List[dict]:
    if not HISTORY_FILE.exists():
        return []
    entries = []
    for line in HISTORY_FILE.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # skip a corrupted line rather than fail the whole read
    return entries[-limit:] if limit else entries


def clear() -> None:
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()

"""Recent translated-video results, stored as receipts without media or secrets."""

import json
import os
import tempfile
import time
from pathlib import Path
from typing import List, Optional

MAX_ENTRIES = 20

# Only receipt fields that describe files and languages are kept.
_KEPT_FIELDS = (
    "subtitle_type", "video_path", "subtitle_paths", "audio_paths", "target_dir",
    "source_video", "source_sub", "target_sub", "source_language_code",
    "target_language_code", "target_language", "output_srt", "video_autorate",
    "bilingual_order", "soft_track_requires_player",
)


def default_history_path() -> Path:
    from videotrans.configure.config import ROOT_DIR

    return Path(ROOT_DIR) / "videotrans" / "result_history.json"


def _sanitize(receipt: dict) -> dict:
    entry = {key: receipt[key] for key in _KEPT_FIELDS if key in receipt}
    entry["finished_at"] = receipt.get("finished_at") or int(time.time())
    return entry


def load_history(path: Optional[Path] = None) -> List[dict]:
    """Return stored entries, newest first; a corrupt file is reset to empty."""
    path = Path(path or default_history_path())
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        try:
            from videotrans.configure.config import logger
            logger.warning(f"Result history is unreadable and was reset: {path}")
        except Exception:
            pass
        _write(path, [])
        return []
    if not isinstance(data, list):
        _write(path, [])
        return []
    return [entry for entry in data if isinstance(entry, dict) and entry.get("video_path")]


def recent_results(path: Optional[Path] = None) -> List[dict]:
    """Entries whose output video still exists."""
    return [entry for entry in load_history(path) if Path(entry["video_path"]).is_file()]


def append_results(receipts, path: Optional[Path] = None) -> List[dict]:
    """Add receipts at the front, de-duplicated by video path and capped."""
    path = Path(path or default_history_path())
    entries = load_history(path)
    for receipt in receipts:
        if not isinstance(receipt, dict) or not receipt.get("video_path"):
            continue
        entry = _sanitize(receipt)
        entries = [item for item in entries if item.get("video_path") != entry["video_path"]]
        entries.insert(0, entry)
    entries = entries[:MAX_ENTRIES]
    _write(path, entries)
    return entries


def _write(path: Path, entries: List[dict]):
    """Atomic replace so a crash never leaves a half-written history file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".result_history-", suffix=".json", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(entries, handle, ensure_ascii=False, indent=2)
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise

"""Shared helpers for autonomy tooling."""
from __future__ import annotations

import importlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


_RECEIPT_TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def load_json(path: Path) -> Any:
    """Read JSON from *path*, returning ``None`` when missing or invalid."""

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def normalise_layer(value: str | None, *, default: str = "L5") -> str:
    """Return canonical layer code (``L0``–``L6``) with fallback."""

    if not value:
        return default
    val = value.strip().upper()
    if val.startswith("L") and val[1:].isdigit():
        return val
    return default


def normalise_scale(value: Any, layer: str, *, lower: int = 1, upper: int = 10) -> int:
    """Normalise systemic scale (1–10) using *layer* as a hint."""

    if isinstance(value, int) and lower <= value <= upper:
        return value
    try:
        layer_num = int(layer[1:]) if layer.startswith("L") else 5
    except ValueError:
        layer_num = 5
    return max(lower, min(upper, 4 + layer_num))


def utc_timestamp() -> str:
    """Return current UTC timestamp compatible with receipt payloads."""

    return datetime.now(timezone.utc).strftime(_RECEIPT_TS_FORMAT)


def git_commit(root: Path) -> str | None:
    """Return short git commit hash for *root*, or ``None`` when unavailable."""

    head = root / ".git" / "HEAD"
    if not head.exists():
        return None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return None
    commit = result.stdout.strip()
    return commit or None


def count_lines(path: Path) -> int:
    """Count text lines in *path*, returning ``0`` when missing or unreadable."""

    count = 0
    try:
        with path.open(encoding="utf-8") as handle:
            for count, _ in enumerate(handle, 1):
                pass
    except (FileNotFoundError, OSError):
        return 0
    return count


def backlog_archive_path(path: Path) -> Path:
    """Return companion archive path for a backlog file."""

    name = path.name
    if name.endswith(".todo.json"):
        archive_name = name.replace(".todo.json", ".archive.json")
    elif name.endswith(".json"):
        archive_name = f"{name[:-5]}.archive.json"
    else:
        archive_name = f"{name}.archive.json"
    return path.with_name(archive_name)


def load_backlog_items(path: Path, *, include_archive: bool = False) -> list[dict[str, Any]]:
    """Return backlog items from *path*; optionally include archived entries."""

    def _normalise(payload: Any) -> list[dict[str, Any]]:
        if not isinstance(payload, dict):
            return []
        entries = payload.get("items")
        return [item for item in entries if isinstance(item, dict)] if isinstance(entries, list) else []

    data = load_json(path)
    items = _normalise(data)
    if not include_archive:
        return items

    archive = load_json(backlog_archive_path(path))
    archive_items = _normalise(archive)
    return items + archive_items


def load_task_items(path: Path) -> list[dict[str, Any]]:
    """Return task dictionaries from *path* (empty list when missing)."""

    data = load_json(path)
    tasks = data.get("tasks") if isinstance(data, dict) else None
    return [task for task in tasks if isinstance(task, dict)] if tasks else []


def load_state_facts(path: Path) -> list[dict[str, Any]]:
    """Return fact dictionaries from *path* (empty list when missing)."""

    data = load_json(path)
    facts = data.get("facts") if isinstance(data, dict) else None
    return [fact for fact in facts if isinstance(fact, dict)] if facts else []


def atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> Path:
    """Write *text* to *path* atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = None
    temp_path: Path | None = None
    try:
        descriptor, temp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.tmp")
        temp_path = Path(temp_name)
        with os.fdopen(descriptor, "w", encoding=encoding) as handle:
            handle.write(text)
        os.replace(temp_name, path)
    except Exception:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        raise
    return path


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    """Write JSON payload atomically with UTF-8 encoding."""

    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    return atomic_write_text(path, text)


def write_receipt_payload(out_path: Path, payload: Mapping[str, Any]) -> Path:
    """Persist *payload* as a receipt, appending ``receipt_sha256`` checksum."""

    _hashlib = importlib.import_module("hashlib")
    data = dict(payload)
    base_json = json.dumps(data, ensure_ascii=False, indent=2)
    checksum = _hashlib.sha256(base_json.encode("utf-8")).hexdigest()
    data["receipt_sha256"] = checksum
    return atomic_write_json(out_path, data)


__all__ = [
    "load_json",
    "normalise_layer",
    "normalise_scale",
    "utc_timestamp",
    "git_commit",
    "count_lines",
    "backlog_archive_path",
    "load_backlog_items",
    "load_task_items",
    "load_state_facts",
    "write_receipt_payload",
    "atomic_write_json",
    "atomic_write_text",
]

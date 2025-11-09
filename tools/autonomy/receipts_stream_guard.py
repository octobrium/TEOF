"""Verify receipts stream pointer freshness/integrity."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POINTER = ROOT / "_report" / "usage" / "receipts-index" / "latest.json"
DEFAULT_MAX_AGE_HOURS = 24.0
MODULE_NAME = "tools.autonomy.receipts_stream_guard"


class GuardError(RuntimeError):
    """Raised when the receipts stream violates CI requirements."""


def _resolve_repo_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _load_json(path: Path, label: str) -> Mapping[str, object]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:  # pragma: no cover - surfaced via GuardError
        raise GuardError(f"{label}: missing file {path}") from exc
    except OSError as exc:  # pragma: no cover - surfaced via GuardError
        raise GuardError(f"{label}: unable to read {path}: {exc}") from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GuardError(f"{label}: invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise GuardError(f"{label}: expected JSON object in {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_iso(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rel_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _emit_receipt(path: Path, payload: Mapping[str, object]) -> None:
    target = path if path.is_absolute() else ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _determine_timestamp(pointer: Mapping[str, object], manifest: Mapping[str, object]) -> datetime | None:
    return _parse_iso(manifest.get("last_timestamp")) or _parse_iso(manifest.get("generated_at")) or _parse_iso(pointer.get("generated_at"))


def verify(pointer: Path | None = None, *, max_age_hours: float | None = DEFAULT_MAX_AGE_HOURS) -> tuple[str, dict[str, object]]:
    pointer_path = _resolve_repo_path(pointer or DEFAULT_POINTER)
    pointer_payload = _load_json(pointer_path, "pointer")
    latest = pointer_payload.get("latest")
    if not isinstance(latest, str) or not latest.strip():
        raise GuardError("pointer missing 'latest' shard path")
    shard_path = _resolve_repo_path(Path(latest))
    if not shard_path.exists():
        raise GuardError(f"shard missing: {shard_path}")
    pointer_sha = pointer_payload.get("sha256")
    if not isinstance(pointer_sha, str) or len(pointer_sha) != 64:
        raise GuardError("pointer missing sha256 hash for latest shard")
    computed_sha = _sha256(shard_path)
    if computed_sha != pointer_sha:
        raise GuardError(f"hash mismatch for shard {shard_path.name}")

    manifest_path = shard_path.with_suffix(".manifest.json")
    if not manifest_path.exists():
        raise GuardError(f"manifest missing for shard {shard_path.name}")
    manifest = _load_json(manifest_path, "manifest")
    manifest_sha = manifest.get("sha256")
    if manifest_sha != pointer_sha:
        raise GuardError("manifest sha256 does not match pointer hash")

    pointer_seq = pointer_payload.get("sequence")
    manifest_seq = manifest.get("sequence")
    if isinstance(pointer_seq, int) and isinstance(manifest_seq, int) and pointer_seq != manifest_seq:
        raise GuardError(f"sequence mismatch between pointer ({pointer_seq}) and manifest ({manifest_seq})")

    timestamp = _determine_timestamp(pointer_payload, manifest)
    if timestamp is None:
        raise GuardError("unable to determine latest shard timestamp")

    now = datetime.now(timezone.utc)
    age_hours = (now - timestamp).total_seconds() / 3600
    if max_age_hours is not None and max_age_hours > 0 and age_hours > max_age_hours:
        raise GuardError(f"shard stale: age {age_hours:.1f}h exceeds {max_age_hours:.1f}h threshold")

    age_str = f"{age_hours:.1f}h"
    seq_display = manifest_seq if isinstance(manifest_seq, int) else "?"
    message = f"receipts_stream_guard: shard {shard_path.name} ok (seq={seq_display}, age={age_str})"
    context = {
        "module": MODULE_NAME,
        "generated_at": _iso_now(),
        "status": "ok",
        "message": message,
        "pointer": _rel_path(pointer_path),
        "pointer_sha256": pointer_sha,
        "shard": _rel_path(shard_path),
        "manifest": _rel_path(manifest_path),
        "sequence": manifest_seq,
        "age_hours": age_hours,
        "max_age_hours": max_age_hours,
    }
    return message, context


def record_failure(pointer: Path, receipt: Path, error: str) -> None:
    payload = {
        "module": MODULE_NAME,
        "generated_at": _iso_now(),
        "status": "error",
        "message": error,
        "pointer": _rel_path(pointer),
    }
    _emit_receipt(receipt, payload)


def run(pointer: Path | None = None, *, max_age_hours: float | None = DEFAULT_MAX_AGE_HOURS, receipt: Path | None = None) -> str:
    message, context = verify(pointer=pointer, max_age_hours=max_age_hours)
    if receipt is not None:
        _emit_receipt(receipt, context)
    return message


__all__ = [
    "DEFAULT_POINTER",
    "DEFAULT_MAX_AGE_HOURS",
    "GuardError",
    "ROOT",
    "verify",
    "run",
    "record_failure",
]

"""Emit alerts when governance or core workflow docs change."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Tuple

from tools.autonomy.shared import write_receipt_payload

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = ROOT / "_report" / "usage" / "governance-alerts"
DEFAULT_STATE_PATH = DEFAULT_OUT_DIR / "state.json"

WATCH_TARGETS = [
    ROOT / "governance",
    ROOT / "docs" / "workflow.md",
    ROOT / "docs" / "architecture.md",
    ROOT / "docs" / "promotion-policy.md",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _iter_files(target: Path) -> Iterable[Path]:
    if target.is_dir():
        for entry in sorted(target.rglob("*")):
            if entry.is_file():
                yield entry
    elif target.is_file():
        yield target


def compute_hashes(targets: Iterable[Path]) -> Dict[str, str]:
    hashes: Dict[str, str] = {}
    for target in targets:
        if not target.exists():
            continue
        for file_path in _iter_files(target):
            rel = file_path.relative_to(ROOT).as_posix()
            hashes[rel] = _hash_path(file_path)
    return hashes


def _diff_hashes(old: Mapping[str, str], new: Mapping[str, str]) -> Tuple[List[str], List[str], List[Mapping[str, str]]]:
    added = sorted(path for path in new.keys() if path not in old)
    removed = sorted(path for path in old.keys() if path not in new)
    changed: List[Mapping[str, str]] = []
    for path, new_hash in new.items():
        old_hash = old.get(path)
        if old_hash is not None and old_hash != new_hash:
            changed.append({"path": path, "old_hash": old_hash, "new_hash": new_hash})
    changed.sort(key=lambda entry: entry["path"])
    return added, removed, changed


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _load_state(path: Path) -> Mapping[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_state(path: Path, hashes: Mapping[str, str]) -> None:
    payload = {
        "generated_at": _utc_now(),
        "hashes": dict(hashes),
    }
    _ensure_dir(path)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def emit_alert(
    *,
    out_dir: Path,
    state_path: Path,
    targets: Iterable[Path],
) -> Tuple[bool, Path | None]:
    new_hashes = compute_hashes(targets)
    state_exists = state_path.exists()
    state = _load_state(state_path)
    old_hashes = state.get("hashes", {}) if isinstance(state, Mapping) else {}
    if not isinstance(old_hashes, Mapping):
        old_hashes = {}
    if not state_exists:
        _write_state(state_path, new_hashes)
        return False, None
    added, removed, changed = _diff_hashes(old_hashes, new_hashes)
    if not (added or removed or changed):
        _write_state(state_path, new_hashes)
        return False, None

    timestamp = _utc_now()
    out_dir.mkdir(parents=True, exist_ok=True)
    alert_path = out_dir / f"alert-{timestamp.replace(':', '').replace('-', '')}.json"
    payload = {
        "generated_at": timestamp,
        "added": added,
        "removed": removed,
        "changed": changed,
    }
    write_receipt_payload(alert_path, payload)
    _write_state(state_path, new_hashes)

    latest_path = out_dir / "latest.json"
    write_receipt_payload(latest_path, payload)
    return True, alert_path


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Directory for alert receipts")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE_PATH, help="Path to state JSON storing last hashes")
    parser.add_argument("--quiet", action="store_true", help="Suppress stdout")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    triggered, alert_path = emit_alert(
        out_dir=args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir,
        state_path=args.state if args.state.is_absolute() else ROOT / args.state,
        targets=WATCH_TARGETS,
    )
    if triggered and not args.quiet:
        if alert_path is not None:
            try:
                display_path = alert_path.relative_to(ROOT).as_posix()
            except ValueError:
                display_path = alert_path.as_posix()
        else:
            display_path = "<unknown>"
        print(f"governance alert written → {display_path}")
    elif not triggered and not args.quiet:
        print("governance alert: no changes detected")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

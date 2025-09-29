"""Emit queue stubs from retro advisories."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ADVISORY = REPO_ROOT / "_report" / "fractal" / "advisories" / "latest.json"
QUEUE_DIR = REPO_ROOT / "queue"

SLUG_RE = re.compile(r"[^a-z0-9-]+")


def _slugify(value: str) -> str:
    value = value.lower().replace("_", "-")
    value = SLUG_RE.sub("-", value)
    return value.strip("-")


def _coord_from_advisory(advisory: dict) -> str:
    systemic = advisory.get("systemic_scale")
    layer = advisory.get("layer")
    if systemic and layer:
        return f"S{systemic}:{layer}"
    return "S5:L5"


def _queue_filename(advisory_id: str, target: str) -> Path:
    suffix = _slugify(target.split("/")[-1])[:24]
    name = f"BF-{advisory_id.split('-')[-1]}-{suffix}.md"
    return QUEUE_DIR / name


def build_queue_entry(advisory: dict, source_receipt: str) -> str:
    target = advisory.get("targets", ["unknown"])[0]
    ocers = advisory.get("ocers_target", {}).get("trait", "Self-repair")
    coord = _coord_from_advisory(advisory)
    claim = advisory.get("claim", "")
    lines = [
        f"# Task: Backfill {target}",
        f"Goal: Resolve advisory {advisory['id']} (see {source_receipt}).",
        f"OCERS Target: {ocers}↑",
        f"Coordinate: {coord}",
        f"Notes: {claim}",
        f"Advisory: {advisory['id']}",
        f"Receipts: {source_receipt}",
        "Sunset: close once supersession recorded.",
        "Fallback: track advisory in _report/fractal/advisories until addressed.",
    ]
    return "\n".join(lines) + "\n"


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--advisories", type=Path, default=DEFAULT_ADVISORY, help="Path to advisories JSON")
    parser.add_argument("--apply", action="store_true", help="Write queue files; default prints paths only")
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = json.loads(args.advisories.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"error: advisories not found: {args.advisories}")
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON: {exc}")
        return 2

    advisories = payload.get("advisories", [])
    if not advisories:
        print("no advisories to emit")
        return 0

    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    for advisory in advisories:
        queue_path = _queue_filename(advisory["id"], advisory.get("targets", ["unknown"])[0])
        content = build_queue_entry(advisory, payload.get("source_receipt", ""))
        if args.apply:
            if queue_path.exists():
                continue
            queue_path.write_text(content, encoding="utf-8")
            print(f"wrote {queue_path.relative_to(REPO_ROOT)}")
        else:
            print(f"would write {queue_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

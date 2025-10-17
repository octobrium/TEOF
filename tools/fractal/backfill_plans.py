"""Backfill missing systemic targets and coordinates in plan files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, Optional

from tools.planner.systemic_targets import ensure_axes

from tools.fractal import conformance

REPO_ROOT = Path(__file__).resolve().parents[2]
PLANS_DIR = REPO_ROOT / "_plans"


def _parse_coordinate(coord: str) -> tuple[Optional[int], Optional[str]]:
    coord = coord.strip()
    if not coord:
        return None, None
    if ":" not in coord:
        return None, None
    left, right = coord.split(":", 1)
    systemic_scale: Optional[int] = None
    layer: Optional[str] = None
    if left.upper().startswith("S"):
        try:
            systemic_scale = int(left[1:])
        except ValueError:
            systemic_scale = None
    candidate_layer = right.strip().upper()
    if candidate_layer.startswith("L") and len(candidate_layer) >= 2 and candidate_layer[1].isdigit():
        layer = candidate_layer[:2]
    return systemic_scale, layer


def backfill_plan(path: Path, queue_index: Dict[str, conformance.QueueEntry]) -> bool:
    data = json.loads(path.read_text(encoding="utf-8"))

    links = data.get("links") or []
    queue_refs = [
        entry.get("ref")
        for entry in links
        if isinstance(entry, dict) and entry.get("type") == "queue"
    ]

    queue_entry: Optional[conformance.QueueEntry] = None
    for ref in queue_refs:
        if ref in queue_index:
            queue_entry = queue_index[ref]
            break

    changed = False

    coord_source: Optional[str] = None
    coord_layers: list[str] = []
    if queue_entry and queue_entry.coordinates:
        coord_source = queue_entry.coordinates[0]
        for coord in queue_entry.coordinates:
            _, layer_hint = _parse_coordinate(coord)
            if layer_hint and layer_hint not in coord_layers:
                coord_layers.append(layer_hint)

    if queue_entry and queue_entry.systemic_targets and not data.get("systemic_targets"):
        try:
            data["systemic_targets"] = ensure_axes(queue_entry.systemic_targets)
        except ValueError:
            data["systemic_targets"] = queue_entry.systemic_targets
        changed = True

    if coord_source:
        systemic_scale, layer = _parse_coordinate(coord_source)
        if systemic_scale is not None and data.get("systemic_scale") is None:
            data["systemic_scale"] = systemic_scale
            changed = True
        if layer and not data.get("layer"):
            data["layer"] = layer
            changed = True

    if not data.get("layer_targets"):
        layer_targets: list[str] = []
        layer_value = data.get("layer")
        if isinstance(layer_value, str):
            layer_targets.append(layer_value)
        for hint in coord_layers:
            if hint not in layer_targets:
                layer_targets.append(hint)
        if layer_targets:
            data["layer_targets"] = layer_targets
            changed = True

    if changed:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes back to plan files (default: dry run)",
    )
    parser.add_argument(
        "--plan",
        action="append",
        help="Specific plan file(s) to process; defaults to all",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    queue_index = conformance.gather_queue_entries()

    targets: Iterable[Path]
    if args.plan:
        targets = [PLANS_DIR / plan if not plan.endswith(".json") else PLANS_DIR / plan for plan in args.plan]
    else:
        targets = PLANS_DIR.glob("*.plan.json")

    changed_paths = []
    for path in sorted(set(Path(t).resolve() for t in targets)):
        if not path.exists():
            print(f"skip (missing): {path}")
            continue
        if path.suffix != ".json":
            print(f"skip (not json): {path}")
            continue
        if args.apply:
            if backfill_plan(path, queue_index):
                changed_paths.append(path)
        else:
            # Dry run: simulate and report potential change
            snapshot = json.loads(path.read_text(encoding="utf-8"))
            if snapshot.get("layer") and snapshot.get("systemic_scale") is not None and snapshot.get("systemic_targets"):
                continue
            queue_entry = None
            links = snapshot.get("links") or []
            for entry in links:
                if isinstance(entry, dict) and entry.get("type") == "queue":
                    ref = entry.get("ref")
                    if ref in queue_index:
                        queue_entry = queue_index[ref]
                        break
            missing = []
            if not snapshot.get("layer"):
                missing.append("layer")
            if snapshot.get("systemic_scale") is None:
                missing.append("systemic_scale")
            if not snapshot.get("systemic_targets"):
                missing.append("systemic_targets")
            if missing:
                hint = f"via {queue_entry.path}" if queue_entry else "no queue ref"
                print(f"would update {path} (missing {', '.join(missing)}; {hint})")

    if args.apply:
        for path in changed_paths:
            print(f"updated {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

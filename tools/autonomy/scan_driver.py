"""Dynamic coordinator for `teof scan` runs.

Chooses which OCERS guards to execute based on recent changes to
`_plans/next-development.todo.json`, `agents/tasks/tasks.json`, and
`memory/state.json`, then delegates to :mod:`teof.bootloader`.

The driver appends execution metadata to `_report/usage/scan-history.jsonl`
so subsequent runs can avoid repeating work when inputs have not changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, MutableMapping, Sequence

from teof import bootloader
from tools.autonomy.shared import utc_timestamp


ROOT = Path(__file__).resolve().parents[2]
HISTORY_PATH = ROOT / "_report" / "usage" / "scan-history.jsonl"

TRACKED_INPUTS: Mapping[str, Path] = {
    "backlog": ROOT / "_plans" / "next-development.todo.json",
    "tasks": ROOT / "agents" / "tasks" / "tasks.json",
    "state": ROOT / "memory" / "state.json",
}

COMPONENT_TRIGGERS: Mapping[str, tuple[str, ...]] = {
    "frontier": ("backlog", "tasks"),
    "critic": ("backlog", "state"),
    "tms": ("state",),
    "ethics": ("backlog", "tasks"),
}


@dataclass
class ScanDecision:
    components: tuple[str, ...]
    changed_inputs: dict[str, bool]
    reasons: dict[str, list[str]]


def _fingerprint(path: Path) -> dict[str, object] | None:
    try:
        stat_result = path.stat()
    except FileNotFoundError:
        return None
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                digest.update(chunk)
    except OSError:
        return {"mtime_ns": stat_result.st_mtime_ns, "sha256": None}
    return {"mtime_ns": stat_result.st_mtime_ns, "sha256": digest.hexdigest()}


def _current_inputs() -> dict[str, dict[str, object] | None]:
    return {name: _fingerprint(path) for name, path in TRACKED_INPUTS.items()}


def _read_last_history(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    last_line = None
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                last_line = line
    if not last_line:
        return None
    try:
        return json.loads(last_line)
    except json.JSONDecodeError:
        return None


def _normalise_previous(previous: Mapping[str, object] | None) -> MutableMapping[str, dict[str, object] | None]:
    normalised: MutableMapping[str, dict[str, object] | None] = {}
    if not previous:
        return normalised
    for name, value in previous.items():
        if isinstance(value, Mapping):
            normalised[name] = dict(value)
        elif isinstance(value, (int, float)):
            normalised[name] = {"mtime_ns": int(value), "sha256": None}
        else:
            normalised[name] = None
    return normalised


def _detect_changes(
    current: Mapping[str, dict[str, object] | None],
    previous: Mapping[str, object] | None,
) -> dict[str, bool]:
    if previous is None:
        return {name: True for name in current}
    previous_map = _normalise_previous(previous)
    result: dict[str, bool] = {}
    for name, value in current.items():
        result[name] = value != previous_map.get(name)
    return result


def _choose_components(changed: Mapping[str, bool]) -> dict[str, list[str]]:
    reasons: dict[str, list[str]] = {}
    for component, triggers in COMPONENT_TRIGGERS.items():
        hit = [trigger for trigger in triggers if changed.get(trigger, False)]
        if hit:
            reasons[component] = hit
    return reasons


def make_decision(
    *,
    forced: Iterable[str],
    skipped: Iterable[str],
    current_inputs: Mapping[str, dict[str, object] | None],
    previous_inputs: Mapping[str, object] | None,
) -> ScanDecision:
    changed = _detect_changes(current_inputs, previous_inputs)
    reason_map = _choose_components(changed)
    selected = set(reason_map)
    forced_set = {comp for comp in forced if comp in bootloader.SCAN_COMPONENTS}
    skip_set = {comp for comp in skipped if comp in bootloader.SCAN_COMPONENTS}
    selected.update(forced_set)
    selected.difference_update(skip_set)
    ordered = tuple(comp for comp in bootloader.SCAN_COMPONENTS if comp in selected)
    reasons = {comp: reason_map.get(comp, []) for comp in ordered}
    return ScanDecision(components=ordered, changed_inputs=dict(changed), reasons=reasons)


def _write_history(path: Path, entry: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=10, help="Frontier entry limit (default: 10)")
    parser.add_argument("--format", choices=("table", "json"), default="table", help="Output format for `teof scan`")
    parser.add_argument("--out", type=Path, help="Directory to write receipts (passed to `teof scan`)")
    parser.add_argument("--emit-bus", action="store_true", help="Forward to `teof scan --emit-bus`")
    parser.add_argument("--emit-plan", action="store_true", help="Forward to `teof scan --emit-plan`")
    parser.add_argument("--summary", action="store_true", help="Request summary counts instead of tables (table format only)")
    parser.add_argument("--force", action="append", choices=bootloader.SCAN_COMPONENTS, help="Always run the specified component(s)")
    parser.add_argument("--skip", action="append", choices=bootloader.SCAN_COMPONENTS, help="Never run the specified component(s)")
    parser.add_argument("--history", type=Path, help="Override scan history path")
    parser.add_argument("--dry-run", action="store_true", help="Print planned execution without running `teof scan`")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    if args.summary and args.format != "table":
        print("::error:: --summary is only available with table output")
        return 2

    history_path = args.history if args.history is not None else HISTORY_PATH
    previous_entry = _read_last_history(history_path)
    previous_inputs = (
        previous_entry.get("inputs") if isinstance(previous_entry, Mapping) else None
    )
    current_inputs = _current_inputs()

    forced = args.force or []
    skipped = args.skip or []
    decision = make_decision(
        forced=forced,
        skipped=skipped,
        current_inputs=current_inputs,
        previous_inputs=previous_inputs if isinstance(previous_inputs, Mapping) else None,
    )

    if not decision.components:
        print("scan_driver: no components selected (nothing to run)")
        history_entry = {
            "generated_at": utc_timestamp(),
            "components": [],
            "changed": decision.changed_inputs,
            "reasons": {},
            "forced": list(forced),
            "skipped": list(skipped),
            "inputs": current_inputs,
            "dry_run": bool(args.dry_run),
            "exit_code": 0,
        }
        _write_history(history_path, history_entry)
        return 0

    ordered_components = list(decision.components)
    if args.dry_run:
        print("scan_driver: would run", ", ".join(ordered_components))
        for comp in ordered_components:
            reasons = decision.reasons.get(comp)
            if reasons:
                print(f"  - {comp}: triggered by {', '.join(reasons)}")
        history_entry = {
            "generated_at": utc_timestamp(),
            "components": ordered_components,
            "changed": decision.changed_inputs,
            "reasons": decision.reasons,
            "forced": list(forced),
            "skipped": list(skipped),
            "inputs": current_inputs,
            "dry_run": True,
            "exit_code": 0,
        }
        _write_history(history_path, history_entry)
        return 0

    scan_args: list[str] = ["scan", "--limit", str(max(0, args.limit))]
    if args.format != "table":
        scan_args.extend(["--format", args.format])
    if args.summary:
        scan_args.append("--summary")
    if args.out:
        out_path = args.out if args.out.is_absolute() else ROOT / args.out
        scan_args.extend(["--out", str(out_path)])
    if args.emit_bus:
        scan_args.append("--emit-bus")
    if args.emit_plan:
        scan_args.append("--emit-plan")
    for component in ordered_components:
        scan_args.extend(["--only", component])

    exit_code = bootloader.main(scan_args)

    history_entry = {
        "generated_at": utc_timestamp(),
        "components": ordered_components,
        "changed": decision.changed_inputs,
        "reasons": decision.reasons,
        "forced": list(forced),
        "skipped": list(skipped),
        "inputs": current_inputs,
        "exit_code": exit_code,
        "summary": bool(args.summary),
        "format": args.format,
        "emit_bus": bool(args.emit_bus),
        "emit_plan": bool(args.emit_plan),
        "out": str(args.out) if args.out else None,
        "limit": max(0, args.limit),
    }
    _write_history(history_path, history_entry)

    return exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

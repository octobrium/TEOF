"""Dynamic coordinator for `teof scan` runs.

Chooses which OCERS guards to execute based on policy-defined inputs,
delegates to :mod:`teof.bootloader`, and records history so future runs can
skip redundant checks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, MutableMapping, Sequence

from teof import bootloader
from tools.agent import parallel_guard, session_guard
from tools.autonomy.shared import load_json, utc_timestamp


ROOT = Path(__file__).resolve().parents[2]
HISTORY_PATH = ROOT / "_report" / "usage" / "scan-history.jsonl"
DEFAULT_POLICY_PATH = ROOT / "docs" / "automation" / "scan-policy.json"

DEFAULT_TRACKED_INPUTS: Mapping[str, str] = {
    "backlog": "_plans/next-development.todo.json",
    "tasks": "agents/tasks/tasks.json",
    "state": "memory/state.json",
}

DEFAULT_COMPONENT_TRIGGERS: Mapping[str, tuple[str, ...]] = {
    "frontier": ("backlog", "tasks"),
    "critic": ("backlog", "state"),
    "tms": ("state",),
    "ethics": ("backlog", "tasks"),
}


@dataclass(frozen=True)
class ScanPolicy:
    tracked_inputs: Mapping[str, Path]
    component_triggers: Mapping[str, tuple[str, ...]]
    reuse_window_seconds: int
    reuse_requires_summary: bool


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


def _current_inputs(tracked_inputs: Mapping[str, Path]) -> dict[str, dict[str, object] | None]:
    return {name: _fingerprint(path) for name, path in tracked_inputs.items()}


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


def _choose_components(
    changed: Mapping[str, bool],
    component_triggers: Mapping[str, tuple[str, ...]],
) -> dict[str, list[str]]:
    reasons: dict[str, list[str]] = {}
    for component, triggers in component_triggers.items():
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
    component_triggers: Mapping[str, tuple[str, ...]],
) -> ScanDecision:
    changed = _detect_changes(current_inputs, previous_inputs)
    reason_map = _choose_components(changed, component_triggers)
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


def _resolve_agent_id(agent: str | None) -> str | None:
    try:
        return session_guard.resolve_agent_id(agent)
    except SystemExit:
        return None


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
    parser.add_argument("--policy", type=Path, help="Override scan policy path")
    parser.add_argument("--dry-run", action="store_true", help="Print planned execution without running `teof scan`")
    parser.add_argument("--agent", help="Agent id for guard enforcement (defaults to AGENT_MANIFEST.json)")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    if args.summary and args.format != "table":
        print("::error:: --summary is only available with table output")
        return 2

    policy = load_policy(args.policy if args.policy is not None else DEFAULT_POLICY_PATH)

    agent_id = _resolve_agent_id(args.agent)
    parallel_report = parallel_guard.detect_parallel_state(agent_id)
    print(parallel_guard.format_summary(parallel_report))
    if agent_id and parallel_report.requirements.get("session_boot"):
        try:
            session_guard.ensure_recent_session(agent_id, context="scan_driver")
        except SystemExit as exc:
            print(f"::error:: {exc}")
            return 3
    if agent_id and parallel_report.severity == "hard":
        parallel_guard.write_parallel_receipt(agent_id, parallel_report)

    history_path = args.history if args.history is not None else HISTORY_PATH
    previous_entry = _read_last_history(history_path)
    previous_inputs = previous_entry.get("inputs") if isinstance(previous_entry, Mapping) else None
    current_inputs = _current_inputs(policy.tracked_inputs)

    forced = args.force or []
    skipped = args.skip or []
    decision = make_decision(
        forced=forced,
        skipped=skipped,
        current_inputs=current_inputs,
        previous_inputs=previous_inputs if isinstance(previous_inputs, Mapping) else None,
        component_triggers=policy.component_triggers,
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
            "parallel": parallel_report.to_payload(),
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
            "parallel": parallel_report.to_payload(),
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
        "parallel": parallel_report.to_payload(),
    }
    _write_history(history_path, history_entry)

    return exit_code


def load_policy(candidate: Path | None) -> ScanPolicy:
    path = candidate if candidate is not None else DEFAULT_POLICY_PATH
    data = load_json(path) if path.exists() else None

    tracked_inputs: dict[str, Path] = {}
    component_triggers: dict[str, tuple[str, ...]] = {}
    reuse_window_seconds = 0
    reuse_requires_summary = True

    if isinstance(data, Mapping):
        inputs = data.get("tracked_inputs")
        if isinstance(inputs, Mapping):
            for name, entry in inputs.items():
                rel = None
                if isinstance(entry, Mapping):
                    rel = entry.get("path")
                elif isinstance(entry, str):
                    rel = entry
                if isinstance(rel, str):
                    tracked_inputs[name] = (ROOT / rel).resolve()

        components = data.get("components")
        if isinstance(components, Mapping):
            for name, entry in components.items():
                triggers: Sequence[str] | None = None
                if isinstance(entry, Mapping):
                    trig_val = entry.get("triggers")
                    if isinstance(trig_val, Sequence):
                        triggers = [str(item) for item in trig_val if isinstance(item, str)]
                if isinstance(entry, Sequence) and not isinstance(entry, (str, bytes)):
                    triggers = [str(item) for item in entry if isinstance(item, str)]
                if triggers:
                    component_triggers[name] = tuple(triggers)

        cache = data.get("cache")
        if isinstance(cache, Mapping):
            window = cache.get("reuse_window_seconds")
            if isinstance(window, int) and window >= 0:
                reuse_window_seconds = window
            summary_flag = cache.get("reuse_requires_summary")
            if isinstance(summary_flag, bool):
                reuse_requires_summary = summary_flag

    if not tracked_inputs:
        tracked_inputs = {
            name: (ROOT / rel).resolve()
            for name, rel in DEFAULT_TRACKED_INPUTS.items()
        }

    if not component_triggers:
        component_triggers = dict(DEFAULT_COMPONENT_TRIGGERS)
    else:
        normalized: dict[str, tuple[str, ...]] = {}
        for name, triggers in component_triggers.items():
            normalized[name] = tuple(
                trig for trig in triggers if trig in tracked_inputs
            )
        component_triggers = normalized

    # Ensure every bootloader component has a trigger mapping
    for comp in bootloader.SCAN_COMPONENTS:
        component_triggers.setdefault(comp, DEFAULT_COMPONENT_TRIGGERS.get(comp, tuple()))

    return ScanPolicy(
        tracked_inputs=tracked_inputs,
        component_triggers=component_triggers,
        reuse_window_seconds=reuse_window_seconds,
        reuse_requires_summary=reuse_requires_summary,
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

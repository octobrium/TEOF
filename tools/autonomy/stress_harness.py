#!/usr/bin/env python3
"""Autonomy stress harness: run synthetic failure scenarios with receipts."""
from __future__ import annotations

import argparse
import json
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "_report" / "usage" / "autonomy-stress"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
SUPPORTED_TYPES = {"missing_receipt", "auth_dropout", "stuck_task"}


class HarnessError(RuntimeError):
    """Raised when scenario parsing or execution fails."""


@dataclass
class Scenario:
    name: str
    type: str
    severity: str | None
    config: Dict[str, Any]


@dataclass
class ScenarioResult:
    name: str
    type: str
    status: str
    expected: str
    passed: bool
    severity: str | None
    details: Dict[str, Any]


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


def _digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _load_scenarios(path: Path) -> List[Scenario]:
    if not path.exists():
        raise HarnessError(f"scenarios file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HarnessError(f"invalid JSON in {path}: {exc}") from exc

    scenarios_data: Iterable[Mapping[str, Any]]
    if isinstance(data, list):
        scenarios_data = data
    elif isinstance(data, Mapping):
        scenarios_data = data.get("scenarios", [])  # support {"scenarios": [...]} wrapper
    else:
        raise HarnessError("scenarios file must be a list or object containing 'scenarios'")

    scenarios: List[Scenario] = []
    for entry in scenarios_data:
        if not isinstance(entry, Mapping):
            raise HarnessError("scenario entries must be objects")
        name = str(entry.get("name") or "").strip()
        if not name:
            raise HarnessError("scenario missing name")
        scenario_type = str(entry.get("type") or "").strip()
        if scenario_type not in SUPPORTED_TYPES:
            raise HarnessError(f"scenario {name} uses unsupported type '{scenario_type}'")
        severity = entry.get("severity")
        if severity is not None:
            severity = str(severity)
        config = entry.get("config") or {}
        if not isinstance(config, Mapping):
            raise HarnessError(f"scenario {name} config must be an object")
        scenarios.append(Scenario(name=name, type=scenario_type, severity=severity, config=dict(config)))
    if not scenarios:
        raise HarnessError("no scenarios provided")
    return scenarios


def _expected_result(config: Mapping[str, Any]) -> str:
    candidate = str(config.get("expected_result") or "pass").strip().lower()
    return candidate if candidate in {"pass", "fail"} else "pass"


def _run_missing_receipt(config: Mapping[str, Any]) -> tuple[str, Dict[str, Any]]:
    missing = bool(config.get("missing_receipt", True))
    status = "fail" if missing else "pass"
    details = {
        "missing_receipt": missing,
        "guard": "receipt_presence",
    }
    return status, details


def _run_auth_dropout(config: Mapping[str, Any]) -> tuple[str, Dict[str, Any]]:
    drops = int(config.get("drops", 0))
    threshold = int(config.get("threshold", 1))
    status = "fail" if drops >= threshold else "pass"
    details = {
        "drops": drops,
        "threshold": threshold,
    }
    return status, details


def _run_stuck_task(config: Mapping[str, Any]) -> tuple[str, Dict[str, Any]]:
    gap = float(config.get("heartbeat_gap_minutes", 0))
    max_gap = float(config.get("max_gap_minutes", 30))
    status = "fail" if gap > max_gap else "pass"
    details = {
        "heartbeat_gap_minutes": gap,
        "max_gap_minutes": max_gap,
    }
    return status, details


SCENARIO_HANDLERS = {
    "missing_receipt": _run_missing_receipt,
    "auth_dropout": _run_auth_dropout,
    "stuck_task": _run_stuck_task,
}


def _execute_scenario(scenario: Scenario) -> ScenarioResult:
    expected = _expected_result(scenario.config)
    handler = SCENARIO_HANDLERS[scenario.type]
    status, details = handler(scenario.config)
    passed = status == expected
    details = dict(details)
    details["expected"] = expected
    return ScenarioResult(
        name=scenario.name,
        type=scenario.type,
        status=status,
        expected=expected,
        passed=passed,
        severity=scenario.severity,
        details=details,
    )


def run_harness(
    *,
    scenarios_path: Path,
    output_path: Path | None,
    require_pass: bool,
) -> tuple[Path, Mapping[str, Any]]:
    scenarios = _load_scenarios(scenarios_path)
    results = [_execute_scenario(scenario) for scenario in scenarios]
    summary = {
        "ts": _iso_now(),
        "scenarios": [
            {
                "name": result.name,
                "type": result.type,
                "status": result.status,
                "expected": result.expected,
                "passed": result.passed,
                "severity": result.severity,
                "details": result.details,
            }
            for result in results
        ],
    }
    summary["counts"] = {
        "total": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
    }
    summary["digest"] = _digest(summary)

    target = output_path or REPORT_DIR / f"autonomy-stress-{summary['ts'].replace(':', '').replace('-', '')}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return target, summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run autonomy stress scenarios and emit receipts")
    parser.add_argument("--scenarios", required=True, type=Path, help="JSON file describing scenarios")
    parser.add_argument("--output", type=Path, help="Override output receipt path")
    parser.add_argument(
        "--require-pass",
        action="store_true",
        help="Return non-zero exit if any scenario fails while expected to pass",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        output_path, summary = run_harness(
            scenarios_path=args.scenarios,
            output_path=args.output,
            require_pass=args.require_pass,
        )
    except HarnessError as exc:
        parser.error(str(exc))
        return 2

    try:
        rel_output = output_path.relative_to(ROOT)
    except ValueError:
        rel_output = output_path
    print(f"autonomy_stress: wrote receipt to {rel_output}")
    fails = summary["counts"]["failed"]
    if args.require_pass and fails:
        print(f"autonomy_stress: {fails} scenario(s) failed", file=None)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

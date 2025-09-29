#!/usr/bin/env python3
"""Fail when fractal conformance gaps remain."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tools.fractal import conformance
from tools.fractal import advisory as advisory_mod


def main() -> int:
    report = conformance.build_report(strict=True)

    repo_root = REPO_ROOT
    report_path = repo_root / "_report" / "fractal" / "conformance" / "latest.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    advisories = advisory_mod.build_advisories(report_path)
    advisory_path = repo_root / "_report" / "fractal" / "advisories" / "latest.json"
    advisory_path.parent.mkdir(parents=True, exist_ok=True)
    advisory_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_receipt": str(report_path),
        "advisories": advisories,
    }
    advisory_path.write_text(json.dumps(advisory_payload, indent=2) + "\n", encoding="utf-8")

    summary = report.get("summary", {})
    queue_issues = summary.get("queue_with_issues", 0)
    plan_issues = summary.get("plans_with_issues", 0)
    memory_issues = summary.get("memory_with_issues", 0)

    baseline_path = repo_root / "docs" / "fractal" / "baseline.json"
    baseline_summary = {}
    if baseline_path.exists():
        try:
            baseline_summary = json.loads(baseline_path.read_text(encoding="utf-8")).get("summary", {})
        except json.JSONDecodeError:
            baseline_summary = {}

    print(
        "fractal_conformance: queue={}, plans={}, memory={}".format(
            queue_issues, plan_issues, memory_issues
        )
    )

    exceeds = []
    for key in ("queue_with_issues", "plans_with_issues", "memory_with_issues"):
        allowed = baseline_summary.get(key, 0)
        observed = summary.get(key, 0)
        if observed > allowed:
            exceeds.append((key, observed, allowed))

    if not exceeds:
        summary.pop("strict_failure", None)
        print(f"advisories: {len(advisories)}")
    else:
        for key, observed, allowed in exceeds:
            print(
                f"::error:: {key} exceeds baseline ({observed} > {allowed})",
                flush=True,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

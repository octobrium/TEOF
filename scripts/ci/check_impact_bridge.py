#!/usr/bin/env python3
"""CI guard ensuring impact ledger entries stay linked to plans/backlog."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from tools.impact import bridge


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        summary_path = tmp_path / "impact-bridge.json"
        markdown_path = tmp_path / "impact-bridge.md"
        args = [
            "--report-dir",
            str(tmp_path),
            "--summary",
            str(summary_path),
            "--markdown",
            str(markdown_path),
        ]
        rc = bridge.main(args)
        if rc != 0:
            return rc
        stats = json.loads(summary_path.read_text(encoding="utf-8")).get("stats", {})
        total = stats.get("plans_total")
        with_ref = stats.get("plans_with_impact_ref")
        if total is None or with_ref is None:
            print("impact_bridge_guard: summary missing plan coverage stats", file=sys.stderr)
            return 1
        if total != with_ref:
            print(
                f"impact_bridge_guard: {with_ref}/{total} plans expose impact_ref",
                file=sys.stderr,
            )
            return 1
        print("impact_bridge_guard: all plans expose impact_ref")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

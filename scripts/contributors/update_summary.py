#!/usr/bin/env python3
"""Build `_report/usage/contributors/summary.json` from individual receipts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def collect_receipts(contrib_dir: Path) -> Dict[str, Dict]:
    summary: Dict[str, Dict] = {}
    for contributor_path in contrib_dir.iterdir():
        if not contributor_path.is_dir():
            continue
        contrib_id = contributor_path.name
        receipts: List[Dict] = []
        for receipt_file in sorted(contributor_path.glob("contribution-*.json")):
            data = json.loads(receipt_file.read_text(encoding="utf-8"))
            receipts.append(
                {
                    "workload": data.get("workload"),
                    "run_id": data.get("run_id"),
                    "generated_at": data.get("generated_at"),
                    "artifact_dir": data.get("artifacts", {}).get("artifact_dir"),
                    "eval_receipt": data.get("artifacts", {}).get("eval_receipt"),
                }
            )
        summary[contrib_id] = {"total_runs": len(receipts), "runs": receipts}
    return summary


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    contrib_root = root / "_report" / "usage" / "contributors"
    if not contrib_root.exists():
        print("No contributors directory found.")
        return 0
    summary = collect_receipts(contrib_root)
    out_path = contrib_root / "summary.json"
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote contributor summary → {out_path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

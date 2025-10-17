#!/usr/bin/env python3
"""Autocollab dry-run scaffold.

Copies queue items into a timestamped batch folder, mirrors the task text as a
placeholder proposal, and generates a systemic alignment heuristic. Emits
`score.json`, a lightweight `risk.json`, and an `accepted.json` stub so
downstream tooling has consistent signals.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from subprocess import PIPE, run
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

QUEUE = ROOT / "queue"
REPORT = ROOT / "_report" / "autocollab"


def ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def git_meta() -> Dict[str, str]:
    try:
        rev = run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, stdout=PIPE).stdout.strip()
    except Exception:
        rev = "unknown"
    return {"commit": rev or "unknown", "when": ts()}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def infer_risk(score: Dict[str, object]) -> Dict[str, object]:
    total = float(score.get("total", 0))
    signals: Dict[str, bool] = score.get("diagnostics", {}).get("signals", {})  # type: ignore[assignment]

    base = max(0.0, 1.0 - (total / 10.0))
    penalties: List[str] = []

    if not (signals.get("acceptance_has_paths") or signals.get("acceptance_has_metrics")):
        base += 0.2
        penalties.append("acceptance lacks concrete checks")
    if not signals.get("fallback_mentions_manual"):
        base += 0.2
        penalties.append("fallback not actionable")
    if not signals.get("sunset_mentions_trigger"):
        base += 0.1
        penalties.append("sunset lacks trigger")
    if not signals.get("has_references"):
        base += 0.1
        penalties.append("no references cited")

    risk_score = round(min(1.0, base), 3)
    if not penalties:
        penalties.append("healthy")
    return {
        "risk_score": risk_score,
        "penalties": penalties,
        "alignment_total": total,
    }


def infer_acceptance(score: Dict[str, object]) -> Dict[str, object]:
    total = float(score.get("total", 0))
    verdict = str(score.get("verdict", "review")).lower()
    signals: Dict[str, bool] = score.get("diagnostics", {}).get("signals", {})  # type: ignore[assignment]

    has_checks = signals.get("acceptance_has_paths") or signals.get("acceptance_has_metrics")
    resilient = signals.get("fallback_mentions_manual") and signals.get("sunset_mentions_trigger")

    accepted = bool(total >= 9 and verdict == "ready" and has_checks and resilient)
    reason = "meets heuristic thresholds" if accepted else "needs stronger safeguards"
    return {"accepted": accepted, "reason": reason, "scored_at": ts()}


def generate_alignment_stub(text: str) -> Dict[str, object]:
    """Generate a placeholder systemic alignment score for queue items."""
    word_count = len(text.split())
    readiness = "ready" if word_count > 120 else "review"
    total = min(12.5, max(4.0, word_count / 20.0))
    lowered = text.lower()
    diagnostics = {
        "signals": {
            "acceptance_has_paths": "path" in lowered or "procedure" in lowered,
            "acceptance_has_metrics": "metric" in lowered or "kpi" in lowered,
            "fallback_mentions_manual": "manual" in lowered or "human" in lowered,
            "sunset_mentions_trigger": "sunset" in lowered or "trigger" in lowered,
        }
    }
    return {
        "total": round(total, 2),
        "verdict": readiness,
        "diagnostics": diagnostics,
        "summary": "Systemic alignment stub (legacy OCERS heuristic retired)",
    }


def main() -> None:
    ensure_dir(REPORT)
    batch_dir = REPORT / ts()
    ensure_dir(batch_dir)

    items = sorted(QUEUE.glob("*.md"))
    if not items:
        print("No queue items. Add tasks to queue/*.md")
        return

    for idx, task_path in enumerate(items, start=1):
        text = task_path.read_text(encoding="utf-8", errors="ignore")
        item_dir = batch_dir / f"item-{idx:02d}"
        ensure_dir(item_dir)

        (item_dir / "task.md").write_text(text, encoding="utf-8")
        (item_dir / "proposal.md").write_text(text, encoding="utf-8")

        score = generate_alignment_stub(text)
        (item_dir / "score.json").write_text(json.dumps(score, indent=2), encoding="utf-8")
        (item_dir / "risk.json").write_text(json.dumps(infer_risk(score), indent=2), encoding="utf-8")
        (item_dir / "accepted.json").write_text(json.dumps(infer_acceptance(score), indent=2), encoding="utf-8")

        meta = {"meta": git_meta(), "source_task": task_path.name}
        (item_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Wrote dry-run batch: {batch_dir}")


if __name__ == "__main__":
    main()

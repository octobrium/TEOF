#!/usr/bin/env python3
import json, re
from pathlib import Path
from datetime import datetime, timezone

ROOT   = Path(__file__).resolve().parents[2]
AREPORT = ROOT / "_report" / "autocollab"

RISK_MAP = {"low":0.3,"med":0.6,"high":1.0}

def latest_batch():
    batches = [p for p in AREPORT.iterdir() if p.is_dir()] if AREPORT.exists() else []
    return max(batches) if batches else None

def assess(text:str):
    txt = text.lower()
    reasons = []
    risk = "low"
    bump = lambda lvl: "high" if lvl=="high" else ("high" if risk=="med" and lvl=="med" else ("med" if lvl=="med" else lvl))
    # invariants touch (raise)
    if any(k in txt for k in ["governance/anchors.json","capsule/current","hashes.json","scripts/ci/"]):
        risk = "med"; reasons.append("Touches invariants or CI")
    # unsafe automation
    if "auto-merge" in txt or "force-push" in txt:
        risk = "high"; reasons.append("Suggests unsafe merge operations")
    # missing guardrails
    if "sunset" not in txt and "fallback" not in txt:
        risk = "med" if risk!="high" else "high"; reasons.append("No sunset/fallback mentioned")
    # giant scope
    if len(txt) > 10000:
        risk = "med" if risk!="high" else "high"; reasons.append("Large scope")
    return {"risk": risk, "risk_score": RISK_MAP[risk], "reasons": reasons}

def main():
    b = latest_batch()
    if not b:
        print("critic: no batch; run tools/autocollab.sh first"); return
    items = sorted(b.glob("item-*"))
    for it in items:
        prop = it/"proposal.md"
        if not prop.exists(): continue
        res = assess(prop.read_text(encoding="utf-8", errors="ignore"))
        (it/"risk.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"critic: wrote risk.json for {len(items)} items in {b.name}")

if __name__ == "__main__":
    main()

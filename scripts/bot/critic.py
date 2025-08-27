#!/usr/bin/env python3
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREPORT = ROOT / "_report" / "autocollab"
RISK = {"low":0.3,"med":0.6,"high":1.0}

def latest_batch():
    batches = [p for p in AREPORT.iterdir() if p.is_dir()] if AREPORT.exists() else []
    return max(batches) if batches else None

def has(txt,*ws): 
    t = txt.lower()
    return any(w.lower() in t for w in ws)

def assess(text:str):
    t = text
    tl = t.lower()
    reasons = []
    level = "low"

    # Missing acceptance criteria → coherence/safety risk
    if "acceptance:" not in t:
        level = "med"; reasons.append("No Acceptance section")

    # Missing sunset/fallback → raise one notch
    if not (has(tl,"sunset") and has(tl,"fallback")):
        level = "high" if level=="med" else "med"; reasons.append("No sunset/fallback")

    # Touches invariants / governance / CI
    if has(tl,"governance/anchors.json","capsule/","hashes.json","scripts/ci/","capsule/current"):
        level = "high" if level!="high" else "high"; reasons.append("Touches invariants or CI")

    # Large scope or many code fences
    code_fences = len(re.findall(r'(?m)^```', t))
    if len(t) > 12000 or code_fences >= 4:
        level = "high" if level=="med" else ("med" if level=="low" else "high")
        reasons.append("Large scope / many code blocks")

    # Dangerous commands
    if re.search(r'\b(rm\s+-rf|sudo\s+|chmod\s+[-+][rwx]|force-push)\b', tl):
        level = "high"; reasons.append("Potentially dangerous command")

    return {"risk": level, "risk_score": RISK[level], "reasons": reasons}

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

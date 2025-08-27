#!/usr/bin/env python3
import json, os
from pathlib import Path

ROOT   = Path(__file__).resolve().parents[2]
AREPORT = ROOT/"_report"/"autocollab"

# Tunables (kept simple, deterministic)
RISK_WEIGHT = float(os.getenv("RISK_WEIGHT", "4.0"))  # penalty applied to risk_score (0.3/0.6/1.0)
MIN_SCORE   = int(float(os.getenv("MIN_SCORE",   "6")))  # minimum OCERS total to consider
MAX_RISK    = float(os.getenv("MAX_RISK", "0.80"))       # maximum risk_score to consider
TOP_N       = int(os.getenv("TOP_N", "5"))

def latest_batch():
    if not AREPORT.exists(): return None
    batches = [p for p in AREPORT.iterdir() if p.is_dir()]
    return max(batches) if batches else None

def loadj(p): 
    try: return json.loads(p.read_text())
    except: return {}

def desirability(total, risk_score):
    # higher is better; OCERS total 0..10, risk_score ~ {0.3,0.6,1.0}
    # simple linear tradeoff: score - (weight * risk)
    return total - (RISK_WEIGHT * risk_score)

def main():
    b = latest_batch()
    if not b:
        print("selector: no batch; run tools/pulse.sh first"); return
    items = sorted(b.glob("item-*"))
    ranked = []
    for it in items:
        s = loadj(it/"score.json"); r = loadj(it/"risk.json"); a = loadj(it/"accepted.json")
        total = int(s.get("total", 0)); risk = float(r.get("risk_score", 1.0))
        idx = int(it.name.split("-")[-1]) if it.name.split("-")[-1].isdigit() else None
        if total < MIN_SCORE or risk > MAX_RISK: 
            reason = []
            if total < MIN_SCORE: reason.append(f"score<{MIN_SCORE}")
            if risk > MAX_RISK:   reason.append(f"risk>{MAX_RISK}")
            ranked.append({"idx": idx, "total": total, "risk": risk, "keep": False, "why": ",".join(reason)})
            continue
        keep = True
        desir = desirability(total, risk)
        ranked.append({"idx": idx, "total": total, "risk": risk, "keep": keep, "desir": round(desir, 3)})

    # choose top KEEP items by desirability
    kept = [x for x in ranked if x.get("keep")]
    kept.sort(key=lambda d: (-d["desir"], -d["total"], d["risk"]))
    top = kept[:TOP_N]

    # write receipt
    out = {
        "batch": b.name,
        "params": {"RISK_WEIGHT": RISK_WEIGHT, "MIN_SCORE": MIN_SCORE, "MAX_RISK": MAX_RISK, "TOP_N": TOP_N},
        "top": top,
        "filtered_out": [x for x in ranked if not x.get("keep")],
    }
    (b/"selection.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    # pretty print suggestion
    print(f"== Selector v0 (batch {b.name}) ==")
    if not top:
        print("No candidates meet thresholds.")
        print(f"(MIN_SCORE>={MIN_SCORE}, MAX_RISK<={MAX_RISK})")
        return
    print("Top suggestions (idx  total  risk  desirability):")
    for x in top:
        print(f"  {x['idx']:>2}    {x['total']:>2}    {x['risk']:.2f}   {x['desir']:.2f}")
    print("\nNext step:")
    print("  tools/accept.sh <idx>   # mark accepted")
    print("  tools/ledger.sh         # update accept_rate")
    print("  tools/doc-autopr.sh     # create docs-only draft branch (optional)")

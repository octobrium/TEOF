#!/usr/bin/env python3
import json, os
from pathlib import Path
ROOT   = Path(__file__).resolve().parents[2]
AREPORT = ROOT/"_report"/"autocollab"

W_SCORE   = float(os.getenv("SELECT_W_SCORE", "1.0"))
W_RISK    = float(os.getenv("SELECT_W_RISK",  "4.0"))
B_ACCEPT  = float(os.getenv("SELECT_B_ACCEPT","0.5"))
MIN_SCORE = int(float(os.getenv("MIN_SCORE",   "6")))
MAX_RISK  = float(os.getenv("MAX_RISK",  "0.80"))
TOP_N     = int(os.getenv("TOP_N", "5"))

def latest_batch():
    if not AREPORT.exists(): return None
    bs = [p for p in AREPORT.iterdir() if p.is_dir()]
    return max(bs) if bs else None

def loadj(p):
    try: return json.loads(p.read_text())
    except: return {}

def has_acceptance(text: str) -> bool:
    return "acceptance:" in text.lower()

def desirability(total: int, risk: float, accept: bool) -> float:
    return (W_SCORE*total) - (W_RISK*risk) + (B_ACCEPT if accept else 0.0)

def main():
    b = latest_batch()
    if not b:
        print("selector: no batch; run tools/pulse.sh first"); return
    items = sorted(b.glob("item-*"))
    scored = []
    for it in items:
        idx = int(it.name.split("-")[-1]) if it.name.split("-")[-1].isdigit() else None
        s = loadj(it/"score.json"); r = loadj(it/"risk.json")
        total = int(s.get("total", 0)); risk = float(r.get("risk_score", 1.0))
        prop = (it/"proposal.md").read_text(encoding="utf-8", errors="ignore") if (it/"proposal.md").exists() else ""
        accept = has_acceptance(prop)
        if total < MIN_SCORE or risk > MAX_RISK:
            scored.append({"idx": idx, "total": total, "risk": risk, "accept": accept, "keep": False}); continue
        desir = round(desirability(total, risk, accept), 3)
        scored.append({"idx": idx, "total": total, "risk": risk, "accept": accept, "keep": True, "desir": desir})
    kept = [x for x in scored if x.get("keep")]
    kept.sort(key=lambda d: (-d["desir"], -d["total"], d["risk"], (not d["accept"])))
    (b/"selection.json").write_text(json.dumps({
        "batch": b.name,
        "params": {"W_SCORE":W_SCORE,"W_RISK":W_RISK,"B_ACCEPT":B_ACCEPT,
                   "MIN_SCORE":MIN_SCORE,"MAX_RISK":MAX_RISK,"TOP_N":TOP_N},
        "top": kept[:TOP_N],
        "filtered_out": [x for x in scored if not x.get("keep")],
    }, indent=2), encoding="utf-8")
    print(f"== Selector v1 (batch {b.name}) ==")
    if not kept:
        print(f"No candidates >={MIN_SCORE} and risk<={MAX_RISK}"); return
    print("Top (idx  total  risk  accept  desir):")
    for x in kept[:TOP_N]:
        print(f"  {x['idx']:>2}   {x['total']:>2}   {x['risk']:.2f}  {str(x['accept']):>5}  {x['desir']:.2f}")
    print("\nNext: tools/accept.sh <idx> && tools/ledger.sh && tools/doc-autopr.sh")
if __name__ == "__main__":
    main()

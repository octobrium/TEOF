#!/usr/bin/env python3
import os, json, csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AROOT = ROOT / "_report" / "autocollab"
LEDGER = ROOT / "_report" / "ledger.csv"

def latest_batch_dir():
    if not AROOT.exists(): return None
    batches = [p for p in AROOT.iterdir() if p.is_dir()]
    return max(batches) if batches else None  # lexicographic ts

def gather(batch):
    items = sorted(batch.glob("item-*"))
    total = 0; n = 0; risk_sum = 0; risk_n = 0
    for it in items:
        s = it/"score.json"
        if s.exists():
            try:
                data = json.loads(s.read_text())
                total += int(data.get("total", 0))
                n += 1
            except Exception:
                pass
        r = it/"risk.json"
        if r.exists():
            try:
                rr = json.loads(r.read_text())
                risk_sum += float(rr.get("risk_score", 0))
                risk_n += 1
            except Exception:
                pass
    avg = (total / n) if n else 0
    avg_risk = (risk_sum / risk_n) if risk_n else ""
    return n, avg, total, avg_risk

def main():
    batch = latest_batch_dir()
    if not batch:
        print("No batch found; run tools/autocollab.sh first"); return
    n, avg, total, avg_risk = gather(batch)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    hdr = ["batch_ts","total_items","avg_score","total_score","avg_risk","accept_rate","notes"]
    if not LEDGER.exists():
        with open(LEDGER, "w", newline="") as f: csv.writer(f).writerow(hdr)
    with open(LEDGER, "a", newline="") as f:
        csv.writer(f).writerow([batch.name, n, f"{avg:.3f}", total, (f"{avg_risk:.3f}" if avg_risk!="" else ""), "", "dry-run"])
    print(f"ledger: appended {batch.name} n={n} avg={avg:.3f} total={total} avg_risk={avg_risk}")
if __name__ == "__main__":
    main()

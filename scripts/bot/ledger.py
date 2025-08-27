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
    items = sorted(batch.glob("item-*/score.json"))
    total = 0; n = 0
    for s in items:
        try:
            data = json.loads(s.read_text())
            total += int(data.get("total", 0))
            n += 1
        except Exception:
            pass
    avg = (total / n) if n else 0
    return n, avg, total

def main():
    batch = latest_batch_dir()
    if not batch:
        print("No batch found; run tools/autocollab.sh first"); return
    n, avg, total = gather(batch)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    hdr = ["batch_ts","total_items","avg_score","total_score","accept_rate","notes"]
    if not LEDGER.exists():
        with open(LEDGER, "w", newline="") as f: csv.writer(f).writerow(hdr)
    with open(LEDGER, "a", newline="") as f:
        csv.writer(f).writerow([batch.name, n, f"{avg:.3f}", total, "", "dry-run"])
    print(f"ledger: appended {batch.name} n={n} avg={avg:.3f} total={total}")

if __name__ == "__main__":
    main()

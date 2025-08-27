#!/usr/bin/env python3
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREPORT = ROOT / "_report" / "autocollab"

def latest_batch():
    if not AREPORT.exists(): return None
    bs = [p for p in AREPORT.iterdir() if p.is_dir()]
    return max(bs) if bs else None

def main():
    b = latest_batch()
    if not b:
        print("", end=""); return
    sel = b/"selection.json"
    if not sel.exists():
        print("", end=""); return
    data = json.loads(sel.read_text())
    top = data.get("top", [])
    if not top:
        print("", end=""); return
    idx = top[0].get("idx")
    print(idx if idx is not None else "", end="")

if __name__ == "__main__":
    main()

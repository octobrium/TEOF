#!/usr/bin/env python3
import sys, re, json, subprocess, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQ = ["# Task:", "Goal:", "OCERS Target:", "Sunset:", "Fallback:", "Acceptance:"]

def staged_queue_files():
    out = subprocess.check_output(["git","diff","--cached","--name-only"], cwd=ROOT, text=True)
    return [ROOT/p for p in out.splitlines() if p.startswith("queue/") and p.endswith(".md")]

def check_one(p: Path):
    txt = p.read_text(encoding="utf-8", errors="ignore")
    missing = [k for k in REQ if k not in txt]
    return p, missing

def main():
    qs = staged_queue_files()
    bad = []
    for q in qs:
        p, missing = check_one(q)
        if missing: bad.append((p, missing))
    if bad:
        print("❌ queue template check failed:")
        for p, missing in bad:
            print(f"  - {p}: missing {', '.join(missing)}")
        print("Fix queued task(s) to include all required fields.")
        sys.exit(1)
    else:
        if qs:
            print("queue template: OK")
        else:
            print("queue template: no staged queue/*.md")
if __name__ == "__main__":
    main()

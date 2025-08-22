#!/usr/bin/env python3
import json, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ocers = ROOT / "artifacts" / "ocers_out"
anchors = Path(__file__).with_name("anchors.json")

ledger = json.loads(anchors.read_text()) if anchors.exists() else []
errors = 0
for entry in ledger:
    p = ocers / entry["ts"] / "brief.json"
    if not p.exists():
        print(f"MISS: {p}")
        errors += 1
        continue
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != entry["sha256"]:
        print(f"FAIL: {p} hash mismatch")
        errors += 1
print("OK" if errors == 0 else f"{errors} errors")

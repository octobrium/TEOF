#!/usr/bin/env python3
import json, sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
latest = root / "ocers_out" / "latest"
if not latest.exists():
    print("no latest brief found. run: make brief")
    sys.exit(1)

j = json.loads((latest/"brief.json").read_text())
obs = j.get("observations", [])

def bucket(p):
    if not p: return "missing"
    p = str(p)
    if p.startswith("auto:"): return "auto"
    if p.startswith("fallback:"): return p
    if p.startswith("manual://"): return "fallback:env"
    return "unknown"

total = len(obs)
auto = sum(1 for o in obs if bucket(o.get("provenance"))=="auto")
fb_env = sum(1 for o in obs if bucket(o.get("provenance"))=="fallback:env")
fb_stooq = sum(1 for o in obs if bucket(o.get("provenance"))=="fallback:stooq")
missing = sum(1 for o in obs if bucket(o.get("provenance"))=="missing")

print(f"TEOF audit — {latest.name}")
print(f"total={total}  auto={auto}  fb_stooq={fb_stooq}  fb_env={fb_env}  missing={missing}")
print()
print("label  | value   | provenance | ts")
print("-------|---------|------------|---------------------")
for o in obs:
    print(f"{o.get('label'):<6} | {str(o.get('value')):<7} | {bucket(o.get('provenance')):<10} | {o.get('timestamp_utc')}")

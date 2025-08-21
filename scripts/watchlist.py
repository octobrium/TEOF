#!/usr/bin/env python3
import json
from pathlib import Path

def prov_bucket(p):
    if not p: return "missing"
    p = str(p)
    if p.startswith("auto:"): return "auto"
    if p.startswith("fallback:"): return p
    if p.startswith("manual://"): return "fallback:env"
    return "unknown"

def main():
    root = Path(__file__).resolve().parents[1]
    latest = root / "ocers_out" / "latest"
    j = json.loads((latest/"brief.json").read_text())
    obs = j.get("observations", [])
    lines = []
    lines.append("# TEOF Watchlist")
    lines.append("")
    levels = {
        "NVDA": {"low": 150.0, "high": 200.0},
        "PLTR": {"low": 20.0,  "high": 35.0},
        "MSTR": {"low": 300.0, "high": 600.0},
        "BTC":  {"low": 45000, "high": 80000}
    }
    assets = {o["label"].split()[0]: o for o in obs if " last" in o.get("label","") and isinstance(o.get("value"), (int,float))}
    lines.append("## Price nudges")
    for sym, band in levels.items():
        o = assets.get(sym)
        if not o: continue
        v = float(o["value"])
        if v <= band["low"]:
            lines.append(f"- {sym}: {v} <= {band['low']} → consider accumulate (prov={prov_bucket(o.get('provenance'))})")
        elif v >= band["high"]:
            lines.append(f"- {sym}: {v} >= {band['high']} → consider trim/hedge (prov={prov_bucket(o.get('provenance'))})")
    lines.append("")
    lines.append("## Event alerts")
    for o in obs:
        if o.get("label","").startswith("EVT"):
            sev = o["label"].split("(")[-1].rstrip(")")
            lines.append(f"- [{sev}] {o.get('value')}  ({o.get('source')})")
    (latest/"watchlist.md").write_text("\n".join(lines))
    print("watchlist written:", latest/"watchlist.md")
if __name__ == "__main__":
    main()

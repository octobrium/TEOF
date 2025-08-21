#!/usr/bin/env python3
import json, sys, time
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ocers_out"
CFG_EVENTS = ROOT / "config" / "events.json"
ASSETS = {"BTC","IBIT","NVDA","PLTR","MSTR"}  # edit anytime

def _utcnow(): return datetime.now(timezone.utc)
def _parse_iso(s):
    try: return datetime.fromisoformat(s.replace("Z","+00:00"))
    except: return None

def _load_latest_brief():
    if not OUT.exists(): return None
    latest = sorted([p for p in OUT.iterdir() if p.is_dir()])[-1]
    p = latest / "brief.json"
    if not p.exists(): return None
    return json.loads(p.read_text())

def _load_events_cfg():
    if CFG_EVENTS.exists():
        return json.loads(CFG_EVENTS.read_text())
    return {"fresh_hours": 24, "sources": []}

def main():
    brief = _load_latest_brief()
    if not brief:
        print("no brief.json found; run: make brief", file=sys.stderr); sys.exit(1)

    cfg = _load_events_cfg()
    horizon = timedelta(hours=int(cfg.get("fresh_hours", 24)))
    now = _utcnow()

    obs = brief.get("observations", [])
    hits = []
    for o in obs:
        label = str(o.get("label","")).lower()
        ts = _parse_iso(str(o.get("timestamp_utc","")))
        prov = str(o.get("provenance",""))
        src = str(o.get("source",""))
        if not ts: continue
        if now - ts > horizon: continue

        is_evt = label.startswith("evt ")
        if not is_evt: continue

        sev = "low"
        for s in cfg.get("sources", []):
            if s["name"] in src:
                sev = s.get("severity","low")
                break

        # simple impact heuristic: macro tags always matter; or names that match tracked assets
        impact = []
        for a in ASSETS:
            if a.lower() in (label + " " + src):
                impact.append(a)
        if any(t in (label + " " + src) for t in ["macro","monetary","fomc","rates","yields","treasury","sec"]):
            impact.append("macro")

        if sev == "high" and impact:
            hits.append((ts.isoformat(), sev, ",".join(sorted(set(impact))), o.get("label",""), src))

    if not hits:
        print("watchlist: no high-severity fresh impacts.")
        return

    print("watchlist alerts:")
    for ts, sev, imp, lbl, src in sorted(hits, reverse=True):
        print(f"- [{sev.upper()}] {ts} impact={imp} :: {lbl} :: {src}")

if __name__ == "__main__":
    main()

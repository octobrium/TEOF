#!/usr/bin/env python3
import json, hashlib, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = Path(os.environ.get("TEOF_OUT_DIR", ROOT / "artifacts" / "ocers_out"))
RINGS_FILE = ROOT / "rings" / "anchors.json"
def latest_dir():
    dirs = [p for p in OUT_ROOT.iterdir() if p.is_dir()]
    if not dirs: raise SystemExit(f"No runs in {OUT_ROOT}")
    return sorted(dirs)[-1]
run_dir = latest_dir()
brief = run_dir / "brief.json"
sha = hashlib.sha256(brief.read_bytes()).hexdigest()
ts = run_dir.name
RINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
ledger = json.loads(RINGS_FILE.read_text()) if RINGS_FILE.exists() else []
if not any(e.get("ts")==ts and e.get("sha256")==sha for e in ledger):
    ledger.append({"ts": ts, "sha256": sha})
    RINGS_FILE.write_text(json.dumps(ledger, indent=2))
    print(f"Anchored: ts={ts} sha256={sha}")
else:
    print(f"Anchor already present for ts={ts}")

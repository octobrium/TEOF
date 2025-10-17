#!/usr/bin/env python3
import os, json, re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
BROOT = ROOT/"_report"/"autocollab"
OUT   = ROOT/"docs"/"proposals"

MIN_SCORE = int(float(os.getenv("MIN_SCORE", "7")))     # systemic total >= 7/10
MAX_RISK  = float(os.getenv("MAX_RISK", "0.40"))        # critic risk_score <= 0.40 (~low)
MAX_ITEMS = int(os.getenv("MAX_ITEMS", "3"))            # promote at most N
REQUIRE_ACCEPTED = os.getenv("REQUIRE_ACCEPTED", "1") == "1"

def latest_batch():
    if not BROOT.exists(): return None
    batches = [p for p in BROOT.iterdir() if p.is_dir()]
    return max(batches) if batches else None

def load_json(p:Path):
    try: return json.loads(p.read_text())
    except Exception: return {}

def pick_items(bdir:Path):
    items = []
    for it in sorted(bdir.glob("item-*")):
        s = load_json(it/"score.json")
        r = load_json(it/"risk.json")
        a = load_json(it/"accepted.json")
        total = int(s.get("total",0))
        rscore = float(r.get("risk_score", 1.0))
        ok = total >= MIN_SCORE and rscore <= MAX_RISK
        if REQUIRE_ACCEPTED and not a.get("accepted"): ok = False
        if ok:
            items.append(dict(dir=it, total=total, risk=rscore))
    # Highest score first, then lowest risk
    items.sort(key=lambda d: (-d["total"], d["risk"]))
    return items[:MAX_ITEMS]

def write_draft(batch_ts:str, itmeta:dict, idx:int):
    it = Path(itmeta["dir"])
    prop = it/"proposal.md"
    if not prop.exists(): return None
    text = prop.read_text(encoding="utf-8", errors="ignore")
    # minimal scrub: ensure LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    OUT.mkdir(parents=True, exist_ok=True)
    fname = f"{batch_ts}__item-{idx:02d}__draft.md"
    p = OUT/fname
    header = [
        f"---",
        f"title: Auto-imported proposal (batch {batch_ts}, item {idx:02d})",
        f"batch: {batch_ts}",
        f"item: {idx:02d}",
        f"systemic_total: {itmeta['total']}",
        f"risk_score: {itmeta['risk']}",
        f"generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"note: docs-only draft; no invariants touched",
        f"---",
        "",
        "# Proposal (draft)",
        "",
    ]
    p.write_text("\n".join(header)+text, encoding="utf-8")
    return p

def main():
    b = latest_batch()
    if not b:
        print("doc-autopr: no batch found; run tools/autocollab.sh first")
        return
    batch_ts = b.name
    picked = pick_items(b)
    if not picked:
        print("doc-autopr: nothing meets thresholds "
              f"(MIN_SCORE={MIN_SCORE}, MAX_RISK={MAX_RISK}, REQUIRE_ACCEPTED={REQUIRE_ACCEPTED})")
        return
    created = []
    for i,meta in enumerate(picked, start=1):
        # item folder name ends with item-XX, extract XX
        try:
            idx = int(Path(meta["dir"]).name.split("-")[-1])
        except Exception:
            idx = i
        p = write_draft(batch_ts, meta, idx)
        if p: created.append(str(p.relative_to(ROOT)))
    print("doc-autopr: created drafts:")
    for c in created: print("  -", c)

if __name__ == "__main__":
    main()

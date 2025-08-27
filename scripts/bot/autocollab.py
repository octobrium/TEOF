#!/usr/bin/env python3
import os, time, json, shutil
from pathlib import Path
from datetime import datetime, timezone
from subprocess import run, PIPE

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT/"queue"
REPORT = ROOT/"_report"/"autocollab"

def ts():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def git_meta():
    try:
        rev = run(["git","rev-parse","--short","HEAD"], cwd=ROOT, text=True, stdout=PIPE).stdout.strip()
    except Exception:
        rev = "unknown"
    return {"commit": rev, "when": ts()}

def ensure_dir(d:Path): d.mkdir(parents=True, exist_ok=True)

def main():
    ensure_dir(REPORT)
    batch_dir = REPORT/ts()
    ensure_dir(batch_dir)

    items = sorted(QUEUE.glob("*.md"))
    if not items:
        print("No queue items. Add tasks to queue/*.md"); return

    for i,p in enumerate(items, start=1):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        item_dir = batch_dir/f"item-{i:02d}"
        ensure_dir(item_dir)
        (item_dir/"task.md").write_text(txt, encoding="utf-8")

        # Placeholder "proposal"—future: call LLM(s); for now copy task
        (item_dir/"proposal.md").write_text(txt, encoding="utf-8")

        # Score via minimal OCERS stub
        scorer = ROOT/"teof"/"eval"/"ocers_min.py"
        if scorer.exists():
            out = run([str(scorer), str(item_dir/"proposal.md")], text=True, stdout=PIPE).stdout
            (item_dir/"score.json").write_text(out or "{}", encoding="utf-8")

        # Metadata
        meta = {"meta": git_meta(), "source_task": p.name}
        (item_dir/"meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Wrote dry-run batch: {batch_dir}")

if __name__ == "__main__":
    main()

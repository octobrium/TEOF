#!/usr/bin/env python3
"""End-to-end reconciliation pipeline (prototype)."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent

HELLO = SCRIPT_DIR / "reconcile_hello.py"
DIFF = SCRIPT_DIR / "reconcile_diff.py"
FETCH = SCRIPT_DIR / "reconcile_fetch.py"
MERGE = SCRIPT_DIR / "reconcile_merge.py"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run reconciliation pipeline against peer")
    parser.add_argument("peer_packet", help="Hello packet from peer (JSON)")
    parser.add_argument("--instance-id", default="local", help="Instance id for new hello packet")
    parser.add_argument("--out-dir", default="_report/reconciliation/pipeline", help="Directory for outputs")
    parser.add_argument("--capability", action="append", default=[], help="Capability tag to advertise")
    parser.add_argument("--include-receipt", action="append", default=[], help="Local receipt to include")
    args = parser.parse_args()

    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    local_hello = out_dir / "hello.local.json"
    cmd = [sys.executable, str(HELLO), args.instance_id, "--output", str(local_hello)]
    for cap in args.capability:
        cmd.extend(["--capability", cap])
    for receipt in args.include_receipt:
        cmd.extend(["--receipt", receipt])
    hello_proc = run(cmd)
    if hello_proc.returncode != 0:
        sys.stderr.write(hello_proc.stderr)
        return hello_proc.returncode

    diff_proc = run([sys.executable, str(DIFF), str(local_hello), args.peer_packet])
    sys.stdout.write(diff_proc.stdout)
    sys.stderr.write(diff_proc.stderr)

    fetched_dir = out_dir / "fetched"
    fetch_proc = run([sys.executable, str(FETCH), args.peer_packet, str(fetched_dir)])
    sys.stdout.write(fetch_proc.stdout)
    sys.stderr.write(fetch_proc.stderr)

    merge_summary = out_dir / "merge-summary.json"
    merge_proc = run([sys.executable, str(MERGE), str(local_hello), args.peer_packet, "--output", str(merge_summary)])
    sys.stdout.write(merge_proc.stdout)
    sys.stderr.write(merge_proc.stderr)

    summary = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "local_packet": str(local_hello.relative_to(ROOT)),
        "peer_packet": args.peer_packet,
        "diff_exit": diff_proc.returncode,
        "fetch_exit": fetch_proc.returncode,
        "merge_output": str(merge_summary.relative_to(ROOT)),
    }
    metrics_path = out_dir / 'metrics.jsonl'
    metrics_entry = {
        "generated": summary['generated'],
        "local_instance": summary['local_packet'],
        "peer_packet": summary['peer_packet'],
        "diff_exit": summary['diff_exit'],
        "fetch_exit": summary['fetch_exit'],
        "matches": summary['diff_exit'] == 0,
    }
    with metrics_path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(metrics_entry, ensure_ascii=False) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if merge_proc.returncode == 0 else merge_proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())

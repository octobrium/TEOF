#!/usr/bin/env python3
"""Execute shell commands with receipts and optional caching."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RECEIPT_DIR = ROOT / "_report" / "runner"
CACHE_DIR = ROOT / ".cache" / "runner"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run commands with receipts and cache")
    parser.add_argument("--cache", action="store_true", help="Use cached result when available")
    parser.add_argument("--force", action="store_true", help="Ignore cache even if present")
    parser.add_argument("--label", help="Optional label for the receipt")
    parser.add_argument("--receipt-dir", default=str(DEFAULT_RECEIPT_DIR))
    parser.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to execute (prefix with --)")
    args = parser.parse_args()
    if not args.cmd:
        parser.error("provide command after `--`")
    if args.cmd[0] == "--":
        args.cmd = args.cmd[1:]
    if not args.cmd:
        parser.error("provide command after `--`")
    return args


def command_hash(cmd: List[str], cwd: Path) -> str:
    h = hashlib.sha256()
    h.update("\0".join(cmd).encode("utf-8"))
    h.update(str(cwd).encode("utf-8"))
    env_keys = ["PYTHONPATH"]
    for key in env_keys:
        h.update(f"{key}={os.environ.get(key,'')}".encode("utf-8"))
    return h.hexdigest()


def load_cache(cache_path: Path) -> dict | None:
    if not cache_path.exists():
        return None
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def save_cache(cache_path: Path, payload: dict) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_receipt(receipt_dir: Path, payload: dict) -> Path:
    receipt_dir.mkdir(parents=True, exist_ok=True)
    ts = payload["timestamp"].replace(":", "").replace("-", "")
    short = payload["hash"][:8]
    path = receipt_dir / f"{ts}-{short}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    args = parse_args()
    cwd = Path.cwd()
    digest = command_hash(args.cmd, cwd)
    cache_path = CACHE_DIR / f"{digest}.json"

    cached_payload = None
    if args.cache and not args.force:
        cached_payload = load_cache(cache_path)

    if cached_payload:
        print(f"[runner] cache hit ({cache_path})")
        if cached_payload.get("stdout"):
            sys.stdout.write(cached_payload["stdout"])
        if cached_payload.get("stderr"):
            sys.stderr.write(cached_payload["stderr"])
        return cached_payload.get("exit_code", 0)

    print(f"[runner] exec: {' '.join(args.cmd)}")
    proc = subprocess.run(args.cmd, capture_output=True, text=True)

    payload = {
        "timestamp": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "label": args.label,
        "command": args.cmd,
        "cwd": str(cwd),
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "hash": digest,
        "cached": False,
    }

    plan_id = os.environ.get("TEOF_PLAN_ID")
    plan_step_id = os.environ.get("TEOF_PLAN_STEP_ID")
    if plan_id:
        payload["plan_id"] = plan_id
    if plan_step_id:
        payload["plan_step_id"] = plan_step_id

    save_cache(cache_path, payload)
    receipt_path = save_receipt(Path(args.receipt_dir), payload)
    print(f"[runner] receipt: {receipt_path.relative_to(ROOT)}")

    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())

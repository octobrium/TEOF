#!/usr/bin/env python3
"""
TEOF anchors tool (minimal, future-proof)

Subcommands:
  init                 -> create governance/anchors.json if missing
  append "note ..."    -> append an event (auto ts/by/prev_content_hash)
  verify               -> check append-only vs previous committed file
  show                 -> print a short summary

Design:
- No heredocs, no shell gymnastics.
- Uses `git show HEAD:governance/anchors.json` to obtain the previous
  committed content and compute prev_content_hash for verify.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, subprocess, sys, getpass, shutil
from typing import Any, Dict

ANCHORS_PATH = os.path.join("governance", "anchors.json")


def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256(); h.update(b); return h.hexdigest()


def read_file_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_or_seed(path: str) -> Dict[str, Any]:
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "version": 1,
        "policy": "append-only",
        "anchors": [],
        "immutable_scope": ["capsule.txt", "hashes.json"],
        "events": [],
        "releases": []
    }


def git_prev_bytes(path: str) -> bytes | None:
    # Return bytes of the file as of HEAD, or None if no commit yet
    try:
        # Ensure the file has been committed at least once
        revs = subprocess.check_output(
            ["git", "rev-list", "-n", "1", "HEAD", "--", path],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        if not revs:
            return None
        return subprocess.check_output(
            ["git", "show", f"HEAD:{path}"], stderr=subprocess.DEVNULL
        )
    except Exception:
        return None


def cmd_init(args) -> int:
    data = load_or_seed(ANCHORS_PATH)
    write_json(ANCHORS_PATH, data)
    print(f"initialized {ANCHORS_PATH}")
    return 0


def cmd_append(args) -> int:
    note = args.note
    now = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    by = os.environ.get("GITHUB_ACTOR") or getpass.getuser() or "unknown"

    # prev_content_hash = sha256(previous file content)
    prev = git_prev_bytes(ANCHORS_PATH)
    prev_hash = sha256_bytes(prev) if prev is not None else None

    # load current (or seed), then append event
    data = load_or_seed(ANCHORS_PATH)
    event = {"ts": now, "by": by, "note": note}
    if prev_hash:
        event["prev_content_hash"] = prev_hash
    data.setdefault("events", []).append(event)
    write_json(ANCHORS_PATH, data)

    print(f"appended: ts={now} by={by}")
    if prev_hash:
        print(f"prev_content_hash={prev_hash[:12]}…")
    return 0


def cmd_verify(args) -> int:
    if not os.path.isfile(ANCHORS_PATH):
        print(f"::warning::{ANCHORS_PATH} missing")
        return 0

    cur = read_file_bytes(ANCHORS_PATH)
    cur_hash = sha256_bytes(cur)
    prev = git_prev_bytes(ANCHORS_PATH)
    if prev is None:
        print("no prior commit for anchors; nothing to verify")
        return 0

    if sha256_bytes(prev) == cur_hash:
        print("anchors unchanged since last commit")
        return 0

    try:
        data = json.loads(cur.decode("utf-8"))
    except Exception as e:
        print(f"::error::invalid JSON: {e}")
        return 1

    events = data.get("events") or []
    if not events:
        print("::error::anchors changed but no events present")
        return 1

    last = events[-1]
    want = sha256_bytes(prev)
    got = last.get("prev_content_hash")
    if got != want:
        print("::error::append-only violation: last event.prev_content_hash "
              f"!= sha256(previous content)\n expected={want}\n      got={got}")
        return 1

    print("append-only OK")
    return 0


def cmd_show(args) -> int:
    if not os.path.isfile(ANCHORS_PATH):
        print(f"{ANCHORS_PATH} not found")
        return 0
    with open(ANCHORS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    evs = data.get("events") or []
    print(f"{ANCHORS_PATH}: {len(evs)} event(s)")
    for e in evs[-5:]:
        print(f" - {e.get('ts')} by {e.get('by')}: {e.get('note')}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="anchors", description="TEOF governance anchors tool")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="seed anchors.json if missing")
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("append", help="append an event with auto prev hash")
    sp.add_argument("note", help="event note/description")
    sp.set_defaults(func=cmd_append)

    sp = sub.add_parser("verify", help="verify append-only vs previous commit")
    sp.set_defaults(func=cmd_verify)

    sp = sub.add_parser("show", help="show last events")
    sp.set_defaults(func=cmd_show)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

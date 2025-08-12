#!/usr/bin/env python3
import argparse, hashlib, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_json(p: Path):
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}

def write_json_sorted(p: Path, obj: dict):
    # Stable key order, pretty formatting, newline at EOF
    p.write_text(json.dumps(dict(sorted(obj.items())), indent=2) + "\n", encoding="utf-8")

def ensure_file(p: Path, header: str):
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(header, encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--capsule-dir", required=True)      # e.g., capsule/v1.5
    ap.add_argument("--hashes", required=True)           # e.g., capsule/v1.5/hashes.json
    ap.add_argument("--provenance", required=True)       # e.g., capsule/v1.5/PROVENANCE.md
    args = ap.parse_args()

    repo = Path(args.root).resolve()
    capdir = (repo / args.capsule-dir).resolve()
    hashes_path = (repo / args.hashes).resolve()
    prov_path = (repo / args.provenance).resolve()

    # Files to hash: allowlist by directory (v1.5), but skip the generated files themselves.
    tracked = []
    for p in capdir.glob("*"):
        if p.is_file():
            rel = p.relative_to(repo).as_posix()
            if rel not in {args.hashes, args.provenance}:
                tracked.append(p)

    old = load_json(hashes_path)
    new = {}

    # Compute fresh hashes
    for p in tracked:
        rel = p.relative_to(repo).as_posix()
        new[rel] = sha256_file(p)

    # Determine changes (additions / removals / mods)
    changed = []
    all_keys = set(old.keys()) | set(new.keys())
    for k in sorted(all_keys):
        if old.get(k) != new.get(k):
            changed.append(k)

    if not changed:
        print("No changes detected in tracked capsule files.")
        return 0

    # Write hashes.json
    write_json_sorted(hashes_path, new)
    print(f"Updated {hashes_path}")

    # Prepare provenance header if new
    prov_header = (
        "# PROVENANCE — TEOF Capsule v1.5\n\n"
        "This log appends verifiable updates to the canonical v1.5 capsule artifacts.\n\n"
    )
    ensure_file(prov_path, prov_header)

    # Append provenance entry
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    commit = os.getenv("GITHUB_SHA", "unknown")
    actor = os.getenv("GITHUB_ACTOR", "unknown")

    lines = []
    lines.append(f"## Update — {ts}")
    lines.append(f"- Source commit: `{commit}`")
    lines.append(f"- Actor: `{actor}`")
    lines.append(f"- Changed files ({len(changed)}):")
    for k in changed:
        lines.append(f"  - `{k}`: `{old.get(k, '∅')}` → `{new.get(k, '∅')}`")
    lines.append("")  # newline

    with prov_path.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Appended provenance entry to {prov_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

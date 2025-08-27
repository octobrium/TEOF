#!/usr/bin/env python3
import os, sys, json, hashlib, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def regen_hashes(capsule_dir: Path):
    files = []
    for p in sorted(capsule_dir.rglob("*")):
        if p.is_file() and p.name != "hashes.json" and ".DS_Store" not in p.name:
            rel = p.relative_to(capsule_dir).as_posix()
            files.append({"path": rel, "sha256": sha256_file(p)})
    return {"root": capsule_dir.name, "count": len(files), "files": files}

def verify_one(hfile: Path):
    capsule_dir = hfile.parent
    data = json.loads(hfile.read_text())
    # structural checks
    assert data["root"] == capsule_dir.name, f"{hfile}: root mismatch"
    assert isinstance(data.get("files"), list), f"{hfile}: files[] missing"
    # sorted paths
    paths = [f["path"] for f in data["files"]]
    assert paths == sorted(paths), f"{hfile}: files not sorted by path"
    # no duplicates
    assert len(paths) == len(set(paths)), f"{hfile}: duplicate entries"
    # deterministic regeneration
    regen = regen_hashes(capsule_dir)
    if regen != data:
        # Write diff artifact to help debugging in CI
        out = ROOT / "_report" / "freeze-verify"
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{capsule_dir.name}.expected.json").write_text(json.dumps(regen, indent=2))
        (out / f"{capsule_dir.name}.actual.json").write_text(json.dumps(data, indent=2))
        raise AssertionError(f"{hfile}: content differs from deterministic regeneration")

def changed_hashes(base_ref="origin/main"):
    try:
        out = subprocess.check_output(["git","diff","--name-only",f"{base_ref}...HEAD"], cwd=ROOT, text=True)
    except Exception:
        out = ""
    files = [ROOT / p for p in out.splitlines() if p.endswith("/hashes.json")]
    return [p for p in files if p.exists()]

def main():
    base = os.environ.get("BASE_REF","origin/main")
    targets = changed_hashes(base)
    if not targets:
        print("freeze-verify: no capsule hashes.json changes"); return
    for t in targets:
        verify_one(t)
        print(f"freeze-verify: OK {t}")
    print("freeze-verify: all good")
if __name__ == "__main__":
    main()

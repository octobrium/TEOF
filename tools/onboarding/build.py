"""Build the TEOF package and emit a receipt."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
DIST_DIR = ROOT / "dist"
REPORT_DIR = ROOT / "_report" / "usage" / "onboarding"


def _ensure_build_module() -> None:
    try:
        import build  # type: ignore
    except ModuleNotFoundError:
        subprocess.run([sys.executable, "-m", "pip", "install", "build"], check=True)


def _sha256(path: Path, chunk_size: int = 65536) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def build_package(outdir: Path) -> list[Path]:
    _ensure_build_module()
    outdir.mkdir(parents=True, exist_ok=True)
    before = set(outdir.glob("*"))
    cmd = [sys.executable, "-m", "build", "--outdir", str(outdir)]
    subprocess.run(cmd, check=True, cwd=ROOT)
    after = set(outdir.glob("*"))
    created = sorted(after - before)
    if not created:
        # fallback: include most recent artifacts (build may overwrite files)
        created = sorted(after, key=lambda p: p.stat().st_mtime, reverse=True)[:2]
    return created


def write_receipt(artifacts: Iterable[Path], out_path: Path) -> Path:
    timestamp = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "generated_at": timestamp,
        "python": sys.version,
        "command": [sys.executable, "-m", "build", "--outdir", str(DIST_DIR.relative_to(ROOT))],
        "artifacts": [
            {
                "path": _relative(path),
                "sha256": _sha256(path),
                "size": path.stat().st_size,
            }
            for path in artifacts
        ],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        help="Optional receipt path (default: _report/usage/onboarding/build-<UTC>.json)",
    )
    parser.add_argument(
        "--dist",
        type=Path,
        default=DIST_DIR,
        help="Output directory for build artifacts (default: dist/)",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    artifacts = build_package(args.dist)
    if not artifacts:
        print("::warning:: No build artifacts detected", file=sys.stderr)
    timestamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or (REPORT_DIR / f"build-{timestamp}.json")
    receipt = write_receipt(artifacts, out_path)
    print(f"build: wrote receipt → {_relative(receipt)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

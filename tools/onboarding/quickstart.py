"""Run the onboarding quickstart in a fresh virtualenv and emit receipts."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / ".cache"
DEFAULT_VENV = CACHE_DIR / "onboarding-venv"
REPORT_DIR = ROOT / "_report" / "usage" / "onboarding"
ARTIFACTS_DIR = ROOT / "artifacts" / "ocers_out"


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _latest_wheel(dist_dir: Path) -> Path | None:
    wheels = sorted(dist_dir.glob("*.whl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return wheels[0] if wheels else None


def _python_executable(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def _teof_executable(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "teof.exe"
    return venv / "bin" / "teof"


def _create_venv(venv: Path) -> None:
    if venv.exists():
        shutil.rmtree(venv)
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _run(cmd: Iterable[str], *, cwd: Path | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=True,
        cwd=cwd,
        text=True,
        capture_output=capture,
    )


def run_quickstart(venv: Path, wheel: Path | None, *, use_editable: bool) -> dict:
    _create_venv(venv)
    py = _python_executable(venv)
    _run([str(py), "-m", "pip", "install", "--upgrade", "pip"], cwd=ROOT)
    install_source = "wheel"
    if wheel is not None:
        _run([str(py), "-m", "pip", "install", str(wheel)], cwd=ROOT)
    else:
        install_source = "editable" if use_editable else "sdist"
        target = [str(py), "-m", "pip", "install"]
        if use_editable:
            target.append("-e")
            target.append(str(ROOT))
        else:
            target.append(str(ROOT))
        _run(target, cwd=ROOT)
    teof = _teof_executable(venv)
    result = _run([str(teof), "brief"], cwd=ROOT, capture=True)

    latest_symlink = ARTIFACTS_DIR / "latest"
    latest_target = latest_symlink.resolve() if latest_symlink.exists() else None
    payload = {
        "install_source": install_source,
        "wheel": _relative(wheel) if wheel is not None else None,
        "teof_brief": {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
        "artifacts": {
            "latest_symlink": _relative(latest_symlink) if latest_symlink.exists() else None,
            "latest_target": _relative(latest_target) if latest_target else None,
        },
    }
    return payload


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--venv",
        type=Path,
        default=DEFAULT_VENV,
        help="Virtualenv location (default: .cache/onboarding-venv)",
    )
    parser.add_argument(
        "--wheel",
        type=Path,
        help="Optional wheel to install (defaults to latest dist/*.whl)",
    )
    parser.add_argument(
        "--dist",
        type=Path,
        default=ROOT / "dist",
        help="Directory to search for wheels (default: dist/)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Receipt path (default: _report/usage/onboarding/quickstart-<UTC>.json)",
    )
    parser.add_argument(
        "--editable",
        action="store_true",
        help="Fallback to editable install when no wheel is present",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    wheel = args.wheel
    if wheel is None:
        wheel = _latest_wheel(args.dist)
    payload = run_quickstart(args.venv, wheel, use_editable=args.editable)
    timestamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or (REPORT_DIR / f"quickstart-{timestamp}.json")
    _ensure_dir(out_path.parent)
    payload.update(
        {
            "generated_at": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "python": sys.version,
            "venv": _relative(args.venv),
        }
    )
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"quickstart: wrote receipt → {_relative(out_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

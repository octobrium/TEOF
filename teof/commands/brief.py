from __future__ import annotations

import datetime as dt
import json
import shutil
from argparse import Namespace
from pathlib import Path

from extensions.validator.scorers.ensemble import score_file
from teof._paths import repo_root

ROOT = repo_root(default=Path(__file__).resolve().parents[2])
EXAMPLES_DIR = ROOT / "docs" / "examples" / "brief" / "inputs"
ARTIFACT_ROOT = ROOT / "artifacts" / "systemic_out"


def _write_brief_outputs(output_dir: Path) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    files = sorted(EXAMPLES_DIR.glob("*.txt"))
    records: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    for path in files:
        try:
            result = score_file(path)
        except Exception as exc:  # pragma: no cover - exercised via dedicated test
            message = str(exc)
            records.append({"input": path.name, "status": "error", "error": message})
            failures.append({"input": path.name, "error": message})
            continue
        out_path = output_dir / f"{path.stem}.ensemble.json"
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        records.append(
            {
                "input": path.name,
                "output": out_path.name,
                "result": result,
                "status": "ok",
            }
        )
    return records, failures


def run(args: Namespace) -> int:
    fmt = getattr(args, "format", "text")
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dest = ARTIFACT_ROOT / timestamp
    dest.mkdir(parents=True, exist_ok=True)

    records, failures = _write_brief_outputs(dest)
    successful = [record for record in records if record.get("status") == "ok"]

    summary = {
        "generated_at": timestamp,
        "inputs": [record["input"] for record in records],
        "artifacts": [record["output"] for record in successful],
        "status": "ok" if not failures else "partial",
        "failures": failures,
        "failure_count": len(failures),
        "success_count": len(successful),
    }
    summary_path = dest / "brief.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (dest / "score.txt").write_text(f"ensemble_count={len(successful)}\n", encoding="utf-8")

    latest = ARTIFACT_ROOT / "latest"
    if latest.exists() or latest.is_symlink():
        if latest.is_symlink() or latest.is_file():
            latest.unlink()
        else:
            shutil.rmtree(latest)
    try:
        latest.symlink_to(dest, target_is_directory=True)
    except OSError:
        shutil.copytree(dest, latest)

    dest_rel = dest.relative_to(ROOT).as_posix()
    if fmt == "json":
        payload = {
            "generated_at": timestamp,
            "output_dir": dest_rel,
            "summary_path": summary_path.relative_to(ROOT).as_posix(),
            "inputs": summary["inputs"],
            "artifacts": summary["artifacts"],
            "artifact_paths": [
                (dest / record["output"]).relative_to(ROOT).as_posix() for record in successful
            ],
            "artifact_count": len(successful),
            "failures": failures,
            "failure_count": len(failures),
            "status": summary["status"],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"brief: wrote {dest_rel}")
    return 0 if not failures else 1


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    import argparse

    parser = subparsers.add_parser(
        "brief", help="Run bundled brief example through the ensemble scorer"
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format for the CLI summary (default: text)",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]

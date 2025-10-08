from __future__ import annotations

import datetime as dt
import json
import shutil
from argparse import Namespace
from pathlib import Path

from extensions.validator.scorers.ensemble import score_file

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = ROOT / "docs" / "examples" / "brief" / "inputs"
ARTIFACT_ROOT = ROOT / "artifacts" / "ocers_out"


def _write_brief_outputs(output_dir: Path) -> list[dict[str, object]]:
    files = sorted(EXAMPLES_DIR.glob("*.txt"))
    records: list[dict[str, object]] = []
    for path in files:
        result = score_file(path)
        out_path = output_dir / f"{path.stem}.ensemble.json"
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        records.append({"input": path.name, "output": out_path.name, "result": result})
    return records


def run(_: Namespace) -> int:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dest = ARTIFACT_ROOT / timestamp
    dest.mkdir(parents=True, exist_ok=True)

    records = _write_brief_outputs(dest)

    summary = {
        "generated_at": timestamp,
        "inputs": [record["input"] for record in records],
        "artifacts": [record["output"] for record in records],
    }
    (dest / "brief.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (dest / "score.txt").write_text(f"ensemble_count={len(records)}\n", encoding="utf-8")

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
    print(f"brief: wrote {dest.relative_to(ROOT)}")
    return 0


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    import argparse

    parser = subparsers.add_parser(
        "brief", help="Run bundled brief example through the ensemble scorer"
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]

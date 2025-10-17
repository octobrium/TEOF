#!/usr/bin/env python3
"""Systemic readiness validator CLI."""
from __future__ import annotations

import datetime
import hashlib
import json
import pathlib
import sys

from teof.eval.systemic_min import evaluate

__all__ = ["read_text", "evaluate_cli"]


def read_text(path: str) -> str:
    return pathlib.Path(path).read_text(encoding="utf-8", errors="ignore")


def evaluate_cli(raw_text: str) -> dict:
    return evaluate(raw_text)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 2:
        print("Usage: teof_systemic_min.py <input.txt> <outdir>")
        return 2

    inpath = pathlib.Path(args[0]).resolve()
    outdir = pathlib.Path(args[1]).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    raw = read_text(str(inpath))
    result = evaluate_cli(raw)

    scores = result["scores"]
    total = result["total"]
    verdict = result["verdict"]

    payload = {
        "stamp": datetime.datetime.utcnow().isoformat() + "Z",
        "input_file": inpath.name,
        "hash_sha256": hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest(),
        "systemic": {
            "Structure": float(scores.get("structure", 0)),
            "Alignment": float(scores.get("alignment", 0)),
            "Verification": float(scores.get("verification", 0)),
            "Risk": float(scores.get("risk", 0)),
            "Recovery": float(scores.get("recovery", 0)),
            "total": total,
            "verdict": verdict,
        },
        "signals": result["signals"],
    }
    output_path = outdir / f"{inpath.stem}.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[systemic] {inpath.stem}: total={total}/10 verdict={verdict} {scores}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

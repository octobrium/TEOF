#!/usr/bin/env python3
"""
TEOF OCERS Minimal Heuristic Validator (v0.5)
- Shared heuristics live in extensions.validator.ocers_rules
- Preserves CLI + helper functions consumed by the ensemble runner
"""

from __future__ import annotations

import datetime
import hashlib
import json
import pathlib
import sys

from .ocers_rules import (
    OCERSJudgement,
    evaluate_text,
    justify,
    norm_text,
    score_coherence,
    score_ethics,
    score_observation,
    score_repro,
    score_selfrepair,
)

__all__ = [
    "read_text",
    "norm_text",
    "score_observation",
    "score_coherence",
    "score_ethics",
    "score_repro",
    "score_selfrepair",
    "justify",
]


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        return handle.read()


def _evaluate(raw_text: str) -> OCERSJudgement:
    return evaluate_text(raw_text)


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: teof_ocers_min.py <input.txt> <outdir>")
        sys.exit(2)
    inpath = pathlib.Path(sys.argv[1]).resolve()
    outdir = pathlib.Path(sys.argv[2]).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    raw = read_text(str(inpath))
    judgement = _evaluate(raw)

    ocer_scores = judgement.scores
    total = judgement.total
    verdict = judgement.verdict

    src_hash = hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()
    stamp = datetime.datetime.utcnow().isoformat() + "Z"
    base = inpath.stem

    out_json = {
        "stamp": stamp,
        "input_file": inpath.name,
        "hash_sha256": src_hash,
        "ocers": {
            "O": ocer_scores["O"],
            "C": ocer_scores["C"],
            "E": ocer_scores["E"],
            "R": ocer_scores["R"],
            "S": ocer_scores["S"],
            "total": total,
            "verdict": verdict,
        },
        "notes": judgement.notes,
    }
    with open(outdir / f"{base}.json", "w", encoding="utf-8") as handle:
        json.dump(out_json, handle, ensure_ascii=False, indent=2)

    print(
        "[OCERS] {base}: total={total}/25 verdict={verdict} (O={O} C={C} E={E} R={R} S={S})".format(
            base=base,
            total=total,
            verdict=verdict,
            O=ocer_scores["O"],
            C=ocer_scores["C"],
            E=ocer_scores["E"],
            R=ocer_scores["R"],
            S=ocer_scores["S"],
        )
    )


if __name__ == "__main__":
    main()

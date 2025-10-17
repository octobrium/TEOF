#!/usr/bin/env python3
import argparse
import datetime
import hashlib
import json
import pathlib

from extensions.validator import teof_systemic_min as val


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Systemic readiness validator for a single text file.")
    parser.add_argument("input", help="Path to input .txt")
    parser.add_argument("outdir", help="Directory for outputs")
    args = parser.parse_args(argv)

    inpath = pathlib.Path(args.input).resolve()
    outdir = pathlib.Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    raw = val.read_text(str(inpath))
    result = val.evaluate_cli(raw)

    scores = result["scores"]
    total = result["total"]
    verdict = result["verdict"]

    out_json = {
        "stamp": datetime.datetime.utcnow().isoformat() + "Z",
        "input_file": inpath.name,
        "hash_sha256": hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest(),
        "systemic": {**scores, "total": total, "verdict": verdict},
        "signals": result["signals"],
    }
    base = inpath.stem
    with open(outdir / f"{base}.json", "w", encoding="utf-8") as f:
        json.dump(out_json, f, ensure_ascii=False, indent=2)
    print(f"[systemic] {base}: total={total}/10 {verdict} {scores}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

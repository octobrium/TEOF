#!/usr/bin/env python3
import argparse, json, sys, hashlib, datetime, re
from typing import Tuple, Dict

# Required OCERS fields and optional extras (kept minimal by design)
REQ = ["O","C","E","R","S"]
OPT = ["OpenQuestions"]

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def now_utc_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def load_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def try_parse_json(b: bytes) -> Tuple[bool, dict]:
    try:
        obj = json.loads(b.decode("utf-8"))
        if isinstance(obj, dict):
            return True, obj
        return False, {}
    except Exception:
        return False, {}

def parse_headed_text(s: str) -> Dict[str, str]:
    """
    Parse headed OCERS text:
      O: ...
      C: ...
      E: ...
      R: ...
      S: ...
    Accepts multi-line sections; continues until next recognized head.
    """
    out = {}
    heads = ["O","C","E","R","S","OpenQuestions"]
    pattern = re.compile(r"^([A-Za-z]+)\s*:\s*(.*)$")
    current = None
    for raw in s.splitlines():
        line = raw.rstrip()
        m = pattern.match(line.strip())
        if m and m.group(1) in heads:
            current = m.group(1)
            out.setdefault(current, "")
            out[current] = m.group(2).strip()
        elif current:
            out[current] = (out[current] + "\n" + line).strip()
    return out

def normalize_obj(obj: dict) -> dict:
    # Keep required + optional only and coerce to strings
    clean = {}
    for k in REQ:
        if k in obj:
            clean[k] = str(obj[k]).strip()
    if "OpenQuestions" in obj:
        clean["OpenQuestions"] = str(obj["OpenQuestions"]).strip()
    return clean

def validate_ocers_obj(obj: dict):
    reasons = []
    missing = [k for k in REQ if k not in obj]
    empty = [k for k in REQ if not str(obj.get(k, "")).strip()]
    extra = [k for k in obj.keys() if k not in REQ + OPT]
    if missing: reasons.append(f"missing={','.join(missing)}")
    if empty: reasons.append(f"empty={','.join(empty)}")
    if extra: reasons.append(f"extra={','.join(extra)}")
    return (len(reasons) == 0, reasons)

def main():
    ap = argparse.ArgumentParser(description="TEOF OCERS Validator (minimal v0.1)")
    ap.add_argument("--input", required=True, help="Path to OCERS output (JSON or headed text)")
    ap.add_argument("--runmeta", required=True, help="Path to run meta JSON (model, runner_digest, temp)")
    ap.add_argument("--commit", required=True, help="Commit short SHA or identifier")
    ap.add_argument("--receipt-json", default=None, help="Optional: write machine-readable receipt JSON")
    ap.add_argument("--schema", default=None, help="(Reserved) optional custom schema path")
    args = ap.parse_args()

    ts = now_utc_iso()
    reasons = []
    passed = True
    is_json = False

    # Read inputs
    try:
        out_bytes = load_bytes(args.input)
    except Exception as e:
        print(f"FAIL: cannot read input ({e})")
        sys.exit(3)

    try:
        meta = json.loads(load_bytes(args.runmeta).decode("utf-8"))
    except Exception as e:
        print(f"FAIL: cannot read runmeta ({e})")
        sys.exit(3)

    # Parse JSON first; fallback to headed text
    j_ok, j_obj = try_parse_json(out_bytes)
    if j_ok:
        is_json = True
        ocers = normalize_obj(j_obj)
    else:
        headed = out_bytes.decode("utf-8", errors="replace")
        ocers = normalize_obj(parse_headed_text(headed))

    ok, why = validate_ocers_obj(ocers)
    if not ok:
        passed = False
        reasons.extend(why)

    # Single-line receipt to STDOUT (human- and machine-greppable)
    # Format:
    #   OCERS-VALIDATOR v0.1 | verdict=PASS/FAIL | commit=... | model=... | runner=... | ocers_json=0/1 | out_sha256=... | utc=...
    receipt = {
        "verdict": "PASS" if passed else "FAIL",
        "commit": args.commit,
        "model": str(meta.get("model", "unknown")),
        "runner": str(meta.get("runner_digest", "unknown")),
        "ocers_json": 1 if is_json else 0,
        "out_sha256": sha256_bytes(out_bytes),
        "utc": ts
    }
    line = (
        f"OCERS-VALIDATOR v0.1 | verdict={receipt['verdict']} | "
        f"commit={receipt['commit']} | model={receipt['model']} | "
        f"runner={receipt['runner']} | ocers_json={receipt['ocers_json']} | "
        f"out_sha256={receipt['out_sha256']} | utc={receipt['utc']}"
    )
    if reasons:
        line += " | reasons=" + ";".join(reasons)
    print(line)

    # Optional JSON artifact
    if args.receipt_json:
        try:
            with open(args.receipt_json, "w") as f:
                json.dump({**receipt, "reasons": reasons, "ocers": ocers}, f, indent=2)
        except Exception as e:
            # Non-fatal
            print(f"WARN: could not write receipt JSON ({e})", file=sys.stderr)

    # Exit codes
    if not passed:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()

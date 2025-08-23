#!/usr/bin/env python3
"""
TEOF bootloader (minimal)
- Validates an OCERS file (JSON or headed text) by calling the validator extension.
- Writes a machine-readable receipt into reports/.
"""
import argparse, json, os, re, subprocess, sys, hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
EXT_VALIDATOR = ROOT / "extensions" / "validator" / "teof_validator.py"
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

def utc_stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def git_short():
    try:
        return subprocess.check_output(["git","rev-parse","--short","HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "nogit"

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def parse_headed_text(text: str):
    fields = {"O":"", "C":"", "E":"", "R":"", "S":""}
    curr = None
    for line in text.splitlines():
        m = re.match(r"^\s*([OCERS]):\s*(.*)$", line)
        if m:
            curr = m.group(1)
            fields[curr] = m.group(2).strip()
        elif curr:
            fields[curr] = (fields[curr] + "\n" + line).strip()
    return fields

def ensure_ocers_json(input_path: Path) -> Path:
    raw = input_path.read_text(encoding="utf-8")
    try:
        obj = json.loads(raw)
        data = {k: str(obj.get(k,"")).strip() for k in ["O","C","E","R","S"]}
    except Exception:
        data = parse_headed_text(raw)
    out = REPORTS / f"tmp-ocers-{utc_stamp()}.json"
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return out

def write_runmeta() -> Path:
    rm = {
        "model": "unknown",
        "runner_digest": sha256_bytes(Path(__file__).read_bytes()),
        "temp": "n/a",
        "ts": utc_stamp(),
    }
    p = REPORTS / f"runmeta-{utc_stamp()}.json"
    p.write_text(json.dumps(rm, indent=2), encoding="utf-8")
    return p

def run_validator(ocers_json: Path, runmeta: Path, commit_short: str, receipt_path: Path) -> int:
    if not EXT_VALIDATOR.exists():
        print(f"ERROR: validator not found at {EXT_VALIDATOR}", file=sys.stderr)
        return 2
    cmd = [
        sys.executable,
        str(EXT_VALIDATOR),
        "--input", str(ocers_json),
        "--runmeta", str(runmeta),
        "--commit", commit_short,
        "--receipt-json", str(receipt_path),
    ]
    proc = subprocess.run(cmd, cwd=ROOT)
    return proc.returncode

def main():
    ap = argparse.ArgumentParser(description="TEOF CLI bootloader")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_val = sub.add_parser("validate", help="Validate an OCERS file (JSON or headed text)")
    ap_val.add_argument("path", help="Path to OCERS content")

    ap_frz = sub.add_parser("freeze", help="Regenerate capsule/current/hashes.json")

    args = ap.parse_args()

    if args.cmd == "freeze":
        script = ROOT / "scripts" / "freeze.sh"
        if not script.exists():
            print("ERROR: scripts/freeze.sh not found", file=sys.stderr)
            sys.exit(1)
        sys.exit(subprocess.run([script.as_posix()], cwd=ROOT).returncode)

    if args.cmd == "validate":
        input_path = Path(args.path).expanduser().resolve()
        if not input_path.exists():
            print(f"ERROR: file not found: {input_path}", file=sys.stderr)
            sys.exit(1)
        ocers_json = ensure_ocers_json(input_path)
        runmeta = write_runmeta()
        receipt = REPORTS / f"receipt-{utc_stamp()}.json"
        rc = run_validator(ocers_json, runmeta, git_short(), receipt)
        # pretty summary
        try:
            data = json.loads(receipt.read_text(encoding="utf-8"))
            passed = data.get("passed")
            reasons = data.get("reasons", [])
            print(f"\nResult: {'PASS ✅' if passed else 'FAIL ❌'}")
            if reasons:
                print("Reasons:", "; ".join(map(str, reasons)))
            print(f"Receipt: {receipt}")
        except Exception:
            print(f"Receipt: {receipt} (could not read JSON)", file=sys.stderr)
        sys.exit(rc)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run scaffold verification commands and emit hashed receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_ROOT = ROOT / "docs" / "receipts" / "attest"
INDEX_PATH = ROOT / "docs" / "receipts" / "index.md"


class StepResult(dict):
    """Dictionary with typed helpers for step results."""

    @property
    def success(self) -> bool:
        return bool(self.get("success", False))


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_bytes(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return _sha256(data)


def _run_command(cmd: str, *, dest: Path, name: str) -> StepResult:
    result = subprocess.run(
        ["bash", "-lc", cmd],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    stdout_bytes = result.stdout.encode("utf-8")
    stderr_bytes = result.stderr.encode("utf-8")
    stdout_path = dest / f"{name}.stdout.txt"
    stderr_path = dest / f"{name}.stderr.txt"
    stdout_sha = _write_bytes(stdout_path, stdout_bytes)
    stderr_sha = _write_bytes(stderr_path, stderr_bytes)
    return StepResult(
        name=name,
        command=cmd,
        exit_code=result.returncode,
        stdout_path=str(stdout_path.relative_to(ROOT)),
        stderr_path=str(stderr_path.relative_to(ROOT)),
        stdout_sha256=stdout_sha,
        stderr_sha256=stderr_sha,
        success=result.returncode == 0,
    )


def _log_summary() -> dict[str, int]:
    log_path = ROOT / "memory" / "log.jsonl"
    log_entries = 0
    if log_path.exists():
        with log_path.open(encoding="utf-8") as handle:
            for _ in handle:
                log_entries += 1
    state_path = ROOT / "memory" / "state.json"
    facts = 0
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        facts = len(data.get("facts", [])) if isinstance(data, dict) else 0
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {"log_entries": log_entries, "facts": facts}


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def _workspace_status() -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    output = result.stdout.strip()
    return "clean" if not output else output


def gather_env() -> dict[str, str]:
    def _cmd_output(cmd: Iterable[str]) -> str:
        try:
            result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except Exception:
            return ""

    return {
        "python": _cmd_output(["python3", "--version"]),
        "git": _cmd_output(["git", "--version"]),
        "rg": _cmd_output(["rg", "--version"]),
        "os": platform.platform(),
    }


STEPS = [
    ("01-fractal-coords", "rg -n '\"layer\"|systemic(_scale)?|\"(S|L)[0-9]\"' _plans memory tools agents _bus | head -n 40"),
    ("02-memory-list", "{ ls -la memory/; echo ''; wc -l memory/log.jsonl memory/state.json; }"),
    ("03-hash-chain", "rg -n 'hash_prev|hash_self' tools/memory/memory.py memory/log.jsonl"),
    ("04-ci-guards", "rg -n 'append-only|receipt|required|promotion' scripts/ci/"),
    ("05-capsule", "{ ls -la capsule/v1.6/; echo ''; rg -n 'STATUS|hash|provenance' capsule/v1.6; }"),
    ("06-bus-cli", "{ ls -la _bus/claims _bus/events; echo ''; rg -n 'tasks_report|bootloader' teof/; }"),
    ("07-ethics-wiring", "{ rg -n 'Legible Continuity' 'governance/core/L3 - properties/properties.md'; echo ''; rg -n 'State promotions must cite their receipts' docs/automation/memory-layer.md; }"),
    ("08-ethics-gate", "python3 tools/autonomy/ethics_gate.py --format json"),
]


def attest(out_root: Path, *, emit_log: bool, summary: str | None) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = out_root / timestamp
    dest.mkdir(parents=True, exist_ok=True)

    step_records: list[StepResult] = []
    all_success = True
    ethics_violation_detected = False

    for name, cmd in STEPS:
        result = _run_command(cmd, dest=dest, name=name)
        step_records.append(result)
        if not result.success:
            all_success = False
        if name == "08-ethics-gate":
            stdout_path = ROOT / result["stdout_path"]
            try:
                payload = json.loads(stdout_path.read_text(encoding="utf-8"))
                if payload:
                    ethics_violation_detected = bool(payload)
            except json.JSONDecodeError:
                pass

    timestamp_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    receipt = {
        "timestamp": timestamp_iso,
        "git_commit": _git_commit(),
        "workspace_status": _workspace_status(),
        "environment": gather_env(),
        "state_snapshot": _log_summary(),
        "steps": step_records,
        "ethics_violation_detected": ethics_violation_detected,
        "verdict": "PASS" if all_success and not ethics_violation_detected else "FAIL",
    }

    receipt_json = json.dumps(receipt, ensure_ascii=False, indent=2).encode("utf-8")
    checksum = _sha256(receipt_json)
    receipt["receipt_sha256"] = checksum
    (dest / "receipt.json").write_bytes(json.dumps(receipt, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")

    notes = summary or ("Automated attestation" if emit_log else "Automated attestation (no log)")
    _update_index(timestamp_iso, "Automated attestation", receipt["verdict"], dest.relative_to(ROOT), notes)

    if emit_log and receipt["verdict"] == "PASS":
        log_summary = summary or "Attestation of repo scaffold guardrails"
        subprocess.run(
            [
                "python3",
                "tools/memory/log-entry.py",
                "--summary",
                log_summary,
                "--ref",
                f"governance/attest/{timestamp}",
                "--artifact",
                str((dest / "receipt.json").relative_to(ROOT)),
                "--receipt",
                str((dest / "receipt.json").relative_to(ROOT)),
                "--task",
                "2025-09-25-oversight-guard",
                "--layer",
                "L4",
                "--systemic-scale",
                "8",
            ],
            cwd=ROOT,
            check=False,
        )

    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT, help="Base directory for receipts")
    parser.add_argument("--no-log", action="store_true", help="Do not append to memory log")
    parser.add_argument("--summary", help="Custom summary for memory log entry")
    args = parser.parse_args()

    dest = attest(args.out_root if args.out_root.is_absolute() else ROOT / args.out_root, emit_log=not args.no_log, summary=args.summary)
    print(f"wrote attestation to {dest.relative_to(ROOT)}")
    return 0


def _update_index(timestamp: str, entry_type: str, verdict: str, rel_path: Path, notes: str) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "| Timestamp (UTC)       | Type                  | Verdict | Path                                              | Notes |\n"
    )
    separator = (
        "|-----------------------|-----------------------|---------|---------------------------------------------------|-------|\n"
    )

    if not INDEX_PATH.exists():
        INDEX_PATH.write_text(f"# Receipt Index\n\n" + header + separator, encoding="utf-8")

    lines = INDEX_PATH.read_text(encoding="utf-8").splitlines()
    if header.strip() not in lines:
        lines.insert(0, "# Receipt Index")
        lines.insert(1, "")
        lines.insert(2, header.strip())
        lines.insert(3, separator.strip())

    row = f"| {timestamp:<21}| {entry_type:<23}| {verdict:<7}| {str(rel_path):<51}| {notes} |"

    existing = [line for line in lines if str(rel_path) in line]
    if existing:
        lines = [row if str(rel_path) in line else line for line in lines]
    else:
        lines.append(row)

    INDEX_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from teof._paths import repo_root
from teof.commands import brief as brief_cmd

ROOT = repo_root(default=Path(__file__).resolve().parents[2])
ARTIFACT_ROOT = ROOT / "artifacts" / "systemic_out"
REPORT_DIR = ROOT / "_report" / "usage" / "onboarding"

BOLD = "\033[1m"
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
YELLOW = "\033[0;33m"
RESET = "\033[0m"


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _run(cmd: Iterable[str]) -> None:
    subprocess.run(
        [str(part) for part in cmd],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _pip_install(*, skip: bool) -> None:
    if skip:
        return
    _run([sys.executable, "-m", "pip", "install", "-e", str(ROOT)])


def _load_artifacts() -> tuple[Path, list[str], str, int]:
    latest_symlink = ARTIFACT_ROOT / "latest"
    if not latest_symlink.exists():
        raise RuntimeError("brief artifacts missing; expected artifacts/systemic_out/latest")
    target = latest_symlink.resolve()
    brief_path = target / "brief.json"
    score_path = target / "score.txt"
    if not brief_path.exists():
        raise RuntimeError(f"brief.json missing under {target}")
    data = json.loads(brief_path.read_text(encoding="utf-8"))
    inputs = data.get("inputs") or []
    ensembles = sorted(str(p.name) for p in target.glob("*.ensemble.json"))
    score_text = score_path.read_text(encoding="utf-8").strip() if score_path.exists() else ""
    return target, ensembles, score_text, len(inputs)


def _latest_quickstart_receipt() -> Path | None:
    receipts = sorted(REPORT_DIR.glob("quickstart-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return receipts[0] if receipts else None


def _write_receipt(target: Path, ensembles: list[str], score_text: str, doc_count: int, receipt_dir: Path) -> Path:
    timestamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "mode": "tier1-eval-prototype",
        "generated_at": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "artifact_dir": _rel(target),
        "document_count": doc_count,
        "ensembles": ensembles,
        "score": score_text,
    }
    receipt_dir.mkdir(parents=True, exist_ok=True)
    out_path = receipt_dir / f"tier1-evaluation-{timestamp}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path


def _header() -> None:
    box = (
        "╔════════════════════════════════════════════════════════════════╗\n"
        "║                                                                ║\n"
        "║  TEOF Tier 1: Evaluate                                         ║\n"
        "║  Every decision should be traceable.                           ║\n"
        "║  TEOF makes that automatic. Run one command, get proof.        ║\n"
        "║                                                                ║\n"
        "╚════════════════════════════════════════════════════════════════╝\n"
    )
    print(box)


def _section(title: str) -> None:
    print(f"{BOLD}{title}{RESET}")


def _info(message: str) -> None:
    print(f"{BLUE}→{RESET} {message}")


def _highlight(message: str) -> None:
    print(f"{GREEN}✓{RESET} {message}")


def _run_eval(skip_install: bool, receipt_dir: Path) -> int:
    _header()

    _section("Step 1/3: Installing TEOF")
    if skip_install:
        _info("Skipping install (requested)")
    else:
        _info("Creating clean environment...")
    _pip_install(skip=skip_install)
    _highlight("Ready to run brief")
    print()

    _section("Step 2/3: Running analysis")
    _info("Analyzing sample documents...")
    rc = brief_cmd.run(argparse.Namespace())
    if rc != 0:
        raise RuntimeError("teof brief failed")
    _highlight("Analysis complete")
    print()

    _section("Step 3/3: Here's what happened")
    print()
    _info("TEOF just created these files:")
    print()

    target, ensembles, score_text, doc_count = _load_artifacts()
    latest_rel = _rel(target)
    print(f"  {GREEN}{latest_rel}/{RESET}")
    print(f"    • brief.json          {BLUE}← Summary of {doc_count} sample documents{RESET}")
    if ensembles:
        print(f"    • *.ensemble.json     {BLUE}← {len(ensembles)} generated analysis files{RESET}")
    if score_text:
        print(f"    • score.txt           {BLUE}← Quick metrics ({score_text}){RESET}")
    print()

    quickstart = _latest_quickstart_receipt()
    if quickstart:
        print(f"  {GREEN}_report/usage/onboarding/{RESET}")
        print(f"    • {_rel(quickstart)}  {BLUE}← Prior quickstart receipt{RESET}")
        print()

    eval_receipt = _write_receipt(target, ensembles, score_text, doc_count, receipt_dir)
    print(f"  {GREEN}{_rel(receipt_dir)}/{RESET}")
    print(f"    • {_rel(eval_receipt)}  {BLUE}← Tier 1 evaluation receipt{RESET}")
    print()

    divider = f"{BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}"
    print(divider)
    print()
    print(f"{BOLD}The Key Insight:{RESET}\n")
    print(f"Those files {BOLD}ARE{RESET} the point. They're your automatic audit trail.\n")
    print(f"  • {GREEN}brief.json{RESET}      → What happened (analysis processed {doc_count} sample documents)")
    if score_text:
        print(f"  • {GREEN}score.txt{RESET}       → Quick metrics to sanity-check the run ({score_text})")
    print(f"  • {GREEN}{eval_receipt.name}{RESET} → Full execution record (reproducible)")
    print()
    print(f"{YELLOW}Why this matters:{RESET}\n")
    print(f"  When you run TEOF, you don't just get outputs — you get {BOLD}proof of")
    print(f"  how they were created.{RESET}")
    print()
    print(f"  Changes aren't just tracked — they're {BOLD}reversible by design.{RESET}")
    print()
    print(f"  Decisions aren't just made — they're {BOLD}auditable forever.{RESET}")
    print()
    print(divider)
    print()

    print(f"{BOLD}Next Steps{RESET}\n")
    print(f"{BOLD}Ready to build with TEOF?{RESET}")
    _info("Tier 2 (30 min): Learn architecture, workflows, and how to create your own projects")
    print(f"  → {GREEN}docs/onboarding/tier2-solo-dev-PROTOTYPE.md{RESET}\n")

    print(f"{BOLD}Want multi-agent coordination?{RESET}")
    _info("Tier 3 (60 min): Full onboarding with manifests, bus system, and collaboration")
    print(f"  → {GREEN}docs/onboarding/README.md{RESET}\n")

    print(f"{BOLD}Just exploring?{RESET}")
    _info(f"You've seen the core value: {BOLD}automatic accountability.{RESET}")
    print(f"{YELLOW}Note:{RESET} TEOF turns 'trust me, I ran the tests' into 'here's the timestamped receipt with hashes.'\n")

    print(f"{BOLD}Want to inspect the receipts?{RESET}\n")
    print(f"  {BLUE}cat{RESET} artifacts/systemic_out/latest/brief.json")
    print(f"  {BLUE}cat{RESET} {_rel(eval_receipt)}\n")
    print(f"{GREEN}✓{RESET} Evaluation complete. Time: ~5 minutes.\n")
    return 0


def run(args: argparse.Namespace) -> int:
    if not getattr(args, "eval", False):
        parser = getattr(args, "_teof_up_parser", None)
        if parser is not None:
            parser.error("Specify --eval to run the Tier 1 evaluation prototype.")
        raise SystemExit("--eval required")
    try:
        return _run_eval(bool(getattr(args, "skip_install", False)), getattr(args, "receipt_dir"))
    except RuntimeError as exc:
        print(f"teof up --eval: {exc}", file=sys.stderr)
        return 1


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    parser = subparsers.add_parser(
        "up",
        help="Bootstrap helpers (Tier 1 evaluation prototype)",
        description="Bootstrap helpers (Tier 1 evaluation prototype)",
    )
    parser.add_argument(
        "--eval",
        action="store_true",
        help="Run the Tier 1 Evaluate prototype flow.",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--receipt-dir",
        type=Path,
        default=REPORT_DIR,
        help=argparse.SUPPRESS,
    )
    parser.set_defaults(func=run, _teof_up_parser=parser)


__all__ = ["register", "run"]

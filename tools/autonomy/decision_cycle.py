"""Orchestrate decision proposals and critique prompts."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
DECISION_DIR = ROOT / "memory" / "decisions"
OUTPUT_DIR = ROOT / "_report" / "usage" / "decision-loop"


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _resolve_decision(path: Path) -> Path:
    if path.is_absolute():
        return path
    candidate = DECISION_DIR / path
    if candidate.exists():
        return candidate
    return path


def _load_decision(path: Path) -> Mapping[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"decision file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid decision JSON: {path}") from exc


def _build_proposal_prompt(decision: Mapping[str, Any], guardrails: Mapping[str, Any]) -> str:
    constraints = decision.get("constraints") or []
    constraints_text = "\n".join(f"- {item}" for item in constraints) if constraints else "- None"
    references = decision.get("references") or []
    references_text = "\n".join(f"- {ref}" for ref in references) if references else "- None"
    success = decision.get("success_metric") or "Not specified"

    return (
        "You are Codex acting as an optimisation strategist for TEOF.\n"
        f"Decision: {decision.get('title')}\n"
        f"Objective: {decision.get('objective')}\n"
        f"Success metric: {success}\n\n"
        "Constraints:\n"
        f"{constraints_text}\n\n"
        "Context receipts:\n"
        f"{references_text}\n\n"
        "Guardrails:\n"
        f"- Diff limit: {guardrails.get('diff_limit')} lines\n"
        f"- Tests: {', '.join(guardrails.get('tests', [])) or 'none'}\n"
        f"- Receipts directory: {guardrails.get('receipts_dir')}\n\n"
        "Respond in JSON with keys `analysis`, `strategy`, `commands`, `tests`."
    )


def _build_critique_prompt(decision: Mapping[str, Any], guardrails: Mapping[str, Any]) -> str:
    return (
        "You are Codex auditing a proposed decision plan for TEOF."
        " Review the `strategy` and `commands` suggested by another agent."
        " Cite any conflicts with objectives or constraints and recommend adjustments"
        " while respecting diff/test guardrails."
        " Respond in JSON with keys `risks`, `alignment`, `recommendations`."
        " Guardrails reminder: diff limit {diff_limit}, tests {tests}, receipts {receipts}."
    ).format(
        diff_limit=guardrails.get("diff_limit"),
        tests=", ".join(guardrails.get("tests", [])) or "none",
        receipts=guardrails.get("receipts_dir"),
    )


def _write_cycle(payload: Mapping[str, Any], *, dry_run: bool) -> Path | None:
    if dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return None
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = payload["generated_at"].replace(":", "").replace("-", "")
    path = OUTPUT_DIR / f"cycle-{ts}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rel = path
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        pass
    print(f"decision-cycle: wrote {rel}")
    return path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decision", type=Path, help="Path to decision JSON (relative to memory/decisions/)" )
    parser.add_argument("--diff-limit", type=int, default=200, help="Maximum diff lines to allow")
    parser.add_argument(
        "--test",
        dest="tests",
        action="append",
        default=["pytest"],
        help="Test command to enforce (repeatable)",
    )
    parser.add_argument(
        "--receipts-dir",
        default="_report/usage/decision-loop",
        help="Directory where downstream receipts should be stored",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print payload without writing")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    decision_path = _resolve_decision(args.decision)
    decision = _load_decision(decision_path)

    guardrails = {
        "diff_limit": args.diff_limit,
        "tests": args.tests,
        "receipts_dir": args.receipts_dir,
    }

    payload = {
        "generated_at": _iso_now(),
        "decision_path": str(decision_path.relative_to(ROOT)) if decision_path.is_absolute() else str(decision_path),
        "decision": {
            "title": decision.get("title"),
            "objective": decision.get("objective"),
            "constraints": decision.get("constraints"),
            "success_metric": decision.get("success_metric"),
            "references": decision.get("references"),
            "plan_id": decision.get("plan_id"),
        },
        "guardrails": guardrails,
        "prompts": {
            "proposal": _build_proposal_prompt(decision, guardrails),
            "critique": _build_critique_prompt(decision, guardrails),
        },
    }
    _write_cycle(payload, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

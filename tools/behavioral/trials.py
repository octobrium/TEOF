"""Behavioral gap trial logging utilities."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from teof._paths import repo_root

ROOT = repo_root(default=Path(__file__).resolve().parents[2])
TRIAL_DIR = ROOT / "_report" / "usage" / "behavioral-trials"
INDEX_FILE = TRIAL_DIR / "index.jsonl"


@dataclass
class TrialEntry:
    trial_id: str
    plan_id: str
    agent_id: str
    prompt: str
    result: str
    bes_score: float
    receipt_path: str
    ts: str

    def to_dict(self) -> dict[str, object]:
        return {
            "trial_id": self.trial_id,
            "plan_id": self.plan_id,
            "agent_id": self.agent_id,
            "prompt": self.prompt,
            "result": self.result,
            "bes_score": self.bes_score,
            "receipt": self.receipt_path,
            "ts": self.ts,
        }


def _ensure_dir() -> None:
    TRIAL_DIR.mkdir(parents=True, exist_ok=True)


def _normalise_path(path: str | Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            candidate = candidate.resolve().relative_to(ROOT)
        except ValueError as exc:
            raise ValueError("receipt must live under repo root") from exc
    return candidate.as_posix()


def record_trial(
    *,
    trial_id: str,
    plan_id: str,
    agent_id: str,
    prompt: str,
    result: str,
    bes_score: float,
    receipt_path: str,
    ts: str | None = None,
) -> TrialEntry:
    ts_val = ts or datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(timespec="seconds")
    entry = TrialEntry(
        trial_id=trial_id,
        plan_id=plan_id,
        agent_id=agent_id,
        prompt=prompt,
        result=result,
        bes_score=bes_score,
        receipt_path=_normalise_path(receipt_path),
        ts=ts_val,
    )
    _ensure_dir()
    with INDEX_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
    return entry


def iter_trials() -> Iterable[Mapping[str, object]]:
    if not INDEX_FILE.exists():
        return []
    with INDEX_FILE.open(encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            try:
                yield json.loads(raw)
            except json.JSONDecodeError:
                continue


def summarise_trials(entries: Iterable[Mapping[str, object]]) -> dict[str, object]:
    total = 0
    passed = 0
    scores: list[float] = []
    for entry in entries:
        total += 1
        if str(entry.get("result", "")).lower() == "pass":
            passed += 1
        try:
            scores.append(float(entry.get("bes_score", 0.0)))
        except (TypeError, ValueError):
            continue
    avg_score = sum(scores) / len(scores) if scores else 0.0
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "average_bes_score": round(avg_score, 2),
    }


def _cmd_record(args: argparse.Namespace) -> int:
    record_trial(
        trial_id=args.trial_id,
        plan_id=args.plan,
        agent_id=args.agent,
        prompt=args.prompt,
        result=args.result,
        bes_score=args.bes_score,
        receipt_path=args.receipt,
        ts=args.ts,
    )
    print(f"recorded trial {args.trial_id}")
    return 0


def _cmd_summary(args: argparse.Namespace) -> int:
    summary = summarise_trials(iter_trials())
    if args.min_trials and summary["total"] < args.min_trials:
        print(f"::error ::only {summary['total']} trials recorded (< {args.min_trials})")
        rc = 1
    else:
        rc = 0
    if args.out:
        out_path = Path(args.out)
        abs_path = out_path if out_path.is_absolute() else ROOT / out_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        rel_path = abs_path.relative_to(ROOT)
        print(f"wrote summary → {rel_path}")
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return rc


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    rec_cmd = sub.add_parser("record", help="Record a behavioral trial result")
    rec_cmd.add_argument("--trial-id", required=True)
    rec_cmd.add_argument("--plan", required=True)
    rec_cmd.add_argument("--agent", required=True)
    rec_cmd.add_argument("--prompt", required=True)
    rec_cmd.add_argument("--result", choices=["pass", "fail"], required=True)
    rec_cmd.add_argument("--bes-score", type=float, required=True)
    rec_cmd.add_argument("--receipt", required=True)
    rec_cmd.add_argument("--ts", help="ISO timestamp (defaults to now)")
    rec_cmd.set_defaults(func=_cmd_record)

    sum_cmd = sub.add_parser("summary", help="Summarise trial outcomes")
    sum_cmd.add_argument("--out", help="Optional JSON output path")
    sum_cmd.add_argument("--min-trials", type=int, help="Fail when recorded trials < N")
    sum_cmd.set_defaults(func=_cmd_summary)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

"""Capture receipts for mirror drills across observers."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Sequence

from tools.autonomy.shared import utc_timestamp, write_receipt_payload

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RECEIPT_DIR = ROOT / "_report" / "usage" / "mirror-drill"


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", required=True, help="Observer or agent running the drill")
    parser.add_argument("--medium", required=True, help="Substrate or channel under test (e.g. human, LLM, device)")
    parser.add_argument("--plan-id", required=True, help="Plan or queue id coordinating the drill")
    parser.add_argument(
        "--systemic-targets",
        nargs="+",
        required=True,
        help="Systemic axes exercised (e.g. S1 S2 S3 S4)",
    )
    parser.add_argument(
        "--layer-targets",
        nargs="+",
        required=True,
        help="Layers covered during the drill (e.g. L4 L5)",
    )
    parser.add_argument(
        "--artifacts",
        nargs="*",
        default=(),
        help="Receipts or files generated (relative paths)",
    )
    parser.add_argument("--summary", required=True, help="Short outcome summary")
    parser.add_argument(
        "--risks",
        nargs="*",
        default=(),
        help="Observed risks or failure modes (use hyphenated phrases)",
    )
    parser.add_argument(
        "--follow-ups",
        nargs="*",
        default=(),
        help="Next actions or plans spawned by the drill",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Receipt path (default: _report/usage/mirror-drill/mirror-<timestamp>.json)",
    )
    return parser.parse_args(argv)


def _normalise_tokens(values: Sequence[str]) -> list[str]:
    normalised: list[str] = []
    for value in values:
        value = value.strip().upper()
        if not value:
            continue
        normalised.append(value)
    return normalised


def build_payload(args: argparse.Namespace) -> dict[str, object]:
    systemic = _normalise_tokens(args.systemic_targets)
    layers = _normalise_tokens(args.layer_targets)
    return {
        "generated_at": utc_timestamp(),
        "agent": args.agent,
        "medium": args.medium,
        "plan_id": args.plan_id,
        "systemic_targets": systemic,
        "layer_targets": layers,
        "summary": args.summary.strip(),
        "artifacts": sorted(set(args.artifacts)),
        "risks": sorted(set(args.risks)),
        "follow_ups": sorted(set(args.follow_ups)),
    }


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload(args)
    out_path = args.out
    if out_path is None:
        timestamp = payload["generated_at"].replace(":", "").replace("-", "")
        out_path = DEFAULT_RECEIPT_DIR / f"mirror-{timestamp}.json"
    write_receipt_payload(out_path, payload)
    try:
        rel = out_path.relative_to(ROOT)
    except ValueError:
        rel = out_path
    print(f"mirror drill: captured receipt → {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Compute high-level metrics for the Objectives Ledger (L2)."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from tools.autonomy.shared import load_json

ROOT = Path(__file__).resolve().parents[2]
REFLECTION_DIR = ROOT / "memory" / "reflections"
CONDUCTOR_DIR = ROOT / "_report" / "usage" / "autonomy-conductor"
AUTONOMY_ACTIONS_DIR = ROOT / "_report" / "usage" / "autonomy-actions"
AUTH_PATH_JSON = ROOT / "_report" / "usage" / "external-authenticity.json"
AUTH_PATH_MD = ROOT / "_report" / "usage" / "external-authenticity.md"
EXTERNAL_SUMMARY = ROOT / "_report" / "usage" / "external-summary.json"
COORDINATION_AGENT_DIR = ROOT / "_report" / "agent"
COORDINATION_DASHBOARD_PATTERN = "**/dashboard*.md"
COORDINATION_DOC_PATHS = (
    ROOT / "docs" / "vision" / "multi-neuron-playbook.md",
    ROOT / "docs" / "vision" / "properties-ledger.md",
    ROOT / "docs" / "vision" / "objectives-ledger.md",
    ROOT / "docs" / "quick-links.md",
)
IMPACT_LOG_PATH = ROOT / "memory" / "impact" / "log.jsonl"
IMPACT_LEDGER_PATH = ROOT / "docs" / "vision" / "impact-ledger.md"
CLAIMS_DIR = ROOT / "_bus" / "claims"


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _mtime(path: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except FileNotFoundError:
        return None


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def _reflections_since(threshold: datetime) -> int:
    if not REFLECTION_DIR.exists():
        return 0
    count = 0
    for path in REFLECTION_DIR.glob("reflection-*.json"):
        raw = load_json(path)
        data = raw if isinstance(raw, Mapping) else None
        captured = _parse_iso(data.get("captured_at") if data else None)
        if captured and captured >= threshold:
            count += 1
    return count


def _conductor_cycles_since(threshold: datetime) -> int:
    if not CONDUCTOR_DIR.exists():
        return 0
    count = 0
    for path in CONDUCTOR_DIR.glob("conductor-*.json"):
        raw = load_json(path)
        data = raw if isinstance(raw, Mapping) else None
        generated = _parse_iso(data.get("generated_at") if data else None)
        if generated and generated >= threshold:
            count += 1
    return count


def _auth_status() -> Mapping[str, Any] | None:
    raw = load_json(AUTH_PATH_JSON)
    data = raw if isinstance(raw, Mapping) else None
    if data is None:
        return None
    overall = data.get("overall_avg_trust")
    attention = data.get("attention_feeds") or []
    return {
        "overall_avg_trust": overall,
        "attention_feeds": attention,
        "meets_minimum": isinstance(overall, (int, float)) and overall >= 0.7 and not attention,
    }


def _external_summary_recent(threshold: datetime) -> bool:
    if not EXTERNAL_SUMMARY.exists():
        return False
    mtime = datetime.fromtimestamp(EXTERNAL_SUMMARY.stat().st_mtime, tz=timezone.utc)
    return mtime >= threshold


def _coordination_state(threshold: datetime) -> dict[str, Any]:
    missing_docs: list[str] = []
    recent_docs: list[str] = []
    for doc_path in COORDINATION_DOC_PATHS:
        if not doc_path.exists():
            missing_docs.append(_relative(doc_path))
            continue
        touched = _mtime(doc_path)
        if touched and touched >= threshold:
            recent_docs.append(_relative(doc_path))

    dashboards_recent = False
    if COORDINATION_AGENT_DIR.exists():
        for path in COORDINATION_AGENT_DIR.glob(COORDINATION_DASHBOARD_PATTERN):
            if not path.is_file():
                continue
            touched = _mtime(path)
            if touched and touched >= threshold:
                dashboards_recent = True
                break

    return {
        "docs_present": not missing_docs,
        "missing_docs": missing_docs,
        "recent_docs": recent_docs,
        "recent_coordination_receipts": dashboards_recent,
    }


def _impact_entries_since(threshold: datetime) -> int:
    if not IMPACT_LOG_PATH.exists():
        return 0
    count = 0
    for line in IMPACT_LOG_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        recorded = _parse_iso(data.get("recorded_at") if isinstance(data, Mapping) else None)
        if recorded and recorded >= threshold:
            count += 1
    return count


def _impact_ledger_has_summary() -> bool:
    if not IMPACT_LEDGER_PATH.exists():
        return False
    for line in IMPACT_LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("- *"):
            return True
    return False


def _unique_agents_since(threshold: datetime) -> int:
    if not CLAIMS_DIR.exists():
        return 0
    agents: set[str] = set()
    for path in CLAIMS_DIR.glob("*.json"):
        raw = load_json(path)
        data = raw if isinstance(raw, Mapping) else None
        if data is None:
            continue
        claimed = _parse_iso(data.get("claimed_at"))
        if claimed and claimed >= threshold:
            agent = data.get("agent_id")
            if isinstance(agent, str) and agent:
                agents.add(agent)
    return len(agents)


def compute_status(window_days: float) -> Mapping[str, Any]:
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(days=window_days)
    reflections = _reflections_since(threshold)
    cycles = _conductor_cycles_since(threshold)
    auth = _auth_status()
    external_recent = _external_summary_recent(threshold)
    coordination = _coordination_state(threshold)
    impact_entries = _impact_entries_since(threshold)
    impact_summary = _impact_ledger_has_summary()
    unique_agents = _unique_agents_since(threshold)

    return {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_days": window_days,
        "objectives": {
            "O1": {
                "reflections_last_window": reflections,
                "meets_target": reflections >= 1,
            },
            "O2": {
                "autonomy_cycles_last_window": cycles,
                "meets_target": cycles >= 1,
            },
            "O3": {
                "docs_present": coordination["docs_present"],
                "missing_docs": coordination["missing_docs"],
                "recent_docs": coordination["recent_docs"],
                "recent_coordination_receipts": coordination["recent_coordination_receipts"],
                "meets_target": coordination["docs_present"]
                and coordination["recent_coordination_receipts"],
            },
            "O4": {
                "impact_entries_last_window": impact_entries,
                "ledger_has_summary": impact_summary,
                "meets_target": impact_entries > 0 and impact_summary,
            },
            "O5": auth,
            "O6": {
                "unique_agents_last_window": unique_agents,
                "meets_target": unique_agents >= 2,
            },
            "O7": {
                "external_summary_recent": external_recent,
                "meets_target": external_recent,
            },
        },
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window-days", type=float, default=7.0, help="Sliding window in days")
    parser.add_argument("--out", type=Path, help="Optional path to write JSON summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    status = compute_status(window_days=args.window_days)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

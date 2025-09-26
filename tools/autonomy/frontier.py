"""Frontier scoring loop for prioritising next coordinates."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[2]
BACKLOG_PATH = ROOT / "_plans" / "next-development.todo.json"
TASKS_PATH = ROOT / "agents" / "tasks" / "tasks.json"
STATE_PATH = ROOT / "memory" / "state.json"


@dataclass
class Candidate:
    source: str
    identifier: str
    title: str
    layer: str
    systemic_scale: int
    status: str | None = None
    priority: str | None = None
    plan_id: str | None = None
    plan_suggestion: str | None = None
    receipts: list[str] = field(default_factory=list)
    confidence: float | None = None
    role: str | None = None


@dataclass
class FrontierEntry:
    candidate: Candidate
    impact: float
    dependency_weight: float
    confidence_gap: float
    cohesion_gain: float
    effort: float

    @property
    def score(self) -> float:
        numerator = self.impact * self.dependency_weight * self.confidence_gap * self.cohesion_gain
        return numerator / max(self.effort, 0.1)

    def as_dict(self) -> dict[str, Any]:
        return {
            "coord": {
                "layer": self.candidate.layer,
                "systemic_scale": self.candidate.systemic_scale,
            },
            "source": self.candidate.source,
            "id": self.candidate.identifier,
            "title": self.candidate.title,
            "status": self.candidate.status,
            "priority": self.candidate.priority,
            "plan_id": self.candidate.plan_id or self.candidate.plan_suggestion,
            "receipts": self.candidate.receipts,
            "components": {
                "impact": self.impact,
                "dependency_weight": self.dependency_weight,
                "confidence_gap": self.confidence_gap,
                "cohesion_gain": self.cohesion_gain,
                "effort": self.effort,
            },
            "score": self.score,
        }


LAYER_WEIGHTS = {
    "L0": 1.20,
    "L1": 1.18,
    "L2": 1.15,
    "L3": 1.15,
    "L4": 1.20,
    "L5": 1.10,
    "L6": 1.05,
}

STATUS_CONFIDENCE = {
    "pending": 1.0,
    "open": 1.0,
    "todo": 1.0,
    "active": 0.9,
    "in_progress": 0.7,
    "review": 0.6,
    "blocked": 1.2,
    "paused": 1.1,
}

PRIORITY_WEIGHTS = {
    "high": 3.0,
    "medium": 2.0,
    "low": 1.0,
}


def _normalise_layer(raw: str | None) -> str:
    value = (raw or "L5").strip().upper()
    if value.startswith("L") and value[1:].isdigit():
        return value
    return "L5"


def _normalise_scale(value: Any, layer: str) -> int:
    if isinstance(value, int) and 1 <= value <= 10:
        return value
    # Approximate systemic scale from layer when missing
    layer_number = 5
    if layer.startswith("L") and layer[1:].isdigit():
        try:
            layer_number = int(layer[1:])
        except ValueError:
            layer_number = 5
    return max(1, min(10, 4 + layer_number))


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def _load_backlog() -> Iterable[Candidate]:
    data = _load_json(BACKLOG_PATH)
    if not isinstance(data, dict):
        return []
    items = data.get("items")
    if not isinstance(items, list):
        return []
    candidates: list[Candidate] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        status = (item.get("status") or "").lower()
        if status == "done":
            continue
        identifier = str(item.get("id") or "")
        title = str(item.get("title") or identifier)
        layer = _normalise_layer(item.get("layer"))
        systemic_scale = _normalise_scale(item.get("systemic_scale"), layer)
        receipts = [r for r in (item.get("receipts") or []) if isinstance(r, str)]
        candidates.append(
            Candidate(
                source="backlog",
                identifier=identifier,
                title=title,
                layer=layer,
                systemic_scale=systemic_scale,
                status=status or None,
                priority=item.get("priority"),
                plan_suggestion=item.get("plan_suggestion"),
                receipts=receipts,
            )
        )
    return candidates


def _load_tasks() -> Iterable[Candidate]:
    data = _load_json(TASKS_PATH)
    if not isinstance(data, dict):
        return []
    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        return []
    candidates: list[Candidate] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        status = (task.get("status") or "").lower()
        if status == "done":
            continue
        identifier = str(task.get("id") or "")
        title = str(task.get("title") or identifier)
        layer = _normalise_layer(task.get("layer"))
        systemic_scale = _normalise_scale(task.get("systemic_scale"), layer)
        receipts = [r for r in (task.get("receipts") or []) if isinstance(r, str)]
        candidates.append(
            Candidate(
                source="task",
                identifier=identifier,
                title=title,
                layer=layer,
                systemic_scale=systemic_scale,
                status=status or None,
                priority=task.get("priority"),
                plan_id=task.get("plan_id"),
                receipts=receipts,
                role=task.get("role"),
            )
        )
    return candidates


def _load_state_facts() -> Iterable[Candidate]:
    data = _load_json(STATE_PATH)
    if not isinstance(data, dict):
        return []
    facts = data.get("facts")
    if not isinstance(facts, list):
        return []
    candidates: list[Candidate] = []
    for fact in facts:
        if not isinstance(fact, dict):
            continue
        identifier = str(fact.get("id") or "")
        title = str(fact.get("statement") or identifier)
        layer = _normalise_layer(fact.get("layer"))
        systemic_scale = _normalise_scale(fact.get("systemic_scale"), layer)
        confidence = fact.get("confidence")
        try:
            conf_val = float(confidence) if confidence is not None else None
        except (TypeError, ValueError):
            conf_val = None
        candidates.append(
            Candidate(
                source="state",
                identifier=identifier,
                title=title,
                layer=layer,
                systemic_scale=systemic_scale,
                status="fact",
                confidence=conf_val,
                receipts=[r for r in [fact.get("source_run")] if isinstance(r, str)],
            )
        )
    return candidates


def _impact(candidate: Candidate) -> float:
    if candidate.source == "state":
        gap = max(0.0, 1.0 - (candidate.confidence or 0.0))
        return 1.0 + gap * 2.0
    priority = (candidate.priority or "").lower()
    return PRIORITY_WEIGHTS.get(priority, 1.0)


def _dependency_weight(candidate: Candidate) -> float:
    weight = 1.0
    if candidate.receipts:
        weight += 0.1 * min(len(candidate.receipts), 3)
    if candidate.plan_id or candidate.plan_suggestion:
        weight += 0.1
    return weight


def _confidence_gap(candidate: Candidate) -> float:
    if candidate.source == "state":
        return max(0.1, 1.0 - (candidate.confidence or 0.0))
    status = (candidate.status or "").lower()
    return STATUS_CONFIDENCE.get(status, 1.0)


def _cohesion_gain(candidate: Candidate) -> float:
    base = LAYER_WEIGHTS.get(candidate.layer, 1.0)
    scale_adjust = max(0, candidate.systemic_scale - 5) * 0.03
    return base + scale_adjust


def _effort(candidate: Candidate) -> float:
    effort = 1.0
    status = (candidate.status or "").lower()
    if status == "in_progress":
        effort += 0.2
    if status == "blocked":
        effort += 0.4
    if status == "active":
        effort += 0.1
    if (candidate.role or "").lower() == "manager":
        effort += 0.1
    return effort


def compute_frontier(limit: int = 10) -> list[FrontierEntry]:
    candidates = list(_load_backlog()) + list(_load_tasks()) + list(_load_state_facts())
    entries: list[FrontierEntry] = []
    for candidate in candidates:
        entry = FrontierEntry(
            candidate=candidate,
            impact=_impact(candidate),
            dependency_weight=_dependency_weight(candidate),
            confidence_gap=_confidence_gap(candidate),
            cohesion_gain=_cohesion_gain(candidate),
            effort=_effort(candidate),
        )
        if entry.score > 0:
            entries.append(entry)
    entries.sort(key=lambda e: (e.score, e.impact, e.candidate.identifier), reverse=True)
    return entries[: max(0, limit)]


def render_table(entries: Sequence[FrontierEntry]) -> str:
    if not entries:
        return "(no candidates)"
    headers = ["Score", "Coord", "Source", "ID", "Title"]
    rows = []
    for entry in entries:
        coord = f"S{entry.candidate.systemic_scale}:" + entry.candidate.layer
        rows.append([
            f"{entry.score:.2f}",
            coord,
            entry.candidate.source,
            entry.candidate.identifier,
            entry.candidate.title,
        ])
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))
    fmt = " ".join(f"{{:<{w}}}" for w in widths)
    lines = [fmt.format(*headers), "-" * (sum(widths) + len(widths) - 1)]
    for row in rows:
        lines.append(fmt.format(*row))
    return "\n".join(lines)


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _log_summary() -> dict[str, int]:
    log_path = ROOT / "memory" / "log.jsonl"
    state_path = ROOT / "memory" / "state.json"
    log_count = 0
    if log_path.exists():
        with log_path.open(encoding="utf-8") as handle:
            for _ in handle:
                log_count += 1
    facts_count = 0
    data = _load_json(state_path)
    if isinstance(data, dict) and isinstance(data.get("facts"), list):
        facts_count = len(data["facts"])
    return {"log_entries": log_count, "facts": facts_count}


def write_receipt(entries: Sequence[FrontierEntry], out_path: Path, *, limit: int) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": _git_commit(),
        "parameters": {"limit": limit},
        "state_snapshot": _log_summary(),
        "entries": [entry.as_dict() for entry in entries],
    }
    base_json = json.dumps(payload, ensure_ascii=False, indent=2)
    checksum = hashlib.sha256(base_json.encode("utf-8")).hexdigest()
    payload["receipt_sha256"] = checksum
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=10, help="Number of entries to show")
    parser.add_argument("--format", choices=("table", "json"), default="table", help="Output format")
    parser.add_argument("--out", type=Path, help="Optional path to write receipt JSON")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    entries = compute_frontier(limit=max(0, args.limit))
    if args.format == "json":
        print(json.dumps([entry.as_dict() for entry in entries], ensure_ascii=False, indent=2))
    else:
        print(render_table(entries))
    if args.out:
        out_path = args.out if args.out.is_absolute() else (ROOT / args.out)
        receipt_path = write_receipt(entries, out_path, limit=max(0, args.limit))
        print(f"wrote receipt → {receipt_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

#!/usr/bin/env python3
"""Emit provenance graphs linking queue briefs, plans, claims, and receipts."""
from __future__ import annotations

import argparse
import json
import hashlib
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
QUEUE_DIR = ROOT / "queue"
PLANS_DIR = ROOT / "_plans"
CLAIMS_DIR = ROOT / "_bus" / "claims"
USAGE_DIR = ROOT / "_report" / "usage" / "receipt-graph"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


class ReceiptGraphError(RuntimeError):
    """Raised when required artifacts are missing."""


@dataclass
class GraphResult:
    graph_path: Path
    mermaid_path: Path | None
    graph: Mapping[str, object]


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


def _relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _default_output(task_id: str) -> Path:
    slug = task_id.lower()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return USAGE_DIR / f"{slug}-{timestamp}.json"


def _canonical_digest(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _find_queue_doc(task_id: str) -> Path:
    normalized = task_id.lower()
    tokens = {normalized}
    if "-" in normalized:
        tokens.add(normalized.split("-", 1)[1])
    if normalized.startswith("queue-"):
        tokens.add(normalized.replace("queue-", "", 1))
    matches = sorted(
        path
        for path in QUEUE_DIR.glob("*.md")
        if any(token and token in path.name.lower() for token in tokens)
    )
    if not matches:
        raise ReceiptGraphError(f"queue brief for {task_id} not found under {QUEUE_DIR}")
    return matches[0]


def _load_json(path: Path) -> Mapping[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:  # pragma: no cover - guarded earlier
        raise ReceiptGraphError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReceiptGraphError(f"invalid JSON in {path}: {exc}") from exc


def _load_plan(plan_id: str | None) -> tuple[str, Path, Mapping[str, object]]:
    if not plan_id:
        raise ReceiptGraphError("plan id missing; pass --plan or ensure claim includes plan_id")
    plan_path = PLANS_DIR / f"{plan_id}.plan.json"
    if not plan_path.exists():
        raise ReceiptGraphError(f"plan file not found: {plan_path}")
    data = _load_json(plan_path)
    return plan_id, plan_path, data


def _load_claim(task_id: str) -> tuple[Path, Mapping[str, object]]:
    claim_path = CLAIMS_DIR / f"{task_id}.json"
    if not claim_path.exists():
        raise ReceiptGraphError(f"claim file missing for {task_id} (expected {claim_path})")
    data = _load_json(claim_path)
    return claim_path, data


def _collect_receipts(plan_data: Mapping[str, object], extras: Iterable[str] | None) -> list[str]:
    receipts: list[str] = []

    def _append(values: Iterable[str]) -> None:
        for value in values:
            if value and value not in receipts:
                receipts.append(value)

    raw = plan_data.get("receipts")
    if isinstance(raw, Sequence):
        _append(str(item).strip() for item in raw if isinstance(item, str))
    steps = plan_data.get("steps")
    if isinstance(steps, Sequence):
        for step in steps:
            if not isinstance(step, Mapping):
                continue
            step_receipts = step.get("receipts")
            if isinstance(step_receipts, Sequence):
                _append(str(item).strip() for item in step_receipts if isinstance(item, str))
    if extras:
        _append(extra.strip() for extra in extras if isinstance(extra, str))
    return receipts


def _mermaid_id(node_id: str) -> str:
    return node_id.replace(":", "_").replace("/", "_").replace("-", "_")


def _render_mermaid(nodes: Sequence[Mapping[str, object]], edges: Sequence[Mapping[str, str]]) -> str:
    parts = ["graph TD"]
    for node in nodes:
        node_id = str(node["id"])
        label = node.get("label") or node_id
        kind = node.get("type", "")
        parts.append(f'  {_mermaid_id(node_id)}["{label} ({kind})"]')
    for edge in edges:
        source = _mermaid_id(edge["source"])
        target = _mermaid_id(edge["target"])
        label = edge.get("type", "")
        label_part = f"|{label}|" if label else ""
        parts.append(f"  {source} -->{label_part} {target}")
    return "\n".join(parts) + "\n"


def _build_graph(
    *,
    task_id: str,
    queue_path: Path,
    claim_path: Path,
    claim_data: Mapping[str, object],
    plan_id: str,
    plan_path: Path,
    plan_data: Mapping[str, object],
    receipts: Sequence[str],
) -> Mapping[str, object]:
    nodes: dict[str, dict[str, object]] = {}
    edges: set[tuple[str, str, str]] = set()

    def add_node(node_id: str, *, node_type: str, **fields: object) -> None:
        nodes.setdefault(node_id, {"id": node_id, "type": node_type}).update(fields)

    def add_edge(source: str, target: str, edge_type: str) -> None:
        edges.add((source, target, edge_type))

    queue_node_id = f"task:{task_id}"
    add_node(
        queue_node_id,
        node_type="task",
        label=task_id,
        path=_relative(queue_path),
    )

    claim_node_id = f"claim:{task_id}"
    add_node(
        claim_node_id,
        node_type="claim",
        label=f"Claim {task_id}",
        path=_relative(claim_path),
        status=claim_data.get("status"),
        agent=claim_data.get("agent_id"),
    )

    plan_node_id = f"plan:{plan_id}"
    add_node(
        plan_node_id,
        node_type="plan",
        label=plan_id,
        path=_relative(plan_path),
        summary=plan_data.get("summary"),
    )

    add_edge(queue_node_id, plan_node_id, "planned")
    add_edge(queue_node_id, claim_node_id, "claimed")
    add_edge(claim_node_id, plan_node_id, "references")

    for receipt in receipts:
        receipt_id = f"receipt:{receipt}"
        add_node(
            receipt_id,
            node_type="receipt",
            label=receipt,
            path=receipt,
        )
        add_edge(plan_node_id, receipt_id, "produced")

    graph: dict[str, object] = {
        "task_id": task_id,
        "plan_id": plan_id,
        "generated_at": _iso_now(),
        "nodes": list(nodes.values()),
        "edges": [{"source": s, "target": t, "type": et} for (s, t, et) in sorted(edges)],
        "sources": {
            "queue": _relative(queue_path),
            "claim": _relative(claim_path),
            "plan": _relative(plan_path),
        },
        "receipts": receipts,
    }
    graph["digest"] = _canonical_digest(graph)
    return graph


def build_graph(
    *,
    task_id: str,
    plan_id: str | None,
    extra_receipts: Iterable[str] | None,
    output_path: Path | None = None,
    mermaid_path: Path | None = None,
) -> GraphResult:
    queue_path = _find_queue_doc(task_id)
    claim_path, claim_data = _load_claim(task_id)

    effective_plan_id = plan_id or str(claim_data.get("plan_id") or "").strip() or None
    plan_id, plan_path, plan_data = _load_plan(effective_plan_id)
    receipts = _collect_receipts(plan_data, extra_receipts)

    graph = _build_graph(
        task_id=task_id,
        queue_path=queue_path,
        claim_path=claim_path,
        claim_data=claim_data,
        plan_id=plan_id,
        plan_path=plan_path,
        plan_data=plan_data,
        receipts=receipts,
    )

    target = output_path or _default_output(task_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")

    mermaid_target: Path | None = mermaid_path
    if mermaid_target:
        mermaid_target.parent.mkdir(parents=True, exist_ok=True)
        mermaid_target.write_text(
            _render_mermaid(graph["nodes"], graph["edges"]),
            encoding="utf-8",
        )

    return GraphResult(graph_path=target, mermaid_path=mermaid_target, graph=graph)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit observation receipt graphs")
    parser.add_argument("--task", required=True, help="Task/queue identifier (e.g., QUEUE-053)")
    parser.add_argument("--plan", help="Plan id (defaults to claim's plan_id when present)")
    parser.add_argument(
        "--extra-receipt",
        action="append",
        help="Additional receipt path(s) to include (repeatable)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Override output path (default: _report/usage/receipt-graph/<task>-<timestamp>.json)",
    )
    parser.add_argument(
        "--mermaid",
        type=Path,
        help="Optional path for a Mermaid graph (disabled when omitted)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = build_graph(
            task_id=args.task.strip(),
            plan_id=(args.plan.strip() if args.plan else None),
            extra_receipts=args.extra_receipt,
            output_path=args.output,
            mermaid_path=args.mermaid,
        )
    except ReceiptGraphError as exc:
        print(f"receipt_graph: {exc}", file=sys.stderr)
        return 1

    graph_rel = _relative(result.graph_path)
    print(f"receipt_graph: wrote graph to {graph_rel} (digest={result.graph['digest']})")
    if result.mermaid_path:
        print(f"  mermaid={_relative(result.mermaid_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

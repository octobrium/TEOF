"""Summarise backlog advisories for triage."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from tools.autonomy.shared import load_json

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TODO = ROOT / "_plans" / "next-development.todo.json"


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _extract_target(notes: str | None) -> str | None:
    if not notes:
        return None
    prefix = "Target: "
    for line in notes.splitlines():
        line = line.strip()
        if line.startswith(prefix):
            target = line[len(prefix) :].strip()
            return target or None
    return None


def _collect_advisories(todo: Mapping[str, object]) -> list[Mapping[str, object]]:
    items = todo.get("items")
    if not isinstance(items, list):
        return []
    advisories: list[Mapping[str, object]] = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        if item.get("source") != "fractal-advisory":
            continue
        advisories.append(item)
    return advisories


def build_clusters(advisories: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    clusters: dict[str, dict[str, object]] = {}
    extras: defaultdict[str, list[Mapping[str, object]]] = defaultdict(list)

    for advisory in advisories:
        notes = advisory.get("notes") if isinstance(advisory.get("notes"), str) else None
        target = _extract_target(notes) or advisory.get("plan_suggestion") or "unknown"
        target_str = str(target)
        bucket = clusters.setdefault(
            target_str,
            {
                "target": target_str,
                "count": 0,
                "plan_suggestion": advisory.get("plan_suggestion"),
                "layer": advisory.get("layer"),
                "systemic_scales": set(),
                "sample_claims": [],
                "ids": [],
            },
        )
        bucket["count"] += 1
        bucket["ids"].append(advisory.get("id"))
        layer = advisory.get("layer")
        if isinstance(layer, str) and not bucket.get("layer"):
            bucket["layer"] = layer
        systemic = advisory.get("systemic_scale")
        if isinstance(systemic, int):
            bucket["systemic_scales"].add(systemic)
        extras[target_str].append(advisory)

    results: list[dict[str, object]] = []
    for target, bucket in clusters.items():
        sample = extras[target][:3]
        bucket["sample_claims"] = [adv.get("title") or adv.get("claim") for adv in sample]
        bucket["systemic_scales"] = sorted(bucket["systemic_scales"])
        results.append(bucket)

    results.sort(key=lambda entry: entry["count"], reverse=True)
    return results


def _render_markdown(payload: Mapping[str, object], limit: int | None = None) -> str:
    clusters = payload.get("clusters", [])
    rows: list[str] = []
    header = "| Target | Count | Layer | Systemic | Plan Suggestion | Sample Claim |"
    divider = "| --- | --- | --- | --- | --- | --- |"
    rows.extend([header, divider])
    count = 0
    for cluster in clusters:
        if limit is not None and count >= limit:
            break
        count += 1
        systemic = ", ".join(str(val) for val in cluster.get("systemic_scales", []) or [])
        sample = cluster.get("sample_claims") or []
        sample_str = sample[0] if sample else ""
        rows.append(
            "| {target} | {count} | {layer} | {sys} | {plan} | {sample} |".format(
                target=cluster.get("target", ""),
                count=cluster.get("count", 0),
                layer=cluster.get("layer", ""),
                sys=systemic,
                plan=cluster.get("plan_suggestion", ""),
                sample=sample_str.replace("|", "/"),
            )
        )
    return "\n".join(rows) + "\n"


def generate_report(todo_path: Path, limit: int | None = None) -> dict[str, object]:
    todo_payload = load_json(todo_path)
    if not isinstance(todo_payload, Mapping):
        raise ValueError(f"invalid todo payload: {todo_path}")
    advisories = _collect_advisories(todo_payload)
    clusters = build_clusters(advisories)
    if limit is not None:
        clusters = clusters[:limit]
    timestamp = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    return {
        "generated_at": timestamp,
        "todo_path": _relative(todo_path),
        "total_advisories": len(advisories),
        "clusters": clusters,
    }


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--todo", type=Path, default=DEFAULT_TODO, help="Path to next-development TODO backlog")
    parser.add_argument("--out", type=Path, help="Write report to this path (defaults to stdout)")
    parser.add_argument("--top", type=int, help="Only include the top N clusters")
    parser.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format")
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    todo_path = args.todo if args.todo.is_absolute() else ROOT / args.todo
    report = generate_report(todo_path, limit=args.top)

    if args.format == "markdown":
        content = _render_markdown(report, limit=args.top)
    else:
        content = json.dumps(report, ensure_ascii=False, indent=2) + "\n"

    if args.out:
        out_path = args.out if args.out.is_absolute() else ROOT / args.out
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

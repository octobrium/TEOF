from __future__ import annotations

import json
from argparse import Namespace
import datetime as dt
from pathlib import Path
from typing import Any, Iterable, Sequence

from teof._paths import repo_root

ROOT = repo_root(default=Path(__file__).resolve().parents[1])
DEFAULT_HISTORY = ROOT / "_report" / "usage" / "systemic-scan" / "ratchet-history.jsonl"
RECEIPT_DIR = ROOT / "_report" / "usage" / "scan-history" / "receipts"
COMPONENT_ORDER = ("frontier", "critic", "tms", "ethics")


def _resolve_history(path: Path | None) -> Path:
    if path is None:
        return DEFAULT_HISTORY
    if path.is_absolute():
        return path
    return ROOT / path


def _normalize_components(values: Sequence[str] | None) -> list[str]:
    if not values:
        return []
    normalized: list[str] = []
    for value in values:
        token = value.strip().lower()
        if token and token not in normalized:
            normalized.append(token)
    return normalized


def _load_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        payload = line.strip()
        if not payload:
            continue
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            entries.append(data)
    return entries


def _utc_now() -> str:
    return dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_receipt_path() -> Path:
    timestamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return RECEIPT_DIR / f"scan_history-{timestamp}.json"


def _resolve_receipt_path(path: Path | None) -> Path:
    if path is None:
        return _default_receipt_path()
    if path.is_absolute():
        return path
    return ROOT / path


def _write_receipt(
    path: Path,
    *,
    history_path: Path,
    limit: int,
    components: list[str],
    entries: list[dict[str, Any]],
    output_format: str,
    summary_only: bool,
    summary_counts: dict[str, int],
) -> Path:
    payload = {
        "generated_at": _utc_now(),
        "command": "scan_history",
        "query": {
            "history_path": str(history_path),
            "limit": limit,
            "components": components or None,
            "format": output_format,
            "summary": summary_only,
        },
        "count": len(entries),
        "summary_counts": summary_counts,
        "entries": entries,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _format_counts(payload: dict[str, Any]) -> str:
    counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}
    parts = []
    for key in COMPONENT_ORDER:
        value = counts.get(key, 0)
        parts.append(f"{key[0].upper()}:{value}")
    return " ".join(parts)


def _format_components(payload: dict[str, Any]) -> str:
    comps = payload.get("components")
    if isinstance(comps, Iterable):
        tokens = [str(comp) for comp in comps if isinstance(comp, str)]
        if tokens:
            return ",".join(tokens)
    return "-"


def _format_flags(payload: dict[str, Any]) -> str:
    flags = []
    if payload.get("summary"):
        flags.append("S")
    if payload.get("format") == "json":
        flags.append("J")
    if payload.get("emit_bus"):
        flags.append("B")
    if payload.get("emit_plan"):
        flags.append("P")
    return "".join(flags) or "-"


def _entry_components(entry: dict[str, Any]) -> set[str]:
    comps_field = entry.get("components")
    results: set[str] = set()
    if isinstance(comps_field, Iterable):
        for comp in comps_field:
            if isinstance(comp, str):
                token = comp.strip().lower()
                if token:
                    results.add(token)
    return results


def _filter_entries(entries: list[dict[str, Any]], components: list[str]) -> list[dict[str, Any]]:
    if not components:
        return entries
    target = set(components)
    filtered: list[dict[str, Any]] = []
    for entry in entries:
        if target.issubset(_entry_components(entry)):
            filtered.append(entry)
    return filtered


def _aggregate_counts(entries: list[dict[str, Any]]) -> dict[str, int]:
    totals = {key: 0 for key in COMPONENT_ORDER}
    for entry in entries:
        counts = entry.get("counts")
        if not isinstance(counts, dict):
            continue
        for key in COMPONENT_ORDER:
            value = counts.get(key)
            if isinstance(value, int):
                totals[key] += value
    return totals


def run(args: Namespace) -> int:
    history_path = _resolve_history(getattr(args, "path", None))
    limit = getattr(args, "limit", 10)
    output_format = getattr(args, "format", "table")
    components = _normalize_components(getattr(args, "component", None))
    receipt_flag = bool(getattr(args, "emit_receipt", False))
    receipt_path_arg = getattr(args, "receipt_path", None)
    summary_only = bool(getattr(args, "summary", False))

    entries = _load_entries(history_path)
    entries = _filter_entries(entries, components)
    if limit >= 0:
        entries = entries[-limit:]
    entries = list(reversed(entries))
    totals = _aggregate_counts(entries)

    if output_format == "json":
        payload = {
            "path": str(history_path),
            "count": len(entries),
            "components": components or None,
            "summary": summary_only,
            "summary_counts": totals,
            "entries": [] if summary_only else entries,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if summary_only:
            filter_desc = ", ".join(components) if components else "all components"
            print(f"entries: {len(entries)} (filter: {filter_desc})")
            for key in COMPONENT_ORDER:
                print(f"- {key}: {totals[key]}")
        else:
            headers = ["ts", "components", "counts", "flags"]
            rows = []
            for entry in entries:
                rows.append(
                    [
                        str(entry.get("ts", "-")),
                        _format_components(entry),
                        _format_counts(entry),
                        _format_flags(entry),
                    ]
                )

            widths = [len(header) for header in headers]
            for row in rows:
                for idx, cell in enumerate(row):
                    widths[idx] = max(widths[idx], len(cell))

            fmt = " ".join(f"{{:<{w}}}" for w in widths)
            print(fmt.format(*headers))
            print("-" * (sum(widths) + len(widths) - 1))
            if rows:
                for row in rows:
                    print(fmt.format(*row))
            else:
                print("(no history entries found)")

    if receipt_flag or receipt_path_arg is not None:
        receipt_path = _resolve_receipt_path(receipt_path_arg)
        _write_receipt(
            receipt_path,
            history_path=history_path,
            limit=limit,
            components=components,
            entries=list(reversed(entries)) if limit >= 0 else entries,
            output_format=output_format,
            summary_only=summary_only,
            summary_counts=totals,
        )
        try:
            rel_path = receipt_path.relative_to(ROOT)
        except ValueError:
            rel_path = receipt_path
        print(f"[receipt] wrote {rel_path}")

    return 0


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    import argparse

    parser = subparsers.add_parser(
        "scan_history",
        help="Display recent systemic scan history entries",
    )
    parser.add_argument(
        "--path",
        type=Path,
        help="Path to scan history JSONL (default: _report/usage/scan-history.jsonl)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum history entries to show (default: 10, use -1 for all)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print aggregated component totals instead of per-entry detail",
    )
    parser.add_argument(
        "--component",
        action="append",
        help="Filter entries to those that include the specified component(s) (repeatable)",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--emit-receipt",
        action="store_true",
        help="Write a JSON receipt under _report/usage/scan-history/receipts/",
    )
    parser.add_argument(
        "--receipt-path",
        type=Path,
        help="Write the receipt to this path (implies --emit-receipt)",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]

"""Summaries for captured reflections stored under ``memory/reflections``."""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from teof._paths import repo_root

ROOT = repo_root(default=Path(__file__).resolve().parents[1])
REFLECTION_RELATIVE = Path("memory") / "reflections"
REFLECTION_DIR = ROOT / REFLECTION_RELATIVE
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass()
class ReflectionRecord:
    """Normalised view of a single reflection entry."""

    captured_at: datetime | None
    captured_raw: str | None
    title: str
    layers: list[str]
    summary: str | None
    signals: str | None
    actions: str | None
    tags: list[str]
    plan_suggestion: str | None
    notes: str | None
    receipt: str

    @property
    def captured_at_iso(self) -> str | None:
        if self.captured_at:
            return self.captured_at.strftime(ISO_FMT)
        return self.captured_raw


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _load_json(path: Path) -> Mapping[str, object] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, Mapping) else None


def _normalise_str_list(items: object, *, transform=lambda x: x) -> list[str]:
    results: list[str] = []
    if isinstance(items, Sequence) and not isinstance(items, (str, bytes)):
        for entry in items:
            if isinstance(entry, str):
                normalised = transform(entry)
                if normalised:
                    results.append(normalised)
    return results


def collect_reflections(root: Path | None = None) -> list[ReflectionRecord]:
    """Load reflection records sorted by newest first."""

    base = root or ROOT
    directory = base / REFLECTION_RELATIVE
    if not directory.exists():
        return []

    records: list[ReflectionRecord] = []
    for path in sorted(directory.glob("reflection-*.json")):
        payload = _load_json(path)
        if payload is None:
            continue
        captured_raw = payload.get("captured_at") if isinstance(payload.get("captured_at"), str) else None
        captured_at = _parse_iso(captured_raw)
        title_field = payload.get("title")
        title = title_field.strip() if isinstance(title_field, str) and title_field.strip() else path.stem
        layers = _normalise_str_list(payload.get("layers"), transform=lambda s: s.strip().upper())
        tags = _normalise_str_list(payload.get("tags"), transform=lambda s: s.strip())
        plan_suggestion = payload.get("plan_suggestion") if isinstance(payload.get("plan_suggestion"), str) else None
        summary = payload.get("summary") if isinstance(payload.get("summary"), str) else None
        signals = payload.get("signals") if isinstance(payload.get("signals"), str) else None
        actions = payload.get("actions") if isinstance(payload.get("actions"), str) else None
        notes = payload.get("notes") if isinstance(payload.get("notes"), str) else None
        receipt_field = payload.get("receipt") if isinstance(payload.get("receipt"), str) else None
        receipt = receipt_field or path.relative_to(base).as_posix()
        records.append(
            ReflectionRecord(
                captured_at=captured_at,
                captured_raw=captured_raw,
                title=title,
                layers=layers,
                summary=summary,
                signals=signals,
                actions=actions,
                tags=tags,
                plan_suggestion=plan_suggestion,
                notes=notes,
                receipt=receipt,
            )
        )

    records.sort(
        key=lambda record: (
            record.captured_at or datetime.min.replace(tzinfo=timezone.utc),
            record.receipt,
        ),
        reverse=True,
    )
    return records


def filter_reflections(
    reflections: Iterable[ReflectionRecord],
    *,
    layers: Sequence[str] | None = None,
    tags: Sequence[str] | None = None,
    since: datetime | None = None,
) -> list[ReflectionRecord]:
    layer_set = {layer.strip().upper() for layer in (layers or []) if layer.strip()}
    tag_set = {tag.strip().lower() for tag in (tags or []) if tag.strip()}

    results: list[ReflectionRecord] = []
    for record in reflections:
        if layer_set and not (layer_set & set(record.layers)):
            continue
        if tag_set and not (tag_set & {tag.lower() for tag in record.tags}):
            continue
        if since:
            if record.captured_at is None or record.captured_at < since:
                continue
        results.append(record)
    return results


def summarize(
    reflections: Iterable[ReflectionRecord],
    *,
    window_days: float | None = 7.0,
) -> dict[str, object]:
    """Compute aggregate statistics for the provided reflections."""

    now = datetime.now(timezone.utc)
    threshold = None
    if window_days is not None:
        threshold = now - timedelta(days=window_days)

    total = 0
    last_captured: datetime | None = None
    by_layer: Counter[str] = Counter()
    by_tag: Counter[str] = Counter()
    missing_plan: list[str] = []
    missing_tags: list[str] = []
    recent = 0

    for record in reflections:
        total += 1
        if record.captured_at and (last_captured is None or record.captured_at > last_captured):
            last_captured = record.captured_at
        if record.layers:
            by_layer.update(record.layers)
        if record.tags:
            by_tag.update(tag.lower() for tag in record.tags)
        else:
            missing_tags.append(record.receipt)
        if not record.plan_suggestion:
            missing_plan.append(record.receipt)
        if threshold and record.captured_at and record.captured_at >= threshold:
            recent += 1

    warnings: list[str] = []
    if missing_plan:
        warnings.append(f"{len(missing_plan)} reflection(s) missing plan suggestion")
    if missing_tags:
        warnings.append(f"{len(missing_tags)} reflection(s) missing tags")

    by_layer_sorted = dict(sorted(by_layer.items(), key=lambda item: (item[0])))
    by_tag_sorted = dict(sorted(by_tag.items(), key=lambda item: (-item[1], item[0])))

    return {
        "generated_at": now.strftime(ISO_FMT),
        "total": total,
        "last_captured": last_captured.strftime(ISO_FMT) if last_captured else None,
        "recent_window_days": window_days,
        "recent_count": recent,
        "by_layer": by_layer_sorted,
        "by_tag": by_tag_sorted,
        "missing_plan": missing_plan,
        "missing_tags": missing_tags,
        "warnings": warnings,
    }


def render_table(reflections: Sequence[ReflectionRecord], *, limit: int | None = None) -> str:
    """Render a compact table for terminal display."""

    rows: list[list[str]] = []
    selected = reflections[: limit if isinstance(limit, int) and limit >= 0 else None]
    for record in selected:
        captured = record.captured_at_iso or "-"
        layer_text = ",".join(record.layers) if record.layers else "-"
        plan = record.plan_suggestion or "-"
        tag_text = ",".join(record.tags) if record.tags else "-"
        rows.append([captured, layer_text, plan, tag_text, record.title])

    headers = ["Captured", "Layers", "Plan", "Tags", "Title"]
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    fmt = " ".join(f"{{:<{width}}}" for width in widths)
    lines = [fmt.format(*headers)]
    lines.append("-" * (sum(widths) + len(widths) - 1))
    for row in rows:
        lines.append(fmt.format(*row))
    if not rows:
        lines.append("(no reflections found)")
    return "\n".join(lines)


def to_payload(
    reflections: Sequence[ReflectionRecord],
    *,
    limit: int | None = None,
    summary: Mapping[str, object] | None = None,
    filters: Mapping[str, object] | None = None,
) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    selected = reflections[: limit if isinstance(limit, int) and limit >= 0 else None]
    entries = [
        {
            "captured_at": record.captured_at_iso,
            "title": record.title,
            "layers": record.layers,
            "summary": record.summary,
            "signals": record.signals,
            "actions": record.actions,
            "tags": record.tags,
            "plan_suggestion": record.plan_suggestion,
            "notes": record.notes,
            "receipt": record.receipt,
        }
        for record in selected
    ]

    payload: dict[str, object] = {
        "generated_at": now.strftime(ISO_FMT),
        "total_returned": len(entries),
        "reflections": entries,
    }
    if summary is not None:
        payload["summary"] = dict(summary)
    if filters is not None:
        payload["filters"] = dict(filters)
    return payload


def format_summary(summary: Mapping[str, object]) -> str:
    """Render a short summary block for terminal output."""

    lines: list[str] = []
    total = summary.get("total")
    last = summary.get("last_captured")
    if total is not None:
        line = f"Total reflections: {total}"
        if isinstance(last, str) and last:
            line += f" (latest: {last})"
        lines.append(line)

    window_days = summary.get("recent_window_days")
    recent = summary.get("recent_count")
    if isinstance(window_days, (int, float)) and isinstance(recent, int):
        lines.append(f"Reflections in last {window_days:g} day(s): {recent}")

    by_layer = summary.get("by_layer")
    if isinstance(by_layer, Mapping) and by_layer:
        parts = [f"{layer}={count}" for layer, count in by_layer.items()]
        lines.append("Layer coverage: " + ", ".join(parts))

    by_tag = summary.get("by_tag")
    if isinstance(by_tag, Mapping) and by_tag:
        parts = [f"{tag}={count}" for tag, count in by_tag.items()]
        lines.append("Top tags: " + ", ".join(parts[:5]))

    warnings = summary.get("warnings")
    if isinstance(warnings, Sequence):
        for warning in warnings:
            if isinstance(warning, str) and warning.strip():
                lines.append(f"warning: {warning.strip()}")

    return "\n".join(lines)


__all__ = [
    "ReflectionRecord",
    "collect_reflections",
    "filter_reflections",
    "summarize",
    "render_table",
    "to_payload",
    "format_summary",
]

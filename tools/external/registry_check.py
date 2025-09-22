"""Validate external feed registry and configuration integrity."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_MD = ROOT / "docs" / "adoption" / "external-feed-registry.md"
REGISTRY_CONFIG = ROOT / "docs" / "adoption" / "external-feed-registry.config.json"
SUMMARY_JSON = ROOT / "_report" / "usage" / "external-summary.json"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


class RegistryCheckError(RuntimeError):
    """Raised when registry validation fails."""


@dataclass
class FeedEntry:
    feed_id: str
    steward: str
    plan_path: Path
    key_path: Path
    latest_receipt: Path
    summary_path: Path


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY_MD, help="Path to registry markdown")
    parser.add_argument("--config", type=Path, default=REGISTRY_CONFIG, help="Path to registry config JSON")
    parser.add_argument("--summary", type=Path, default=SUMMARY_JSON, help="Path to external summary JSON")
    parser.add_argument(
        "--max-age-hours",
        type=float,
        default=24.0,
        help="Fail if latest receipt age exceeds this threshold",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON summary")
    return parser.parse_args(argv)


def _parse_markdown_link(cell: str) -> tuple[str, str]:
    cell = cell.strip()
    if not cell:
        return "", ""
    if cell.startswith("[`") and "](" in cell:
        label_part, path_part = cell.split("](", 1)
        label = label_part[2:]
        path = path_part.rstrip(")")
        return label, path
    return cell, ""


def _normalise_path(path_str: str, *, base: Path) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        return (base / path).resolve()
    return path


def _parse_registry(registry_path: Path) -> Dict[str, FeedEntry]:
    text = registry_path.read_text(encoding="utf-8")
    entries: Dict[str, FeedEntry] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells or cells[0] in {"feed_id", "---"}:
            continue
        if len(cells) < 6:
            raise RegistryCheckError(f"Registry row malformed: {line}")
        feed_id = cells[0]
        steward = cells[1]
        _, plan_rel = _parse_markdown_link(cells[2])
        _, key_rel = _parse_markdown_link(cells[3])
        _, receipt_rel = _parse_markdown_link(cells[4])
        _, summary_rel = _parse_markdown_link(cells[5])
        if not all([plan_rel, key_rel, receipt_rel, summary_rel]):
            raise RegistryCheckError(f"Registry row missing links for feed {feed_id}")
        base = registry_path.parent
        entries[feed_id] = FeedEntry(
            feed_id=feed_id,
            steward=steward,
            plan_path=_normalise_path(plan_rel, base=base),
            key_path=_normalise_path(key_rel, base=base),
            latest_receipt=_normalise_path(receipt_rel, base=base),
            summary_path=_normalise_path(summary_rel, base=base),
        )
    return entries


def _load_config(config_path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RegistryCheckError(f"Config not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise RegistryCheckError(f"Config not valid JSON: {config_path}") from exc
    feeds = data.get("feeds")
    if not isinstance(feeds, dict):
        raise RegistryCheckError("Config missing 'feeds' mapping")
    return feeds


def _load_summary(summary_path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(summary_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RegistryCheckError(f"Summary not found: {summary_path}") from exc
    except json.JSONDecodeError as exc:
        raise RegistryCheckError(f"Summary not valid JSON: {summary_path}") from exc
    feeds = data.get("feeds")
    if not isinstance(feeds, dict):
        raise RegistryCheckError("Summary missing feeds mapping")
    return data


def _age_seconds(iso_ts: str | None) -> float | None:
    if not iso_ts:
        return None
    dt_obj = datetime.strptime(iso_ts, ISO_FMT).replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt_obj).total_seconds()


def check_registry(
    *,
    registry_path: Path,
    config_path: Path,
    summary_path: Path,
    max_age_hours: float,
) -> Dict[str, Any]:
    registry_entries = _parse_registry(registry_path)
    config = _load_config(config_path)
    summary = _load_summary(summary_path)
    summary_feeds: Dict[str, Dict[str, Any]] = summary["feeds"]  # type: ignore[assignment]
    issues: list[Dict[str, Any]] = []
    ok_feeds: list[str] = []
    missing_in_registry = sorted(set(summary_feeds).difference(registry_entries))
    if missing_in_registry:
        issues.append({"type": "missing_registry_entry", "feeds": missing_in_registry})
    max_age_seconds = max_age_hours * 3600
    for feed_id, entry in registry_entries.items():
        feed_issues: list[str] = []
        if feed_id not in config:
            feed_issues.append("config_missing")
        else:
            cfg = config[feed_id]
            for key in ("steward", "plan_path", "key_path"):
                if key not in cfg:
                    feed_issues.append(f"config_missing_{key}")
        if not entry.plan_path.exists():
            feed_issues.append("plan_missing")
        if not entry.key_path.exists():
            feed_issues.append("key_missing")
        if not entry.latest_receipt.exists():
            feed_issues.append("receipt_missing")
        if not entry.summary_path.exists():
            feed_issues.append("summary_missing")
        feed_summary = summary_feeds.get(feed_id)
        if not feed_summary:
            feed_issues.append("summary_feed_missing")
        else:
            latest_receipt = feed_summary.get("latest_receipt")
            if latest_receipt:
                receipt_path = _normalise_path(latest_receipt, base=ROOT)
                if receipt_path.resolve() != entry.latest_receipt.resolve():
                    feed_issues.append("latest_receipt_mismatch")
            latest_ts = feed_summary.get("latest_issued_at")
            age = _age_seconds(latest_ts)
            if age is None:
                feed_issues.append("latest_issued_at_missing")
            elif age > max_age_seconds:
                feed_issues.append(f"stale_{age/3600:.2f}h")
        if feed_issues:
            issues.append({"type": "feed", "feed_id": feed_id, "issues": feed_issues})
        else:
            ok_feeds.append(feed_id)
    return {
        "registry": str(registry_path),
        "config": str(config_path),
        "summary": str(summary_path),
        "ok_feeds": sorted(ok_feeds),
        "issues": issues,
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    registry = args.registry if args.registry.is_absolute() else (ROOT / args.registry).resolve()
    config = args.config if args.config.is_absolute() else (ROOT / args.config).resolve()
    summary = args.summary if args.summary.is_absolute() else (ROOT / args.summary).resolve()
    result = check_registry(
        registry_path=registry,
        config_path=config,
        summary_path=summary,
        max_age_hours=args.max_age_hours,
    )
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"registry: {result['registry']}")
        print(f"config:   {result['config']}")
        print(f"summary:  {result['summary']}")
        if result["ok_feeds"]:
            print("ok feeds: " + ", ".join(result["ok_feeds"]))
        if result["issues"]:
            for issue in result["issues"]:
                if issue["type"] == "feed":
                    print(f"issue[{issue['feed_id']}]: {', '.join(issue['issues'])}")
                else:
                    print(f"issue[{issue['type']}]: {issue['feeds']}")
        else:
            print("no issues detected")
    return 1 if result["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

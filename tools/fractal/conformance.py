"""Generate a fractal conformance report for OCERS + coordinate coverage."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
QUEUE_DIR = REPO_ROOT / "queue"
PLANS_DIR = REPO_ROOT / "_plans"
MEMORY_LOG = REPO_ROOT / "memory" / "log.jsonl"

OCERS_LINE_RE = re.compile(r"^OCERS\s*Target\s*:\s*(.+)$", re.IGNORECASE)
COORD_LINE_RE = re.compile(r"^Coordinate\s*:\s*(.+)$", re.IGNORECASE)
SYSTEMIC_TOKEN_RE = re.compile(r"S(\d{1,2})")
LAYER_TOKEN_RE = re.compile(r"L(\d)")


@dataclass
class QueueEntry:
    path: str
    ocers_target: Optional[str]
    coordinates: List[str]
    issues: List[str]

    def as_dict(self) -> Dict[str, object]:
        return {
            "path": self.path,
            "ocers_target": self.ocers_target,
            "coordinates": self.coordinates,
            "issues": self.issues,
        }


@dataclass
class PlanEntry:
    path: str
    plan_id: str
    ocers_target: Optional[str]
    layer: Optional[str]
    systemic_scale: Optional[int]
    inferred_coordinate: Optional[str]
    issues: List[str]
    referenced_queue: List[str]

    def as_dict(self) -> Dict[str, object]:
        return {
            "path": self.path,
            "plan_id": self.plan_id,
            "ocers_target": self.ocers_target,
            "layer": self.layer,
            "systemic_scale": self.systemic_scale,
            "inferred_coordinate": self.inferred_coordinate,
            "referenced_queue": self.referenced_queue,
            "issues": self.issues,
        }


@dataclass
class MemoryEntry:
    index: int
    layer: Optional[str]
    systemic_scale: Optional[int]
    run_id: Optional[str]
    summary: str
    issues: List[str]

    def as_dict(self) -> Dict[str, object]:
        return {
            "index": self.index,
            "layer": self.layer,
            "systemic_scale": self.systemic_scale,
            "run_id": self.run_id,
            "summary": self.summary,
            "issues": self.issues,
        }


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_ocers(text: str) -> Optional[str]:
    for line in text.splitlines():
        match = OCERS_LINE_RE.match(line.strip())
        if match:
            value = match.group(1).strip().rstrip(".")
            return value or None
    return None


def _extract_coordinates(text: str) -> List[str]:
    coordinates: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        coord_match = COORD_LINE_RE.match(stripped)
        if coord_match:
            coord_value = coord_match.group(1).strip()
            if coord_value:
                coordinates.append(coord_value)
            continue
        systemics = SYSTEMIC_TOKEN_RE.findall(stripped)
        layers = LAYER_TOKEN_RE.findall(stripped)
        if systemics and layers:
            for systemic in systemics:
                for layer in layers:
                    coordinates.append(f"S{systemic}:L{layer}")
    return sorted(set(coordinates))


def gather_queue_entries() -> Dict[str, QueueEntry]:
    entries: Dict[str, QueueEntry] = {}
    if not QUEUE_DIR.exists():
        return entries
    for path in sorted(QUEUE_DIR.glob("*.md")):
        text = _read_text(path)
        ocers = _extract_ocers(text)
        coords = _extract_coordinates(text)
        issues: List[str] = []
        if not ocers:
            issues.append("missing_ocers_target")
        if not coords:
            issues.append("missing_coordinate")
        rel_path = path.relative_to(REPO_ROOT).as_posix()
        entries[rel_path] = QueueEntry(rel_path, ocers, coords, issues)
    return entries


def _load_json(path: Path) -> Dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def gather_plan_entries(queue_index: Dict[str, QueueEntry]) -> List[PlanEntry]:
    entries: List[PlanEntry] = []
    if not PLANS_DIR.exists():
        return entries
    for path in sorted(PLANS_DIR.glob("*.plan.json")):
        data = _load_json(path)
        ocers = data.get("ocers_target")
        referenced_queue = [
            item.get("ref")
            for item in data.get("links", [])
            if isinstance(item, dict) and item.get("type") == "queue"
        ]
        for ref in referenced_queue:
            if not ocers and ref in queue_index:
                ocers = queue_index[ref].ocers_target
        layer = data.get("layer")
        systemic_scale = data.get("systemic_scale")
        inferred_coordinate: Optional[str] = None
        if isinstance(systemic_scale, int) and layer:
            inferred_coordinate = f"S{systemic_scale}:L{layer}"
        issues: List[str] = []
        if not ocers:
            issues.append("missing_ocers_target")
        if not layer:
            issues.append("missing_layer")
        if systemic_scale is None:
            issues.append("missing_systemic_scale")
        rel_path = path.relative_to(REPO_ROOT).as_posix()
        entries.append(
            PlanEntry(
                path=rel_path,
                plan_id=str(data.get("plan_id", "")),
                ocers_target=ocers,
                layer=layer,
                systemic_scale=systemic_scale if isinstance(systemic_scale, int) else None,
                inferred_coordinate=inferred_coordinate,
                referenced_queue=referenced_queue,
                issues=issues,
            )
        )
    return entries


def gather_memory_entries() -> List[MemoryEntry]:
    entries: List[MemoryEntry] = []
    if not MEMORY_LOG.exists():
        return entries
    with MEMORY_LOG.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                entries.append(
                    MemoryEntry(
                        index=idx,
                        layer=None,
                        systemic_scale=None,
                        run_id=None,
                        summary="<invalid json>",
                        issues=["invalid_json"],
                    )
                )
                continue
            layer = payload.get("layer")
            systemic_scale = payload.get("systemic_scale")
            issues: List[str] = []
            if not layer:
                issues.append("missing_layer")
            if systemic_scale is None:
                issues.append("missing_systemic_scale")
            entries.append(
                MemoryEntry(
                    index=idx,
                    layer=layer if isinstance(layer, str) else None,
                    systemic_scale=systemic_scale if isinstance(systemic_scale, int) else None,
                    run_id=payload.get("run_id"),
                    summary=str(payload.get("summary", "")),
                    issues=issues,
                )
            )
    return entries


def build_report(strict: bool = False) -> Dict[str, object]:
    queue_entries = gather_queue_entries()
    plan_entries = gather_plan_entries(queue_entries)
    memory_entries = gather_memory_entries()

    queue_issue_count = sum(1 for entry in queue_entries.values() if entry.issues)
    plan_issue_count = sum(1 for entry in plan_entries if entry.issues)
    memory_issue_count = sum(1 for entry in memory_entries if entry.issues)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "queue_total": len(queue_entries),
            "queue_with_issues": queue_issue_count,
            "plans_total": len(plan_entries),
            "plans_with_issues": plan_issue_count,
            "memory_total": len(memory_entries),
            "memory_with_issues": memory_issue_count,
        },
        "queue": [entry.as_dict() for entry in queue_entries.values()],
        "plans": [entry.as_dict() for entry in plan_entries],
        "memory": [entry.as_dict() for entry in memory_entries],
    }

    if strict and (queue_issue_count or plan_issue_count or memory_issue_count):
        report["summary"]["strict_failure"] = True

    return report


def _write_report(report: Dict[str, object], out_path: Optional[Path], pretty: bool) -> None:
    text = json.dumps(report, indent=2 if pretty else None, sort_keys=pretty)
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
    else:
        print(text)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Check fractal conformance across TEOF artifacts")
    parser.add_argument(
        "--out",
        type=str,
        help="Optional path to write the conformance report (default: stdout)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON (indent + stable key ordering)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any artifact is missing OCERS or coordinate metadata",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    report = build_report(strict=args.strict)
    out_path = Path(args.out).resolve() if args.out else None
    _write_report(report, out_path, pretty=args.pretty)

    if args.strict and report["summary"].get("strict_failure"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

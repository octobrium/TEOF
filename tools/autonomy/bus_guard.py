from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
VALID_STATUS = {"active", "paused", "released", "done"}
STATUS_AUTOFIX = {"pending": "active", "in_progress": "active"}
ISO_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FORMAT)


def _normalize_time(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    if ISO_REGEX.match(value):
        return value
    return None


@dataclass
class BusIssue:
    scope: str
    path: str
    message: str
    line: int | None = None
    fixed: bool = False


class BusGuard:
    """Validate and optionally repair agent bus artifacts."""

    def __init__(self, root: Path, now_fn: Callable[[], str] | None = None) -> None:
        self.root = root
        self._now = now_fn or _iso_now
        self.claims_dir = self.root / "_bus" / "claims"
        self.assignments_dir = self.root / "_bus" / "assignments"
        self.messages_dir = self.root / "_bus" / "messages"
        self.events_log = self.root / "_bus" / "events" / "events.jsonl"

    def run(self, autofix: bool = False) -> list[BusIssue]:
        issues: list[BusIssue] = []
        issues.extend(self._scan_claims(autofix))
        issues.extend(self._scan_events())
        issues.extend(self._scan_assignments(autofix))
        issues.extend(self._scan_messages(autofix))
        issues.extend(self._scan_directives())
        return issues

    # ------------------------------------------------------------------ claims
    def _scan_claims(self, autofix: bool) -> list[BusIssue]:
        issues: list[BusIssue] = []
        if not self.claims_dir.exists():
            return issues
        for path in sorted(self.claims_dir.glob("*.json")):
            raw = self._load_json(path, issues, scope="claim")
            if raw is None:
                continue
            changed = False
            expected_task = path.stem
            if raw.get("task_id") != expected_task:
                issues.append(
                    BusIssue(
                        scope="claim",
                        path=self._rel(path),
                        message=f"task_id '{raw.get('task_id')}' must match filename '{expected_task}'",
                    )
                )
            agent_id = raw.get("agent_id")
            status = raw.get("status")
            if status not in VALID_STATUS:
                replacement = STATUS_AUTOFIX.get(str(status)) if status is not None else None
                if autofix and replacement:
                    raw["status"] = replacement
                    changed = True
                    issues.append(
                        BusIssue(
                            scope="claim",
                            path=self._rel(path),
                            message=f"status '{status}' → '{replacement}'",
                            fixed=True,
                        )
                    )
                else:
                    issues.append(
                        BusIssue(
                            scope="claim",
                            path=self._rel(path),
                            message=f"status '{status}' not in {sorted(VALID_STATUS)}",
                        )
                    )
            branch = raw.get("branch")
            if not isinstance(branch, str) or not branch.strip():
                issues.append(
                    BusIssue(scope="claim", path=self._rel(path), message="branch must be non-empty string")
                )
            elif not branch.startswith("agent/"):
                if autofix and isinstance(agent_id, str) and agent_id.strip():
                    slug = expected_task.lower().replace("_", "-")
                    raw["branch"] = f"agent/{agent_id}/{slug}"
                    changed = True
                    issues.append(
                        BusIssue(
                            scope="claim",
                            path=self._rel(path),
                            message=f"branch '{branch}' → '{raw['branch']}'",
                            fixed=True,
                        )
                    )
                else:
                    issues.append(
                        BusIssue(
                            scope="claim",
                            path=self._rel(path),
                            message=f"branch '{branch}' must start with 'agent/'",
                        )
                    )
            claimed_at = raw.get("claimed_at")
            normalized = _normalize_time(claimed_at)
            if normalized is None:
                if autofix:
                    replacement = _normalize_time(raw.get("released_at")) or self._now()
                    raw["claimed_at"] = replacement
                    changed = True
                    issues.append(
                        BusIssue(
                            scope="claim",
                            path=self._rel(path),
                            message=f"claimed_at '{claimed_at}' → '{replacement}'",
                            fixed=True,
                        )
                    )
                else:
                    issues.append(
                        BusIssue(
                            scope="claim",
                            path=self._rel(path),
                            message="claimed_at must be ISO8601 UTC (YYYY-MM-DDTHH:MM:SSZ)",
                        )
                    )
            if changed:
                self._write_json(path, raw)
        return issues

    # ------------------------------------------------------------------ events
    def _scan_events(self) -> list[BusIssue]:
        issues: list[BusIssue] = []
        if not self.events_log.exists():
            return issues
        with self.events_log.open(encoding="utf-8") as fh:
            for idx, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as exc:
                    issues.append(
                        BusIssue(
                            scope="events",
                            path=self._rel(self.events_log),
                            line=idx,
                            message=f"invalid JSON: {exc}",
                        )
                    )
                    continue
                for field in ("ts", "agent_id", "event", "summary"):
                    if field not in data:
                        issues.append(
                            BusIssue(
                                scope="events",
                                path=self._rel(self.events_log),
                                line=idx,
                                message=f"missing field '{field}'",
                            )
                        )
                ts = data.get("ts")
                if not isinstance(ts, str) or _normalize_time(ts) is None:
                    issues.append(
                        BusIssue(
                            scope="events",
                            path=self._rel(self.events_log),
                            line=idx,
                            message="ts must be ISO8601 UTC",
                        )
                    )
        return issues

    # --------------------------------------------------------------- assignments
    def _scan_assignments(self, autofix: bool) -> list[BusIssue]:
        issues: list[BusIssue] = []
        if not self.assignments_dir.exists():
            return issues
        for path in sorted(self.assignments_dir.glob("*.json")):
            raw = self._load_json(path, issues, scope="assignments")
            if raw is None:
                continue
            changed = False
            for field in ("task_id", "engineer", "manager", "assigned_at"):
                value = raw.get(field)
                if field == "assigned_at":
                    normalized = _normalize_time(value)
                    if normalized is None:
                        if autofix:
                            raw["assigned_at"] = self._now()
                            changed = True
                            issues.append(
                                BusIssue(
                                    scope="assignments",
                                    path=self._rel(path),
                                    message=f"assigned_at '{value}' → '{raw['assigned_at']}'",
                                    fixed=True,
                                )
                            )
                        else:
                            issues.append(
                                BusIssue(
                                    scope="assignments",
                                    path=self._rel(path),
                                    message="assigned_at must be ISO8601 UTC",
                                )
                            )
                    continue
                if isinstance(value, str) and value.strip():
                    continue
                if autofix and field == "engineer":
                    raw["engineer"] = "unassigned"
                    changed = True
                    issues.append(
                        BusIssue(
                            scope="assignments",
                            path=self._rel(path),
                            message="engineer → 'unassigned'",
                            fixed=True,
                        )
                    )
                else:
                    issues.append(
                        BusIssue(
                            scope="assignments",
                            path=self._rel(path),
                            message=f"missing or empty field '{field}'",
                        )
                    )
            if changed:
                self._write_json(path, raw)
        return issues

    # ----------------------------------------------------------------- messages
    def _scan_messages(self, autofix: bool) -> list[BusIssue]:
        issues: list[BusIssue] = []
        if not self.messages_dir.exists():
            return issues
        for path in sorted(self.messages_dir.glob("*.jsonl")):
            lines = path.read_text(encoding="utf-8").splitlines()
            changed = False
            new_lines: list[str] = []
            for idx, raw_line in enumerate(lines, start=1):
                line = raw_line.strip()
                if not line:
                    new_lines.append(raw_line)
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as exc:
                    issues.append(
                        BusIssue(
                            scope="messages",
                            path=self._rel(path),
                            line=idx,
                            message=f"invalid JSON: {exc}",
                        )
                    )
                    new_lines.append(raw_line)
                    continue
                entry_changed = False
                for field in ("ts", "from", "type", "task_id", "summary"):
                    if field == "ts":
                        ts_val = data.get("ts")
                        normalized = _normalize_time(ts_val)
                        if normalized is None:
                            if autofix:
                                candidate = None
                                if isinstance(ts_val, str):
                                    candidate = _normalize_time(ts_val)
                                    if candidate is None:
                                        candidate = _normalize_time(f"{ts_val}Z")
                                if candidate is None:
                                    candidate = self._now()
                                data["ts"] = candidate
                                entry_changed = True
                                issues.append(
                                    BusIssue(
                                        scope="messages",
                                        path=self._rel(path),
                                        line=idx,
                                        message=f"ts normalized to '{candidate}'",
                                        fixed=True,
                                    )
                                )
                            else:
                                issues.append(
                                    BusIssue(
                                        scope="messages",
                                        path=self._rel(path),
                                        line=idx,
                                        message="ts must be ISO8601 UTC",
                                    )
                                )
                        continue
                    if field in data and isinstance(data[field], str) and data[field].strip():
                        continue
                    if not autofix:
                        issues.append(
                            BusIssue(
                                scope="messages",
                                path=self._rel(path),
                                line=idx,
                                message=f"missing field '{field}'",
                            )
                        )
                        continue
                    if field == "from" and isinstance(data.get("agent_id"), str):
                        data["from"] = data["agent_id"]
                    elif field == "type" and isinstance(data.get("event"), str):
                        data["type"] = data["event"]
                    elif field == "task_id":
                        data["task_id"] = "manager-report"
                    elif field == "summary":
                        data["summary"] = "(missing summary)"
                    else:
                        data[field] = "unknown"
                    entry_changed = True
                    issues.append(
                        BusIssue(
                            scope="messages",
                            path=self._rel(path),
                            line=idx,
                            message=f"{field} autofilled",
                            fixed=True,
                        )
                    )
                if entry_changed:
                    changed = True
                    new_lines.append(json.dumps(data, ensure_ascii=False))
                else:
                    new_lines.append(raw_line)
            if changed:
                path.write_text("\n".join(new_lines) + ("\n" if new_lines else ""), encoding="utf-8")
        return issues

    # ----------------------------------------------------------- directive ptrs
    def _scan_directives(self) -> list[BusIssue]:
        issues: list[BusIssue] = []
        manager_path = self.messages_dir / "manager-report.jsonl"
        if not manager_path.exists():
            return issues
        pointers = self._collect_manager_directives(manager_path)
        for path in sorted(self.messages_dir.glob("BUS-COORD-*.jsonl")):
            directive_id = path.stem
            if self._has_directive_entry(path) and directive_id not in pointers:
                issues.append(
                    BusIssue(
                        scope="messages",
                        path=self._rel(path),
                        message=f"manager-report.jsonl missing pointer for directive {directive_id}",
                    )
                )
        return issues

    # ---------------------------------------------------------------- utilities
    def _load_json(self, path: Path, issues: list[BusIssue], scope: str) -> dict | None:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(
                BusIssue(scope=scope, path=self._rel(path), message=f"invalid JSON: {exc}")
            )
            return None

    def _write_json(self, path: Path, payload: dict) -> None:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def _collect_manager_directives(self, manager_path: Path) -> dict[str, list[dict]]:
        pointers: dict[str, list[dict]] = {}
        with manager_path.open(encoding="utf-8") as fh:
            for idx, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                meta = data.get("meta")
                if isinstance(meta, dict):
                    directive_id = meta.get("directive")
                    if isinstance(directive_id, str) and directive_id.strip():
                        pointers.setdefault(directive_id.strip(), []).append({"line": idx, "payload": data})
        return pointers

    def _has_directive_entry(self, path: Path) -> bool:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if str(data.get("type")) == "directive":
                    return True
        return False

    def _rel(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return str(path)


def run_guard(root: Path, autofix: bool = False) -> list[BusIssue]:
    guard = BusGuard(root)
    return guard.run(autofix=autofix)


__all__ = ["BusGuard", "BusIssue", "run_guard", "VALID_STATUS"]

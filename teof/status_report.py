from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - fallback for older runtimes
    import tomli as tomllib  # type: ignore

from teof._paths import repo_root
from tools.maintenance import capability_inventory
from tools.maintenance import automation_inventory
from tools.planner.exploratory_lane import scan_lane as scan_exploratory_lane

ROOT = repo_root(default=Path(__file__).resolve().parents[1])
ISO_FMT = "%Y-%m-%dT%H:%M:%S%zZ"


def _footprint_log_path(base: Path | None = None) -> Path:
    root = base or ROOT
    return root / "_report" / "usage" / "autonomy-footprint.jsonl"


def _footprint_baseline_path(base: Path | None = None) -> Path:
    root = base or ROOT
    return root / "docs" / "automation" / "autonomy-footprint-baseline.json"


@dataclass
class Objective:
    objective_id: str
    description: str
    detector: Callable[[Path], tuple[bool, str]]


def _now_iso() -> str:
    # Include explicit +00:00Z suffix to mirror existing docs
    ts = dt.datetime.now(dt.timezone.utc)
    return ts.strftime("%Y-%m-%dT%H:%M:%S+00:00Z")


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path.resolve())


def _capsule_line(root: Path) -> str:
    capsule_current = root / "capsule" / "current"
    target = "missing"
    if capsule_current.exists():
        if capsule_current.is_symlink():
            target = str(capsule_current.readlink())
        elif capsule_current.is_dir():
            target = capsule_current.name
        else:
            target = capsule_current.as_posix()
    combo = str(capsule_current)
    return f"Capsule: {combo} -> {target}"


def _package_line(root: Path) -> str:
    version = "unknown"
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            with pyproject.open("rb") as handle:
                data = tomllib.load(handle)
            version = str(data.get("project", {}).get("version", version))
        except Exception:
            version = "unknown"
    return f"Package: teof {version}"


def _cli_line() -> str:
    return "CLI: `teof brief` → writes `artifacts/systemic_out/<UTCSTAMP>/` and updates `artifacts/systemic_out/latest/`"


def _artifacts_line(root: Path) -> str:
    latest = root / "artifacts" / "systemic_out" / "latest"
    ready = latest.is_dir() or latest.is_symlink()
    brief = latest / "brief.json"
    score = latest / "score.txt"
    ready = ready and brief.exists() and score.exists()
    status = "yes" if ready else "no"
    latest_path = str(latest)
    return f"Artifacts latest: {latest_path} (ready: {status})"


def _authenticity_line(root: Path) -> str:
    auth_md = root / "_report" / "usage" / "external-authenticity.md"
    if auth_md.exists():
        rel = _relative(auth_md, root)
        return f"Authenticity dashboard: `{rel}` (auto-refreshes with each summary run)"
    rel = _relative(auth_md, root)
    return f"Authenticity dashboard: `{rel}` (missing — run `teof-external-summary`)"


def _parse_expires_at(raw: object) -> dt.datetime | None:
    if not isinstance(raw, str) or not raw:
        return None
    try:
        stamp = dt.datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None
    return stamp.replace(tzinfo=dt.timezone.utc)


def _exploratory_lane_line(root: Path) -> str:
    try:
        summary = scan_exploratory_lane(root=root)
    except Exception:  # pragma: no cover - defensive guard
        return "Exploratory lane: status unavailable (scan error)"

    counts = summary.get("counts", {})
    total = counts.get("total", 0)
    if total == 0:
        return "Exploratory lane: (inactive — use `teof-plan new <slug> --exploratory` to bootstrap)"

    active = counts.get("active", 0)
    expired = counts.get("expired", 0)
    expiring = counts.get("expiring", 0)
    missing = counts.get("receipts_missing", 0)
    receipts_total = sum(plan.get("receipts_count", 0) for plan in summary.get("plans", []))
    warning_hours = summary.get("warning_hours")
    warning_label = f"{warning_hours:.0f}h" if isinstance(warning_hours, (int, float)) else "threshold"
    parts = [
        f"Exploratory lane: plans={total}",
        f"(active={active}, expired={expired}, expiring<={warning_label}={expiring})",
        f"receipts={receipts_total} (missing={missing})",
    ]
    errors = summary.get("errors")
    if errors:
        parts.append(f"errors={len(errors)}")
    return " | ".join(parts)


def _count_autonomy_metrics(root: Path) -> tuple[int, int, int]:
    """Return (python_file_count, loc, helper_defs) for tools.autonomy."""

    autonomy_dir = root / "tools" / "autonomy"
    if not autonomy_dir.exists():
        return 0, 0, 0

    python_files = [path for path in autonomy_dir.rglob("*.py") if path.name != "__init__.py"]
    file_count = 0
    loc_total = 0
    helper_defs = 0

    for path in python_files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        file_count += 1
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            loc_total += 1
            if stripped.startswith("def _"):
                helper_defs += 1
    return file_count, loc_total, helper_defs


def _count_autonomy_receipts(root: Path) -> int:
    usage_dir = root / "_report" / "usage"
    if not usage_dir.exists():
        return 0
    count = 0
    for path in usage_dir.rglob("*.json"):
        if "autonomy" in path.stem:
            count += 1
    return count


def _find_autonomy_receipts(root: Path) -> list[Path]:
    usage_dir = root / "_report" / "usage"
    if not usage_dir.exists():
        return []
    matches: list[Path] = []
    for path in usage_dir.rglob("*.json"):
        if "autonomy" in path.stem:
            matches.append(path)
    return matches


def _load_autonomy_baseline(root: Path | None = None) -> dict[str, int] | None:
    path = _footprint_baseline_path(root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict):
        return {key: int(data.get(key, 0)) for key in ("module_files", "loc", "helper_defs", "receipt_count")}
    return None


def get_autonomy_footprint(root: Path | None = None) -> dict[str, int]:
    """Return current autonomy footprint metrics for reporting/tests."""

    root = root or ROOT
    files, loc, helpers = _count_autonomy_metrics(root)
    receipts = _count_autonomy_receipts(root)
    return {
        "module_files": files,
        "loc": loc,
        "helper_defs": helpers,
        "receipt_count": receipts,
    }


def get_autonomy_baseline(root: Path | None = None) -> dict[str, int] | None:
    return _load_autonomy_baseline(root)


def log_autonomy_footprint(root: Path | None = None) -> dict[str, int]:
    """Append current autonomy footprint to the JSONL log and return metrics."""

    root = root or ROOT
    metrics = get_autonomy_footprint(root)
    youngest_receipts = _find_autonomy_receipts(root)
    log_path = _footprint_log_path(root)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "generated_at": _now_iso(),
        **metrics,
        "receipt_paths": [str(p.relative_to(root)) for p in youngest_receipts[:20]],
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    _trim_autonomy_footprint_log(log_path)
    return metrics


def get_recent_autonomy_footprint_entries(
    root: Path | None = None, limit: int = 5
) -> list[dict[str, str | int]]:
    log_path = _footprint_log_path(root)
    if not log_path.exists():
        return []
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    entries: list[dict[str, str | int]] = []
    for raw in lines[-limit:]:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            entries.append(parsed)
    return entries


def _trim_autonomy_footprint_log(log_path: Path, max_entries: int = 100) -> None:
    if not log_path.exists():
        return
    data = log_path.read_text(encoding="utf-8").splitlines()
    if len(data) <= max_entries:
        return
    trimmed = data[-max_entries:]
    log_path.write_text("\n".join(trimmed) + "\n", encoding="utf-8")


def _format_delta_label(current: int, baseline: int | None) -> str:
    if baseline is None:
        return str(current)
    delta = current - baseline
    if delta == 0:
        return f"{current} (Δ0)"
    sign = "+" if delta > 0 else ""
    return f"{current} ({sign}{delta})"


def detect_sustained_autonomy_growth(
    entries: list[dict[str, str | int]],
    baseline: dict[str, int] | None,
    *,
    lookback: int = 3,
) -> bool:
    if len(entries) < lookback or not baseline:
        return False
    metrics = ("module_files", "loc", "helper_defs")
    window = entries[-lookback:]
    # ensure chronological order
    try:
        window = sorted(
            window,
            key=lambda item: str(item.get("generated_at", "")),
        )
    except Exception:
        pass
    for metric in metrics:
        try:
            values = [int(item.get(metric, 0)) for item in window]
        except (TypeError, ValueError):
            continue
        if all(b > a for a, b in zip(values, values[1:])):
            if values[-1] > baseline.get(metric, values[0]):
                return True
    return False


def _detect_obj_a4(root: Path) -> tuple[bool, str]:
    quickstart = root / "docs" / "quickstart.md"
    if not quickstart.exists():
        return False, "docs/quickstart.md missing"
    text = quickstart.read_text(encoding="utf-8")
    missing: list[str] = []
    if "python3 -m pip install -e ." not in text:
        missing.append("`pip install -e .`")
    if "teof brief" not in text:
        missing.append("`teof brief`")
    if missing:
        return False, "Missing commands: " + ", ".join(missing)
    return True, "Confirmed Quickstart snippet includes editable install + brief run"


def _detect_obj_a5(root: Path) -> tuple[bool, str]:
    hook = root / ".githooks" / "pre-commit"
    if not hook.exists():
        return False, "`.githooks/pre-commit` missing"
    text = hook.read_text(encoding="utf-8", errors="ignore")
    has_status = "teof status" in text
    has_add = "git add docs/status.md" in text
    if has_status and has_add:
        return True, "Pre-commit hook refreshes docs/status.md"
    missing: list[str] = []
    if not has_status:
        missing.append("`teof status` step")
    if not has_add:
        missing.append("`git add docs/status.md`")
    detail = "Missing " + " & ".join(missing)
    return False, detail


OBJECTIVES: tuple[Objective, ...] = (
    Objective(
        objective_id="OBJ-A4",
        description="Update docs/quickstart.md with editable install and CLI",
        detector=_detect_obj_a4,
    ),
    Objective(
        objective_id="OBJ-A5",
        description="Append STATUS refresh to pre-commit",
        detector=_detect_obj_a5,
    ),
)


def gather_snapshot_lines(root: Path) -> list[str]:
    return [
        _capsule_line(root),
        _package_line(root),
        _cli_line(),
        _artifacts_line(root),
        _authenticity_line(root),
        _exploratory_lane_line(root),
    ]


def gather_objective_lines(root: Path, objectives: Iterable[Objective]) -> list[str]:
    lines: list[str] = []
    for objective in objectives:
        done, detail = objective.detector(root)
        status = "done" if done else "todo"
        lines.append(
            f"[{status}] {objective.objective_id} — {objective.description} — {detail}"
        )
    return lines


def _capability_summary(root: Path, *, stale_days: float = 30.0) -> list[str]:
    try:
        inventory = capability_inventory.generate_inventory(stale_days=stale_days)
    except Exception:  # pragma: no cover - defensive guard
        return ["- Capability inventory unavailable"]

    now = dt.datetime.now(dt.timezone.utc)
    threshold = dt.timedelta(days=stale_days)

    stale_entries = []
    missing_tests = []
    for usage in inventory:
        if not usage.tests:
            missing_tests.append(usage)
        last = usage.last_receipt
        if last is None or now - last > threshold:
            stale_entries.append(usage)

    lines = [
        "- Commands: "
        + f"{len(inventory)} | missing tests: {len(missing_tests)} | stale>{int(stale_days)}d: {len(stale_entries)}"
    ]

    if missing_tests:
        lines.append(
            "- Missing tests: "
            + ", ".join(sorted(usage.name for usage in missing_tests[:5]))
            + (" …" if len(missing_tests) > 5 else "")
        )

    if stale_entries:
        lines.append("- Stale commands (limit 5):")
        for usage in sorted(stale_entries[:5], key=lambda item: item.name):
            last = usage.last_receipt.isoformat() if usage.last_receipt else "never"
            lines.append(f"  - {usage.name}: last_receipt={last}")
        if len(stale_entries) > 5:
            lines.append(f"  - (+{len(stale_entries) - 5} more)")
    return lines


def _automation_summary(root: Path, *, stale_days: float = 30.0) -> list[str]:
    try:
        entries = automation_inventory.generate_inventory(stale_days=stale_days)
    except Exception:  # pragma: no cover - defensive guard
        return ["- Automation inventory unavailable"]

    threshold = dt.timedelta(days=stale_days)
    missing_receipts = [entry for entry in entries if not entry.receipts]
    stale_receipts = [entry for entry in entries if entry.is_stale(threshold)]
    missing_tests = [entry for entry in entries if not entry.tests]

    lines = [
        "- Modules: "
        + f"{len(entries)} | missing receipts: {len(missing_receipts)} | stale>{int(stale_days)}d: {len(stale_receipts)} | missing tests: {len(missing_tests)}"
    ]

    def _list_entries(label: str, items: list[automation_inventory.AutomationEntry]) -> None:
        if not items:
            return
        lines.append(label)
        for entry in sorted(items, key=lambda e: e.module)[:5]:
            last = entry.last_receipt.isoformat() if entry.last_receipt else "never"
            lines.append(f"  - {entry.module}: last_receipt={last}")
        if len(items) > 5:
            lines.append(f"  - (+{len(items) - 5} more)")

    _list_entries("- Stale receipts (limit 5):", stale_receipts)
    if not stale_receipts:
        _list_entries("- Missing receipts (limit 5):", missing_receipts)
    _list_entries("- No direct tests detected (limit 5):", missing_tests)
    return lines


def generate_status(root: Path | None = None, *, log: bool = True) -> str:
    root = root or ROOT
    timestamp = _now_iso()
    if log and root.resolve() == ROOT.resolve():
        footprint = log_autonomy_footprint(root)
    else:
        footprint = get_autonomy_footprint(root)
    baseline = _load_autonomy_baseline(root)
    baseline_lookup = baseline or {}
    recent_entries = get_recent_autonomy_footprint_entries(root)
    lines: list[str] = []
    lines.append(f"# TEOF Status ({timestamp})")
    lines.append("")
    lines.append("## Snapshot")
    for entry in gather_snapshot_lines(root):
        lines.append(f"- {entry}")
    lines.append("")
    lines.append("## Autonomy Footprint")
    lines.append(
        "- Modules: "
        + " · ".join(
            [
                f"{_format_delta_label(footprint['module_files'], baseline_lookup.get('module_files'))} files",
                f"{_format_delta_label(footprint['loc'], baseline_lookup.get('loc'))} LOC",
                f"{_format_delta_label(footprint['helper_defs'], baseline_lookup.get('helper_defs'))} helper defs",
            ]
        )
    )
    receipt_label = _format_delta_label(
        footprint["receipt_count"], baseline_lookup.get("receipt_count")
    )
    lines.append(
        f"- Receipts: {receipt_label} JSON receipts under `_report/usage` containing 'autonomy'"
    )
    if footprint["receipt_count"] > 200:
        lines.append(
            "- Warning: autonomy receipts exceed 200; prune stale entries under `_report/usage`."
        )
    growth_flag = detect_sustained_autonomy_growth(recent_entries, baseline_lookup)
    if recent_entries:
        lines.append("- Recent Footprint Deltas:")
        for entry in reversed(recent_entries[-3:]):
            stamp = entry.get("generated_at", "?")
            modules = entry.get("module_files", "?")
            loc = entry.get("loc", "?")
            helpers = entry.get("helper_defs", "?")
            receipts = entry.get("receipt_count", "?")
            lines.append(
                f"  - {stamp}: modules={modules}, loc={loc}, helpers={helpers}, receipts={receipts}"
            )
    else:
        lines.append("- Recent Footprint Deltas: (no log entries)")
    if growth_flag:
        lines.append(
            "- Warning: sustained autonomy growth detected across recent runs; prune receipts or reassess scope."
        )
    lines.append("")
    lines.append("## CLI Capability Health")
    for entry in _capability_summary(root):
        lines.append(entry)
    lines.append("")
    lines.append("## Automation Health")
    for entry in _automation_summary(root):
        lines.append(entry)
    lines.append("")
    lines.append("## Auto Objectives (detected)")
    for entry in gather_objective_lines(root, OBJECTIVES):
        lines.append(f"- {entry}")
    lines.append("")
    lines.append("## Manual Objectives (optional)")
    lines.append("- (none listed)")
    lines.append("")
    lines.append("## Notes")
    lines.append("- Keep `capsule/current` as a symlink.")
    lines.append("- Python ≥3.9 for local dev.")
    lines.append("")
    return "\n".join(lines)


def write_status(path: Path, *, root: Path | None = None, quiet: bool = False) -> Path:
    root = root or ROOT
    content = generate_status(root, log=root.resolve() == ROOT.resolve())
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if not quiet:
        rel = _relative(path, root)
        print(f"wrote {rel}")
    return path


__all__ = [
    "generate_status",
    "write_status",
    "OBJECTIVES",
    "get_autonomy_footprint",
    "get_autonomy_baseline",
    "log_autonomy_footprint",
    "get_recent_autonomy_footprint_entries",
    "detect_sustained_autonomy_growth",
]

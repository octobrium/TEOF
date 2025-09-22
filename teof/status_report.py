from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - fallback for older runtimes
    import tomli as tomllib  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
ISO_FMT = "%Y-%m-%dT%H:%M:%S%zZ"


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
    return "CLI: `teof brief` → writes `artifacts/ocers_out/<UTCSTAMP>/` and updates `artifacts/ocers_out/latest/`"


def _artifacts_line(root: Path) -> str:
    latest = root / "artifacts" / "ocers_out" / "latest"
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
    has_add = "git add docs/STATUS.md" in text
    if has_status and has_add:
        return True, "Pre-commit hook refreshes docs/STATUS.md"
    missing: list[str] = []
    if not has_status:
        missing.append("`teof status` step")
    if not has_add:
        missing.append("`git add docs/STATUS.md`")
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


def generate_status(root: Path | None = None) -> str:
    root = root or ROOT
    timestamp = _now_iso()
    lines: list[str] = []
    lines.append(f"# TEOF Status ({timestamp})")
    lines.append("")
    lines.append("## Snapshot")
    for entry in gather_snapshot_lines(root):
        lines.append(f"- {entry}")
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
    content = generate_status(root)
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if not quiet:
        rel = _relative(path, root)
        print(f"wrote {rel}")
    return path


__all__ = ["generate_status", "write_status", "OBJECTIVES"]

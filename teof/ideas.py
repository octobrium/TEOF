"""Helpers for managing TEOF idea artifacts."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - Python <3.11 fallback
    import tomli as tomllib  # type: ignore

from teof._paths import repo_root

ROOT = repo_root(default=Path(__file__).resolve().parents[1])
IDEA_DIR = ROOT / "docs" / "ideas"
FRONTMATTER_DELIM = "+++"
DEFAULT_STATUS = "draft"
VALID_STATUSES: tuple[str, ...] = ("draft", "triage", "in_review", "in_progress", "promoted", "archived")
STATUS_WEIGHT = {
    "draft": 2,
    "triage": 4,
    "in_review": 5,
    "in_progress": 3,
    "promoted": 1,
    "archived": -5,
}


@dataclass
class Idea:
    path: Path
    meta: dict[str, Any]
    body: str

    @property
    def id(self) -> str:
        value = self.meta.get("id")
        if isinstance(value, str) and value.strip():
            return value.strip()
        return self.path.stem

    @property
    def status(self) -> str:
        value = self.meta.get("status")
        if isinstance(value, str) and value.strip():
            lowered = value.strip().lower()
            if lowered in VALID_STATUSES:
                return lowered
        return DEFAULT_STATUS

    @property
    def title(self) -> str:
        value = self.meta.get("title")
        if isinstance(value, str) and value.strip():
            return value.strip()
        for line in self.body.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip() or self.id
        return self.id


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith(FRONTMATTER_DELIM):
        return {}, text
    remainder = text[len(FRONTMATTER_DELIM) :]
    if remainder.startswith("\n"):
        remainder = remainder[1:]
    closing_token = f"\n{FRONTMATTER_DELIM}\n"
    end_idx = remainder.find(closing_token)
    if end_idx == -1:
        # Allow files that end with +++ without newline
        alt_closing = f"\n{FRONTMATTER_DELIM}"
        end_idx = remainder.find(alt_closing)
        if end_idx == -1:
            raise ValueError("idea frontmatter is not terminated")
        body_start = end_idx + len(alt_closing)
    else:
        body_start = end_idx + len(closing_token)
    frontmatter_raw = remainder[:end_idx]
    body = remainder[body_start:]
    try:
        meta = tomllib.loads(frontmatter_raw) if frontmatter_raw.strip() else {}
    except tomllib.TOMLDecodeError as exc:  # pragma: no cover - defensive
        raise ValueError(f"failed to parse idea frontmatter: {exc}") from exc
    return meta, body.lstrip("\n")


def _format_value(value: Any) -> str:
    if isinstance(value, str):
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return "[" + ", ".join(_format_value(item) for item in value) + "]"
    raise ValueError(f"unsupported frontmatter value type: {type(value)!r}")


def _dump_frontmatter(meta: dict[str, Any]) -> str:
    if not meta:
        return ""
    # Stable ordering: id, title, status, created, updated, then sorted remainder
    ordered_keys: list[str] = []
    for key in ("id", "title", "status", "layers", "systemic", "created", "updated", "owner", "links"):
        if key in meta:
            ordered_keys.append(key)
    for key in sorted(meta):
        if key not in ordered_keys:
            ordered_keys.append(key)
    lines = []
    for key in ordered_keys:
        lines.append(f"{key} = {_format_value(meta[key])}")
    return "\n".join(lines)


def load_idea(path: Path) -> Idea:
    text = path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(text)
    meta = dict(meta)
    meta.setdefault("id", path.stem)
    meta.setdefault("status", DEFAULT_STATUS)
    if "created" not in meta:
        meta["created"] = _now_iso()
    return Idea(path=path, meta=meta, body=body)


def write_idea(idea: Idea) -> None:
    meta = dict(idea.meta)
    meta.setdefault("id", idea.id)
    meta.setdefault("status", idea.status)
    meta.setdefault("created", _now_iso())
    meta["updated"] = _now_iso()
    frontmatter = _dump_frontmatter(meta)
    body = idea.body.lstrip("\n")
    if not body.endswith("\n"):
        body = body + "\n"
    content = (
        f"{FRONTMATTER_DELIM}\n{frontmatter}\n{FRONTMATTER_DELIM}\n\n{body}"
    )
    idea.path.parent.mkdir(parents=True, exist_ok=True)
    idea.path.write_text(content, encoding="utf-8")


def iter_ideas(directory: Path | None = None) -> list[Idea]:
    root = directory or IDEA_DIR
    ideas: list[Idea] = []
    if not root.exists():
        return ideas
    for path in sorted(root.glob("*.md")):
        if path.name.lower() in {"readme.md", "index.md"}:
            continue
        ideas.append(load_idea(path))
    return ideas


def resolve_idea(identifier: str | Path, directory: Path | None = None) -> Path:
    candidate = Path(identifier)
    if candidate.exists():
        return candidate.resolve()
    directory = directory or IDEA_DIR
    base = directory / Path(identifier).name
    if base.exists():
        return base.resolve()
    for suffix in (".md", ".markdown", ".txt"):
        alt = directory / f"{Path(identifier).name}{suffix}"
        if alt.exists():
            return alt.resolve()
    raise FileNotFoundError(f"idea not found: {identifier}")


def set_status(idea: Idea, status: str) -> Idea:
    normalized = status.strip().lower()
    if normalized not in VALID_STATUSES:
        raise ValueError(f"status must be one of {', '.join(VALID_STATUSES)}")
    idea.meta = dict(idea.meta)
    idea.meta["status"] = normalized
    idea.meta["updated"] = _now_iso()
    return idea


def _parse_iso_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def evaluate_idea(idea: Idea, *, now: datetime | None = None) -> dict[str, Any]:
    """Return heuristic scores and reasoning for prioritising an idea."""

    now = now or _now_utc()
    meta = idea.meta
    status = idea.status
    layers_raw = meta.get("layers")
    systemic_raw = meta.get("systemic")
    layers = (
        [entry for entry in layers_raw if isinstance(entry, str)]
        if isinstance(layers_raw, Sequence) and not isinstance(layers_raw, (str, bytes))
        else []
    )
    systemic = (
        [entry for entry in systemic_raw if isinstance(entry, (int, float))]
        if isinstance(systemic_raw, Sequence) and not isinstance(systemic_raw, (str, bytes))
        else []
    )
    plan_id = meta.get("plan_id") if isinstance(meta.get("plan_id"), str) else None

    status_score = STATUS_WEIGHT.get(status, 0)
    layer_score = len(list(layers)) * 1.5 if layers else 0.0
    systemic_score = max((float(s) for s in systemic if isinstance(s, (int, float))), default=0.0) * 0.5 if systemic else 0.0

    updated = _parse_iso_datetime(meta.get("updated")) or _parse_iso_datetime(meta.get("created"))
    recency_score = 0.0
    if updated:
        age_days = (now - updated).total_seconds() / 86400.0
        if age_days <= 7:
            recency_score = 5 - (age_days * 0.5)

    plan_penalty = -5.0 if plan_id else 0.0

    raw_score = status_score + layer_score + systemic_score + recency_score + plan_penalty

    reasons: list[str] = []
    reasons.append(f"status={status} (weight {status_score:+.1f})")
    if layers:
        reasons.append(f"{len(layers)} layer tag(s) (+{layer_score:.1f})")
    if systemic:
        reasons.append(f"systemic max={max(systemic)} (+{systemic_score:.1f})")
    if updated:
        reasons.append(f"updated {updated.isoformat()} (Δ {recency_score:+.1f})")
    if plan_id:
        reasons.append("already linked to plan (promotion penalty)")
    return {
        "id": idea.id,
        "title": idea.title,
        "status": status,
        "score": round(raw_score, 2),
        "layers": list(layers),
        "systemic": list(systemic),
        "plan_id": plan_id,
        "path": idea.path,
        "reasons": reasons,
        "updated": updated.isoformat() if updated else None,
        "created": (_parse_iso_datetime(meta.get("created")) or updated).isoformat() if (meta.get("created") or updated) else None,
    }


def evaluate_ideas(ideas: Iterable[Idea], *, now: datetime | None = None) -> list[dict[str, Any]]:
    scored = [evaluate_idea(idea, now=now) for idea in ideas]
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored


__all__ = [
    "Idea",
    "IDEA_DIR",
    "VALID_STATUSES",
    "iter_ideas",
    "load_idea",
    "resolve_idea",
    "set_status",
    "evaluate_idea",
    "evaluate_ideas",
    "write_idea",
]

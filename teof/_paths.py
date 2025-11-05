"""Repo root resolution utilities."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Iterator

__all__ = ["RepoRootError", "repo_root", "set_repo_root"]


class RepoRootError(RuntimeError):
    """Raised when the repository root cannot be determined."""


_ROOT_CACHE: Path | None = None
_ENV_VARS = ("TEOF_ROOT", "TEOF_REPO_ROOT")
_MARKERS = ("pyproject.toml", "README.md", "teof")


def set_repo_root(path: Path) -> None:
    """Force the repository root to *path* (used by tests)."""

    global _ROOT_CACHE
    _ROOT_CACHE = path.resolve()


def _iter_env_candidates() -> Iterator[Path]:
    for name in _ENV_VARS:
        value = os.environ.get(name)
        if not value:
            continue
        candidate = Path(value).expanduser()
        yield candidate


def _iter_default_candidates(start: Path) -> Iterator[Path]:
    for candidate in (start, *start.parents):
        yield candidate
    yield Path.cwd()


def _is_repo_root(path: Path) -> bool:
    return all((path / marker).exists() for marker in _MARKERS)


def _unique(paths: Iterable[Path]) -> Iterator[Path]:
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        yield resolved


def repo_root(*, default: Path | None = None, start: Path | None = None) -> Path:
    """Return the repository root directory.

    Resolution order:
    1. Explicit override via :func:`set_repo_root`.
    2. Environment variables (``TEOF_ROOT`` or ``TEOF_REPO_ROOT``).
    3. Walk up from *start* (defaults to this module) searching for repo markers.
    4. Current working directory.

    If no candidate matches the expected markers and *default* is provided, the
    fallback is returned. Otherwise :class:`RepoRootError` is raised with guidance.
    """

    global _ROOT_CACHE
    if _ROOT_CACHE is not None:
        return _ROOT_CACHE

    start_path = start or Path(__file__).resolve()
    candidates = list(_iter_env_candidates()) + list(_iter_default_candidates(start_path))
    for candidate in _unique(candidates):
        if _is_repo_root(candidate):
            _ROOT_CACHE = candidate
            return _ROOT_CACHE

    if default is not None:
        _ROOT_CACHE = default.resolve()
        return _ROOT_CACHE

    env_hint = " or ".join(_ENV_VARS)
    raise RepoRootError(
        "Unable to locate the TEOF repository root. "
        f"Set {env_hint} to the repo path or run within a cloned workspace."
    )

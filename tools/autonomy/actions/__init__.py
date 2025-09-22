"""Action registry for autonomy execution hooks."""
from __future__ import annotations

from importlib import import_module
from typing import Callable, Mapping

_ACTION_SPECS: Mapping[str, str] = {
    "2025-09-23-repo-hygiene": "tools.autonomy.actions.hygiene:run",
}


def resolve(plan_id: str) -> Callable[..., dict] | None:
    """Return the callable action associated with a plan id, if any."""

    spec = _ACTION_SPECS.get(plan_id)
    if not spec:
        return None
    module_name, _, attr = spec.partition(":")
    if not module_name or not attr:
        return None
    module = import_module(module_name)
    action = getattr(module, attr, None)
    if callable(action):
        return action
    return None


__all__ = ["resolve"]

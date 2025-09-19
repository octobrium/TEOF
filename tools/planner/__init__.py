"""Planner tooling for plan validation and automation."""
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = [
    "PLAN_STATUS",
    "STEP_STATUS",
    "ValidationResult",
    "strict_checks",
    "validate_plan",
    "PlannerCliError",
    "build_cli_parser",
    "cli_main",
    "link_memory_main",
    "validate",
    "cli",
]

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from .cli import PlannerCliError, build_parser as build_cli_parser, main as cli_main
    from .link_memory import main as link_memory_main
    from .validate import (
        PLAN_STATUS,
        STEP_STATUS,
        ValidationResult,
        strict_checks,
        validate_plan,
    )


_VALIDATE_ATTRS = {
    "PLAN_STATUS",
    "STEP_STATUS",
    "ValidationResult",
    "strict_checks",
    "validate_plan",
}

_CLI_ATTR_MAP = {
    "PlannerCliError": "PlannerCliError",
    "build_cli_parser": "build_parser",
    "cli_main": "main",
}

_MODULE_EXPORTS = {
    "validate": "tools.planner.validate",
    "cli": "tools.planner.cli",
}


def __getattr__(name: str) -> Any:
    if name in _MODULE_EXPORTS:
        module = import_module(_MODULE_EXPORTS[name])
        globals()[name] = module
        return module

    if name in _VALIDATE_ATTRS:
        module = import_module("tools.planner.validate")
        value = getattr(module, name)
        globals()[name] = value
        return value

    if name in _CLI_ATTR_MAP:
        module = import_module("tools.planner.cli")
        attr_name = _CLI_ATTR_MAP[name]
        value = getattr(module, attr_name)
        globals()[name] = value
        return value

    if name == "link_memory_main":
        module = import_module("tools.planner.link_memory")
        value = module.main
        globals()[name] = value
        return value

    raise AttributeError(name)


def __dir__() -> list[str]:
    return sorted(__all__)

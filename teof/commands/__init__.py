from __future__ import annotations

from importlib import import_module
from typing import Iterable

_COMMAND_MODULES: tuple[str, ...] = (
    "brief",
    "status",
    "tasks",
    "reflections",
    "ttd_trend",
    "scan",
    "frontier",
    "critic",
    "tms",
    "ethics",
)


def register_commands(subparsers: "argparse._SubParsersAction[object]") -> None:  # pragma: no cover - thin orchestrator
    """Attach all supported subcommands to *subparsers*.

    Command modules expose ``register(subparsers)`` so the bootloader only declares
    dispatch order here. Keeping the list centralized makes it obvious which
    commands ship with the repo-local CLI and simplifies future additions.
    """

    import argparse

    for name in _COMMAND_MODULES:
        module = import_module(f".{name}", __name__)
        register = getattr(module, "register", None)
        if register is None:
            raise RuntimeError(f"teof.commands.{name} missing register()")
        register(subparsers)


__all__ = ["register_commands"]
COMMAND_MODULES = _COMMAND_MODULES
__all__.append("COMMAND_MODULES")

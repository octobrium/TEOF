"""Onboarding helpers (packaging + quickstart receipts)."""

from __future__ import annotations

__all__ = [
    "build_main",
    "quickstart_main",
]


def build_main(*args, **kwargs):
    """Lazily dispatch to ``tools.onboarding.build.main``."""

    from . import build

    return build.main(*args, **kwargs)


def quickstart_main(*args, **kwargs):
    """Lazily dispatch to ``tools.onboarding.quickstart.main``."""

    from . import quickstart

    return quickstart.main(*args, **kwargs)

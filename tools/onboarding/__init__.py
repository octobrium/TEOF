"""Onboarding helpers (packaging + quickstart receipts)."""

from __future__ import annotations

from .build import main as build_main
from .quickstart import main as quickstart_main

__all__ = [
    "build_main",
    "quickstart_main",
]

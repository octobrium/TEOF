import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def disable_session_guard(monkeypatch):
    """Disable the session guard in most tests; opt-in per test when needed."""

    monkeypatch.setenv("TEOF_SESSION_GUARD_DISABLED", "1")

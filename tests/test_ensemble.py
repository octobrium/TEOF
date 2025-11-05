from __future__ import annotations

from pathlib import Path

import pytest

from extensions.validator.scorers import ensemble


@pytest.fixture(autouse=True)
def restore_runners() -> None:
    original = dict(ensemble._RUNNERS)
    try:
        yield
    finally:
        ensemble._RUNNERS.clear()
        ensemble._RUNNERS.update(original)


def _dummy_runner(_: str) -> dict[str, float]:
    return {
        "structure": 0.0,
        "alignment": 0.0,
        "verification": 0.0,
        "risk": 0.0,
        "recovery": 0.0,
    }


def test_register_runner_rejects_invalid_tag() -> None:
    with pytest.raises(ValueError, match="uppercase alphanumeric"):
        ensemble.register_runner("invalid tag", _dummy_runner)


def test_register_runner_requires_overwrite_flag() -> None:
    ensemble.register_runner("X", _dummy_runner)
    with pytest.raises(ValueError, match="overwrite=True"):
        ensemble.register_runner("X", _dummy_runner)
    # Overwrite succeeds when flag is provided
    ensemble.register_runner("X", _dummy_runner, overwrite=True)


def test_score_file_unknown_runner(tmp_path: Path) -> None:
    sample = tmp_path / "proposal.txt"
    sample.write_text("observation first", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown runner 'Z'"):
        ensemble.score_file(sample, which=("Z",))

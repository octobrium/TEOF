from pathlib import Path

import pytest

from tools.tests import coverage_guard


def _write_coverage(path: Path, rate: float) -> None:
    path.write_text(
        f'<?xml version="1.0" ?><coverage line-rate="{rate}" branch-rate="0.0"></coverage>',
        encoding="utf-8",
    )


def test_parse_coverage_rate(tmp_path: Path) -> None:
    xml_path = tmp_path / "coverage.xml"
    _write_coverage(xml_path, 0.82)

    rate = coverage_guard.parse_coverage_rate(xml_path)

    assert pytest.approx(rate, rel=1e-9) == 0.82


def test_enforce_threshold_passes(tmp_path: Path) -> None:
    xml_path = tmp_path / "coverage.xml"
    _write_coverage(xml_path, 0.75)

    rc = coverage_guard.main(["--path", str(xml_path), "--threshold", "0.70", "--quiet"])

    assert rc == 0


def test_enforce_threshold_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    xml_path = tmp_path / "coverage.xml"
    _write_coverage(xml_path, 0.60)

    rc = coverage_guard.main(["--path", str(xml_path), "--threshold", "0.70", "--quiet"])

    assert rc == 1
    assert "below threshold" in capsys.readouterr().err


def test_default_threshold_enforced(tmp_path: Path) -> None:
    xml_path = tmp_path / "coverage.xml"
    _write_coverage(xml_path, 0.80)

    rc = coverage_guard.main(["--path", str(xml_path), "--quiet"])

    assert rc == 0


def test_guard_rejects_invalid_threshold(tmp_path: Path) -> None:
    xml_path = tmp_path / "coverage.xml"
    _write_coverage(xml_path, 0.95)

    with pytest.raises(SystemExit):
        coverage_guard.main(["--path", str(xml_path), "--threshold", "1.20"])

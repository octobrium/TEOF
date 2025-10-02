from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import teof.bootloader as bootloader
from teof import status_report


def _setup_repo(root: Path) -> None:
    # pyproject
    pyproject = root / "pyproject.toml"
    pyproject.write_text("""
[project]
name = "teof"
version = "9.9.9"
""".strip()
, encoding="utf-8")
    # capsule
    capsule_dir = root / "capsule"
    capsule_dir.mkdir(parents=True, exist_ok=True)
    (capsule_dir / "v9.9").mkdir(parents=True, exist_ok=True)
    current = capsule_dir / "current"
    if current.exists() or current.is_symlink():
        current.unlink()
    current.symlink_to("v9.9")
    # artifacts
    latest = root / "artifacts" / "ocers_out" / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    (latest / "brief.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
    (latest / "score.txt").write_text("ensemble_count=1\n", encoding="utf-8")
    # quickstart
    quickstart = root / "docs" / "quickstart.md"
    quickstart.parent.mkdir(parents=True, exist_ok=True)
    quickstart.write_text(
        """
# Quickstart

```
python3 -m pip install -e .
teof brief
```
""".strip()
        + "\n",
        encoding="utf-8",
    )
    # pre-commit hook
    hook = root / ".githooks" / "pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(
        "#!/bin/sh\nset -e\nteof status --out docs/STATUS.md --quiet\ngit add docs/STATUS.md\n",
        encoding="utf-8",
    )
    # authenticity dashboard
    auth = root / "_report" / "usage"
    auth.mkdir(parents=True, exist_ok=True)
    (auth / "external-authenticity.md").write_text("# Dashboard\n", encoding="utf-8")


def test_generate_status(tmp_path: Path) -> None:
    _setup_repo(tmp_path)
    report = status_report.generate_status(tmp_path)
    assert "# TEOF Status" in report
    assert "Package: teof 9.9.9" in report
    assert "Artifacts latest" in report
    assert "Authenticity dashboard" in report
    assert "## Autonomy Footprint" in report
    assert "Modules:" in report
    assert "Receipts:" in report
    assert "Recent Footprint Deltas" in report
    assert "[done] OBJ-A4" in report
    assert "[done] OBJ-A5" in report
    assert report.strip().endswith("Python ≥3.9 for local dev.")


def test_cli_writes_file(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path)
    # Ensure CLI looks at tmp_path
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(status_report, "ROOT", tmp_path)
    out_path = tmp_path / "docs" / "STATUS.md"
    result = bootloader.main(["status", "--out", str(out_path), "--quiet"])
    assert result == 0
    assert out_path.exists()
    expected = status_report.generate_status(tmp_path, log=False)
    assert out_path.read_text(encoding="utf-8") == expected

    # Without --quiet, CLI should print to stdout
    buffer = io.StringIO()
    monkeypatch.setattr(sys, 'stdout', buffer)
    bootloader.main(['status'])
    expected_after = status_report.generate_status(tmp_path, log=False)
    assert buffer.getvalue().rstrip('\n') == expected_after.rstrip('\n')

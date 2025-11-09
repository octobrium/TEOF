from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import teof.bootloader as bootloader
import teof.commands as commands_mod
from teof import status_report
from tools.maintenance import capability_inventory
from tools.maintenance import automation_inventory


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
    latest = root / "artifacts" / "systemic_out" / "latest"
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
        "#!/bin/sh\nset -e\nteof status --out docs/status.md --quiet\ngit add docs/status.md\n",
        encoding="utf-8",
    )
    # authenticity dashboard
    auth = root / "_report" / "usage"
    auth.mkdir(parents=True, exist_ok=True)
    (auth / "external-authenticity.md").write_text("# Dashboard\n", encoding="utf-8")


def _install_inventory_stubs(root: Path, monkeypatch) -> None:
    cap_entry = capability_inventory.CommandUsage(
        name="brief",
        module_path=root / "teof" / "commands" / "brief.py",
        tests=[root / "tests" / "test_brief.py"],
        receipt_paths=[],
        last_receipt=None,
    )
    auto_entry = automation_inventory.AutomationEntry(
        module="tools.autonomy.frontier",
        path=root / "tools" / "autonomy" / "frontier.py",
        tests=[root / "tests" / "test_frontier.py"],
        receipts=[],
        last_receipt=None,
    )

    monkeypatch.setattr(
        capability_inventory,
        "generate_inventory",
        lambda stale_days=30.0: [cap_entry],
    )
    monkeypatch.setattr(
        automation_inventory,
        "generate_inventory",
        lambda stale_days=30.0: [auto_entry],
    )


def test_generate_status(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path)
    _install_inventory_stubs(tmp_path, monkeypatch)
    report = status_report.generate_status(tmp_path)
    assert "# TEOF Status" in report
    assert "Package: teof 9.9.9" in report
    assert "Artifacts latest" in report
    assert "Authenticity dashboard" in report
    assert "Exploratory lane" in report
    assert "## Autonomy Footprint" in report
    assert "Modules:" in report
    assert "Receipts:" in report
    assert "Recent Footprint Deltas" in report
    assert "## CLI Capability Health" in report
    assert "Commands:" in report
    assert "## Automation Health" in report
    assert "Modules:" in report
    assert "[done] OBJ-A4" in report
    assert "[done] OBJ-A5" in report
    assert report.strip().endswith("Python ≥3.9 for local dev.")


def test_cli_writes_file(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path)
    _install_inventory_stubs(tmp_path, monkeypatch)
    _restrict_commands(monkeypatch)
    # Ensure CLI looks at tmp_path
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(status_report, "ROOT", tmp_path)
    out_path = tmp_path / "docs" / "status.md"
    result = bootloader.main(["status", "--out", str(out_path), "--quiet"])
    assert result == 0
    assert out_path.exists()
    expected = status_report.generate_status(tmp_path, log=False)
    actual_lines = out_path.read_text(encoding="utf-8").splitlines()
    expected_lines = expected.splitlines()
    assert actual_lines[1:] == expected_lines[1:]

    # Without --quiet, CLI should print to stdout
    buffer = io.StringIO()
    monkeypatch.setattr(sys, 'stdout', buffer)
    bootloader.main(['status'])
    expected_after = status_report.generate_status(tmp_path, log=False)
    printed_lines = buffer.getvalue().rstrip('\n').splitlines()
    expected_lines = expected_after.rstrip('\n').splitlines()
    assert printed_lines[1:] == expected_lines[1:]


def test_status_cli_json_output(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path)
    _install_inventory_stubs(tmp_path, monkeypatch)
    _restrict_commands(monkeypatch)
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(status_report, "ROOT", tmp_path)

    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)
    result = bootloader.main(["status", "--format", "json"])
    assert result == 0
    payload = json.loads(buffer.getvalue())
    assert payload["snapshot"]
    assert "autonomy_footprint" in payload
    assert "cli_capability" in payload
    assert payload["notes"]


def test_status_cli_json_out_file(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path)
    _install_inventory_stubs(tmp_path, monkeypatch)
    _restrict_commands(monkeypatch)
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(status_report, "ROOT", tmp_path)

    out_path = tmp_path / "status.json"
    result = bootloader.main(
        ["status", "--format", "json", "--out", str(out_path), "--quiet"]
    )
    assert result == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert isinstance(payload["autonomy_footprint"]["metrics"]["module_files"], int)
def _restrict_commands(monkeypatch) -> None:
    allowed = ("status",)
    monkeypatch.setattr(commands_mod, "_COMMAND_MODULES", allowed, raising=False)
    monkeypatch.setattr(commands_mod, "COMMAND_MODULES", allowed, raising=False)

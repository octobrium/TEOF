import importlib
import json
from pathlib import Path

import pytest

from teof import _paths


@pytest.fixture(name="restore_repo_root")
def _restore_repo_root():
    original = _paths.repo_root()
    yield original
    _paths.set_repo_root(original)
    importlib.reload(importlib.import_module("tools.memory.reflection_audit"))


def _bootstrap_repo(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    (tmp_path / "README.md").write_text("", encoding="utf-8")
    (tmp_path / "teof").mkdir()
    (tmp_path / "memory" / "reflections").mkdir(parents=True)
    (tmp_path / "_report" / "analysis").mkdir(parents=True)


def _write_reflection(root: Path, name: str, payload: dict) -> None:
    path = root / "memory" / "reflections" / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_reflection_audit_detects_missing_metadata(tmp_path: Path, restore_repo_root: Path) -> None:
    _bootstrap_repo(tmp_path)
    _paths.set_repo_root(tmp_path)

    _write_reflection(
        tmp_path,
        "reflection-complete.json",
        {
            "captured_at": "2025-11-09T10:00:00Z",
            "title": "Complete reflection",
            "plan_suggestion": "plan-1",
            "tags": ["foo", "bar"],
        },
    )
    _write_reflection(
        tmp_path,
        "reflection-missing-plan.json",
        {
            "captured_at": "2025-11-09T11:00:00Z",
            "title": "Missing plan",
            "plan_suggestion": "",
            "tags": ["tag"],
        },
    )
    _write_reflection(
        tmp_path,
        "reflection-missing-tags.json",
        {
            "captured_at": "2025-11-09T12:00:00Z",
            "title": "Missing tags",
            "plan_suggestion": "plan-2",
            "tags": [],
        },
    )

    module = importlib.reload(importlib.import_module("tools.memory.reflection_audit"))
    summary, out_path = module.run_audit(out=tmp_path / "out.json")

    assert out_path.exists()
    assert summary["total"] == 3
    assert summary["missing_plan_suggestion"]["count"] == 1
    assert summary["missing_tags"]["count"] == 1
    missing_paths = {entry["path"] for entry in summary["missing_plan_suggestion"]["entries"]}
    assert "memory/reflections/reflection-missing-plan.json" in missing_paths
    missing_tag_paths = {entry["path"] for entry in summary["missing_tags"]["entries"]}
    assert "memory/reflections/reflection-missing-tags.json" in missing_tag_paths

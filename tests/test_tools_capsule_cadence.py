import json
import os
import re
from importlib import reload
from pathlib import Path

import pytest

from tools.capsule import cadence


ISO_COMPACT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _setup_repo(root: Path) -> None:
    (root / "capsule" / "v1.7").mkdir(parents=True, exist_ok=True)
    (root / "capsule" / "v1.7" / "hashes.json").write_text("{}", encoding="utf-8")
    (root / "capsule" / "README.md").write_text("capsule", encoding="utf-8")
    (root / "governance").mkdir(parents=True, exist_ok=True)
    (root / "governance" / "anchors.json").write_text("[]", encoding="utf-8")
    (root / "_report" / "consensus").mkdir(parents=True, exist_ok=True)
    (root / "_report" / "consensus" / "summary-latest.json").write_text("{}", encoding="utf-8")
    current = root / "capsule" / "current"
    target = Path("v1.7")
    if current.exists() or current.is_symlink():
        current.unlink()
    os.symlink(target, current)


def test_summary_cli_writes_default_paths(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    _setup_repo(repo_root)

    monkeypatch.setattr(cadence, "ROOT", repo_root)
    reload(cadence)
    monkeypatch.setattr(cadence, "ROOT", repo_root)

    rc = cadence.main(["summary"])
    assert rc == 0

    out_path = repo_root / "_report" / "capsule" / "summary-latest.json"
    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))

    assert data["capsule_version"] == "v1.7"
    assert data["required_receipts"] == [
        "capsule/README.md",
        "capsule/current/hashes.json",
        "governance/anchors.json",
    ]
    assert data["consensus_summary"] == "_report/consensus/summary-latest.json"
    assert ISO_COMPACT.match(data["generated_at"])


def test_detect_capsule_version_falls_back(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    capsule_dir = repo_root / "capsule"
    capsule_dir.mkdir(parents=True, exist_ok=True)
    (capsule_dir / "v1.6").mkdir()

    monkeypatch.setattr(cadence, "ROOT", repo_root)
    reload(cadence)
    monkeypatch.setattr(cadence, "ROOT", repo_root)

    version = cadence._detect_capsule_version(capsule_dir)
    assert version == "v1.6"

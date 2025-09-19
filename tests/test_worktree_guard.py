import os
import subprocess
from pathlib import Path

import pytest

from tools.maintenance import worktree_guard


def init_repo(tmp_path: Path) -> Path:
    """Initialise a minimal git repo with one commit."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True)
    return tmp_path


def test_guard_allows_small_change(tmp_path):
    repo = init_repo(tmp_path)
    (repo / "README.md").write_text("hello world\n", encoding="utf-8")
    rc = worktree_guard.check_worktree(root=repo, max_changes=5)
    assert rc == 0


def test_guard_blocks_large_change(tmp_path):
    repo = init_repo(tmp_path)
    for idx in range(6):
        (repo / f"file{idx}.txt").write_text("x\n", encoding="utf-8")
    rc = worktree_guard.check_worktree(root=repo, max_changes=5)
    assert rc == 1


def test_guard_cli(tmp_path, monkeypatch):
    repo = init_repo(tmp_path)
    (repo / "new.txt").write_text("content\n", encoding="utf-8")
    monkeypatch.chdir(repo)
    rc = worktree_guard.main(["--max-changes", "0"])
    assert rc == 1

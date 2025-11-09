from __future__ import annotations

import io
import json
import sys
from pathlib import Path

from tools.autonomy import build_guard


def test_detect_tracked_artifacts_returns_matches(monkeypatch, tmp_path: Path) -> None:
    def fake_ls_files(root: Path, pattern: str) -> list[str]:
        if pattern == "dist/**":
            return ["dist/demo.whl"]
        return []

    monkeypatch.setattr(build_guard, "_git_ls_files", fake_ls_files)

    matches = build_guard.detect_tracked_artifacts(tmp_path)
    assert len(matches) == 1
    match = matches[0]
    assert match.pattern == "dist/**"
    assert "dist/demo.whl" in match.paths


def test_detect_tracked_artifacts_honours_allow(monkeypatch, tmp_path: Path) -> None:
    def fake_ls_files(root: Path, pattern: str) -> list[str]:
        if pattern == "dist/**":
            return ["dist/demo.whl"]
        return []

    monkeypatch.setattr(build_guard, "_git_ls_files", fake_ls_files)

    matches = build_guard.detect_tracked_artifacts(tmp_path, allow=["dist/**"])
    assert matches == []


def test_main_text_success(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(build_guard, "detect_tracked_artifacts", lambda root, allow=None: [])
    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)

    rc = build_guard.main(["--root", str(tmp_path)])
    assert rc == 0
    assert "no tracked build artifacts" in buffer.getvalue()


def test_main_json_failure(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        build_guard,
        "detect_tracked_artifacts",
        lambda root, allow=None: [
            build_guard.Match(pattern="dist/**", reason="dist artifacts", paths=("dist/demo.whl",))
        ],
    )
    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)

    rc = build_guard.main(["--root", str(tmp_path), "--format", "json"])
    assert rc == 1
    payload = json.loads(buffer.getvalue())
    assert payload["status"] == "fail"
    assert payload["matches"][0]["pattern"] == "dist/**"

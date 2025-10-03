from __future__ import annotations

from pathlib import Path

import tools.maintenance.repo_anatomy as repo_anatomy


def test_collect_stats_includes_requested_paths():
    stats = repo_anatomy.collect_stats(["docs"])
    assert stats, "expected at least one stats entry"
    entry = stats[0]
    assert entry["path"] == "docs"
    assert isinstance(entry["files"], int)
    assert isinstance(entry["commits"], int)


def test_main_json_output(tmp_path: Path):
    out = tmp_path / "anatomy.json"
    rc = repo_anatomy.main([
        "--paths",
        "docs",
        "--format",
        "json",
        "--out",
        str(out),
    ])
    assert rc == 0
    assert out.exists(), "expected output file to be written"

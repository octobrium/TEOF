import json
from importlib import reload
from pathlib import Path

import pytest

import scripts.ci.check_readability as check_readability


@pytest.fixture
def tmp_repo(tmp_path, monkeypatch):
    root = tmp_path
    report_dir = root / "_report" / "readability"
    report_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(check_readability, "ROOT", root)
    reload(check_readability)
    monkeypatch.setattr(check_readability, "ROOT", root)
    check_readability.SUMMARY_PATH = report_dir / "summary-latest.json"
    return report_dir


def test_missing_summary(tmp_repo):
    rc = check_readability.main()
    assert rc == 1


def test_failure(tmp_repo):
    data = {"results": [{"path": "docs/bad.md", "pass": False, "avg_sentence_words": 50, "avg_word_length": 7}]}
    (tmp_repo / "summary-latest.json").write_text(json.dumps(data), encoding="utf-8")

    rc = check_readability.main()
    assert rc == 1


def test_success(tmp_repo):
    data = {"results": [{"path": "docs/good.md", "pass": True}]}
    (tmp_repo / "summary-latest.json").write_text(json.dumps(data), encoding="utf-8")

    rc = check_readability.main()
    assert rc == 0

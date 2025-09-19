from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.receipts import utils


def _write_plan(tmp_path: Path, name: str, receipts: list[str], step_receipts: list[str]) -> Path:
    plan = tmp_path / f"{name}.plan.json"
    data = {
        "receipts": receipts,
        "steps": [
            {
                "id": "S1",
                "receipts": step_receipts,
            }
        ],
    }
    plan.write_text(json.dumps(data), encoding="utf-8")
    return plan


def test_iter_plan_receipts_yields_all(tmp_path, monkeypatch):
    plan = _write_plan(tmp_path, "example", ["a.txt"], ["b.txt"])
    monkeypatch.setattr(utils, "ROOT", tmp_path)

    receipts = list(utils.iter_plan_receipts(plan))
    assert receipts == [(plan, "a.txt"), (plan, "b.txt")]


def test_find_missing_receipts_detects_missing(tmp_path, monkeypatch):
    plan = _write_plan(tmp_path, "missing", ["exists.txt"], ["missing.txt"])
    (tmp_path / "exists.txt").write_text("ok", encoding="utf-8")
    monkeypatch.setattr(utils, "ROOT", tmp_path)

    missing = utils.find_missing_receipts([plan])
    assert missing == [(plan, "missing.txt")]


def test_resolve_plan_paths_raises_for_unknown(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "ROOT", tmp_path)
    monkeypatch.setattr(utils, "PLANS_DIR", tmp_path / "_plans")

    with pytest.raises(FileNotFoundError):
        utils.resolve_plan_paths(["does-not-exist.plan.json"])


def test_resolve_plan_paths_default(tmp_path, monkeypatch):
    plans_dir = tmp_path / "_plans"
    plans_dir.mkdir()
    plan = _write_plan(plans_dir, "auto", [], [])
    monkeypatch.setattr(utils, "ROOT", tmp_path)
    monkeypatch.setattr(utils, "PLANS_DIR", plans_dir)

    paths = utils.resolve_plan_paths(None)
    assert paths == [plan]

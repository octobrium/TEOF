import importlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from teof import _paths


@pytest.fixture(name="repo_root")
def _repo_root(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    (tmp_path / "README.md").write_text("", encoding="utf-8")
    (tmp_path / "teof").mkdir()
    (tmp_path / "_bus" / "claims").mkdir(parents=True)
    (tmp_path / "_bus" / "events").mkdir(parents=True)
    return tmp_path


@pytest.fixture(autouse=True)
def _override_root(repo_root: Path):
    original = _paths.repo_root()
    _paths.set_repo_root(repo_root)
    module = importlib.import_module("tools.agent.stale_claims")
    importlib.reload(module)
    yield
    _paths.set_repo_root(original)
    importlib.reload(module)


def _write_claim(path: Path, name: str, payload: dict) -> None:
    target = path / "_bus" / "claims" / name
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_events(path: Path, entries: list[dict]) -> None:
    text = "\n".join(json.dumps(entry, ensure_ascii=False) for entry in entries)
    (path / "_bus" / "events" / "events.jsonl").write_text(text + "\n", encoding="utf-8")


def test_find_stale_claims_detects_idle_tasks(repo_root: Path):
    base_ts = "2025-11-09T00:00:00Z"
    _write_claim(
        repo_root,
        "TASK-1.json",
        {
            "agent_id": "codex-tier2",
            "plan_id": "demo-plan",
            "task_id": "TASK-1",
            "claimed_at": base_ts,
            "status": "active",
        },
    )
    _write_claim(
        repo_root,
        "TASK-2.json",
        {
            "agent_id": "codex-tier3",
            "plan_id": "demo-plan",
            "task_id": "TASK-2",
            "claimed_at": "2025-11-09T05:00:00Z",
            "status": "active",
        },
    )
    _write_events(
        repo_root,
        [
            {
                "task_id": "TASK-2",
                "ts": "2025-11-09T07:00:00Z",
            }
        ],
    )

    module = importlib.import_module("tools.agent.stale_claims")
    stale = module.find_stale_claims(
        agent=None,
        threshold_hours=6,
        now=datetime(2025, 11, 9, 12, 0, 0, tzinfo=timezone.utc),
    )

    assert len(stale) == 1
    assert stale[0].claim.task_id == "TASK-1"
    assert stale[0].age_hours == 12.0


def test_find_stale_claims_respects_agent_filter(repo_root: Path):
    _write_claim(
        repo_root,
        "TASK-3.json",
        {
            "agent_id": "codex-tier2",
            "plan_id": "demo-plan",
            "task_id": "TASK-3",
            "claimed_at": "2025-11-09T00:00:00Z",
            "status": "active",
        },
    )
    module = importlib.import_module("tools.agent.stale_claims")
    stale = module.find_stale_claims(
        agent="codex-tier3",
        threshold_hours=1,
        now=datetime(2025, 11, 9, 1, 0, 0, tzinfo=timezone.utc),
    )
    assert not stale


def test_cli_json_output(repo_root: Path, capsys):
    _write_claim(
        repo_root,
        "TASK-4.json",
        {
            "agent_id": "codex-tier2",
            "plan_id": "demo-plan",
            "task_id": "TASK-4",
            "claimed_at": "2025-11-09T00:00:00Z",
            "status": "active",
        },
    )
    module = importlib.import_module("tools.agent.stale_claims")

    def fake_now():
        return datetime(2025, 11, 9, 10, 0, 0, tzinfo=timezone.utc)

    module._utc_now = fake_now  # type: ignore[attr-defined]
    rc = module.main(["--json", "--threshold-hours", "6", "--fail-on-stale"])
    assert rc == 1
    output = capsys.readouterr().out
    json_text = output.split("::error", 1)[0].strip()
    data = json.loads(json_text)
    assert data[0]["task_id"] == "TASK-4"

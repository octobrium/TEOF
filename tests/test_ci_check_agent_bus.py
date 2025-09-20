import json
from importlib import reload
from pathlib import Path

import pytest

import scripts.ci.check_agent_bus as check_agent_bus


@pytest.fixture
def tmp_repo(tmp_path, monkeypatch):
    root = tmp_path
    messages_dir = root / "_bus" / "messages"
    messages_dir.mkdir(parents=True, exist_ok=True)
    claims_dir = root / "_bus" / "claims"
    claims_dir.mkdir(parents=True, exist_ok=True)
    assignments_dir = root / "_bus" / "assignments"
    assignments_dir.mkdir(parents=True, exist_ok=True)
    events_dir = root / "_bus" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(check_agent_bus, "ROOT", root)
    reload(check_agent_bus)
    monkeypatch.setattr(check_agent_bus, "ROOT", root)
    check_agent_bus.CLAIMS_DIR = claims_dir
    check_agent_bus.MESSAGES_DIR = messages_dir
    check_agent_bus.ASSIGNMENTS_DIR = assignments_dir
    check_agent_bus.EVENTS_LOG = events_dir / "events.jsonl"

    return root


def _write_jsonl(path: Path, entries: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(entry) for entry in entries) + "\n", encoding="utf-8")


def test_directive_requires_manager_pointer(tmp_repo):
    messages_dir = tmp_repo / "_bus" / "messages"
    directive_path = messages_dir / "BUS-COORD-0005.jsonl"
    _write_jsonl(
        directive_path,
        [
            {
                "ts": "2025-09-21T00:00:00Z",
                "from": "codex-1",
                "type": "directive",
                "task_id": "BUS-COORD-0005",
                "summary": "Directive without pointer",
            }
        ],
    )

    rc = check_agent_bus.main()
    assert rc == 1


def test_directive_pointer_present(tmp_repo):
    messages_dir = tmp_repo / "_bus" / "messages"
    directive_id = "BUS-COORD-0006"
    _write_jsonl(
        messages_dir / f"{directive_id}.jsonl",
        [
            {
                "ts": "2025-09-21T01:00:00Z",
                "from": "codex-1",
                "type": "directive",
                "task_id": directive_id,
                "summary": "Directive with pointer",
            }
        ],
    )
    _write_jsonl(
        messages_dir / "manager-report.jsonl",
        [
            {
                "ts": "2025-09-21T01:05:00Z",
                "from": "codex-1",
                "type": "status",
                "task_id": "manager-report",
                "summary": "Directive BUS-COORD-0006 posted",
                "meta": {"directive": directive_id},
            }
        ],
    )

    rc = check_agent_bus.main()
    assert rc == 0

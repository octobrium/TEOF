from __future__ import annotations

from teof import bootloader
from teof.commands import tasks as tasks_cmd


def test_bootloader_dispatches_tasks(monkeypatch) -> None:
    called = {}

    def fake_run(args):
        called["args"] = args
        return 0

    monkeypatch.setattr(tasks_cmd, "run", fake_run)
    result = bootloader.main(["tasks", "--summary"])
    assert result == 0
    assert called["args"].summary is True

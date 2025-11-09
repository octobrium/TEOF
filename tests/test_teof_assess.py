from __future__ import annotations

import json

import teof.bootloader as bootloader


def test_assess_json_output(capsys) -> None:
    exit_code = bootloader.main(
        ["assess", "--format", "json", "--frontier-limit", "1", "--task-limit", "1"]
    )
    assert exit_code == 0

    output = capsys.readouterr().out
    payload = json.loads(output)

    assert "status" in payload
    assert "scan" in payload
    assert "tasks" in payload
    assert payload["scan"]["counts"]["frontier"] >= 0
    assert payload["tasks"]["summary"]["total"] >= 0


def test_assess_text_output(capsys) -> None:
    exit_code = bootloader.main(["assess", "--frontier-limit", "1", "--task-limit", "1"])
    assert exit_code == 0

    output = capsys.readouterr().out
    assert "# TEOF Assess" in output
    assert "## Frontier / Guards" in output
    assert "## Task Warnings" in output

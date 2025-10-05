from __future__ import annotations

from pathlib import Path

import json

from tools.autonomy import commitment_guard


def test_commitment_guard_detects_phrase(tmp_path: Path) -> None:
    target = tmp_path / "message.jsonl"
    target.write_text('{"ts": "now", "msg": "Next time I will remember."}\n', encoding="utf-8")

    matches = commitment_guard.scan([target], ["next time"])
    assert matches
    assert matches[0]["path"].endswith("message.jsonl")


def test_commitment_guard_cli_json(tmp_path: Path, capsys) -> None:
    note = tmp_path / "note.md"
    note.write_text("This is a mental note to follow up.\n", encoding="utf-8")

    exit_code = commitment_guard.main(["--json", str(note)])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["path"].endswith("note.md")

import json
from pathlib import Path

import pytest

import teof.bootloader as bootloader
from tools.autonomy import macro_hygiene


def _setup_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path
    docs_dir = root / "docs" / "maintenance"
    docs_dir.mkdir(parents=True, exist_ok=True)
    config_path = docs_dir / "macro-hygiene.objectives.json"
    plan_path = root / "_plans" / "demo.plan.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps({"status": "done"}), encoding="utf-8")
    config_path.write_text(
        json.dumps(
            {
                "version": 1,
                "objectives": [
                    {
                        "id": "MH-DEMO",
                        "title": "Demo objective",
                        "checks": [
                            {"kind": "plan_done", "path": "_plans/demo.plan.json"},
                            {"kind": "path_exists", "path": "_plans/demo.plan.json"},
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    receipt = root / "_report" / "usage" / "macro-hygiene-status.json"
    monkeypatch.setattr(macro_hygiene, "ROOT", root)
    monkeypatch.setattr(macro_hygiene, "CONFIG_PATH", config_path)
    monkeypatch.setattr(macro_hygiene, "DEFAULT_RECEIPT", receipt)


def test_teof_macro_hygiene_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup_config(tmp_path, monkeypatch)

    exit_code = bootloader.main(["macro_hygiene", "--no-write"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ready"
    assert payload["summary"]["total"] == 1


def test_teof_macro_hygiene_human(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup_config(tmp_path, monkeypatch)

    exit_code = bootloader.main(["macro_hygiene", "--human", "--no-write"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Macro hygiene objectives" in out

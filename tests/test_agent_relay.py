from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.autonomy import agent_relay


def test_build_response_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    conductor_payload = {
        "generated_at": "2025-09-23T20:00:00Z",
        "task": {"id": "ND-999"},
        "guardrails": {"diff_limit": 123},
        "prompt": "demo",
    }
    conductor_path = tmp_path / "conductor-20250923T200000Z.json"
    conductor_path.write_text(json.dumps(conductor_payload), encoding="utf-8")

    record = agent_relay.build_response_record(
        conductor_path=conductor_path, prompt="demo", raw_response="result", dry_run=False
    )
    assert record["conducted_at"] == "2025-09-23T20:00:00Z"
    assert record["task"]["id"] == "ND-999"
    assert record["api_response"] == "result"
    assert record["dry_run"] is False


def test_make_response_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path
    conductor_dir = root / "_report" / "usage" / "autonomy-conductor"
    relay_dir = conductor_dir / "api-relay"
    consent_path = root / "docs" / "automation" / "autonomy-consent.json"
    auth_path = root / "_report" / "usage" / "external-authenticity.json"
    conductor_dir.mkdir(parents=True)
    payload = {
        "generated_at": "2025-09-23T20:00:00Z",
        "task": {"id": "ND-888"},
        "guardrails": {},
        "prompt": "demo",
    }
    receipt = conductor_dir / "conductor-20250923T200000Z.json"
    receipt.write_text(json.dumps(payload), encoding="utf-8")

    consent_path.parent.mkdir(parents=True, exist_ok=True)
    consent_path.write_text(json.dumps({"auto_enabled": True, "halt_on_attention_feeds": True}), encoding="utf-8")
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    auth_path.write_text(json.dumps({"overall_avg_trust": 0.8, "attention_feeds": []}), encoding="utf-8")

    def fake_call(prompt: str, *, api_key: str, model: str) -> str:
        assert prompt == "demo"
        assert api_key == "key"
        assert model == "model"
        return "completed"

    monkeypatch.setattr(agent_relay, "call_openai_api", fake_call)
    monkeypatch.setattr(agent_relay, "ROOT", root)
    monkeypatch.setattr(agent_relay, "CONDUCTOR_DIR", conductor_dir)
    monkeypatch.setattr(agent_relay, "RELAY_DIR", relay_dir)
    monkeypatch.setattr(agent_relay, "METABOLITE_DIR", relay_dir / "metabolites")
    monkeypatch.setattr(agent_relay, "CONSENT_PATH", consent_path)
    monkeypatch.setattr(agent_relay, "AUTH_PATH", auth_path)

    agent_relay.relay(
        api_key="key",
        model="model",
        watch=False,
        sleep_seconds=0.1,
        paths=None,
        dry_run=False,
    )

    outputs = list(relay_dir.glob("relay-*.json"))
    assert outputs
    data = json.loads(outputs[0].read_text(encoding="utf-8"))
    assert data["api_response"] == "completed"
    assert data["task"]["id"] == "ND-888"
    metabolite = list((relay_dir / "metabolites").glob("metabolite-*.json"))
    assert metabolite
    meta = json.loads(metabolite[0].read_text(encoding="utf-8"))
    assert meta["task_id"] == "ND-888"


def test_relay_dry_run_skips_api(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path
    conductor_dir = root / "_report" / "usage" / "autonomy-conductor"
    relay_dir = conductor_dir / "api-relay"
    consent_path = root / "docs" / "automation" / "autonomy-consent.json"
    auth_path = root / "_report" / "usage" / "external-authenticity.json"
    conductor_dir.mkdir(parents=True)
    receipt = conductor_dir / "conductor-20250101T000000Z.json"
    receipt.write_text(json.dumps({"generated_at": "2025-01-01T00:00:00Z", "task": {"id": "ND-123"}, "prompt": "demo"}), encoding="utf-8")
    consent_path.parent.mkdir(parents=True, exist_ok=True)
    consent_path.write_text(json.dumps({"auto_enabled": True}), encoding="utf-8")
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    auth_path.write_text(json.dumps({"overall_avg_trust": 0.9, "attention_feeds": []}), encoding="utf-8")

    monkeypatch.setattr(agent_relay, "ROOT", root)
    monkeypatch.setattr(agent_relay, "CONDUCTOR_DIR", conductor_dir)
    monkeypatch.setattr(agent_relay, "RELAY_DIR", relay_dir)
    monkeypatch.setattr(agent_relay, "METABOLITE_DIR", relay_dir / "metabolites")
    monkeypatch.setattr(agent_relay, "CONSENT_PATH", consent_path)
    monkeypatch.setattr(agent_relay, "AUTH_PATH", auth_path)

    called = False

    def fake_call(*args: object, **kwargs: object) -> str:  # pragma: no cover
        nonlocal called
        called = True
        return "unexpected"

    monkeypatch.setattr(agent_relay, "call_openai_api", fake_call)

    agent_relay.relay(
        api_key="key",
        model="model",
        watch=False,
        sleep_seconds=0.1,
        paths=None,
        dry_run=True,
    )

    outputs = list(relay_dir.glob("relay-*.json"))
    assert outputs
    data = json.loads(outputs[0].read_text(encoding="utf-8"))
    assert data["dry_run"] is True
    assert data["api_response"].startswith("[dry-run")
    assert called is False

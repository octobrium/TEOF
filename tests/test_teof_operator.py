from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta
import io
from pathlib import Path

import teof.bootloader as bootloader
import teof._paths as teof_paths
from teof.commands import operator as operator_cmd
from tools.agent import session_guard
from tools.planner import evidence_scope as planner_evidence
from tools.planner import validate as planner_validate


def _setup_agent(root: Path, agent_id: str = "codex-verify") -> None:
    manifest = root / "AGENT_MANIFEST.json"
    manifest.write_text(json.dumps({"agent_id": agent_id}), encoding="utf-8")
    session_dir = root / "_report" / "session" / agent_id
    session_dir.mkdir(parents=True, exist_ok=True)
    freshness = (datetime.utcnow() - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    (session_dir / "manager-report-tail.txt").write_text(
        f"# captured_at={freshness}\n# source=tests\n",
        encoding="utf-8",
    )


def _patch_session_guard(monkeypatch, root: Path) -> None:
    monkeypatch.setattr(session_guard, "ROOT", root)
    monkeypatch.setattr(session_guard, "SESSION_DIR", root / "_report" / "session")
    monkeypatch.setattr(session_guard, "AGENT_REPORT_DIR", root / "_report" / "agent")
    monkeypatch.setattr(session_guard, "MANIFEST_PATH", root / "AGENT_MANIFEST.json")


def _patch_repo_root(monkeypatch, root: Path):
    monkeypatch.setattr(teof_paths, "_ROOT_CACHE", root.resolve())


def _fake_plan_summary(path: Path) -> None:
    payload = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "strict": True,
        "exit_code": 0,
        "plans": [],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_plan_with_evidence(root: Path, plan_id: str, *, include_receipt: bool) -> None:
    plan_dir = root / "_plans"
    plan_dir.mkdir(parents=True, exist_ok=True)
    scope = {
        "internal": [{"ref": "docs/architecture.md", "summary": "Repo map"}],
        "external": [{"ref": "https://example.org/field", "summary": "Field study"}],
        "comparative": [{"ref": "https://example.org/trend", "summary": "Comparative trend"}],
    }
    if include_receipt:
        receipt_rel = f"_report/evidence/{plan_id}/survey.json"
        receipt_path = root / receipt_rel
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text("{}", encoding="utf-8")
        scope["receipts"] = [receipt_rel]
    payload = {
        "version": 1,
        "plan_id": plan_id,
        "created": "2025-11-09T00:00:00Z",
        "actor": "tester",
        "summary": "Evidence plan",
        "status": "in_progress" if include_receipt else "queued",
        "impact_ref": plan_id,
        "layer": "L4",
        "systemic_scale": 5,
        "systemic_targets": ["S4", "S5"],
        "layer_targets": ["L4"],
        "steps": [
            {
                "id": "S1",
                "title": "Observe",
                "status": "in_progress" if include_receipt else "queued",
                "notes": "",
                "receipts": [],
            }
        ],
        "checkpoint": {
            "description": "Evidence receipt guard",
            "owner": "tester",
            "status": "pending",
        },
        "receipts": [],
        "links": [],
        "evidence_scope": scope,
    }
    plan_path = plan_dir / f"{plan_id}.plan.json"
    plan_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_operator_verify_generates_receipt(tmp_path: Path, monkeypatch) -> None:
    for slug in operator_cmd.REQUIRED_PATHS:
        (tmp_path / slug).mkdir(parents=True, exist_ok=True)
    (tmp_path / "_report").mkdir(exist_ok=True)
    _setup_agent(tmp_path)
    _patch_session_guard(monkeypatch, tmp_path)
    _patch_repo_root(monkeypatch, tmp_path)

    monkeypatch.setattr(
        operator_cmd.repo_anatomy,
        "collect_stats",
        lambda paths: [{"path": path, "files": 0, "commits": 0, "last_touch": None} for path in paths],
    )

    called = {"plan": False}

    def fake_runner(root: Path, summary_path: Path) -> subprocess.CompletedProcess[str]:
        called["plan"] = True
        _fake_plan_summary(summary_path)
        return subprocess.CompletedProcess(args=["validate"], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(operator_cmd, "_run_planner_validate", fake_runner)

    result = bootloader.main(["operator", "verify"])
    assert result == 0
    assert called["plan"] is False

    receipts = sorted((tmp_path / "_report" / "operator" / "verify").glob("operator-verify-*.json"))
    assert receipts, "expected operator verify summary"
    summary = json.loads(receipts[-1].read_text(encoding="utf-8"))
    assert summary["status"] == "ok"
    check_names = {entry["name"] for entry in summary["checks"]}
    assert {"session_receipt", "structure"} <= check_names


def test_operator_verify_fails_when_structure_missing(tmp_path: Path, monkeypatch) -> None:
    # Deliberately omit _bus to trigger failure.
    for slug in operator_cmd.REQUIRED_PATHS:
        if slug == "_bus":
            continue
        (tmp_path / slug).mkdir(parents=True, exist_ok=True)
    (tmp_path / "_report").mkdir(parents=True, exist_ok=True)
    _setup_agent(tmp_path)
    _patch_session_guard(monkeypatch, tmp_path)
    _patch_repo_root(monkeypatch, tmp_path)

    monkeypatch.setattr(
        operator_cmd.repo_anatomy,
        "collect_stats",
        lambda paths: [{"path": path, "files": 0, "commits": 0, "last_touch": None} for path in paths],
    )

    def fake_runner(root: Path, summary_path: Path) -> subprocess.CompletedProcess[str]:
        _fake_plan_summary(summary_path)
        return subprocess.CompletedProcess(args=["validate"], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(operator_cmd, "_run_planner_validate", fake_runner)

    rc = bootloader.main(["operator", "verify"])
    assert rc == 2

    receipt = sorted((tmp_path / "_report" / "operator" / "verify").glob("operator-verify-*.json"))[-1]
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert payload["status"] == "fail"
    structure = next(entry for entry in payload["checks"] if entry["name"] == "structure")
    assert "_bus" in structure["details"]["missing_paths"]


def test_operator_verify_strict_plan_runs_validation(tmp_path: Path, monkeypatch) -> None:
    for slug in operator_cmd.REQUIRED_PATHS:
        (tmp_path / slug).mkdir(parents=True, exist_ok=True)
    (tmp_path / "_report").mkdir(exist_ok=True)
    _setup_agent(tmp_path)
    _patch_session_guard(monkeypatch, tmp_path)
    _patch_repo_root(monkeypatch, tmp_path)

    monkeypatch.setattr(
        operator_cmd.repo_anatomy,
        "collect_stats",
        lambda paths: [{"path": path, "files": 0, "commits": 0, "last_touch": None} for path in paths],
    )

    called = {"plan": False}

    def fake_runner(root: Path, summary_path: Path) -> subprocess.CompletedProcess[str]:
        called["plan"] = True
        _fake_plan_summary(summary_path)
        return subprocess.CompletedProcess(args=["validate"], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(operator_cmd, "_run_planner_validate", fake_runner)

    rc = bootloader.main(["operator", "verify", "--strict-plan"])
    assert rc == 0
    assert called["plan"] is True

    receipt = sorted((tmp_path / "_report" / "operator" / "verify").glob("operator-verify-*.json"))[-1]
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    plan_entries = [entry for entry in payload["checks"] if entry["name"] == "plan_validation"]
    assert plan_entries, "strict plan flag must capture plan validation receipt"


def test_operator_verify_json_output(tmp_path: Path, monkeypatch) -> None:
    for slug in operator_cmd.REQUIRED_PATHS:
        (tmp_path / slug).mkdir(parents=True, exist_ok=True)
    (tmp_path / "_report").mkdir(exist_ok=True)
    _setup_agent(tmp_path)
    _patch_session_guard(monkeypatch, tmp_path)
    _patch_repo_root(monkeypatch, tmp_path)

    monkeypatch.setattr(
        operator_cmd.repo_anatomy,
        "collect_stats",
        lambda paths: [{"path": path, "files": 0, "commits": 0, "last_touch": None} for path in paths],
    )

    def fake_runner(root: Path, summary_path: Path) -> subprocess.CompletedProcess[str]:
        _fake_plan_summary(summary_path)
        return subprocess.CompletedProcess(args=["validate"], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(operator_cmd, "_run_planner_validate", fake_runner)

    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)

    rc = bootloader.main(["operator", "verify", "--format", "json"])
    assert rc == 0
    payload = json.loads(buffer.getvalue())
    assert payload["status"] == "ok"
    assert payload["checks"], "json output should include check details"


def test_operator_verify_evidence_guard(tmp_path: Path, monkeypatch) -> None:
    for slug in operator_cmd.REQUIRED_PATHS:
        (tmp_path / slug).mkdir(parents=True, exist_ok=True)
    (tmp_path / "_report").mkdir(exist_ok=True)
    _setup_agent(tmp_path)
    _patch_session_guard(monkeypatch, tmp_path)
    _patch_repo_root(monkeypatch, tmp_path)

    monkeypatch.setattr(
        operator_cmd.repo_anatomy,
        "collect_stats",
        lambda paths: [{"path": path, "files": 0, "commits": 0, "last_touch": None} for path in paths],
    )

    plan_id = "2025-11-10-evidence-guard"
    _seed_plan_with_evidence(tmp_path, plan_id, include_receipt=False)
    monkeypatch.setattr(planner_evidence, "ROOT", tmp_path)
    monkeypatch.setattr(planner_evidence, "PLANS_DIR", tmp_path / "_plans")
    monkeypatch.setattr(planner_validate, "ROOT", tmp_path)
    monkeypatch.setattr(planner_validate, "PLANS_DIR", tmp_path / "_plans")
    planner_validate._git_tracked_paths.cache_clear()
    planner_validate._QUEUE_INDEX = None

    rc_fail = bootloader.main(["operator", "verify", "--require-evidence-plan", plan_id])
    assert rc_fail == 2

    _seed_plan_with_evidence(tmp_path, plan_id, include_receipt=True)
    planner_validate._git_tracked_paths.cache_clear()
    rc_pass = bootloader.main(["operator", "verify", "--require-evidence-plan", plan_id])
    assert rc_pass == 0

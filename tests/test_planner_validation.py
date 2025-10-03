import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.fractal import conformance as fractal_conformance
from tools.planner import validate as planner_validate
from tools.planner.validate import validate_plan

REPO_ROOT = Path(__file__).resolve().parents[1]


def base_payload(plan_id: str = "2025-09-17-sample") -> dict:
    return {
        "version": 0,
        "plan_id": plan_id,
        "created": "2025-09-17T00:00:00Z",
        "actor": "tester",
        "summary": "Sample plan",
        "status": "queued",
        "layer": "L5",
        "systemic_scale": 5,
        "ocers_target": "Observation↑ Evidence↑",
        "steps": [
            {
                "id": "S1",
                "title": "Do thing",
                "status": "queued",
                "notes": "",
                "receipts": [],
            }
        ],
        "checkpoint": {
            "description": "Ensure validator passes",
            "owner": "tester",
            "status": "pending",
        },
        "receipts": [],
        "links": [],
    }


def write_plan(tmp_dir: Path, payload: dict) -> Path:
    path = tmp_dir / f"{payload['plan_id']}.plan.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_validate_plan_happy_path(tmp_path: Path) -> None:
    payload = base_payload()
    path = write_plan(tmp_path, payload)
    result = validate_plan(path)
    assert result.ok, result.errors
    assert result.plan is not None
    assert result.plan["plan_id"] == payload["plan_id"]


def test_validate_plan_requires_checkpoint_description(tmp_path: Path) -> None:
    payload = base_payload()
    payload["checkpoint"]["description"] = ""
    path = write_plan(tmp_path, payload)
    result = validate_plan(path)
    assert not result.ok
    assert any("checkpoint.description" in err for err in result.errors)


def test_validate_plan_rejects_duplicate_step_ids(tmp_path: Path) -> None:
    payload = base_payload()
    payload["steps"].append(
        {
            "id": "S1",
            "title": "Duplicate",
            "status": "queued",
            "receipts": [],
        }
    )
    path = write_plan(tmp_path, payload)
    result = validate_plan(path)
    assert not result.ok
    assert any("duplicates" in err for err in result.errors)


def test_validate_plan_requires_metadata(tmp_path: Path) -> None:
    payload = base_payload()
    payload.pop("layer")
    path = write_plan(tmp_path, payload)
    result = validate_plan(path)
    assert not result.ok
    assert any("layer" in err for err in result.errors)


def test_validate_plan_validates_systemic_range(tmp_path: Path) -> None:
    payload = base_payload()
    payload["systemic_scale"] = 11
    path = write_plan(tmp_path, payload)
    result = validate_plan(path)
    assert not result.ok
    assert any("systemic_scale" in err for err in result.errors)


def test_validate_plan_requires_ocers_direction(tmp_path: Path) -> None:
    payload = base_payload()
    payload["ocers_target"] = "Observation"
    path = write_plan(tmp_path, payload)
    result = validate_plan(path)
    assert not result.ok
    assert any("ocers_target" in err for err in result.errors)


def test_validate_plan_strict_requires_receipt_presence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    plans_dir = repo_root / "_plans"
    receipt_dir = repo_root / "_report" / "runner"
    plans_dir.mkdir(parents=True)
    receipt_dir.mkdir(parents=True)

    subprocess.run(["git", "init"], check=True, cwd=repo_root)

    payload = base_payload(plan_id="2025-09-17-with-receipt")
    payload["checkpoint"]["status"] = "satisfied"
    payload["receipts"] = ["_report/runner/receipt.json"]
    payload["steps"][0]["receipts"] = ["_report/runner/receipt.json"]
    plan_path = write_plan(plans_dir, payload)

    monkeypatch.setattr(planner_validate, "ROOT", repo_root)
    monkeypatch.setattr(planner_validate, "PLANS_DIR", plans_dir)
    planner_validate._git_tracked_paths.cache_clear()

    result_missing = validate_plan(plan_path, strict=True)
    assert not result_missing.ok
    assert any("receipts[0]" in err for err in result_missing.errors)

    # Create the expected receipt and re-run.
    receipt_rel = Path("_report/runner/receipt.json")
    (receipt_dir / "receipt.json").write_text("{}", encoding="utf-8")
    subprocess.run(["git", "add", str(plan_path.relative_to(repo_root))], check=True, cwd=repo_root)
    subprocess.run(["git", "add", str(receipt_rel)], check=True, cwd=repo_root)
    planner_validate._git_tracked_paths.cache_clear()
    result_ok = validate_plan(plan_path, strict=True)
    assert result_ok.ok, result_ok.errors


def test_validate_plan_strict_rejects_untracked_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    plans_dir = repo_root / "_plans"
    receipt_dir = repo_root / "_report" / "runner"
    plans_dir.mkdir(parents=True)
    receipt_dir.mkdir(parents=True)

    subprocess.run(["git", "init"], check=True, cwd=repo_root)

    payload = base_payload(plan_id="2025-09-17-untracked")
    payload["receipts"] = ["_report/runner/untracked.json"]
    payload["steps"][0]["receipts"] = ["_report/runner/untracked.json"]
    plan_path = write_plan(plans_dir, payload)

    monkeypatch.setattr(planner_validate, "ROOT", repo_root)
    monkeypatch.setattr(planner_validate, "PLANS_DIR", plans_dir)
    planner_validate._git_tracked_paths.cache_clear()

    (receipt_dir / "untracked.json").write_text("{}", encoding="utf-8")
    subprocess.run(["git", "add", str(plan_path.relative_to(repo_root))], check=True, cwd=repo_root)

    result = validate_plan(plan_path, strict=True)
    assert not result.ok
    assert any("not tracked by git" in err for err in result.errors)


def test_cli_output_summary(tmp_path: Path) -> None:
    payload = base_payload(plan_id="2025-09-17-cli")
    plan_path = write_plan(tmp_path, payload)
    output_path = tmp_path / "summary.json"

    proc = subprocess.run(
        [sys.executable, '-m', 'tools.planner.validate', str(plan_path), '--output', str(output_path)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert 'RuntimeWarning' not in proc.stderr
    assert output_path.exists()

    data = json.loads(output_path.read_text(encoding='utf-8'))
    assert isinstance(data, dict)
    assert data['exit_code'] == 0
    assert data['plans'], 'summary should include plan entries'
    entry = data['plans'][0]
    assert entry['ok'] is True
    assert entry['errors'] == []
    assert 'queue_warnings' in entry


def test_queue_warning_mismatch_detected(tmp_path: Path) -> None:
    payload = base_payload(plan_id="2025-09-17-queue-mismatch")
    payload["links"] = [{"type": "queue", "ref": "queue/030-consensus-ledger-cli.md"}]
    path = write_plan(tmp_path, payload)

    entry = fractal_conformance.QueueEntry(
        path="queue/030-consensus-ledger-cli.md",
        ocers_target="Observation↑ Coherence↑",
        coordinates=["S6:L5"],
        issues=[],
    )
    original_index = planner_validate._QUEUE_INDEX
    try:
        planner_validate._QUEUE_INDEX = {"queue/030-consensus-ledger-cli.md": entry}
        result = validate_plan(path)
        assert result.ok, result.errors
        assert result.plan is not None
        warnings = planner_validate._detect_queue_warnings(
            result.plan,
            planner_validate._QUEUE_INDEX,
        )
        assert warnings, "expected queue mismatch warnings"
        assert any(warning.get("issue") == "ocers_mismatch" for warning in warnings)
    finally:
        planner_validate._QUEUE_INDEX = original_index



def test_cli_default_output(tmp_path: Path) -> None:
    payload = base_payload(plan_id="2025-09-17-default")
    plan_path = write_plan(tmp_path, payload)

    proc = subprocess.run(
        [sys.executable, '-m', 'tools.planner.validate', str(plan_path)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    line = proc.stdout.strip().splitlines()[-1]
    assert line.startswith('wrote summary to ')
    rel = line.split('wrote summary to ', 1)[1].strip()
    summary_path = (REPO_ROOT / rel).resolve()
    assert summary_path.exists(), f"expected {summary_path} to exist"

    data = json.loads(summary_path.read_text(encoding='utf-8'))
    assert data['exit_code'] == 0
    summary_path.unlink()
    if not any(summary_path.parent.iterdir()):
        summary_path.parent.rmdir()

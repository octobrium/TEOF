import json
from pathlib import Path

import pytest

from tools.planner import cli as planner_cli
from tools.planner import validate as planner_validate
from tools.planner.validate import validate_plan


def read_plan(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_cli(argv: list[str]) -> int:
    return planner_cli.main(argv)


@pytest.fixture
def planner_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "repo"
    plan_dir = root / "_plans"
    plan_dir.mkdir(parents=True)
    monkeypatch.setattr(planner_cli, "ROOT", root)
    monkeypatch.setattr(planner_cli, "DEFAULT_PLAN_DIR", plan_dir)
    monkeypatch.setattr(planner_validate, "ROOT", root)
    monkeypatch.setattr(planner_validate, "PLANS_DIR", plan_dir)
    return root


def test_cli_new_creates_valid_plan(planner_root: Path) -> None:
    plan_dir = planner_root / "_plans"
    exit_code = run_cli(
        [
            "new",
            "example-slug",
            "--summary",
            "Bootstrap test plan",
            "--actor",
            "tester",
            "--owner",
            "owner",
            "--checkpoint",
            "Ensure test coverage",
            "--step",
            "S1:Implement",
            "--step",
            "S2:Verify",
            "--plan-dir",
            str(plan_dir),
            "--timestamp",
            "2025-09-17T00:00:00Z",
        ]
    )
    assert exit_code == 0

    plan_path = plan_dir / "2025-09-17-example-slug.plan.json"
    data = read_plan(plan_path)
    assert data["actor"] == "tester"
    assert data["status"] == "queued"
    assert [step["id"] for step in data["steps"]] == ["S1", "S2"]
    assert data["checkpoint"]["description"] == "Ensure test coverage"

    result = validate_plan(plan_path, strict=True)
    assert result.ok, result.errors


def test_cli_new_normalizes_slug(planner_root: Path) -> None:
    plan_dir = planner_root / "plans"
    run_cli(
        [
            "new",
            "New Feature",
            "--summary",
            "Normalized slug",
            "--actor",
            "tester",
            "--plan-dir",
            str(plan_dir),
            "--timestamp",
            "2025-09-17T00:00:00Z",
        ]
    )
    plan_path = plan_dir / "2025-09-17-new-feature.plan.json"
    assert plan_path.exists()


def test_cli_new_rejects_duplicate_steps(planner_root: Path) -> None:
    plan_dir = planner_root / "_plans"
    with pytest.raises(SystemExit):
        run_cli(
            [
                "new",
                "example",
                "--summary",
                "Duplicate steps",
                "--actor",
                "tester",
                "--plan-dir",
                str(plan_dir),
                "--timestamp",
                "2025-09-17T00:00:00Z",
                "--step",
                "S1:Do one",
                "--step",
                "S1:Do again",
            ]
        )


def test_cli_status_updates_plan(planner_root: Path) -> None:
    plan_dir = planner_root / "_plans"
    plan_path = plan_dir / "2025-09-17-status-test.plan.json"
    run_cli(
        [
            "new",
            "status-test",
            "--summary",
            "Status plan",
            "--actor",
            "tester",
            "--plan-dir",
            str(plan_dir),
            "--timestamp",
            "2025-09-17T00:00:00Z",
        ]
    )

    exit_code = run_cli(["status", str(plan_path), "in_progress"])
    assert exit_code == 0
    data = read_plan(plan_path)
    assert data["status"] == "in_progress"

    # done cannot revert to in_progress
    exit_code = run_cli(["status", str(plan_path), "done"])
    assert exit_code == 0
    with pytest.raises(SystemExit):
        run_cli(["status", str(plan_path), "in_progress"])


def test_cli_step_add_and_set(planner_root: Path) -> None:
    plan_dir = planner_root / "_plans"
    plan_path = plan_dir / "2025-09-17-steps.plan.json"
    run_cli(
        [
            "new",
            "steps",
            "--summary",
            "Steps plan",
            "--actor",
            "tester",
            "--plan-dir",
            str(plan_dir),
            "--timestamp",
            "2025-09-17T00:00:00Z",
        ]
    )

    exit_code = run_cli(
        [
            "step",
            "add",
            str(plan_path),
            "--desc",
            "Implement feature",
        ]
    )
    assert exit_code == 0

    data = read_plan(plan_path)
    assert len(data["steps"]) == 2
    new_step = data["steps"][1]
    assert new_step["title"] == "Implement feature"
    assert new_step["status"] == "queued"

    exit_code = run_cli(
        [
            "step",
            "set",
            str(plan_path),
            new_step["id"],
            "--status",
            "in_progress",
            "--note",
            "Working on it",
        ]
    )
    assert exit_code == 0

    data = read_plan(plan_path)
    updated_step = next(step for step in data["steps"] if step["id"] == new_step["id"])
    assert updated_step["status"] == "in_progress"
    assert updated_step["notes"] == "Working on it"
    with pytest.raises(SystemExit):
        run_cli(
            [
                "step",
                "set",
                str(plan_path),
                new_step["id"],
                "--status",
                "queued",
            ]
        )


def test_cli_attach_receipt_updates_plan_and_receipt(planner_root: Path) -> None:
    plan_dir = planner_root / "_plans"
    report_dir = planner_root / "_report" / "runner"
    report_dir.mkdir(parents=True)
    plan_path = plan_dir / "2025-09-17-receipt.plan.json"

    run_cli(
        [
            "new",
            "receipt",
            "--summary",
            "Receipt plan",
            "--actor",
            "tester",
            "--plan-dir",
            str(plan_dir),
            "--timestamp",
            "2025-09-17T00:00:00Z",
        ]
    )

    receipt_path = report_dir / "receipt.json"
    receipt_path.write_text("{}\n", encoding="utf-8")
    step_id = read_plan(plan_path)["steps"][0]["id"]

    exit_code = run_cli(
        [
            "attach-receipt",
            str(plan_path),
            step_id,
            "--file",
            str(receipt_path),
        ]
    )
    assert exit_code == 0

    data = read_plan(plan_path)
    step = next(step for step in data["steps"] if step["id"] == step_id)
    rel = f"_report/runner/{receipt_path.name}"
    assert rel in step["receipts"]
    assert rel in data["receipts"]

    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert payload["plan_id"] == data["plan_id"]
    assert payload["plan_step_id"] == step_id



def test_cli_show_outputs_summary(planner_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    plan_dir = planner_root / "_plans"
    plan_path = plan_dir / "2025-09-17-show.plan.json"
    run_cli(
        [
            "new",
            "show",
            "--summary",
            "Show test plan",
            "--actor",
            "tester",
            "--plan-dir",
            str(plan_dir),
            "--timestamp",
            "2025-09-17T00:00:00Z",
        ]
    )

    exit_code = run_cli(["show", str(plan_path)])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "plan_id: 2025-09-17-show" in out
    assert "status: queued" in out
    assert "steps:" in out

    # The command should also resolve plan_id automatically.
    capsys.readouterr()
    exit_code = run_cli(["show", "2025-09-17-show.plan"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "plan_id: 2025-09-17-show" in out



def test_cli_list_outputs_table(planner_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    plan_dir = planner_root / "_plans"
    run_cli(
        [
            "new",
            "list-table",
            "--summary",
            "Table plan",
            "--actor",
            "tester",
            "--plan-dir",
            str(plan_dir),
            "--timestamp",
            "2025-09-17T00:00:00Z",
        ]
    )
    capsys.readouterr()
    run_cli(
        [
            "new",
            "list-done",
            "--summary",
            "Done plan",
            "--actor",
            "tester",
            "--plan-dir",
            str(plan_dir),
            "--timestamp",
            "2025-09-18T00:00:00Z",
        ]
    )
    capsys.readouterr()
    plan_path = plan_dir / "2025-09-18-list-done.plan.json"
    data = read_plan(plan_path)
    data["status"] = "done"
    data["steps"][0]["status"] = "done"
    plan_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    exit_code = run_cli(["list"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "plan_id" in out
    assert "2025-09-17-list-table" in out
    assert "plans:" in out


def test_cli_list_outputs_json(planner_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    plan_dir = planner_root / "_plans"
    run_cli(
        [
            "new",
            "list-json",
            "--summary",
            "JSON plan",
            "--actor",
            "tester",
            "--plan-dir",
            str(plan_dir),
            "--timestamp",
            "2025-09-19T00:00:00Z",
        ]
    )
    capsys.readouterr()
    exit_code = run_cli(["list", "--format", "json"])
    assert exit_code == 0
    data = json.loads(capsys.readouterr().out)
    assert any(item["plan_id"] == "2025-09-19-list-json" for item in data)

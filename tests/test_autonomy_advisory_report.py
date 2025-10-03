import json
from pathlib import Path

from tools.autonomy import advisory_report


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_generate_report_groups_by_target(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    todo_path = repo / "_plans" / "next-development.todo.json"
    payload = {
        "items": [
            {
                "id": "ADV-1",
                "title": "Plan A missing metadata",
                "source": "fractal-advisory",
                "plan_suggestion": "plan-A",
                "layer": "L5",
                "systemic_scale": 5,
                "notes": "Target: _plans/plan-A.plan.json",
            },
            {
                "id": "ADV-2",
                "title": "Plan A still missing",
                "source": "fractal-advisory",
                "plan_suggestion": "plan-A",
                "layer": "L5",
                "systemic_scale": 5,
                "notes": "Target: _plans/plan-A.plan.json",
            },
            {
                "id": "ADV-3",
                "title": "Plan B missing",
                "source": "fractal-advisory",
                "plan_suggestion": "plan-B",
                "layer": "L4",
                "systemic_scale": 4,
                "notes": "Target: _plans/plan-B.plan.json",
            },
        ]
    }
    _write_json(todo_path, payload)

    monkeypatch.setattr(advisory_report, "ROOT", repo)
    report = advisory_report.generate_report(todo_path)

    assert report["total_advisories"] == 3
    clusters = report["clusters"]
    assert clusters[0]["target"] == "_plans/plan-A.plan.json"
    assert clusters[0]["count"] == 2
    assert clusters[1]["target"] == "_plans/plan-B.plan.json"
    assert clusters[1]["layer"] == "L4"


def test_render_markdown_limits_rows(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    todo_path = repo / "_plans" / "next-development.todo.json"
    payload = {
        "items": [
            {
                "id": "ADV-1",
                "title": "Plan A missing metadata",
                "source": "fractal-advisory",
                "plan_suggestion": "plan-A",
                "layer": "L5",
                "systemic_scale": 5,
                "notes": "Target: _plans/plan-A.plan.json",
            },
            {
                "id": "ADV-3",
                "title": "Plan B missing",
                "source": "fractal-advisory",
                "plan_suggestion": "plan-B",
                "layer": "L4",
                "systemic_scale": 4,
                "notes": "Target: _plans/plan-B.plan.json",
            },
        ]
    }
    _write_json(todo_path, payload)

    monkeypatch.setattr(advisory_report, "ROOT", repo)
    report = advisory_report.generate_report(todo_path)

    markdown = advisory_report._render_markdown(report, limit=1)
    assert markdown.count("\n") == 3  # header + divider + one row

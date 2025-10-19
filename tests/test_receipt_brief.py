from pathlib import Path

from tools.agent import receipt_brief


def test_generate_plan_brief_includes_targets(tmp_path: Path) -> None:
    brief = receipt_brief.generate_plan_brief("2025-10-07-macro-hygiene-objectives")
    assert "Plan 2025-10-07-macro-hygiene-objectives — status: done" in brief
    assert "systemic targets: S3, S5, S6" in brief
    assert "Steps:" in brief

    out_path = tmp_path / "brief.md"
    out_path.write_text(brief, encoding="utf-8")
    content = out_path.read_text(encoding="utf-8")
    assert "Macro hygiene objectives are measurable" in content


def test_generate_backlog_brief_reports_plan() -> None:
    brief = receipt_brief.generate_backlog_brief("ND-041")
    assert "Backlog ND-041 — Integrate macro hygiene objectives" in brief
    assert "plan: 2025-10-07-macro-hygiene-objectives" in brief
    assert "receipts (" in brief
    assert "receipts_ref: kind=plan" in brief

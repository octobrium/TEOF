import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "reconcile_pipeline.py"
HELLO_ALT = ROOT / "_report" / "reconciliation" / "hello-alt.json"


def test_pipeline_outputs_summary(tmp_path):
    out_rel = f"_report/reconciliation/test-run-{tmp_path.name}"
    cmd = [
        sys.executable,
        str(SCRIPT),
        str(HELLO_ALT.relative_to(ROOT)),
        "--instance-id",
        "test-instance",
        "--capability",
        "autocollab",
        "--out-dir",
        out_rel,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0

    summary_path = ROOT / out_rel / "merge-summary.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "anchor_note" in summary

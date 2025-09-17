import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "reconcile_metrics_summary.py"
SAMPLE = ROOT / "_report" / "reconciliation" / "ci-metrics2" / "metrics.jsonl"


def run_summary(path: Path):
    return subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True, cwd=ROOT)


def test_summary_outputs_expected_fields(tmp_path):
    tmp_file = tmp_path / "metrics.jsonl"
    tmp_file.write_text('\n'.join([
        json.dumps({"matches": True, "difference_count": 0, "missing_receipt_count": 0, "capability_diff_count": 0}),
        json.dumps({"matches": False, "difference_count": 2, "missing_receipt_count": 1, "capability_diff_count": 1}),
    ]) + '\n', encoding='utf-8')
    result = run_summary(tmp_file)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["total_runs"] == 2
    assert payload["difference_total"] == 2
    assert payload["missing_receipt_total"] == 1
    assert payload["capability_diff_total"] == 1


def test_summary_handles_real_metrics():
    samples = list(ROOT.glob("_report/reconciliation/**/metrics.jsonl"))
    if not samples:
        return
    result = run_summary(samples[0])
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert "total_runs" in payload

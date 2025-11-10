import json
import pathlib
import subprocess
from types import SimpleNamespace

from teof.commands import brief


def test_brief_golden() -> None:
    result = subprocess.run(
        ["teof", "brief", "--format", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["artifact_count"] == len(payload["artifacts"]) == len(payload["artifact_paths"])

    output_dir = pathlib.Path(payload["output_dir"])
    assert output_dir.exists()
    summary_path = pathlib.Path(payload["summary_path"])
    assert summary_path.exists()

    latest = pathlib.Path("artifacts/systemic_out/latest")
    produced = json.loads((latest / "001_whitehouse_ai.ensemble.json").read_text())
    expected = json.loads(
        pathlib.Path("docs/examples/brief/expected/001_whitehouse_ai.ensemble.json").read_text()
    )
    assert produced == expected
    assert any(path.endswith("001_whitehouse_ai.ensemble.json") for path in payload["artifact_paths"])
    assert payload["failure_count"] == 0
    assert payload["status"] == "ok"


def test_brief_handles_scoring_errors(monkeypatch, tmp_path, capfd):
    repo = tmp_path / "repo"
    examples_dir = repo / "docs" / "examples" / "brief" / "inputs"
    artifacts_dir = repo / "artifacts" / "systemic_out"
    examples_dir.mkdir(parents=True)
    artifacts_dir.mkdir(parents=True)

    good = examples_dir / "good.txt"
    bad = examples_dir / "bad.txt"
    good.write_text("good", encoding="utf-8")
    bad.write_text("bad", encoding="utf-8")

    monkeypatch.setattr(brief, "ROOT", repo)
    monkeypatch.setattr(brief, "EXAMPLES_DIR", examples_dir)
    monkeypatch.setattr(brief, "ARTIFACT_ROOT", artifacts_dir)

    def fake_score(path: pathlib.Path):
        if path == bad:
            raise RuntimeError("broken input")
        return {"score": 1}

    monkeypatch.setattr(brief, "score_file", fake_score)

    exit_code = brief.run(SimpleNamespace(format="json"))
    assert exit_code == 1
    payload = json.loads(capfd.readouterr().out)
    assert payload["artifact_count"] == 1
    assert payload["failure_count"] == 1
    assert payload["status"] == "partial"
    assert payload["failures"][0]["input"] == "bad.txt"
    assert payload["failures"][0]["error"]
    output_dir = repo / payload["output_dir"]
    assert (output_dir / "good.ensemble.json").exists()

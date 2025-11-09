import json
import pathlib
import subprocess


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

import json, pathlib, subprocess

def test_brief_golden():
    subprocess.run(["teof","brief"], check=True)
    latest = pathlib.Path("artifacts/systemic_out/latest")
    produced = json.loads((latest/"001_whitehouse_ai.ensemble.json").read_text())
    expected = json.loads(pathlib.Path("docs/examples/brief/expected/001_whitehouse_ai.ensemble.json").read_text())
    assert produced == expected

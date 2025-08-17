import importlib
import json
import pathlib
import subprocess
import sys
import tempfile

# Existing minimal validator module (CLI usage: "<input.txt> <outdir>")
_VALIDATOR_MODULE = "extensions.validator.teof_ocers_min"

def _import_validate_func():
    try:
        mod = importlib.import_module(_VALIDATOR_MODULE)
    except ModuleNotFoundError:
        return None
    for name in ("validate_text", "validate", "run_validate"):
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn
    return None

def _read_any_json(outdir: pathlib.Path) -> dict:
    # Prefer report.json; otherwise first *.json file
    pref = outdir / "report.json"
    if pref.exists():
        return json.loads(pref.read_text(encoding="utf-8"))
    jsons = sorted(outdir.glob("*.json"))
    if jsons:
        return json.loads(jsons[0].read_text(encoding="utf-8"))
    raise RuntimeError("Validator outdir did not contain a JSON report.")

def validate_text(text: str) -> dict:
    fn = _import_validate_func()
    if fn is not None:
        return fn(text)

    # Fallback to CLI: python -m extensions.validator.teof_ocers_min <input.txt> <outdir>
    with tempfile.TemporaryDirectory() as td:
        td_path = pathlib.Path(td)
        inp = td_path / "input.txt"
        inp.write_text(text, encoding="utf-8")

        cmd = [sys.executable, "-m", _VALIDATOR_MODULE, str(inp), str(td_path)]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Validator CLI failed: {e.stderr or e.stdout}") from e

        return _read_any_json(td_path)

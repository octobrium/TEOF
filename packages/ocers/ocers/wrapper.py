import importlib
import json
import pathlib
import subprocess
import sys
import tempfile

# Known path to your current minimal validator CLI:
# earlier mapping showed: teof-validate -> extensions.validator.teof_ocers_min:main
_VALIDATOR_MODULE = "extensions.validator.teof_ocers_min"

def _import_validate_func():
    """
    Try to import a function-level API from the existing validator.
    If not found, return None so we can fall back to the CLI path.
    """
    try:
        mod = importlib.import_module(_VALIDATOR_MODULE)
    except ModuleNotFoundError:
        return None

    # common function names we might have defined previously
    for name in ("validate_text", "validate", "run_validate"):
        if hasattr(mod, name):
            fn = getattr(mod, name)
            if callable(fn):
                return fn
    return None

def validate_text(text: str) -> dict:
    """
    Neutral programmatic API.
    1) Prefer a direct function from the existing validator (if available).
    2) Otherwise, invoke the existing CLI in a subprocess and parse its JSON.
    Returns a dict report with OCERS fields/scores, or raises on error.
    """
    fn = _import_validate_func()
    if fn is not None:
        # Direct call path (fastest, no subprocess)
        return fn(text)

    # Fallback: call the existing CLI via subprocess (stdin or temp file)
    # We assume the CLI can read a file path and produce JSON to stdout or an out dir.
    # This wrapper writes a temp file and expects JSON printed to stdout.
    with tempfile.TemporaryDirectory() as td:
        td_path = pathlib.Path(td)
        inp = td_path / "input.txt"
        out = td_path / "report.json"
        inp.write_text(text, encoding="utf-8")

        # Try: `python -m extensions.validator.teof_ocers_min input.txt`
        # If your CLI needs --out, we’ll capture stdout and also read report.json if created.
        cmd = [sys.executable, "-m", _VALIDATOR_MODULE, str(inp), "--out", str(td_path)]
        try:
            cp = subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Validator CLI failed: {e.stderr or e.stdout}") from e

        # Prefer explicit report.json if produced; otherwise try to parse stdout
        if out.exists():
            return json.loads(out.read_text(encoding="utf-8"))

        # Last resort: try stdout as JSON
        stdout = cp.stdout.strip()
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            raise RuntimeError(
                "Validator did not produce JSON. "
                "Ensure the existing CLI writes report.json or JSON to stdout."
            )

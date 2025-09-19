# Quickstart

<!-- generated: quickstart snippet -->
Run this smoke test on a fresh checkout:
```bash
python3 -m pip install -e .
teof brief
ls artifacts/ocers_out/latest
cat artifacts/ocers_out/latest/brief.json
```

- Install exposes the teof console script.
- teof brief scores docs/examples/brief/inputs/ and writes receipts under artifacts/ocers_out/<UTC>.

> Update the snippet via `python3 tools/snippets/render_quickstart.py` after editing `tools/snippets/quickstart.json`.

## Extend the run (optional)
To score your own OCERS drafts, point the ensemble CLI at any directory of `.txt` files:
```bash
python3 -m extensions.validator.scorers.ensemble_cli \
  --in /path/to/notes \
  --out artifacts/ocers_out/$(date -u +%Y%m%dT%H%M%SZ)
```

For the minimal validator only, use:
```bash
python3 -m extensions.validator.teof_ocers_min input.txt artifacts/outdir
```

## Next checkpoints
- If you change validator behaviour, update the goldens under `docs/examples/**/expected/`
- When packaging for others, freeze the capsule (`scripts/freeze.sh`) and append a governance anchor

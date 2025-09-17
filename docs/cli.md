# TEOF CLI Quick Reference

The repository ships a minimal `teof` command for local smoke tests and sample artifact generation. It wraps the bundled ensemble scorer so contributors can validate changes without installing the full external CLI.

## Installation

```bash
pip install -e .
```

## `teof brief`

Run the bundled "brief" example through the ensemble scorer and emit artifacts under `artifacts/ocers_out/<timestamp>/`:

```bash
python -m teof.cli brief
```

Each invocation produces:

- `*.ensemble.json` – ensemble scores for every input in `docs/examples/brief/inputs/`
- `brief.json` – execution summary listing input files, output artifacts, and the UTC timestamp
- `score.txt` – plain-text counter with the number of ensemble outputs
- `latest/` – symlink (or directory fallback) pointing at the most recent run

Use these artifacts as observational checks; they are not considered capsule canon.

## Help & Diagnostics

```bash
python teof/bootloader.py --help
```

Use this smoke test to confirm the bootloader is importable and the CLI entry points are wired correctly. CI tracks the same command in a non-blocking step so regressions surface without blocking the pipeline.

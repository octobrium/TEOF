# TEOF Systemic Validators (minimal)

This package bundles lightweight validators that operate on systemic metadata.
The primary entry point, `teof_systemic_min.py`, evaluates readiness records
against the Unity → Meaning lattice and emits machine-readable receipts.

## `teof_systemic_min.py`

- Accepts a plaintext summary and scores structural signals (`structure`,
  `alignment`, `verification`, `risk`, `recovery`).
- Produces deterministic JSON with the original filename, SHA-256 hash, and a
  verdict derived from total systemic coverage.
- Designed for repository-local use: `python3 extensions/validator/teof_systemic_min.py <input.txt> <outdir>`.

The module exposes helpers (`systemic_rules.py`) that other tools can reuse when
they need simple heuristics for systemic completeness.

## Extending

- Keep new validators deterministic and receipt-friendly.
- Each addition must document how it maps to systemic axes and layers so other
  automation can rely on the output.
- When replacing a legacy workflow, park the retired assets under `archive/`
  instead of expanding this package; the kernel remains minimal by design.

See `docs/automation/systemic-overview.md` for the broader metadata contract.

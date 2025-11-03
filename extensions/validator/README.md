# TEOF Systemic Validators (minimal)

This package bundles lightweight validators that operate on systemic metadata.
The primary entry points, `teof_systemic_min.py` and the receipt-aware ensemble
runner, evaluate readiness records against the Unity → Meaning lattice and emit
machine-readable receipts.

## `teof_systemic_min.py`

- Accepts a plaintext summary and scores structural signals (`structure`,
  `alignment`, `verification`, `risk`, `recovery`).
- Produces deterministic JSON with the original filename, SHA-256 hash, and a
  verdict derived from total systemic coverage.
- Designed for repository-local use: `python3 extensions/validator/teof_systemic_min.py <input.txt> <outdir>`.

- The ensemble scorer (`extensions/validator/scorers/ensemble.py`) now ships two
  runners by default:
  - `H` — the heuristic readiness scorer above.
  - `R` — a receipt-backed evaluator that verifies referenced artifacts and
    rewards hashed, systemic receipts. It reads the repo root (override with
    `TEOF_RECEIPT_ROOT`) so plans must cite actual evidence.

The module exposes helpers (`systemic_rules.py`) that other tools can reuse when
they need simple heuristics for systemic completeness.

## Extending

- Keep new validators deterministic and receipt-friendly.
- Each addition must document how it maps to systemic axes and layers so other
  automation can rely on the output.
- When replacing a legacy workflow, park the retired assets under `archive/`
  instead of expanding this package; the kernel remains minimal by design.

See `docs/automation/systemic-overview.md` for the broader metadata contract.

# TEOF DNA (Spec)

**Purpose:** Keep the directive near-perfect while allowing controlled evolution. Everything else follows the DNA.

## Philosophy → Operational
- **Directive**: observation-first, recursive coherence, power-as-function.
- **Refinement loop**: expansion (experiments), apoptosis (prune/archive), record-keeping (hashes/anchors).
- **Machine guardrails**: invariants are encoded and enforced in CI/preflight.

## Invariants (must always hold)
- Canonical top-level set only (no surprise roots).
- Single canonical `extensions/` at repo root (no duplicates elsewhere).
- Scripts are bucketed: `scripts/ci`, `scripts/dev`, `scripts/ops`.
- `capsule/current` is a **symlink** to a concrete version (e.g., `v1.6`) and that version contains **freeze artifacts**: `count`, `files`, `root`.
- DNA is locked by `governance/dna.lock.json` and enforced by:
  - `scripts/ci/guard_apoptosis.sh`
  - `scripts/ci/guard_dna.sh`

## Evolution path
- Propose changes via `docs/teps/TEP-XXXX.md`.
- Update `governance/DNA.md` (human).
- Regenerate `governance/dna.lock.json` (machine).
- Guards must pass in CI.

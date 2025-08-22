# TEOF Future — North Stars & Guardrails (Canonical, Minimal)

This document prevents mission drift. It states what must remain true for TEOF.
Changes to this file require a TEP (`proposals/`), CODEOWNERS approval, and CI pass.

## Purpose
- Keep TEOF **auditable, deterministic, minimal** as it grows.
- Ensure every change either **increases verifiability** or **reduces cognitive load**.

## North Stars (non-negotiable)
- **Auditable by default** — canonical bytes are covered by capsule `hashes.json` or referenced by `rings/anchors.json`.
- **Deterministic paths** — same inputs → same brief; behavior changes are config-gated and diffable.
- **Observer-led recursion** — each release is an observable node; nothing critical lives only “in flight”.
- **Minimal surface area** — composition over new code; fewer moving parts > cleverness.
- **Portability** — plain text first; scripts run on clean Ubuntu/macOS (no vendor lock).

## Operating Principles
- Additions must **reduce complexity** or **increase integrity**; otherwise defer.
- CI can **reproduce** human steps end-to-end (freeze, verify, brief).
- **Proof-of-authorship**: changelog entry + anchors event with `prev_content_hash`.
- **No silent changes**: Explore vs Strict is documented and config-gated.

## Compatibility Guarantees
- Canonical capsule files change only in tagged releases.
- Changes to evaluator rules (VDP/OGS) land with updated **goldens**, **changelog**, and a **TEP**.

## Non-Goals (out of scope for core)
- No stateful background services in core.
- No opaque binaries in the capsule.
- No bypass of VDP/OGS checks.

## Change Control
1) Create a **TEP** in `proposals/` (motivation, alternatives, impact).  
2) Open a PR referencing the TEP; **CODEOWNERS** approval required.  
3) On release: append event in `rings/anchors.json` (append-only) binding the change.

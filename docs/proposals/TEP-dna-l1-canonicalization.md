Title: TEP-dna-l1-canonicalization
Status: Proposed
Author: codex-4
Date: 2025-09-21

Problem
- L1 (Principles) had multiple overlapping texts (canonical, summary, whitepaper/TAP copies) causing drift risk and unclear authority.
- Architecture coverage was split between a note in `architecture.md` and `bindings.yml`.
- DNA symlink invariant wording was stricter than current practice (accepted plain-text fallback), creating a norm/state mismatch.

Proposal
- Establish a single minimal, testable L1: `governance/core/L1 - principles/canonical-teof.md` with P1–P7.
- Mark `principles.md` as Summary (advisory). Mark “whitepaper copy” and “TAP copy” as Advisory.
- Add `governance/core/INDEX.md` enumerating canonical paths and statuses for L0–L5; mark L6 unassigned.
- Make `bindings.yml` the authoritative enforcement map and update `architecture.md` to point to it.
- Clarify DNA symlink language to prefer symlink, accept fallback, and restore when practical.

Alternatives
- Move or delete advisory copies (blocked by no‑rename/no‑delete policy); defer moves to a later PR.
- Keep multiple L1 sources and rely on social convention (higher drift risk).

Impact
- Reduces ambiguity; improves auditability and downstream adoption.
- No behavioral code changes; CI unaffected.
- Small doc edits only; easy rollback.

Rollback
- Revert the updated files:
  - `governance/core/L1 - principles/canonical-teof.md`
  - `governance/core/L1 - principles/principles.md`
  - `governance/core/L1 - principles/whitepaper copy.md`
  - `governance/core/L1 - principles/TAP copy.md`
  - `governance/core/L4 - architecture/architecture.md`
  - `governance/DNA.md`
  - Remove `governance/core/INDEX.md`


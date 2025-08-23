# TEOF Master Workflow (Minimal v1.2)

## Architecture Gate (before writing code)
- Place new work per `docs/architecture.md` (extensions / experimental / archive / docs / scripts / governance).
- Prototypes start in `experimental/` with a short promotion plan in the PR.
- Kernel code **MUST NOT** import from `experimental/` or `archive/` (the import policy guard enforces this).
- If a new top-level seems required, open a 1‑page TEP in `rfcs/` (purpose, contract, alternatives, rollback).

---

## Non‑negotiables (apply to every change)
- **Minimalism:** Keep complexity the same or lower for equal capability. If complexity increases, justify in one sentence in the PR body.
- **Single Source of Truth:** Immutable baselines live under `capsule/<version>/` and are covered by `capsule/<version>/hashes.json`. `capsule/current` is a plain‑text pointer to the active version.
- **Determinism:** Commands run reproducibly on a clean machine (no hidden state, same output paths).
- **Append‑Only Governance:** `governance/anchors.json` is append‑only; releases map to a baseline with a `prev_content_hash`.
- **Observation Discipline:** Claims follow VDP; reasoning can be scored with OGS. Use **N/A** when not applicable.
- **Stable Interfaces:** Prefer console scripts (`teof-validate`, `teof-ensemble`) or `python -m …` over deep file paths.

---

## DNA Recursion (self‑improvement of the rules)
**Goal:** Continuously refine our own architecture, workflow, and promotion policy without bloating the kernel.

**When to trigger**
- Repeated friction (same exception to rules ≥2 times)  
- Structural drift (files don’t fit placement rules)  
- Material change in scope/audience (new app/repo boundary)  
- Periodic maintenance (optional cadence)

**How (Meta‑TEP)**
1) Open `rfcs/TEP-dna-<short-topic>.md` describing: **Problem**, **Proposal**, **Alternatives**, **Impact**, **Rollback**.  
2) Land the doc change (`docs/architecture.md`, `docs/workflow.md`, `docs/promotion-policy.md`).  
3) Append a governance event (type=`dna-change`) in `governance/anchors.json` (optionally include a hash of the updated DNA docs).  
4) Add a one‑line note to `CHANGELOG.md` under “Docs/DNA”.

**Non‑negotiables for DNA changes**
- **Minimalism:** rule count stays flat or goes down  
- **Stability:** no breaking of public import surface (`extensions.*`)  
- **Provenance:** every DNA change is anchored (append‑only)  
- **CI discipline:** no new CI rules unless they protect the kernel (import policy remains the only hard guard)

---

## PR Checklist (the only 6 checks that must pass)
- [ ] **Objective line (one sentence)**  
  `Class=<Core|Trunk|Branch|Leaf>; Why=…; MinimalStep=…; Direction=…`

- [ ] **Placement & import guard**  
  Files are placed per `docs/architecture.md`. Run `bash scripts/policy_checks.sh` (or let CI run it) — **no** `extensions/` imports from `experimental/` or `archive/`.

- [ ] **Baseline gate**  
  If critical/immutable files changed: put them under `capsule/<version>/`, run `bash scripts/freeze.sh`, and ensure CI verify passes (hashes, anchors, no junk files).

- [ ] **Evidence/goldens**  
  If validator/evaluator logic or reasoning rules changed: update `docs/examples/**/expected/` goldens and include a brief rationale. OCERS/OGS commands must run and produce artifacts.

- [ ] **Minimal surface**  
  Provide the smallest runnable demo or doc snippet (CLI invocation + output path) that shows the change; else **N/A**.

- [ ] **Changelog touch**  
  If behavior or immutable scope changed, update `CHANGELOG.md`. (Tie to anchors event when applicable.)

> If this PR edits the DNA (architecture/workflow/promotion policy), also follow **DNA Recursion** above.

---

## Lean release block (only when tagging)
1) Ensure `capsule/current` points to `vX.Y` and `hashes.json` is final (`bash scripts/freeze.sh`).  
2) Append an anchors event in `governance/anchors.json` (includes `prev_content_hash`, `{tag, baseline}`; if DNA changed, include its hash).  
3) Update `CHANGELOG.md` with date and bullets.  
4) Tag and archive:  
   ```bash
   git tag -a vX.Y.Z -m "…"
   git push origin vX.Y.Z
   # optional: zip capsule for distribution
   (cd capsule && zip -r "../artifacts/teof-vX.Y.Z.zip" "vX.Y")
   ```
5) Publish the release with the zip (optional).

---

## Working order (day‑to‑day)
1) Confirm placement vs Architecture; fix anchors ↔ baseline as needed.  
2) Make CI **verify** green (import policy + brief shape checks).  
3) If reasoning changed, wire evaluator + update goldens.  
4) Expose a minimal surface (one command → artifacts).  
5) Tag & ship when ready.

> **Placement note:** This file lives **outside** the capsule to avoid baseline churn. After it stabilizes (several cycles without edits), move it into `capsule/current/` and re‑freeze hashes.

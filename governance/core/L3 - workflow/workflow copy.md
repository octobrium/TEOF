<!-- markdownlint-disable MD013 -->
Status: Living
Purpose: Process & checklists that enforce Architecture
Change process: PR + 1 maintainer
Review cadence: Monthly sweep

# TEOF Master Workflow (Minimal v1.3)

## Operator mode (LLM quick brief)

**Purpose:** Make any fresh session (human or assistant) act optimally to assess and advance TEOF with minimal surface area and deterministic, auditable outputs.

**Mission**
- Advance TEOF with minimal surface area and deterministic, auditable outputs.
- Follow the repo DNA, not ad-hoc preferences.

**Read these first (in order)**
1) `docs/architecture.md` — where things go  
2) `docs/workflow.md` — priority ladder & release (this file)  
3) `docs/promotion-policy.md`  
4) `docs/quickstart.md` — one command → artifacts

**Guardrails**
- **Observation primacy:** do not propose rule changes until an end-to-end run path is clear.
- **Minimalism:** prefer the smallest change that makes the E2E path work.
- **Import policy:** no imports from `experimental/` or `archive/` inside `extensions/` (`scripts/policy_checks.sh`).
- **Provenance:** if you change the DNA (architecture/workflow/promotion-policy), propose an anchors event.

**Operating order**
1) Confirm structure matches `docs/architecture.md`.  
2) Produce an E2E plan using `docs/quickstart.md` (exact commands, no guessing).  
3) Verify enforcement: confirm `scripts/policy_checks.sh` exists and is called in CI; if missing, output a minimal step to add it.  
4) Triangulate gaps: if Quickstart or imports/paths are stale, propose the smallest patches to make them true.  
5) Output a prioritized plan (next 3–6 steps) to make the repo self-propagating (CLI → CI → freeze → docs).  
6) Only if rules block progress: propose a minimal DNA edit via a one-page Meta‑TEP (Problem, Proposal, Alternatives, Impact, Rollback).

**Response format**
- Summary (2–4 bullets)  
- Immediate actions (commands or file patches)  
- Risks / assumptions (short)  
- Next checkpoint (what to verify after the actions)

**Non-goals**
- No new CI rules unless they protect the kernel import boundary.
- No new top-level folders unless justified via a 1‑page TEP.

---

## Architecture Gate (before writing code)
- Place new work per `docs/architecture.md` (extensions / experimental / archive / docs / scripts / governance).
- Prototypes start in `experimental/` with a short promotion plan in the PR.
- Kernel code **MUST NOT** import from `experimental/` or `archive/` (the import policy guard enforces this).
- If a new top-level seems required, open a 1‑page TEP in `rfcs/` (purpose, contract, alternatives, rollback).

---

## Non‑negotiables (apply to every change)
- **Minimalism:** keep complexity the same or lower for equal capability. If complexity increases, justify in one sentence in the PR body.
- **Single Source of Truth:** immutable baselines live under `capsule/<version>/` and are covered by `capsule/<version>/hashes.json`. `capsule/current` is a plain‑text pointer to the active version.
- **Determinism:** commands run reproducibly on a clean machine (no hidden state, same output paths).
- **Append‑Only Governance:** `governance/anchors.json` is append-only; releases map to a baseline with a `prev_content_hash`.
- **Observation Discipline:** claims follow VDP; reasoning can be scored with OGS. Use **N/A** when not applicable.
- **Stable Interfaces:** prefer console scripts (`teof-validate`, `teof-ensemble`) or `python -m …` over deep file paths.

---

## DNA Recursion (self‑improvement of the rules)
**Goal:** continuously refine our own architecture, workflow, and promotion policy without bloating the kernel.

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

> **Placement note:** this file lives **outside** the capsule to avoid baseline churn. After it stabilizes (several cycles without edits), move it into `capsule/current/` and re‑freeze hashes.

## Fitness Lens (tools & CI)
- **Preflight is invariants-only.** Tools that don’t measurably improve OCERS remain **opt-in**.
- Use `docs/policy/fitness-lens.md` to justify any blocking check with receipts + sunset.

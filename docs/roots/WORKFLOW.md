# TEOF Master Workflow (Minimal v1)

**Non-negotiables (apply to every change)**
- **Minimalism:** Changes should reduce or hold complexity for equal capability. If complexity ↑, justify in one sentence in the PR body.
- **Single Source of Truth:** Critical files live under `seed/capsule/current/` and are covered by `hashes.json`.
- **Determinism:** Checks run reproducibly on a clean machine.
- **Append-Only Governance:** `rings/anchors.json` is append-only; releases map to a baseline.
- **Observation Discipline:** New claims follow VDP; reasoning can be scored with OGS (N/A allowed when not applicable).
- **Future-proofing:** Prefer text formats, stable layouts, and minimal dependencies.

---

## PR Checklist (the only 6 checks that must pass)

- [ ] **Objective line (one sentence)**  
  `Class=<Core|Trunk|Branch|Leaf>; Why=…; MinimalStep=…; Direction=…`
- [ ] **Baseline gate**  
  If critical files changed: place them in `seed/capsule/current/` → run `freeze_hashes` → CI `verify` passes (hashes, anchors, no `.DS_Store`, no secrets).
- [ ] **Evidence gate**  
  If claims changed, VDP cites + OGS runnable; else **N/A**.
- [ ] **Minimal surface**  
  Provide the smallest demo/doc/flag that shows the change; else **N/A**.
- [ ] **No net complexity**  
  If complexity ↑, include one-sentence justification in the PR body.
- [ ] **Changelog touch**  
  If behavior or immutable scope changed, update `CHANGELOG.md`.

---

## Lean release block (only when tagging)

1) Ensure `seed/capsule/current → vX.Y` and `hashes.json` is final.  
2) `rings/anchors.json`: `immutable_scope = keys(hashes.json)`; append `{tag, baseline}` if new.  
3) Update `CHANGELOG.md` with date & bullets.  
4) Tag and archive: `git tag -a vX.Y.Z -m "…"` and zip the capsule dir to `artifacts/teof-vX.Y.Z.zip`.  
5) Publish release with the zip.

---

## Working order (day-to-day)

1) Fix anchors ↔ baseline (trunk)  
2) Pass CI `verify`  
3) Wire evaluator & goldens (if reasoning changed)  
4) Expose minimal surface  
5) Tag & ship when ready

> Placement note: This file lives **outside** the capsule to avoid baseline churn. After it stabilizes (few cycles without edits), move it into `seed/capsule/current/` and re-freeze hashes.

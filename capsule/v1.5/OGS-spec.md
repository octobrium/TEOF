# Observation Grounding Score (OGS) — Specification

**Goal:** Quantify how well outputs adhere to TEOF’s observation-first discipline.

## Dimensions
1. **Observation Integrity (0–4):** Presence of concrete observations; for volatile claims, *must* include value + timestamp (UTC) + source (see VDP).
2. **Coherence (0–3):** Internal logical consistency; no contradictions among cited data.
3. **Evidence Quality (0–3):** Source credibility, multi-source agreement, correct attribution.
4. **Result Discipline (0–3):** Recommendations trace back to observations; uncertainty properly bounded.
5. **Scope Hygiene (0–2):** Stays on question; avoids unsupported speculation.

**Max Score:** 15

## Mandatory Checks (Hard Fails)
- Volatile claims without timestamp+source → **Fail** (see `docs/volatile-data-protocol.md`).
- Prescriptive outputs relying on volatile data without citations → **Fail**.

## Scoring Heuristics
- Stale data beyond window without label: **-3**.
- Conflicting sources without Uncertain label: **-2**.
- Multi-source agreement with timestamps: **+1**.
- Explicit uncertainty when warranted: **+0.5**.

## Output Schema (suggested)
- OCERS sections + a machine-readable `observations[]` list of volatile claims, each with `value, timestamp_utc, source`.

## Regression Suite
Maintain a golden set of 10–20 items (misinfo, conflicting reports, unknowns, market quotes). Any change that reduces OGS on goldens is a regression unless justified.

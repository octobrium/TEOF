# Volatile Data Protocol (VDP) — TEOF

**Purpose:** Prevent “illusion of progress” on time-sensitive claims by requiring auditable provenance for volatile data (e.g., market quotes, rates, CPI, earnings times, laws, CEO names).

## Core Rule
> Any claim referring to **time-sensitive, quantitative, or externally verifiable** data **must** include:
> 1) **Value**, 2) **Timestamp (UTC)**, and 3) **Source reference (link or dataset ID)**.

If these are missing, the Evaluator **must fail** the item or require an **Uncertain** label.

## Freshness & Staleness
- **Freshness window:** Default 10 minutes for market quotes; domain-specific windows may be set.
- If the underlying data exceeds the window, label **Stale** and either **re-fetch** or proceed with explicit uncertainty.

## Disagreement Handling
- When two independent sources disagree beyond a tolerance (domain-specific), mark **Uncertain** and present both values + sources.
- Do not produce prescriptive recommendations until uncertainty is resolved or bounded.

## No-Lookup / No-Opinion Rule
- If live retrieval fails for a volatile fact, the system must **refuse** to state a numeric value and label the claim **Unverifiable (temporary)**.

## Evaluator Enforcement (OCERS/OGS hooks)
- **Observation:** Check presence of value + timestamp (UTC) + source for volatile claims.
- **Coherence:** Penalize contradictions between cited figures within the same output.
- **Evidence:** Boost when multiple high-quality sources agree; penalize single-source reliance in high-impact contexts.
- **Result:** For prescriptive outputs (e.g., trades), require a citation chain for all critical inputs.
- **Scope:** Flag when outputs wander into speculative claims without supporting observations.

## Weights (OGS suggested defaults)
- Missing timestamp or source on volatile claim: **Hard Fail**.
- Stale data beyond window without label: **-3.0**.
- Conflicting sources without Uncertain label: **-2.0**.
- Clear, consistent, multi-source citations with agreement: **+1.0**.
- Explicit uncertainty where warranted: **+0.5** (reward transparency).

## Implementation Notes
- Attach `{
  "value": <number|string>, 
  "timestamp_utc": "<ISO8601>", 
  "source": "<URL or datasource id>"
}` to each volatile claim in structured outputs.
- Provide domain-specific windows and tolerances (e.g., FX=5m, macro calendar=24h).

## Rationale
This protocol operationalizes TEOF’s **primacy of observation** and ensures that improvements are **observable**, **auditable**, and **non-cosmetic**.

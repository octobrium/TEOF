# Relay Insight Sprint Case Study Briefing

## Partner Profile
- **Alias:** relay-pilot (anonymised).
- **Product:** AI research concierge for traders/investors—delivers market
  analytics briefs in 48 hours to inform trading and investment decisions.
- **Engagement:** 48-hour Relay Insight Sprint (Tier B) to produce a cite-backed
  strategy brief.

## Goals
- Prove TEOF guardrails (diff/test receipts, authenticity snapshot, objectives
  ledger) de-risk unattended research loops for market-facing clients.
- Publish a public case study showing faster, auditable decision support.

## Focus Questions (Sprint S3)
1. Which customer segment or scenario should relay-pilot prioritise for the first paid sprint?
2. What differentiators set us apart from generic GPT-style research tools, especially in geopolitics and surveillance contexts?
3. What guardrails (diff/test limits, margin usage, consent) are required before scaling unattended runs?

## Context Inputs
- **Current situation:** Preparing a public case study before pitching new
  partners next month; needs a repeatable sprint template.
- **Competitor X:** ChatGPT-style research assistants (course-seller/guru tools)
  that monetise fear but lack receipts or auditability.
- **Constraints & guardrails:** Deliverables due in ≤48 hours; diff limit 200
  lines; required tests `pytest`; receipts must land under
  `_report/usage/case-study/relay-insight/`.
- **Existing guardrails:** Consent workflow documented; onboarding quickstart
  and package guard already enforced in CI; authenticity feeds recently rotated
  with attention feeds cleared.
- **Risk tolerance:** Aggressive long-term growth investor comfortable with
  volatility but wants clear drawdown expectations.
- **Margin usage:** Allow moderate margin (≤10%) only when catalysts align; aim
  to keep interest costs near zero.
- **Macro assumption:** Base case assumes ongoing monetary expansion (first
  principles).
- **Time horizon:** Duration of the upcoming US administration (e.g., Trump
  presidency term) as the analysis window.
- **Automation preference:** Minimize manual research logging; ingest trusted
  market/macro data automatically and deliver digestible summaries so the
  investor can focus on outcomes rather than raw receipts.

## Deliverables
1. Market insight brief (Notion/PDF) referencing receipts.
2. Command log / conductor receipts detailing actions taken.
3. Post-run reflection + impact log entry linking to outcomes.
4. Public-facing narrative (`docs/impact/relay-insight-case-study.md`).

## Sources / Inputs to Gather
- Partner goals or KPIs (e.g., markets of interest, trading style).
- Any existing research memos or competitor notes (links/emails).
- Constraints on tooling or data access (e.g., APIs allowed, budget limits).
- Recommended data sources: FRED macro series, IMF/BIS liquidity data,
  company filings for PLTR/NVDA/MSTR, defence/security think tanks, on-chain
  BTC analytics (messari, Glassnode, etc.).

## Timeline
- **Day 0:** Confirm consent, gather inputs, align focus questions.
- **Day 1:** Run conductor (dry-run first, then live), collect artifacts.
- **Day 2:** Compile brief, log impact, draft public case study.

## Success Metrics
- Client satisfaction ≥4/5.
- Sprint completed ≤48h with guardrail compliance.
- Published case study links to verifiable receipts and impact ledger entry.

## Next Steps
1. Gather partner inputs (focus answers, sources) and update this briefing.
2. Execute the sprint per plan `2025-09-27-relay-case-run` (S2).
3. Summarise outputs and publish the case study.

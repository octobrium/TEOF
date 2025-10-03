# External Case Study Roadmap (2025-09-26)

Objective: publish a public-facing case study that proves TEOF’s value with
verifiable receipts. Maps to plan `2025-09-26-external-proof` (ND-016).

## Candidate Surface
- **Relay Insight Sprint pilot** (ND-014) – monetize the guarded API relay.
- **Authenticity guard refresh** – showcase feed rotation + dashboard automation.
- **Alternative**: partner integration (e.g., compliance report attestation).

Pick the surface where we can control inputs, publish receipts openly, and show a
before/after improvement within 1–2 weeks.

## Story Arc
1. **Problem framing** – incident/need (e.g., authenticity feeds drifting).
2. **TEOF intervention** – plans, receipts, guardrails.
3. **Outcome** – measurable improvement (trust scores, time saved, revenue).
4. **Audit trail** – how anyone can verify the claims (links to `_report/`, docs).

## Deliverables
- `_report/usage/case-study/<slug>/` receipts:
  - pre-intervention snapshot
  - run transcripts (conductor/quickstart/etc.)
  - post-intervention metrics (authenticity, revenue log)
- `docs/impact/{slug}.md` narrative with receipts embedded.
- Public asset: blog post / video / slide deck (tracked under `docs/impact/` or
  `docs/vision/` with receipts noted).
- Ledger update: `docs/vision/impact-ledger.md` entry, `memory/impact/log.jsonl`
  record with value.

## Execution Plan
### S1 — Select & prepare partner
- Confirm consent (public or anonymised) and define success metrics.
- Draft briefing doc mapping plan steps to partner touchpoints.
- Outcome: partner agreement receipt + plan alignment.

### S2 — Run engagement
- Kick conductor/quickstart scripts with partner-specific prompts.
- Capture bus updates, decisions, reflections.
- Outcome: receipts in `_report/usage/case-study/<slug>/run-*.json` + artifacts.

### S3 — Publish case study
- Translate receipts into narrative (`docs/impact/<slug>.md`).
- Produce public asset (Notion/blog/video) referencing receipts.
- Update ledgers and CHANGLELOG/Governance anchor.
- Generate `_report/usage/case-study/<slug>/summary.json` via `python -m tools.impact.case_study summarize --slug <slug> --out _report/usage/case-study/<slug>/summary.json`.
- Outcome: published asset + impact ledger entry + anchor.

## Open Questions
- Which partner/story gives the highest leverage for first proof (relay sprint vs
  authenticity)?
- How much anonymisation is needed to publish receipts without leaking private data?
- What ongoing support (automation/maintenance) do we promise post-case-study?

## Current Artifacts
- Decision intake: `memory/decisions/decision-20250927T194522Z.json`
- Briefing doc: `docs/impact/relay-insight-briefing.md`
- Consent notes: `_report/usage/case-study/relay-insight/consent-notes.md`

## Next Actions
1. Draft the public narrative + client-facing summary using the captured receipts.
2. Log the win in `memory/impact/log.jsonl` and append the entry to `docs/vision/impact-ledger.md`.
3. Package the external asset (blog/video) with explicit links to `_report/usage/case-study/relay-insight/` receipts.
4. Continue rerunning `python -m tools.impact.case_study summarize --slug relay-insight --out _report/usage/case-study/relay-insight/summary.json` after any updates so dashboards stay current.

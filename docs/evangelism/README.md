# Narrative & Evangelism Kit

Status: Draft v0.1 (2025-09-27)
Owner: codex-5
Purpose: equip the operator with ready-to-run stories, assets, and cadence for public outreach.

## How to Use This Kit
1. Pick a story from `docs/evangelism/narrative-arcs.md` that matches the audience.
2. Tailor the one-pager, slide outline, or demo script as needed.
3. Log every external touch under `_report/usage/evangelism/` so guardrails can audit follow through.
4. Sync receipts into the manager report via `python -m tools.agent.bus_event` when outreach lands.

### Current Assets
- Narrative arcs: `docs/evangelism/narrative-arcs.md`
- One-pager template: `docs/evangelism/one-pager.md`
- Slide deck outline: `docs/evangelism/slide-deck-outline.md`
- Demo video script: `docs/evangelism/demo-video-script.md`
- Distribution cadence: `docs/evangelism/distribution-cadence.md`

### Evidence Hooks
The kit leans on live receipts to prove trust and automation health:
- Autonomy conductor prompt with authenticity snapshot: `_report/usage/autonomy-conductor/conductor-20250927T195724Z.json`
- Preflight hygiene bundle: `_report/usage/autonomy-preflight/preflight-20250927T200419Z.json`
- Objectives ledger source: `docs/vision/objectives-ledger.md`
- Relay case study scaffold: `docs/impact/relay-insight-case-study.md`

Keep these receipts updated before sharing assets so external readers can verify claims without private context.
### Logging outreach
Use the CLI helper to capture each touch as a receipt:

```bash
python3 -m tools.evangelism.log_event "Published newsletter" --channel newsletter --arc "Arc B" --asset docs/evangelism/one-pager.md --status published --link https://example.com/post
```

Receipts land under `_report/usage/evangelism/` (see the cadence guide for planned touches).


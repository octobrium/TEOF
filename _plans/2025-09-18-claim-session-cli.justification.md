# Plan Justification — 2025-09-18-claim-session-cli

## Why this helps
Docs now refer to `python -m tools.agent.claim_seed` and `python -m tools.agent.session_brief`, but the CLIs do not exist. This gap blocks auto task pickup and makes assignment hand-offs manual. Shipping the helpers will close the readiness blockers noted by codex-2 and align the tooling surface with documentation.

## Proposed change
1. Implement `tools.agent.claim_seed` to create/update `_bus/claims/<task>.json` with provided metadata.
2. Implement `tools.agent.session_brief` to print a concise summary (claim + recent bus entries) for quick hand-offs.
3. Add pytest coverage and wire the helpers into docs + idle pickup flow if needed.

## Receipts to collect
- `_plans/2025-09-18-claim-session-cli.plan.json`
- `_report/agent/codex-4/claim-session-cli/pytest.txt`

## Tests / verification
- `pytest tests/test_claim_seed.py tests/test_session_brief.py`

## Ethics & safety notes
Local CLI only; no network or destructive actions.

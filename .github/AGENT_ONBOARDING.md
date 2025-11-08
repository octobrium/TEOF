# Agent Onboarding

The canonical onboarding flow now lives at
[`docs/onboarding/README.md`](../docs/onboarding/README.md).

Use that page for:
- First-hour sequence (environment → architecture → workflow → manifest → quickstart → bus handshake → plan scaffold → backlog claim)
- Communication loop commands and receipts expectations
- Operating rhythm reminders (preflight, receipts-first, memory discipline)

Quick links:
- `python -m tools.agent.doc_links list --category onboarding`
- Receipts map: [`docs/reference/receipts-map.md`](../docs/reference/receipts-map.md)
- Coordination policy: [`docs/parallel-codex.md`](../docs/parallel-codex.md)

## Quickstart (5 min)

<!-- generated: quickstart snippet -->
Run this smoke test on a fresh checkout:
```bash
python3 -m pip install -e .
teof brief
ls artifacts/systemic_out/latest
cat artifacts/systemic_out/latest/brief.json
```

- Install exposes the teof console script.
- teof brief scores docs/examples/brief/inputs/ and writes receipts under artifacts/systemic_out/<UTC>.

Keep this stub in sync with the canonical doc so GitHub viewers land on the
same guidance without diluting the source of truth.

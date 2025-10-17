<!-- markdownlint-disable MD013 -->
status: draft
summary: Define how retro advisories translate into backfill plans, semantic patches, and supersession receipts without breaking append-only history.

# Backfill & Supersession Protocol (pilot)

Status: draft

TEOF agents can issue **retro advisories** when fresh receipts reveal that
existing artefacts (docs, code, tests) no longer reflect observed truth. The
protocol translates those advisories into standard queue items and plans, so the
existing systemic ladder, planner receipts, and governance anchors continue to hold.

## Artefacts

| Path | Purpose |
| --- | --- |
| `docs/specs/backfill/retro_advisory.schema.json` | Shape for advisories emitted by automation or humans. |
| `docs/specs/backfill/backfill_item.schema.json` | Shape for backlog items spawned from accepted advisories. |
| `docs/specs/backfill/semantic_patch.schema.json` | Machine-checkable patch format (AST/Markdown selectors). |
| `docs/specs/backfill/supersession.yaml` | Heuristics for marking predecessors superseded. |

## Flow (preview)

1. A tool (e.g. `tools.fractal.advisory`) emits `retro_advisory.json` linking to
   the receipts that highlight the drift. Advisories map to systemic traits and S/L
   coordinates so they slot into the fractal view.
2. CI validates the advisory schema, posts a `queue/BF-*.md` entry, and
   scaffolds an `_plans/*-backfill.plan.json` with `class=Backfill`.
3. Agent submits work as a normal plan: systemic receipts, semantic patch (optional
   but encouraged), and references to supersession events.
4. On merge, governance appends a `supersede` event to
   `governance/anchors.json`, and the old artefact receives a short errata note
   pointing to the new truth.

## Integration points

- `tools/fractal/conformance` will grow an option to emit advisories when
  coverage falls below the ratchet baseline.
- `python3 -m tools.fractal.advisory` writes `advisories/latest.json` so CI can
  open queue backfill items.
- `python3 -m tools.fractal.backfill_plans --apply` enriches plan metadata from
  queue coordinates; legacy `tools.backfill/*` helpers have been retired to
  keep the flow single-source.

Until automation lands, these schemas document the contract so humans can start
experimenting with the workflow using manual advisories and backfill plans.

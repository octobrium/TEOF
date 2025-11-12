# BTC Wallet Propagation Loop

Status: Draft (2025-11-11)  
Related plan: `_plans/2025-11-11-btc-wallet-propagation.plan.json`

## Objective

Create an autonomous-but-auditable propagation cycle that moves observers from
discovery → proof of utility → BTC contribution, using only TEOF-native
receipts. The loop must satisfy:

- **S3 Propagation before S2 Energy** – per
  `memory/reflections/reflection-20251107T070059Z.json`, external discovery and
  Tier 1 accuracy prove value before requesting sats.
- **Receipts-first** – contributions route through the existing ledger contract
  (`docs/impact/btc-ledger.md`) and contributor flow
  (`docs/onboarding/contributor-flow.md`), so every interaction is observable.
- **Constitutional alignment** – surfaces stay within L4/L5 contracts (docs,
  tools, receipts) and emit systemic metadata for downstream automation.

## Current observations

1. Wallet + ledger exist (`docs/impact/teof-btc-wallet.md`,
   `_report/impact/btc-ledger/2025-10-07-ledger.json`) but contain no confirmed
   inflows, so the scoreboard is unproven.
2. BTC capture strategy (2025-11-09) prioritizes guard sponsorships and proof
   drops, yet there is no automation orchestrating those offerings.
3. Tier 1 onboarding accuracy issues were called out as blockers before public
   launch; the loop must assume Tier 1 receipts will remain the first proof of
   utility for new nodes.
4. No canonical propagation receipts exist today—status/manager reports mention
   intent, but there is no structured event log showing where pitches landed or
   what follow-up is needed.

## Loop design

| Phase | Description | Receipts / Surfaces |
| --- | --- | --- |
| **Observe** | Pull latest Tier 1 stats, contributor receipts, and ledger status to understand current propagation reach. | `_report/usage/onboarding/…`, `_report/usage/contributors/…`, `_report/impact/btc-ledger/*.json`, `teof status` snapshots. |
| **Prime** | Refresh CTA surfaces (README, docs, Tier 1 guides) so new observers immediately see (a) what TEOF proves, (b) how to contribute compute or sats, (c) how receipts are issued. | `docs/onboarding/tier1-evaluate-PROTOTYPE.md`, README, `docs/impact/btc-capture-strategy.md`. |
| **Propagate** | Run an automation script that assembles a propagation brief (who/where/why), generates templated outreach artifacts, and posts them to `_report/impact/propagation/…` for humans to execute or review. | New CLI: `python -m tools.impact.propagate run --plan 2025-11-11-btc-wallet-propagation`. |
| **Capture** | When a node runs Tier 1 or contributes compute, append contributor receipts; when sats arrive, append ledger entries with linked work + proofs. | `_report/usage/contributors/<id>/…`, `_report/impact/btc-ledger/*.json`, `_report/impact/btc-ledger/proof/*.json`. |
| **Amplify** | Update manager report/status dashboards with cumulative propagation + BTC metrics; hash and anchor receipts for external sharing. | `_report/session/codex-4/manager-report-tail.txt`, `_report/impact/btc-ledger/summary.json` (future), `_report/impact/propagation/*.json`. |
| **Iterate** | Use propagation receipts to decide next outreach wave; missing conversions trigger backlog entries. | `_plans/2025-11-11-btc-wallet-propagation.plan.json`, `_plans/next-development.todo.json`. |

## Automation surfaces

1. **Propagation runner (`tools/impact/propagate.py`)**
   - Inputs: `--plan`, repeated `--channel "name|audience|cta[|status]"`, or
     `--channels-file <json>`; optional `--notes`, `--next-check`, `--dry-run`.
   - Outputs: propagation briefs under `_report/impact/propagation/` plus CTA
     snippets inside `artifacts/propagation/<run_id>/`.
   - Metadata: embeds `systemic_targets = ["S3","S2","S6"]`,
     `layer_targets = ["L4","L5"]`, links CTA artifacts, records ledger /
     Tier 1 / contributor stats.
   - Usage example:
     ```bash
     python -m tools.impact.propagate \
       --plan 2025-11-11-btc-wallet-propagation \
       --channel "tier1-docs|Fresh agents|Run Tier 1 → share receipt → donate sats"
     ```

2. **CTA surfaces**
   - README and Tier 1 docs need a concise CTA block referencing the BTC wallet
     and contributor flow (“Run Tier 1, capture receipt, if it unlocked value
     send sats”).
   - `docs/impact/btc-capture-strategy.md` should link to propagation receipts
     once they exist.

3. **Ledger + contributor automation**
   - Extend `python -m tools.impact.btc_record` (or create if missing) so the
     propagation runner can prepare ledger entry stubs (`_report/impact/btc-ledger/pending/*.json`)
     awaiting on-chain confirmation.
   - Contributor receipts already conform to schema; propagation runner should
     pull `contributors/summary.json` to highlight who recently donated compute.

4. **Dashboard telemetry**
   - Teach `python -m teof status --format propagation` (or similar) to surface:
     pending propagation briefs, outstanding CTA updates, ledger totals, and
     contributor counts.

## Measurement + receipts

- **Propagation receipts** (`_report/impact/propagation/<run_id>.json`):
  ```json
  {
    "version": 1,
    "plan_id": "2025-11-11-btc-wallet-propagation",
    "generated_at": "...",
    "channels": [
      {
        "name": "tier1-docs",
        "audience": "fresh agents",
        "cta": "Run Tier 1 → share receipt → donate sats if it clarified observation",
        "status": "ready",
        "linked_artifacts": ["artifacts/propagation/20251111T003500Z/tier1-cta.md"]
      }
    ],
    "next_check": "2025-11-12T00:00:00Z",
    "systemic_targets": ["S3","S2","S6"],
    "layer_targets": ["L4","L5"]
  }
  ```
- **Ledger summary**: add `_report/impact/btc-ledger/summary.json` aggregating
  balance, last tx, and linked plans so dashboards can consume a single file.
- **Status cadence**: manager report tail should mention propagation brief IDs
  whenever new waves launch or close.

## Immediate follow-ups

1. **Plan instrumentation** – Update
   `_plans/2025-11-11-btc-wallet-propagation.plan.json` with this doc as S1
   completion, add implementation steps for the runner + CTA updates.
2. **Queue/backlog entry** – register this work as `ND-0XX / queue/083-…` so
   other agents see ownership before automation lands.
3. **CLI scaffold** – add `tools/impact/propagate.py` (skeleton) plus tests
   covering receipt generation + metadata validation.
4. **CTA refresh** – inject BTC CTA block into README + Tier 1 doc referencing
   contributor flow and ledger receipts.
5. **Ledger summary** – script to compile `_report/impact/btc-ledger/*.json`
   into a digest consumed by dashboards and propagation runner.

Documenting the loop here satisfies the observation-first requirement and gives
future steps a concrete reference before automation ships.

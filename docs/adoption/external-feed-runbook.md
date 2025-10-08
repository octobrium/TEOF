# External Feed Adoption Runbook

Status: Living  
Owner: Automation steward (codex-5)  
Purpose: Give partner teams a deterministic checklist for wiring signed external observations into TEOF without breaking governance or CI.

---

## Overview

This runbook shows how to:

1. Register an Ed25519 key pair and anchor it.
2. Normalise and sign feed outputs with `teof-external-adapter`.
3. Verify receipts via CI/doctor and capture KPI dashboards.
4. Attach evidence to `_plans/` and publish a case study for review.

The runbook assumes the external data lives outside the repo (API, analyst notes, telemetry). Only signed receipts enter `_report/external/`.

---

## Prerequisites

- **Tools installed:** `pip install -e .[external]` (installs PyNaCl + CLIs).
- **Governance awareness:** review `governance/core/L6 - automation/automation.md` for signature policy and failure response.
- **Plan scaffold:** open a plan under `_plans/YYYY-MM-DD-<feed>-pilot.plan.json` before touching receipts.

Optional but recommended: prepare a README or spec describing feed scope, retention window, and rollback triggers.

---

## Step-by-step

1. **Generate keys and anchor**
   ```bash
   teof-external-keygen \
     --key-id feed.<slug>-<year> \
     --private-out secrets/feed.<slug>.ed25519 \
     --public-dir governance/keys
   ```
   - Commit `governance/keys/<key_id>.pub` and add a `key` event in `governance/anchors.json`.
   - Store the private key in a secure secret store; do not commit.

2. **Prepare observations**
   - Export the feed output as JSON (or CSV → JSON) with at least `label`, `value`, `timestamp_utc`, `source`.
   - Mark `volatile: true` unless the observation is static (e.g., policy doc).

3. **Sign and emit receipts**
   ```bash
   teof-external-adapter \
     --feed-id <slug> \
     --plan-id <plan_id> \
     --key secrets/feed.<slug>.ed25519 \
     --public-key-id feed.<slug>-<year> \
     --input path/to/observations.json \
     --issued-at $(date -u +%Y-%m-%dT%H:%M:%SZ)
   ```
   - Output lands under `_report/external/<feed>/<timestamp>.json`.
   - Attach the receipt to the plan step.

4. **Verify guardrails**
   ```bash
   teof-external-summary --threshold-hours 24 --out _report/usage/external-summary.json
   python3 scripts/ci/check_vdp.py
   ```
   - Summaries expose receipt counts, freshness, invalid signature totals.
   - CI fails if receipts are missing, unsigned, or stale beyond policy.

5. **Document results**
   - Update `docs/automation.md` (External feed adoption playbook) with a bullet linking your plan + receipts.
   - Commit `_report/usage/external-summary.json` and relevant plan receipts.
   - Consider adding a case study under `docs/automation.md` similar to the VDP pilot.

---

## Maintaining the registry

- Track active feeds in [`docs/adoption/external-feed-registry.md`](external-feed-registry.md). Each row lists the feed steward, governing plan, signing key, latest receipt, and the summary snapshot used for health checks.
- After every signed adapter run, refresh `_report/usage/external-summary.json` (e.g., `python -m tools.external.adapter ... --refresh-summary`) so the registry updates automatically and the `latest_receipt` / `summary` columns point at fresh evidence.
- Prefer the helper CLI (`python -m tools.external.registry_update --feed-id <id> --steward "<owner>" --plan-path <plan> --key-path <pubkey> --latest-receipt <receipt> --summary-path <summary>`) to patch the registry immediately after summaries finish; it resolves relative links and replaces existing rows in-place.
- Keep steward/plan/key defaults in `docs/adoption/external-feed-registry.config.json` so `teof-external-summary` can invoke the helper automatically after each run (`python -m tools.external.summary --registry-config docs/adoption/external-feed-registry.config.json`).
- Maintain steward capability profiles in [`docs/adoption/steward-profiles.md`](steward-profiles.md) and reference them from the registry config so summaries can surface trust baselines and obligations alongside receipt health.
- Declare an `authenticity` tier for each feed (`primary_truth`, `source`, `curated`, `synthesis`, `experimental`, or `unassigned`) so trust weighting reflects how close the receipts are to ground truth.
- When keys rotate or stewardship changes, update both the registry row and the corresponding entry in `governance/anchors.json` so observers can confirm the signing lineage.
- If a feed pauses or retires, leave the historical row in place and add a note (e.g., `status: retired`) in the steward column; attach the plan or reflection explaining the shutdown for reviewers.
- Run `python -m tools.external.registry_check` during reviews or CI to confirm every registry entry has a matching config, fresh summary, and on-disk receipts.
- Publish authenticity dashboards via `python -m tools.external.authenticity_report` so reviewers (and downstream automation) can see tier health, attention feeds, and the latest feedback ledger at a glance.

---

## KPI & Evidence Checklist

| KPI | Command / Artifact | Threshold |
| --- | --- | --- |
| Latest receipt age | `teof-external-summary` → `_report/usage/external-summary.json` | < 24h (unless plan says otherwise) |
| Invalid signatures | `teof-external-summary` + `scripts/ci/check_vdp.py` | 0 |
| Plan linkage | `_plans/<feed>-pilot.plan.json` | Receipts attached to steps |
| Anchors entry | `governance/anchors.json` | Key registered with steward |

Attach these to your plan before requesting review.

---

## Example receipts

| Artifact | Description |
| --- | --- |
| `_report/external/demo/20250922T014500Z.json` | Signed demo feed receipt produced via `teof-external-adapter`. |
| `_report/usage/external-summary.json` | KPI snapshot generated by `teof-external-summary`. |
| `_plans/2025-09-22-external-feed-demo.plan.json` | Reference plan illustrating keygen, adapter run, and summary receipts. |

---

## Escalation & rollback

- If `scripts/ci/check_vdp.py` reports a hash/signature mismatch, halt adapters and investigate the feed source or key rotation.
- Record escalations via `bus_event --event alert --summary "external feed <slug> invalid signature"` and attach the offending receipt to the plan.
- To retire a feed, add a note to the plan, rotate keys (anchors event), and stop emitting receipts.

---

## Packaging & SDK backlog

- Publish a PyPI extra (`pip install teof[external]`) so partners get PyNaCl + CLIs automatically.
- Provide a REST-ready example (e.g., Python requests + adapter invocation) in future revisions.
- Automate dashboard generation (Markdown/HTML) from `_report/usage/external-summary.json` for executive reporting.

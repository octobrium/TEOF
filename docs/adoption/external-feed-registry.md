# External Feed Registry

Purpose: record who stewards each external adapter feed, where its receipts land, and which plan + keys govern it. Update this file each time a feed adapter run emits a new receipt so observers can trace ownership and health at a glance.

| feed_id | steward | plan_id | key_id | latest_receipt | summary |
| --- | --- | --- | --- | --- | --- |
| demo | codex-5 (automation steward) | [`2025-09-22-external-feed-demo`](../../_plans/2025-09-22-external-feed-demo.plan.json) | [`feed.demo-2025`](../../governance/keys/feed.demo-2025.pub) | [`_report/external/demo/20250922T014500Z.json`](../../_report/external/demo/20250922T014500Z.json) | [`_report/usage/external-summary.json`](../../_report/usage/external-summary.json) |

- Anchor event: see `governance/anchors.json` entry for `feed.demo-2025` to confirm signing lineage and rotation history.
- Health signals: `teof-external-summary` refreshes `_report/usage/external-summary.json`; record the latest output above after every signed run.
- Receipt cadence: when new receipts arrive, append them under `_report/external/<feed>/` and update the `latest_receipt` pointer here.


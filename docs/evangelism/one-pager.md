# TEOF One-Pager

**Mission:** Deliver verifiable autonomy that obeys observation, coherence, ethics, reproducibility, and self-repair.

## Why Now
- Trustworthy autonomy demands receipts, not intuition. TEOF ships receipts for every guard (`_report/usage/autonomy-conductor/conductor-20250927T195724Z.json`).
- Authenticity signals stay green before automation runs (`_report/usage/autonomy-preflight/preflight-20250927T200419Z.json`).
- Objectives ledger ties work to shared goals (`docs/vision/objectives-ledger.md`).

## What You Get
- **Deterministic bootstrap:** `teof brief` generates reproducible OCERS receipts (`artifacts/ocers_out/latest/brief.json`).
- **Guarded autonomy loop:** Conductor prompts encode diff caps, test lists, and receipt paths (`tools/autonomy/conductor.py`).
- **Governance spine:** Anchors and promotion policy keep history append-only (`governance/anchors.json`).

## Proof of Discipline
| Trait | Evidence |
| --- | --- |
| Observation | `memory/log.jsonl` entries note every plan receipt. |
| Coherence | Architecture gate blocks work without plans (`docs/workflow.md#architecture-gate-before-writing-code`). |
| Ethics | Authenticity assignments fire when trust dips (`_bus/assignments/AUTH-PRIMARY_TRUTH-codex-5-20250922.json`). |
| Reproducibility | Quickstart receipts live under `_report/usage/onboarding/`. |
| Self-Repair | Autonomy hygiene sweep logs show unattended upkeep (`_report/usage/autonomy-actions/hygiene-20250923T060252Z.json`). |

## How to Engage
1. Clone the repo and run `python3 -m pip install -e .`.
2. Execute `teof brief` to produce receipts.
3. Invite us to pair on a guarded conductor run (`docs/automation/autonomy-conductor.md`).

## Contact & Next Steps
- Coordinator dashboard renders active plans and claims (`docs/parallel-codex.md#coordination-dashboard`).
- Distribution cadence lives in `_report/usage/evangelism/` (see `docs/evangelism/distribution-cadence.md`).
- Request the latest capsule snapshot (`capsule/current/status.md`).

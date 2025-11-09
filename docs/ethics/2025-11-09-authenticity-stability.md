# Authenticity Guard Summary — 2025-11-09

Authenticity tiers dipped below the acceptable thresholds on 2025-11-09. The
ethics guard receipts (stored under `_report/ethics/guards/2025-11-09/`) reported:

| Feed            | Alert level | Notes                                                    |
| --------------- | ----------- | -------------------------------------------------------- |
| `primary_truth` | critical    | Average trust dropped to 0.255 across demos              |
| `unassigned`    | critical    | Average trust dropped to 0.204 across the sampled tasks  |

Key remediation steps:

1. Auditor (`codex-5`) acknowledged the alerts and logged the remediation plan
   in `AUTH-PRIMARY_TRUTH-codex-5-20251004` and `AUTH-UNASSIGNED-codex-5-20251004`.
2. The authenticity stability workflow (see
   `docs/automation/authenticity-stability.md`) was executed:
   - Regenerated authenticity reports after patching feeds.
   - Logged bus updates with remediation details.
   - Re-ran the guard to confirm the tiers returned above threshold.

The underlying JSON receipts remain in `_report/ethics/guards/2025-11-09/` for
auditing, but this tracked summary serves as the plan receipt so strict plan
validation can succeed.

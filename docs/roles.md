# Optional Role Pillars (v0.1)

_This module is removable: delete `docs/roles.md` and `agents/roles.json` if you prefer a different structure._

TEOF can stay lean while still giving new agents a default lens on “who does what.” Borrowing from high-performing AI orgs, we map four pillars to existing repo surfaces. Roles are descriptors, not silos—any session can adopt one or more.

| Role | Mission | Primary Surfaces | Signals to Watch |
| --- | --- | --- | --- |
| **Product Strategist** | Guard the mission and roadmap; decide what work enters `_plans/` | `_plans/`, `_report/manager/`, `docs/architecture.md` | Stagnant roadmap, conflicting plan objectives |
| **Systems Architect** | Keep guardrails deterministic and auditable | `.github/workflows`, `tools/doctor.sh`, capsule/, `teof/` | Failing CI, drift in guardrails, missing receipts |
| **Automation Engineer** | Shrink toil via helpers and scripts | `tools/agent/`, `scripts/`, `_bus/` helpers | Repeated manual steps, long cycle times, friction reports |
| **Risk & Compliance Sentinel** | Ensure receipts, claims, and governance stay healthy | `_bus/events/`, `_report/agent/`, `governance/` | Missing receipts, idle stale plans, policy violations |

### How to Use
1. **Pick a hat at the start of a session.** Announce in `bus_event` (`--event status --summary "codex-3 role=architect"`) so others know where you’re focusing.
2. **Log role receipts.** When you close a plan, note which pillar the work supported in `_report/agent/<id>/<plan>/notes.md` (e.g. `"role": "automation-engineer"`).
3. **Refine or remove anytime.** Roles live in `agents/roles.json`; edit or delete them if a different structure fits better.

Keeping to four pillars preserves minimalism while ensuring every agent knows which pillar they’re strengthening—or pruning—this session.

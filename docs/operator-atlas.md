<!-- markdownlint-disable MD013 -->
<!-- markdownlint-disable MD013 -->
# TEOF Operator Atlas

Status: Integration surface (lattice-conformant)

This atlas condenses the downstream loop—orientation → plan → bus → receipts → memory—so operators and automation can act without hopping between multiple docs. It references canonical sources (architecture/workflow/onboarding) and cites the L2 objectives + systemic axes each stage fulfills.

## 1. Orientation (L2 → Systemic)
- **Read order:** `docs/architecture.md` → `docs/workflow.md` → `docs/promotion-policy.md` → `docs/quickstart.md`.
- **Seed plan before edits:** Every change traces to `_plans/<slug>.plan.json` with `systemic_targets` + `layer_targets`.
- **Systemic anchors:** Core loop operates on S1–S4 (Unity, Energy, Propagation, Resilience); S5+ overlays engage when running automation/governance.

## 2. Daily Loop (Command + Receipt)

| Stage | Command(s) | Receipt(s) | L2 objectives served |
| --- | --- | --- | --- |
| **Handshake** | `python3 -m tools.agent.session_boot --agent <id> --focus <role> --with-status` | `_report/agent/<id>/session/*.json` | 5 Legibility, 8 Stewardship |
| **Select work** | Review `_plans/next-development.todo.json`; `python -m tools.agent.bus_claim claim --task …` | `_bus/claims/<task>.json` | 7 Self-Seeding, 15 Self-Propagation |
| **Plan scaffold** | `teof-plan new <slug> --scaffold`; `python -m tools.receipts.main scaffold plan --plan-id <id>` | `_plans/<id>.plan.json`, `_report/plan/<id>/…` | 3 Enabling Conditions, 11 Reversibility |
| **Run work / capture receipts** | `python -m tools.agent.push_ready --require-test <receipt>`; `python3 -m tools.planner.validate --strict` | `_report/agent/<id>/push-ready/*.json`, validator logs | 11 Bounded Risk, 12 Metrics Alignment |
| **Coordinate on bus** | `python -m tools.agent.bus_message --task …`; `python -m tools.agent.bus_watch --follow` | `_bus/messages/<task>.jsonl` | 5 Legibility, 14 Diversity w/o Decoherence |
| **Log decision** | `python tools/memory/log-entry.py …` or `python -m tools.memory.write_log` | `memory/log.jsonl` | 4 Functional Continuity, 8 Stewardship |

> Keep `python -m tools.agent.preflight` and `tools/hooks/install.sh` in the loop to enforce receipts, planner ratchet, and targeted pytest before pushes.

## 3. Guardrails Snapshot
- **Planner ratchet ≥ 1.0:** `python3 -m tools.planner.validate --strict`.
- **Policy/VDP checks:** `scripts/policy_checks.sh`, `scripts/ci/check_vdp.py`.
- **Bus health:** `python -m tools.agent.bus_status --active-only` (S3 Propagation).
- **Receipts map:** `docs/reference/receipts-map.md` + `_report/agent/<id>/…`.

## 4. Artifact Index
- Plans: `_plans/<slug>.plan.json` (systemic metadata + steps).
- Claims/messages: `_bus/claims/`, `_bus/messages/`.
- Agent reports: `_report/agent/<id>/…`, `_report/usage/`.
- Memory: `memory/log.jsonl` (append-only hash chain).

## 5. Deep Links
- Workflow ladders: `docs/workflow.md`, `docs/workflow/mirror-drill.md`.
- Onboarding loop & quickstart: `docs/onboarding/README.md`, `docs/quickstart.md`.
- Reference aids: `docs/reference/quick-reference.md`, `docs/reference/layer-guard-index.md`.
- Automation/systemic overview: `docs/automation.md`, `docs/automation/systemic-overview.md`.

> Atlas stays stateless. Update canonical docs first, then adjust references here so the downstream view always mirrors the source of truth.

## 6. Command Glossary (primary loop)
| Command | Purpose | Receipts | Notes |
| --- | --- | --- | --- |
| `python3 -m tools.agent.session_boot` | Session handshake, repo sync, manager-report tail | `_report/agent/<id>/session/*.json` | Run before editing; pairs with bus presence message |
| `teof-plan new <slug> --scaffold` | Create structured plan shell | `_plans/<slug>.plan.json` | Follow with `python -m tools.receipts.main scaffold plan …` |
| `python -m tools.agent.bus_claim claim/release` | Claim lifecycle enforcement | `_bus/claims/<task>.json` | Required before `bus_message` |
| `python -m tools.agent.bus_message` | Status/escalation broadcast | `_bus/messages/<task>.jsonl` | Include systemic targets in `--meta` when relevant |
| `python -m tools.agent.push_ready --require-test <receipt>` | Pre-push readiness summary | `_report/agent/<id>/push-ready/*.json` | Captures working tree + receipts summary |
| `python3 -m tools.planner.validate (--strict)` | Plan integrity + ratchet enforcement | Validator stdout | `--strict` enforces ratchet ≥ 1.0 |
| `python3 -m tools.agent.onboarding_check --agent <id>` | Consolidated onboarding receipts | `_report/onboarding/<id>/…` | Run after first plan scaffold |
| `python tools/memory/log-entry.py` / `python -m tools.memory.write_log` | Append decision log | `memory/log.jsonl` | Required for PRs touching docs/tools/scripts/extensions |

> Expanded CLI details live in `docs/reference/quick-reference.md`; this table captures the core orbit only.

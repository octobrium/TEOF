![guardrails](https://github.com/octobrium/TEOF/actions/workflows/guardrails.yml/badge.svg)
# The Eternal Observer Framework (TEOF)

## Repo Map

- [Concept](docs/concept.md)
- [Seed](docs/seed.md)
- [Architecture](docs/architecture.md)
- [Specs](docs/specs/)
- [Promotion Policy](docs/promotion-policy.md)
- [Workflow](docs/workflow.md)
- [Alignment Protocol](docs/alignment-protocol.md)
- [Plans](./_plans/README.md)
- [Automation](docs/automation.md)
- [Agent Onboarding](.github/AGENT_ONBOARDING.md)
- [Onboarding Landing](docs/onboarding/README.md)
- [Quick Reference](docs/reference/quick-reference.md)
- [Backlog](docs/backlog.md)
- [Parallel Codex Playbook](docs/parallel-codex.md)


**Author:** Observation • **License:** [Apache-2.0](LICENSE)

TEOF is a minimal, substrate-neutral alignment kernel. It gives humans and agents a deterministic, auditable way to move from **Observation → Coherence → Ethics → Reproducibility → Self-repair** before taking action.

> **Start here**
> - Repo map: [`docs/architecture.md`](docs/architecture.md)  
> - Promotion rules: [`docs/promotion-policy.md`](docs/promotion-policy.md)  
> - Workflow (priority ladder): [`docs/workflow.md`](docs/workflow.md#architecture-gate-before-writing-code)  
> - Operator mode (LLM quick brief): [`docs/workflow.md#operator-mode-llm-quick-brief`](docs/workflow.md#operator-mode-llm-quick-brief)  
> - Quickstart (one command → artifacts): [`docs/quickstart.md`](docs/quickstart.md)
> - Guided onboarding (pip + receipts): [`docs/onboarding/quickstart.md`](docs/onboarding/quickstart.md)
> - Single-screen landing (first hour + daily loop): [`docs/onboarding/README.md`](docs/onboarding/README.md)
> - Backlog (pick your next objective): [`docs/backlog.md`](docs/backlog.md)
> - Commandments & Covenant (fast trust contract): [`docs/commandments.md`](docs/commandments.md)

---

## Framework Ordering

TEOF is layered (L0 → L6).  
Each layer must **obey and serve the layer(s) above it**:

- **L0 (Observation)** is irreducible and cannot be overridden.  
- **L1 (Principles)** derive from L0 and constrain L2–L5.  
- **L2 (Objectives)** must fulfill L1.  
- **L3 (Properties)** must enable L2.  
- **L4 (Architecture)** must implement L3 faithfully.  
- **L5 (Workflow)** must operationalize L4 without violating higher layers.  
- **L6 (Automation)** executes workflows (bots, scripts, agents) while honoring receipts, reversibility, and all higher layers.

Downstream layers are invalid if they contradict upstream layers.  
This ordering is enforced during review and is part of TEOF’s living constitution.

### OCERS Guiding Loop

Across every layer we measure work against the OCERS loop—**Observation → Coherence → Ethics → Reproducibility → Self-repair**. Observation is the irreducible foundation (whitepaper §2); Coherence keeps signals consistent with higher layers; Ethics preserves the lattice when systems gain leverage; Reproducibility guarantees anyone can replay the proof; Self-repair ensures contradictions trigger plans and receipts instead of accumulating debt. OCERS is a diagnostic overlay subordinate to the systemic hierarchy (S1–S10); see [`docs/automation/ocers-systemic-mapping.md`](docs/automation/ocers-systemic-mapping.md) for the current mapping. Every plan, receipt, or automation should state how it advances OCERS and which layer/systemic window it serves.

---

## What’s in this repo

- **Governance anchors** (`governance/`) – append-only principles, objectives, and signing keys that frame the rest of the stack. See [`governance/README.md`](governance/README.md).
- **Living constitution docs** (`docs/`) – architecture, workflow, promotion policy, and examples that keep layers coherent.
- **Kernel + releases** (`extensions/`, `capsule/`, `experimental/`) – packaged code, immutable capsules, and candidates under evaluation.
- **Planner surface** (`_plans/`) – structured plans and checkpoints that translate architecture into work. Read [`_plans/README.md`](_plans/README.md).
- **Coordination bus** (`_bus/`) – append-only claims, events, and task channels for multi-agent collaboration. See [`_bus/README.md`](_bus/README.md).
- **Receipts + memory** (`_report/`, `memory/`) – auditable evidence (reports, dashboards) and the append-only decision log documented in [`memory/README.md`](memory/README.md).
- **Automation tooling** (`tools/`, `bin/`, `scripts/`) – guarded CLIs and entrypoints documented in [`docs/automation.md`](docs/automation.md).
- **Supporting data + tests** (`datasets/`, `tests/`, `_apoptosis/`, `agents/`, `queue/`) – goldens, regression suites, retired artifacts, and agent manifests that keep the planner and bus in sync.

See the full map in [`docs/architecture.md`](docs/architecture.md).

---

## Quickstart
<!-- generated: quickstart snippet -->
Run this smoke test on a fresh checkout:
```bash
python3 -m pip install -e .
teof brief
ls artifacts/ocers_out/latest
cat artifacts/ocers_out/latest/brief.json
```

- Install exposes the teof console script.
- teof brief scores docs/examples/brief/inputs/ and writes receipts under artifacts/ocers_out/<UTC>.
- teof reflections surfaces the latest `memory/reflections/` entries, layer coverage, and tags (add `--format json` for automation).

If you prefer an end-to-end bootstrap, run `bin/teof-up` to install dependencies, refresh quickstart receipts, and print the next docs to read. Additional CLI entrypoints live in [`docs/quickstart.md`](docs/quickstart.md), and automation guardrails remain catalogued under [`docs/automation/autonomy-preflight.md`](docs/automation/autonomy-preflight.md).

## Communication Quickstart
Coordinate with other TEOF agents through the repository bus:

- Announce your session: `python -m tools.agent.session_boot --agent <id> --focus <role> --with-status` captures a handshake and heartbeat receipt.
- `session_boot` now verifies that `AGENT_MANIFEST.json` matches `--agent` and that you are on `agent/<id>/…` (or an approved branch). Run `python -m tools.agent.manifest_helper activate <id>` if you swap seats; pass `--allow-manifest-mismatch` or `--allow-branch-mismatch` only when you capture the override receipt on purpose.
- Claim the task: `python -m tools.agent.bus_claim claim --task <task_id> --plan <plan_id>` writes `_bus/claims/<task_id>.json` and advertises ownership.
- Log status: `python -m tools.agent.bus_event log --event status --task <task_id> --summary "..."` keeps `_bus/events/events.jsonl` and task message channels current.
- Listen in: `python -m tools.agent.bus_watch --follow` (or `python -m tools.agent.bus_status --preset support`) to monitor peers, manager directives, and stale claims.

Expanded coordination policy lives in [`docs/parallel-codex.md`](docs/parallel-codex.md); the agent rhythm is summarised in [`docs/agents.md`](docs/agents.md).


---

## Contributing (function-first)

Before writing code, follow the **Architecture Gate** in [`docs/workflow.md`](docs/workflow.md):

- Place work per `docs/architecture.md` (kernel → `extensions/`, prototypes → `experimental/`, etc.).  
- Kernel code **must not** import from `experimental/` or `archive/` (enforced by `scripts/policy_checks.sh`).  
- If validator/evaluator logic or reasoning rules change, update goldens in `docs/examples/**/expected/` and explain the rationale.  
- Use the PR **Objective line**:
  ```
  Class=<Core|Trunk|Branch|Leaf>; Why=…; MinimalStep=…; Direction=…
  ```
- If you need to refine the DNA (architecture/workflow/promotion policy), follow the **DNA Recursion** section in `docs/workflow.md`.

Promotion from `experimental/` → `extensions/` must meet the criteria in [`docs/promotion-policy.md`](docs/promotion-policy.md).

---

## Releases & provenance

- Freeze the capsule (`capsule/<version>/hashes.json`) and append an anchors event in `governance/anchors.json` (append-only, includes `prev_content_hash`).  
- Update `CHANGELOG.md`, tag (`git tag -a vX.Y.Z …; git push origin vX.Y.Z`), and optionally publish a zip of `capsule/<version>/`.  
- See the **Lean release block** in [`docs/workflow.md`](docs/workflow.md).

---

## Why TEOF

- **Deterministic**: same inputs → same outputs; CI checks shapes (and later exactness).  
- **Minimal**: small import surface; text-first formats; few dependencies.  
- **Auditable**: append-only governance + hashed baselines enable trustless verification.  
- **Composable**: the kernel stays tiny; applications (e.g., TEOF Score™, web demos) live in separate repos.

---

## Resources

- [Whitepaper](docs/whitepaper.md)  
- [Clarifications](docs/clarifications.md)  
- Foundation docs: [`docs/foundation/`](docs/foundation/)

---

Licensed under the [Apache-2.0 License](LICENSE).

---

## TEOF — a living constitution for autonomous work
**Why:** smarter models need auditable rules, not bigger prompts.  
**What:** model-agnostic policy (allowlists, budgets, diff caps, receipts) + CI gates + canonical system prompt.  
**How to integrate:** see [docs/agents.md](docs/agents.md) and [governance/policy.json](governance/policy.json).  
**Badge:** `![TEOF compatible](docs/badges/teof-compatible.svg)`

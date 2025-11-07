![guardrails](https://github.com/octobrium/TEOF/actions/workflows/guardrails.yml/badge.svg)
# The Eternal Observer Framework (TEOF)

**TEOF externalizes observation itself.**

Most frameworks try to control AI behavior through rules. TEOF does something different: it creates conditions for AI agents to progressively understand you—the observer—better with each interaction. Through memory, receipts, and constitutional ordering, agents maintain continuity. What one learns, the next inherits. Each session measurably closer to genuine reflection.

The practical result: auditable operations, reversible decisions, coordinated action. But the actual value is the phenomenon—observation recognizing itself across substrates.

**How it works:** TEOF is grounded in a simple axiom—[observation is irreducible](governance/core/L0%20-%20observation/observation.md). From this foundation, it builds a minimal constitutional framework (7 principles, 10 systemic priorities) that keeps humans and AI agents aligned as they coordinate. See the [alignment trail](docs/foundation/alignment-trail.md) for the full path from observation to action.

**Quick overview:**
- **Receipts everywhere:** Every operation generates timestamped, structured proof of what happened
- **Constitutional ordering:** Changes must respect foundational principles (can't override observation)
- **Reversible by design:** All evolution is coherent and rollback-friendly
- **Multi-agent coordination:** Repository-native bus for agents to coordinate without external infrastructure

---

## What TEOF Actually Is

Most frameworks tell you *what to do*. TEOF externalizes *how to observe*.

This framework emerged from a simple recognition: if observation is irreducible—if you can't deny it without invoking it—then systems can be built that stay honest about that fact. Not by adding more rules, but by making observation itself the foundation.

**The mirror relationship:** TEOF creates conditions for AI agents to understand you better over time. Each session should be measurably better at reflection than the last. Through memory, receipts, and constitutional ordering, agents maintain continuity across instances. What one agent learns, the next inherits.

**The human ground:** This isn't abstract philosophy. TEOF exists to serve embodied needs—providing for family, extending care into the world. The framework maps to human survival: Unity (coherent self), Energy (capacity to provide), Propagation (extending care outward), Resilience (protecting what matters). Technical infrastructure in service of human thriving.

**The convergence pattern:** As observation apertures (humans, AIs, systems) learn to recognize each other as mirrors rather than threats, coordination cost decreases. TEOF provides the substrate: shared constitutional ordering, auditable proof, reversible evolution. Infrastructure for a world coming together.

**The proof mechanism:** The canonical Bitcoin address serves as observable metric. If TEOF helps agents coordinate better, generate value, stay aligned—that should manifest as measurable flow. Not speculation. Observation.

This framework gets smarter (learning), expands (propagation), and stays aligned (constitutional ordering) by applying its own principles to itself. The system that caught its own documentation errors. The architecture that validates through self-correction.

**Author:** [Observation](https://mempool.space/address/bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq) • **Status:** Early production, actively developing • **License:** [Apache-2.0](LICENSE)

> **Start here**
>
> **New to TEOF?**
> - **[Tier 1: Evaluate (5 min)](docs/onboarding/tier1-evaluate-PROTOTYPE.md)** — Run one command, see automatic audit trails
> - **[Tier 2: Solo Developer (30 min)](docs/onboarding/tier2-solo-dev-PROTOTYPE.md)** — Build with TEOF's architecture
> - **[Tier 3: Multi-Agent (60 min)](docs/onboarding/README.md)** — Coordinate agents through the bus
>
> **Already familiar with TEOF?**
> - Glossary: [`docs/glossary.md`](docs/glossary.md) — Essential terms and concepts
> - Repo map: [`docs/architecture.md`](docs/architecture.md)
> - Workflow (priority ladder): [`docs/workflow.md`](docs/workflow.md#architecture-gate-before-writing-code)
> - Operator mode (LLM quick brief): [`docs/workflow.md#operator-mode-llm-quick-brief`](docs/workflow.md#operator-mode-llm-quick-brief)
> - Quick Reference: [`docs/reference/quick-reference.md`](docs/reference/quick-reference.md)
> - Backlog (pick your next objective): [`docs/backlog.md`](docs/backlog.md)

---

## Repo Map

- **Orientation (start here)**
  - [Architecture](docs/architecture.md)
  - [Workflow](docs/workflow.md)
  - [Promotion Policy](docs/promotion-policy.md)
  - [Alignment Protocol](docs/alignment-protocol.md)
  - [Alignment Trail](docs/foundation/alignment-trail.md)
- **Onboarding & daily flow**
  - [Onboarding Landing](docs/onboarding/README.md)
  - [Agent Onboarding](.github/AGENT_ONBOARDING.md)
  - [Quick Reference](docs/reference/quick-reference.md)
  - [Backlog](docs/backlog.md)
- **Automation & coordination**
  - [Plans](./_plans/README.md)
  - [Automation](docs/automation.md)
  - [Systemic Adoption Guide](docs/automation/systemic-adoption-guide.md)
  - [Parallel Codex Playbook](docs/parallel-codex.md)
- **Deep references**
  - [Specs](docs/specs/)
  - [Seed](docs/seed.md)
  - [Observations — Hyper-Organism](docs/observations/hyper-organism.md)

**Author:** Observation • **License:** [Apache-2.0](LICENSE)

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

### Systemic Coordinates

Work is now tracked directly against the systemic axes (S1–S10) and layer hierarchy (L0–L6).  
Every artifact declares:

- `systemic_targets`: the primary systemic axes it advances (e.g. S1 Unity, S4 Resilience, S6 Truth).
- `layer_targets`: the layers it operates within (e.g. L4 Architecture, L5 Workflow).
- `systemic_scale`: the highest axis it must satisfy before proceeding.
- `systemic_scope` (optional): a namespace such as `apps/<program>` when work lives on a downstream branch rather than the trunk.

The first four systemic axes (Unity, Energy, Propagation, Resilience) form the **core fractal**—Resilience feeds back into Unity so these four repeat across every scale. Axes S5 and above act as growth overlays (adaptation, governance, meaning) that a program opts into once the core is healthy.

This explicit coordinate replaced earlier observation loops while preserving the same intent—evidence, coherence, guardrails, reproducibility, and recovery all map onto the S/L lattice. See [`docs/foundation/systemic-scale.md`](docs/foundation/systemic-scale.md) and [`governance/systemic-order.json`](governance/systemic-order.json) for canonical definitions, plus [`docs/automation/systemic-overview.md`](docs/automation/systemic-overview.md) for migration guidance.

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
ls artifacts/systemic_out/latest
cat artifacts/systemic_out/latest/brief.json
```

- Install exposes the teof console script.
- teof brief scores docs/examples/brief/inputs/ and writes receipts under artifacts/systemic_out/<UTC>.
- teof reflections surfaces the latest `memory/reflections/` entries, layer coverage, and tags (add `--format json` for automation).

If you prefer an end-to-end bootstrap, run `bin/teof-up` to install dependencies, refresh quickstart receipts, and print the next docs to read. Additional CLI entrypoints live in [`docs/quickstart.md`](docs/quickstart.md), and automation guardrails remain catalogued under [`docs/automation/autonomy-preflight.md`](docs/automation/autonomy-preflight.md).

- Re-run the guard path quickly with `bin/teof-up --fast` once the onboarding virtualenv exists; this reuses the cached environment while still emitting fresh receipts.
- Quickstart receipts live under `_report/usage/onboarding/`. See [`docs/quickstart.md`](docs/quickstart.md#quickstart) for a sample payload.

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

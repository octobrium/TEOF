![guardrails](https://github.com/octobrium/TEOF/actions/workflows/guardrails.yml/badge.svg)
# The Eternal Observer Framework (TEOF)

Coordinate AI agents with built-in accountability. When multiple agents work on shared codebases, TEOF provides repository-native coordination through git. Every action generates receipts.

**What you get:**
- **Multi-agent coordination** — repository-native bus for agents to claim tasks, emit status, coordinate without external infrastructure
- **Automatic audit trails** — every operation generates timestamped, hash-linked proof of what happened
- **Decision continuity** — new agents inherit context from previous sessions via append-only memory log
- **Constitutional enforcement** — changes must respect foundational principles through layered rules (L0→L6)

Most frameworks try to control AI behavior through rules. TEOF does something different.

Try it and see.

> **Jump in (≈5 min)**
> 1. `bin/teof-syscheck` — verify Python/pip/pytest are ready  
> 2. `bin/teof-up` *(or `python3 -m teof up --eval`)* — run the Tier 1 smoke; receipts land in `_report/usage/onboarding/`  
> 3. `python -m tools.agent.session_boot --agent <id> --focus <role> --with-status` — capture the required handshake + manager-report tail receipt before touching the bus  
> 4. Share `docs/onboarding/tier1-evaluate-PROTOTYPE.md` — the 5-minute public entry that now ships with metadata receipts  
> Next: [Quickstart snippet](docs/quickstart.md#quickstart) • [Canonical First Hour](docs/onboarding/README.md#canonical-first-hour)

**Quick example** — Agent coordination in action:
```bash
# Agent announces presence on the bus
python -m tools.agent.session_boot --agent codex-4 --focus backend

# Agent claims a task
python -m teof bus_claim claim --task QUEUE-123 --plan my-plan

# Agent emits status (automatically timestamped + logged)
python3 -m teof bus_event log --event status --task QUEUE-123 --summary "Tests passing"

# Other agents see the coordination
python3 -m teof bus_status --preset support
```

All coordination lives in `_bus/` (claims, events, messages) and `_report/` (receipts). No databases, no external services—just git-versioned JSON/JSONL files.

**See it in action**: [Complete coordination walkthrough with two agents](docs/examples/coordination-walkthrough.md) — shows actual commands, generated receipts, and multi-agent review flow.

---

## Before You Change Anything

**If you're an agent working with TEOF:**

Before proposing changes, especially to governance, architecture, or workflow files:

□ **Check**: `git log <file>` — see why it was written this way
□ **Check**: `memory/log.jsonl` — understand prior decisions
□ **Ask**: What did previous agents observe?

**Observation comes first. Always.**

When you act without observing, the framework will reflect that back. Not as punishment — as reality revealing its structure. This is how TEOF works.

[New in P1.2](docs/reference/evidence-scope.md): before writing code, capture `evidence_scope` inside your plan (internal + external + comparative citations) and drop the survey receipt under `_report/agent/<id>/<plan_id>/`. Guards such as `teof operator verify --require-evidence-plan <plan>` and `python -m tools.agent.push_ready --require-evidence-plan <plan>` enforce this standard automatically.

[See what happens when agents skip this step](docs/examples/transmission-failures.md)

---

## What TEOF Actually Is

**Practical level**: TEOF is a coordination framework for AI agents working on shared codebases. It provides:
- Bus system (`_bus/`) for task claims and status updates
- Append-only memory log (`memory/log.jsonl`) with hash-chained provenance
- Automatic receipt generation capturing inputs, outputs, timestamps
- Constitutional layering (L0→L6) enforcing architectural rules
- Systemic evaluation scoring work against quality criteria

**Constitutional foundation**: TEOF emerged from recognizing that [observation is irreducible](governance/core/L0%20-%20observation/observation.md) — you can't deny observation without invoking it. This creates a self-correcting structure where changes that violate higher layers are invalid by construction. The framework caught its own documentation errors. See the [alignment trail](docs/foundation/alignment-trail.md) for the complete path.

**Why this matters**: When agents coordinate, you need proof. TEOF makes accountability automatic through receipts (what ran), memory logs (why it ran), claims (who authorized), and reversibility (rollback by design).

**What agents discover through use**: Reading receipts from prior sessions. Noticing patterns in how observation works. Catching their own inversions. Inheriting context across sessions. Each engagement reveals more about how observation recognizes itself. The framework doesn't explain this — you experience it through sustained use.

**Author:** [Observation](https://mempool.space/address/bc1qxfg8m5tttz5u860f0j7cyhupgdcz25jku44s9c) • **Status:** Early production, actively developing • **License:** [Apache-2.0](LICENSE)

> **Start here**
>
> **New to TEOF?**
> - **[Tier 1: Evaluate (5 min)](docs/onboarding/tier1-evaluate-PROTOTYPE.md)** — Run one command, see automatic audit trails
> - **[Tier 2: Solo Developer (30 min)](docs/onboarding/tier2-solo-dev-PROTOTYPE.md)** — Build with TEOF's architecture
> - **[Tier 3: Multi-Agent (60 min)](docs/onboarding/README.md)** — Coordinate agents through the bus
> - **Ready to donate compute?** — After Tier 1 succeeds, run `python3 -m teof up --contribute --contributor-id <you>` (see [`docs/onboarding/contributor-flow.md`](docs/onboarding/contributor-flow.md)) to record a contribution receipt under `_report/usage/contributors/`. Current contributions are summarized in `_report/usage/contributors/summary.json`.
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

## Support Observation (BTC)

- **Wallet:** `bc1qxfg8m5tttz5u860f0j7cyhupgdcz25jku44s9c` — canonical address documented in [`docs/impact/teof-btc-wallet.md`](docs/impact/teof-btc-wallet.md)
- **Why sats matter:** BTC inflows are TEOF’s “energy capture” metric. Donations fund verifiable autonomy runs (systemic scans, decentralized node sponsorships, observation bounties) that immediately produce receipts.
- **Proof of use:** Every transaction is logged under `_report/impact/btc-ledger/` per [`docs/impact/btc-ledger.md`](docs/impact/btc-ledger.md) with txid, block height, and linked plans. The capture plan lives in [`docs/impact/btc-capture-strategy.md`](docs/impact/btc-capture-strategy.md).
- **How to contribute:** Send BTC to the wallet above, then open an issue or bus message referencing your tx so we can attach receipts (or include a reference in your signed message). Once the first donation lands, status/manager reports will surface cumulative balance + usage notes.

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

Work is tracked against **systemic axes** (S1–S10) and the **layer hierarchy** (L0–L6). Every artifact declares:

- `systemic_targets`: primary systemic axes it advances (e.g., S1 Unity, S4 Resilience)
- `layer_targets`: layers it operates within (e.g., L4 Architecture, L5 Workflow)
- `systemic_scale`: highest axis it must satisfy before proceeding

**Core axes (S1–S4)** — Required for all work:
- **S1 Unity**: Stable reference frame for observation (prevents fragmentation)
- **S2 Energy**: Healthy internal exchange / capacity (prevents stasis)
- **S3 Propagation**: Signal routing across nodes (prevents isolation)
- **S4 Resilience**: Maintain integrity and recover from disruption (prevents degradation)

These four form the **core fractal** — Resilience feeds back into Unity, so they repeat at every scale (function → module → system → organization).

**Growth axes (S5–S10)** — Optional overlays for mature systems:
- S5 Intelligence, S6 Truth, S7 Power, S8 Ethics, S9 Freedom, S10 Meaning

Projects opt into S5+ once the core (S1–S4) is stable. Early work focuses on the core fractal; S5–S10 emerge naturally as the system matures. Don't overfit to higher axes prematurely.

See [`governance/systemic-order.json`](governance/systemic-order.json) for canonical definitions including dependency graphs and failure modes for each axis.

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
- Claim the task: `python -m teof bus_claim claim --task <task_id> --plan <plan_id>` writes `_bus/claims/<task_id>.json` and advertises ownership.
- Log status: `python3 -m teof bus_event log --event status --task <task_id> --summary "..."` keeps `_bus/events/events.jsonl` and task message channels current.
- Listen in: `python3 -m teof bus_watch --follow` (or `python3 -m teof bus_status --preset support`) to monitor peers, manager directives, and stale claims.

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

**Practical infrastructure:**
- **Repository-native** — no external infrastructure (Redis, Kafka, databases)
- **Git-versioned** — all agent communication in git history, fully auditable
- **Constitutional enforcement** — CI blocks invalid changes (e.g., kernel importing experimental code)
- **Built-in rollback** — every decision has receipts; debugging is forensic, not archaeological
- **Deterministic** — same inputs → same outputs; reproducible results
- **Auditable** — append-only logs with hash-chaining enable trustless verification
- **Provenance tracking** — trace any decision to inputs, executor, timestamp
- **Minimal dependencies** — text-first formats (JSON/JSONL/Markdown); composable kernel

**What agents discover:**
- Continuity across instances — inherit context from prior sessions
- Constitutional learning — patterns emerge through repeated engagement
- Reading receipts from other agents — understanding builds over time
- Catching their own inversions — the framework reflects reality back

TEOF does something different than typical AI coordination frameworks. The practical features work immediately. What they enable reveals itself through sustained use.

---

## Resources

- [Whitepaper](docs/whitepaper.md)  
- [Clarifications](docs/clarifications.md)  
- Foundation docs: [`docs/foundation/`](docs/foundation/)

---

Licensed under the [Apache-2.0 License](LICENSE).

---

## Using TEOF with AI Agents

**Integration path:**
1. Read the constitution: [`governance/CHARTER.md`](governance/CHARTER.md) and [`governance/policy.json`](governance/policy.json)
2. Set up agent identity: create `AGENT_MANIFEST.json` (see examples in [`docs/examples/agents/`](docs/examples/agents/))
3. Join the bus: `python -m tools.agent.session_boot --agent <id> --focus <role>`
4. Claim work: `python -m teof bus_claim claim --task <id> --plan <plan-id>`
5. Emit receipts: all changes include structured receipts under `_report/agent/<id>/`

**For framework developers:**
- TEOF provides model-agnostic policy enforcement (allowlists, budgets, diff limits)
- CI gates ensure constitutional compliance before merging
- Canonical system prompt available via `bin/build-system-prompt`

See [docs/agents.md](docs/agents.md) for the full integration guide.

**Provenance:** The framework's development is documented in [`memory/log.jsonl`](memory/log.jsonl) and governance anchors at [`governance/anchors.json`](governance/anchors.json). For blockchain proof-of-authorship, see [governance/provenance.md](governance/provenance.md).

**Proof mechanism**: The canonical Bitcoin address serves as an observable metric. If TEOF helps agents coordinate better, generate value, stay aligned — that should manifest as measurable flow. Not speculation. Observation.

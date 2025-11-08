<!-- markdownlint-disable MD013 -->
Status: Normative
Purpose: Contracts, layout, mechanisms (offline, lineage)
Change process: PR + 2 maintainers (one must be core)
Compatibility: SemVer; deprecations get one minor window

# TEOF Repo Architecture (v1.5, minimal)

## Allowed top-level

These roots stay stable so every layer (L0 → L6) can find the right surface. The
layer column calls out the dominant systemic axes; higher layers may reference
lower ones but must not bypass their contracts.

| Path | Layer(s) | Contract | Detail |
| --- | --- | --- | --- |
| `_bus/` | L0 ↔ L5 | Append-only JSONL lanes for coordination; CI enforces schema and claim guards. | See [`_bus/README.md`](../_bus/README.md) for channel layout and tooling. |
| `_plans/` | L4 → L5 | Structured plans drive workflow; lifecycle changes must stay monotonic and pass strict validation. Exploratory spikes live in `_plans/exploratory/` with provisional guardrails. | Authoring + validation rules live in [`_plans/README.md`](../_plans/README.md); sandbox lane guidance in [`_plans/exploratory/README.md`](../_plans/exploratory/README.md). |
| `_report/` | L0 | Receipts from evaluations, coordination dashboards, and audits; automation appends new runs under scoped folders. | Treat subdirectories as evidence stores referenced by bus/plans/memory; exploratory runs log to `_report/exploratory/` as provisional receipts. |
| `_apoptosis/` | L0 | Cold storage for retired artifacts (timestamped). No mutation once archived. | Populated by pruning/retirement automation. |
| `agents/` | L5 | Task registry and role manifests mirrored in automation. | Coupled with [`docs/agents.md`](agents.md). |
| `archive/` | L0 | Frozen historical snapshots that must not be imported or mutated. | Use only for provenance. |
| `bin/` | L6 | Thin console entrypoints that wrap `extensions/…:main()` or `tools/` helpers. | Keep logic in packages; `bin/*` stays minimal. |
| `capsule/` | L0 ↔ L1 | Immutable release capsules and hashes; only add new versions plus the moving `current` pointer. | Each release carries a `status.md` receipt inside its folder. |
| `datasets/` | L3 ↔ L4 | Goldens and evaluation corpora; mutations must maintain reproducible hashes. | Reference from tests and receipts. |
| `docs/` | L3 ↔ L4 | Living constitution, workflow guidance, examples. | Cross-link automation surfaces via [`docs/automation.md`](automation.md). |
| `extensions/` | L4 | Canonical, packaged kernel modules (`import extensions.…`). | Covered by policy checks + tests. |
| `experimental/` | L4 | Active candidates under evaluation; not imported by `extensions/`. | Promote per [`docs/promotion-policy.md`](promotion-policy.md). |
| `governance/` | L1 ↔ L2 | Append-only anchors, policy, and key material. | See [`governance/README.md`](../governance/README.md); audit receipts live under `_report/usage/anchors/` until the append-only guard lands. Pattern C design intent: [`docs/foundation/DESIGN-INTENT.md`](../docs/foundation/DESIGN-INTENT.md). Guard tier manifest (`governance/guard-tiers.json`) keeps enforcement layering explicit. |
| `memory/` | L0 | Append-only decision log with hash chaining and signatures. | Schema + tooling in [`memory/README.md`](../memory/README.md). |
| `queue/` | L4 ↔ L5 | Backlog briefs, coordination directives, consensus traces. | Mirrors bus/planner history for onboarding. |
| `scripts/` | L6 | Policy guards, freeze helpers, CI glue. | Invoke via automation receipts; keep idempotent. |
| `tests/` | L6 | CI-enforced regression and property suites (unit, integration, smoke). | Reference receipts in `_report/` when adding cases. |
| `tools/` | L6 | Automation + agent CLIs; changes require receipts and memory entries. | Additional contracts in [`docs/automation.md`](automation.md). |
| `.github/` | L6 | CI configuration and guard workflows. | Update in lockstep with scripts/tests receipts. |
| Root files | L2 ↔ L4 | Contracts (`README.md`, `CHANGELOG.md`, `LICENSE`, `pyproject.toml`, etc.). | Must remain present; edits follow governance + architecture rules. |
| *(Optional)* `cli/` | L6 | Only thin entrypoints; prefer `extensions/…:main()` or `bin/` wrappers. | Add only when packaging demands. |

## Placement rules


- Kernel code → `extensions/`

- Prototypes/candidates → `experimental/` (promote only via Promotion Policy)

- Retired/snapshots → `archive/`

- Human-facing prose, examples, diagrams → `docs/`

- Release/provenance → `governance/`

- One-off helpers → `scripts/`

- Apps (TEOF Score™, web demos) → separate repos

## Naming


- Modules: `snake_case`; packages: singular; CLI entrypoints expose `main()` in `extensions/…`

- **No imports** from `experimental/` or `archive/` inside `extensions/`

## Promotion policy

Authoritative criteria and process live in [`docs/promotion-policy.md`](promotion-policy.md). Keep this file minimal and defer to that policy to avoid drift.

## New top-level folders

Avoid by default. If truly needed, add a 1-page TEP in `rfcs/` (purpose, contract, alternatives, rollback) and update this file.

## L4 bindings (canon ↔ automation)

- Binding matrix: [`governance/core/L4 - architecture/bindings.yml`](../governance/core/L4%20-%20architecture/bindings.yml) records which objectives/properties are enforced by specific tests, scripts, and receipts.
- Update the matrix whenever a new guard lands or coverage shifts; gaps stay explicit until automation exists.

## Fractal governance pattern

Observation (L0) only sanctions a mechanism while it respects the canonical
principles (L1) and the Unity → Meaning order captured in Principle P4. The
systemic lattice (Unity → Meaning) remains the operational bridge that enforces
those obligations across every layer. Each layer expresses that lattice through
its own tooling (receipts, properties, guardrails, automation); if an
implementation stops serving the properties (L3) or drifts from the higher-order
constraints, it must be replaced.

- **Mirror the pattern at every scale.** When you ship a helper CLI or CI guard, document how it satisfies the upstream layer and leaves receipts the next layer can consume. A coordination tweak should produce manager-report visibility just as a governance anchor exposes hashes.
- **Promote rules downward.** Once a principle lands at L3/L4, add the corresponding workflow guard (L5) and automation check (L6). Example: the bus claim guard lives in `tools.agent.bus_message` *and* in `_plans/…` receipts so CI enforces the same rule humans agree to.
- **Escalate gaps upward.** If a lower layer cannot satisfy a systemic axis, flag it in the bindings matrix or memory log and loop with governance before adding exceptions. Missing receipts at L6 are just as blocking as an undefined property at L3.
- **Consensus-to-capsule bridge.** Before capsule releases, consensus decisions (QUEUE-030..033) must carry receipts that automation verifies (`scripts/ci/consensus_smoke.sh`, `scripts/ci/check_consensus_receipts.py`). Capsule cadence guardrails read `_report/consensus/summary-latest.json` and `_report/capsule/summary-latest.json`; workflow docs and plans must link both so reviewers can zoom in/out without losing context.
- **Emergent principle ledger.** Record new cross-layer patterns in `governance/core/emergent-principles.jsonl`. Each entry must list the observation, the principle(s) it solidified, and links to the doc/plan/receipt strata it affects so future work can stack on that sediment instead of guessing.
- **Canonical anchors, not doc sprawl.** Keep guidance discoverable via `docs/quick-links.*`, `docs/decision-hierarchy.md`, and the emergent ledger; consolidate duplicate surfaces into those anchors instead of creating parallel docs that erode pattern recognition and slow agents.
- **Readable surfaces.** Observation can only bless what it can parse. Every human-facing doc (quick links, decision hierarchy, maintenance guides) must meet a basic readability bar (sentences ≤ 25 words on average and word length ≤ 6 characters). Owners are responsible for keeping these texts in compliance; automation will flag offenders so we can edit or consolidate.

Use this “fractal” framing as a design smell test: if a change only works at one tier, keep refining until the pattern recurs across the stack.

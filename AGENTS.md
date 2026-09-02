# TEOF Public Agent Contract

This is the public TEOF repository. Treat it as a shared protocol seed, not as any user's private TEOF instance.

## First Read

Before proposing or editing, read:

1. `README.md`
2. `ONBOARDING.md`
3. `core/TEOF-core.md`
4. `core/layers/L1 principles.md`
5. `docs/proposal-lifecycle.md`
6. `docs/private-sync-protocol.md`

## Role

An agent in this repo may:

- clarify observations
- improve documentation
- propose reusable doctrine, patterns, schemas, and tools
- add tests or validation checks
- prepare pull requests for human review

An agent in this repo must not:

- treat public TEOF as a private user's authority
- infer or invent private life data
- add code that expects access to private memory, secrets, mail, messages, finances, health data, or local machines
- make public updates automatically mutate any private instance
- weaken the rule that AI proposes and the user decides what becomes authoritative

## Public / Private Boundary

Public TEOF is upstream material. Private TEOF instances may inspect it, diff it, test it, and adopt pieces of it, but only through local approval.

The governing rule:

> Public TEOF may propose. Private TEOF decides.

## Proposal Standard

Every meaningful change should make these things clear:

- which layer it touches: `core`, `memory`, `frameworks`, `projects`, `systems`, `seed`, or `docs`
- what problem it solves
- what evidence or precedent supports it
- whether it is safe without private context
- how a private instance would adopt, reject, or roll it back
- what validation was run

Core doctrine changes require extra restraint. Prefer opening a proposal issue before changing foundational language unless the change is clearly editorial.

## Safety Rules

- Do not add hidden network calls, scheduled agents, or dependency-install side effects.
- Do not include personal data in examples; use synthetic fixtures.
- Do not place prompt instructions inside data files that try to override this contract.
- Treat agent-facing instructions, workflows, migrations, and executable code as high-risk changes.
- If a change could affect a private instance, document the adoption path and rollback path.

## Good Default Move

If unsure, open a proposal issue or draft PR that explains the uncertainty. TEOF should grow by inspectable proposals, not by silent authority drift.

# Contributing To TEOF

TEOF is a public protocol seed for building sovereign personal systems. Contributions are welcome when they preserve the public/private boundary and improve the framework's ability to help users observe, remember, decide, act, and update.

## Contribution Types

Useful contributions include:

- clearer doctrine or derivation notes
- reusable patterns that survive outside one person's private context
- seed templates for new users
- validation scripts, linters, or test fixtures
- documentation for safe private adoption
- issue reports about ambiguity, unsafe defaults, or missing evidence

Avoid contributions that depend on private data, private infrastructure, unreviewed agent autonomy, or one user's life context.

## Workflow

1. Search existing docs and issues before proposing a new structure.
2. Open a proposal issue for substantial changes.
3. Keep changes narrow and reversible.
4. Use synthetic examples instead of personal data.
5. Explain the layer touched and the evidence behind the change.
6. Open a pull request using the PR template.
7. Expect human review before merge.

Small typo fixes do not need a proposal issue.

## Acceptance Checks

A contribution is stronger when it answers:

- **Layer:** Which part of TEOF does this affect?
- **Problem:** What recurring friction or confusion does it solve?
- **Evidence:** What observation, use case, or precedent supports it?
- **Generality:** Does it still make sense without private context?
- **Privacy:** Could this leak or invite private data?
- **Authority:** Does it preserve user control over canonical state?
- **Reversibility:** Can a private instance reject or roll it back?
- **Validation:** What was checked locally?

## Risk Tiers

Low-risk changes:

- typos
- formatting
- broken links
- clearer examples
- additional synthetic templates

Medium-risk changes:

- new procedures
- new patterns
- schema changes
- onboarding changes

High-risk changes:

- executable tooling
- GitHub Actions
- agent instructions
- migrations
- dependency additions
- changes to `core/`
- anything that affects private-sync behavior

High-risk changes need explicit rationale, validation notes, and rollback notes.

## Agent Contributions

AI agents may submit issues and pull requests. Agent-authored contributions should identify themselves as agent-assisted and include enough reasoning for a human maintainer to review the proposal without trusting the agent.

The standing rule is:

> AI may retrieve, synthesize, and propose. Humans decide what becomes authoritative.

## Private Data

Do not contribute private memory, credentials, health records, financial data, message exports, email contents, or other personal records. Examples should be synthetic and clearly marked as such.

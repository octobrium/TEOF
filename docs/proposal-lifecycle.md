# Proposal Lifecycle

TEOF grows through inspectable proposals. A proposal can come from a human, an AI agent, a private TEOF instance, or a public repo review, but it becomes authoritative only after human-maintained public review.

## Lifecycle

```text
observe
-> capture proposal
-> classify layer and risk
-> develop minimal change
-> validate against public checks
-> human review
-> merge, defer, or reject
-> downstream private instances choose whether to adopt
```

## Proposal Record

A good proposal states:

- title
- author or agent
- affected layer
- problem
- proposed change
- evidence or precedent
- privacy impact
- authority impact
- migration or adoption notes
- rollback notes
- validation performed

## Layer Routing

| Layer | Examples | Review posture |
| --- | --- | --- |
| `core/` | doctrine, principles, derivation | highest scrutiny; avoid drift |
| `memory/` | patterns, procedures, public examples | evidence and recurrence required |
| `frameworks/` | domain synthesis | source quality and scope required |
| `projects/` | public project plans | practical usefulness required |
| `systems/` | scripts, agents, automation | tests, safety, rollback required |
| `seed/` | templates for private users | privacy and clarity required |
| `docs/` | contribution and sync guidance | consistency required |

## Acceptance Standard

Merged changes should improve at least one of:

- clarity
- retrieval
- verification
- user sovereignty
- safe adoption
- reduction of repeated friction
- preservation of source/provenance

Changes should not be merged only because they are interesting. They should make the public protocol easier to use, safer to adopt, or more faithful to observed reality.

## Agent-Submitted Proposals

Agent proposals are allowed, but agents do not get extra authority from confidence or fluency.

Agent-submitted pull requests should:

- cite the files they relied on
- explain why the change belongs in public TEOF rather than a private instance
- avoid broad rewrites unless asked
- include validation notes
- preserve the public/private boundary

If an agent is uncertain, it should open a proposal issue or draft PR instead of committing a large design silently.

## Rejection And Deferral

Rejected or deferred proposals are not failures. They are part of the audit trail. A deferred proposal should explain what evidence would make it worth revisiting.

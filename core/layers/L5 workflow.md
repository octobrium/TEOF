# L5 — Workflow

**Status:** Public workflow layer  
**Depends on:** 0, L1-L4

---

## Purpose

L5 describes how a human or AI agent should navigate the **public** TEOF repo.

It is intentionally simpler than any private working workflow. The public repo is meant to be:

- readable
- reusable
- safe to fork

not a full autonomous operating environment.

---

## Public Routing Rule

Read the smallest surface that can answer the question.

### Typical sequence

1. `core/TEOF-core.md` for seed grounding
2. `core/layers/L1 principles.md` for doctrine
3. `core/TEOF.md` when the full derivation matters
4. `memory/patterns/` for supporting abstractions
5. `ONBOARDING.md`, `frameworks/`, `projects/`, or `systems/` when the task concerns building a working organism

The point is routing over overloading. Do not read the whole repo just because it exists.

---

## Query Types

| Query Type | Start Here |
|-----------|------------|
| "What is TEOF?" | `core/TEOF-core.md` |
| "What does TEOF claim doctrinally?" | `core/layers/L1 principles.md` |
| "Show me the full reasoning" | `core/TEOF.md` |
| "How do I use this in my own system?" | `ONBOARDING.md` → `memory/README.md` |
| "What patterns support this?" | `memory/patterns/README.md` and specific pattern files |

---

## Workflow Standards

When using the public repo:

- prefer direct citation to the files present
- distinguish doctrine from inference
- do not invent private context that is not in the repo
- do not treat the public repo as if it already contains a user's identity, memory, or project state

That last point is critical. The public repo is a template organism, not a populated private one.

---

## Public-Safe Extension Pattern

If someone wants to build on TEOF:

1. keep the core mostly stable
2. populate memory, frameworks, projects, and systems with real use
3. promote only the patterns and methods that survive contact with reality

This prevents a common failure mode: trying to turn public doctrine directly into a fake fully-personal system without the lived layer that would make it honest.

---

## Output Standard

Good use of the public repo should produce:

- clearer reasoning
- explicit uncertainty
- better diagnosis of structural bottlenecks
- more disciplined separation between doctrine and personal state

If use of the repo produces only impressive language, it is degrading.

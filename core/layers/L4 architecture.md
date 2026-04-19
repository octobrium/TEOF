# L4 — Architecture

**Status:** Public architecture layer  
**Depends on:** 0, L1-L3

---

## Purpose

L4 describes how the public TEOF repo should be organized so that:

- the core remains stable
- the public structure stays legible
- others can fork it into their own systems without inheriting private assumptions

This is a public-safe architecture document, not a description of any private working tree.

---

## Public Structure

The public repo is organized around three visible zones:

| Zone | Purpose |
|------|---------|
| `core/` | Stable doctrine, derivation, and long-form source text |
| `patterns/` | Public supporting patterns and abstractions |
| `seed/` | Blank starter scaffold for a user's own local system |

This is the public expression of the universal pattern:

- **core** = protected
- **translation** = interpretation and starter scaffolding
- **periphery** = user-built local extensions outside public canon

---

## Ordering Principle

Position should encode priority.

Within the public repo:

1. `core/TEOF-core.md`
2. `core/layers/L1 principles.md`
3. `core/TEOF.md`
4. supporting doctrine / derivation docs
5. patterns and seed material

The rule is simple: foundational before explanatory, explanatory before optional.

---

## Public / Local Boundary

The public repo should contain:

- doctrine that survives without private context
- derivation aids that remain generally useful
- starter templates reusable by others

The public repo should not contain:

- personal memories
- live private operating state
- sensitive workflows
- user-specific finance, legal, health, or relationship records

If a file depends on private context to make sense, it belongs in a local extension, not in the public core.

---

## Recommended Fork Pattern

If you fork TEOF into your own working system, a clean pattern is:

```
your-system/
├── core/        ← mostly stable, updated selectively
├── patterns/    ← promoted local patterns
├── seed/        ← starter templates or adapted local docs
├── local/       ← private observations, identity, state, logs
└── projects/    ← execution surfaces
```

The name of the local folders can differ. The architectural point is what matters: keep doctrine separate from volatile state.

---

## Canonical Rule

`core/TEOF.md` is the canonical long-form manuscript.

If sharded chapter files or older summaries exist, they are subordinate to `core/TEOF.md` unless explicitly regenerated from it.

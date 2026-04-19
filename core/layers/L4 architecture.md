# L4 — Architecture

**Status:** Public architecture layer  
**Depends on:** 0, L1-L3

---

## Purpose

L4 describes how the public TEOF repo should be organized so that:

- the core remains stable
- the public structure stays legible
- others can fork it into their own systems without inheriting private assumptions

This is a template architecture document.

---

## Public Structure

The repo is organized around a stable core and blank working layers:

| Zone | Purpose |
|------|---------|
| `core/` | Stable doctrine, derivation, and long-form source text |
| `memory/` | Observations, reflections, patterns, identity, and procedures |
| `frameworks/` | Domain curation and synthesis |
| `projects/` | Active execution surfaces |
| `systems/` | Tooling and automation design surfaces |
| `seed/` | Optional lighter starter scaffold |

This is the public expression of the universal pattern:

- **core** = protected
- **translation** = notes, routing, and interpretive scaffolding
- **periphery** = adaptive user-built layers

---

## Ordering Principle

Position should encode priority.

Within the public repo:

1. `core/TEOF-core.md`
2. `core/layers/L1 principles.md`
3. `core/TEOF.md`
4. supporting doctrine / derivation docs
5. memory, frameworks, projects, systems, and seed material

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
├── core/
├── memory/
├── frameworks/
├── projects/
├── systems/
└── seed/
```

The names can differ. The architectural point is what matters: keep doctrine separate from volatile state, and keep tools downstream of clarified process.

---

## Canonical Rule

`core/TEOF.md` is the canonical long-form manuscript.

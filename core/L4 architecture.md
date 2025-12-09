# L4 — Architecture

**Status:** Living — how the system is organized
**Depends on:** L0 (observation), L1 (principles), L2 (objectives), L3 (properties)
**Ultimate objective:** Unify observation

---

**Purpose:** Explain *why* things are organized, not *what* exists. The filesystem is the source of truth for contents.

**Principle:** Don't maintain state that can be derived. Run `tree -L 2` to see current structure.

---

## The Universal Ordering Principle

**All lists, sections, and structures in TEOF follow one convention:**

```
FOUNDATIONAL → IMPORTANT → PERIPHERAL
(equivalently: STABLE → ACTIVE → ADAPTIVE)
```

**"Foundational" = functionally foundational.** What gets read first, built upon, depended on. Not derivation history. CORE.md is functionally foundational for AI (read first) even though TEOF-complete.md is the source text.

| Context | Ordering Rule |
|---------|---------------|
| Lists within files | Most important/foundational first, descending |
| Sections within files | Core concepts → applications → examples |
| Files within directories | README → *-core.md → chapters/specifics |
| Directories within TEOF | core/ → frameworks/ → projects/ → memory/ |
| Framework domains | By TEOF layer hierarchy (Layer 2 → 3 → 4 → 7 → derived) |
| Source analyses | By track record (longest survival = most tested) |
| Any enumeration | Ranked by importance, never alphabetical |

**The Test:** When adding anything, ask: "Is this more foundational than what's already here?" Insert at appropriate rank.

**The Signal:** First item in any list = most important. Last = least. No exceptions.

**Why:** AI agents reading TEOF can trust that position encodes priority. No need to re-rank or guess importance. Coherent shape maintained as system grows.

---

## Layer Architecture

TEOF follows Pattern C (stable core + adaptive periphery) in its file organization:

| Layer | Directory | Mutation Rate | Purpose |
|-------|-----------|---------------|---------|
| DNA | `core/` | Rare | Axioms, minimal loop, reconstructible seed |
| Protein | `frameworks/` | Moderate | Domain applications (health, finance, social, power) |
| Action | `projects/` | Frequent | Active execution, roadmap, research |
| Memory | `memory/` | Accumulating | Identity, patterns, raw, logs |

**Flow:** Core → Frameworks → Projects → Memory (patterns feed back to frameworks)

---

## File Naming Conventions

| Pattern | Purpose | AI Reads? |
|---------|---------|-----------|
| `README.md` | Directory entry point | Yes — first |
| `CORE.md`, `*-core.md` | Compressed AI reference (<50KB) | **Yes — primary** |
| `*-complete.md` | Full human-readable version | **No** |
| `chapters/*.md` | Chunked sections (<10KB each) | Yes — on demand |

**Rule:** Files >100KB get split into `*-core.md` (AI) + `*-complete.md` (human).

---

## Routing Logic

| Question Type | Start Here |
|---------------|------------|
| How to help user | `ONBOARDING.md` |
| TEOF foundations | `core/CORE.md` |
| Domain question | `frameworks/[domain]/README.md` |
| What to do next | `projects/ROADMAP.md` |
| Personal context | `memory/identity.md` |

---

## Memory Architecture

```
memory/
├── raw/             ← Unprocessed input (user's words verbatim)
├── log/             ← Structured observations
│   ├── reflections/     Internal: thoughts, realizations
│   └── events/          External: milestones, facts
├── identity.md      ← Patterns about user
├── patterns.md      ← Patterns about systems
└── archive/         ← Old prototypes (historical)
```

**Flow:** `raw/` → `log/` → `identity.md` or `patterns.md` → `core/` or `frameworks/`

**All files kept permanently.** Raw material has contextual value even after patterns extracted.

---

## File Hygiene Principles

**Create new file when:**
- New domain framework needed
- New project started

**Edit existing file when:**
- Updating with new insight
- Refining based on feedback

**Delete when:**
- Creates confusion
- Scaffolding outlived its purpose
- Duplicate of existing content

**Avoid:**
- Inventories of files (they go stale)
- Duplicating information across files
- Cross-references that can break silently

---

## Detecting Staleness

This document follows its own principle: it describes organization *logic*, not file *inventory*.

To check current state, observe directly:
```bash
tree -L 2 --dirsfirst -I 'archive|.git|.DS_Store|node_modules'
```

To find broken internal links:
```bash
grep -roh '\[.*\](\.\/[^)]*\.md)' . | sed 's/.*(\.\///' | sed 's/)//' | while read f; do [ -f "$f" ] || echo "Missing: $f"; done
```

---

*Structure should be inferable from principles. If you need to read this file to understand where things go, the principles aren't clear enough.*

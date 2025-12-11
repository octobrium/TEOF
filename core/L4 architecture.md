# L4 — Architecture

**Status:** Living — how the system is organized
**Depends on:** L0 (observation), L1 (principles), L2 (objectives), L3 (properties)

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

**"Foundational" = functionally foundational.** What gets read first, built upon, depended on. Not derivation history. L1 principles.md is functionally foundational for AI (read first for philosophy) even though TEOF-complete.md is the source text.

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

### Attention-Aware Positioning (The Priority Curve)

Ordering isn't just organizational — it's **functional for LLM attention allocation**.

```
Attention
    ▲
    │ █████                              ████
    │ ██████████                      ███████
    │ ████████████████            ████████████
    │ ██████████████████████████████████████████
    └──────────────────────────────────────────► Position
      BEGINNING        MIDDLE            END
      (Primacy)       (Lowest)        (Recency)
```

**Research basis:** [Liu et al., 2024 "Lost in the Middle"](https://aclanthology.org/2024.tacl-1.9/) — U-shaped attention persists even in 1M+ token models.

| Position | Content Type | Rationale |
|----------|--------------|-----------|
| **Beginning** | Highest priority (Quick Scan, Tier 0, current state) | Maximum attention — deliberate |
| **Middle** | Supporting context (history, nuance) | Acceptable degradation |
| **End** | Metadata, version history, references | Recency boost as bonus |

**Why not priority 2 at end?** File length varies (end unpredictable), primacy ~2x stronger than recency, truncation loses end content, breaks human readability.

**Scaling property:** As content grows, hierarchy extends. As models improve, more hierarchy becomes accessible. Position handles it — no restructuring needed.

---

## Layer Architecture

TEOF follows the **Universal Pattern** (stable core + adaptive periphery) in its file organization.

| Layer | Directory | Mutation Rate | Purpose |
|-------|-----------|---------------|---------|
| DNA | `core/` | Rare | Axioms, minimal loop, reconstructible seed |
| Protein | `frameworks/` | Moderate | Domain applications (health, finance, social, power) |
| Action | `projects/` | Frequent | Active execution, roadmap |
| Research | `research/` | Moderate | External validation and decision support |
| Memory | `memory/` | Accumulating | Identity, patterns, raw, logs |

**Flow:** Core → Frameworks → Projects → Memory (patterns feed back to frameworks)

---

## File Naming Conventions

| Pattern | Purpose | AI Reads? |
|---------|---------|-----------|
| `README.md` | Directory entry point | Yes — first |
| `*-core.md` | Compressed AI reference (priority-ordered) | **Yes — primary** |
| `*-complete.md` | Full human-readable version | **No** |
| `chapters/*.md` | Chunked sections | Yes — on demand |

**When to split:** Large files with mixed-priority content benefit from `*-core.md` (high-priority, AI-readable) + `*-complete.md` (full version, human reading). Split for readability and routing clarity, not arbitrary size limits.

**Sizing principle:** Priority ordering > size limits. A well-ordered 80KB file outperforms a poorly-ordered 30KB file. The attention curve handles the rest. Hard cutoffs become tech debt as models improve — context windows have grown 100x in 3 years (4K→200K→1M+).

---

## Routing Logic

| Question Type | Start Here |
|---------------|------------|
| How to help user | `ONBOARDING.md` |
| TEOF foundations | `core/L1 principles.md` |
| Domain question | `frameworks/[domain]/README.md` |
| What to do next | `projects/ROADMAP.md` |
| Personal context | `memory/identity.md` |

---

## Memory Architecture

```
memory/
├── raw/             ← All raw inputs, date-prefixed (2025-12-09-*.md)
├── log/             ← Structured observations
│   ├── reflections/     Internal: thoughts, realizations
│   └── events/          External: milestones, facts
├── identity.md      ← Patterns about user
├── patterns.md      ← Patterns about systems
└── archive/         ← Historical content (flat, domain-prefixed files)
```

**Flow:** `raw/` → `log/` → `identity.md` or `patterns.md` → `core/` or `frameworks/`

**All files kept permanently.** Raw material has contextual value even after patterns extracted.

---

## Structural Decisions Log

Decisions about file organization, with external validation.

### 2025-12-09: Flatten Archive Structure

**Decision:** Single flat `archive/` folder with domain-prefixed files. No nested subfolders.

**Before:**
```
archive/
├── core-versions/
├── framework-versions/
│   ├── finances-versions/
│   └── relationships-versions/
├── project-research/
│   └── research/
└── raw/
```

**After:**
```
archive/
├── core-v1.0-2025-11-15.md
├── finances-finances-v1.0-2025-11-23.md
├── relationships-romance-v2.8-2025-11-23.md
├── legacy-prototypes/      ← Exception: deeply nested historical content
└── legacy-governance/      ← Exception: old GitHub templates
```

**External validation:**

| Source | Finding |
|--------|---------|
| [Zettelkasten (Luhmann)](https://zettelkasten.de/introduction/) | No folders — 90,000 notes, 70 books output |
| [PARA method (Forte)](https://fortelabs.com/blog/para/) | Single Archive folder, max 4 levels |
| [MIT/Harvard file structure](https://mitcommlab.mit.edu/broad/commkit/file-structure/) | Max 3-4 levels recommended |
| [Scientific Reports fMRI study](https://www.nature.com/articles/srep14719) | Nested folders increase cognitive load |
| [Git version control](https://www.atlassian.com/git/tutorials/what-is-version-control) | History built into repository, not folder structure |

**Rationale:**
- Nested archives found in 0/6 established PKM systems
- Date-prefixed files enable chronological sorting without hierarchy
- Reduces cognitive load for AI agents navigating structure
- Git handles versioning for GitHub-tracked files; manual archive only for gitignored content

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

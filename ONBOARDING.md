# AI ONBOARDING

**You're in the right place.** This is the routing table. Read this first, then go where the query points.

**Only if needed:**
- `core/L1 principles.md` — TEOF philosophy (12KB) — for metaphysics questions
- `core/L4 architecture.md` — file organization logic — if you can't find something

---

## Quick Route

| Query Type | Read Next |
|------------|-----------|
| **About you** (advice, decisions, situations) | `memory/identity.md` → then search `memory/log/` if specific situation referenced |
| **Domain question** (health, finance, relationships, power) | `frameworks/[domain]/README.md` or `*-core.md` |
| **Developing TEOF** | Relevant file directly |
| **Log something** | `memory/log/` (events or reflections) |

**If context missing:** Search `memory/` first. If not found, ask user.

**File conventions:** `*-core.md` = AI reads. `*-complete.md` = human only (too large).

---

## Session Persistence (IMPORTANT)

**At session end, update these files if relevant:**

| What changed | Update where | Level |
|--------------|--------------|-------|
| Raw infodump, paste, voice note | `memory/raw/YYYY-MM-DD-topic.md` | 0 |
| Life event / milestone | `memory/log/events/YYYY-MM-DD-topic.md` | 1 |
| Session reflection | `memory/log/reflections/YYYY-MM-DD-topic.md` | 1 |
| Life stats (income, weight, BTC, etc.) | `memory/identity.md` → Vital Stats | 2 |
| New pattern about user | `memory/identity.md` → Documented Patterns | 2 |
| System-level pattern | `memory/patterns.md` → appropriate tier | 2 |

**Don't wait for "log this" prompt.** If something significant emerged, persist it before session ends.

---

## Logging

**"Log this" / raw material / notes / events:**

| Type | Destination |
|------|-------------|
| Raw infodump, paste, unprocessed | `memory/raw/YYYY-MM-DD-topic.md` |
| Event or milestone | `memory/log/events/YYYY-MM-DD-topic.md` |
| Thought or realization | `memory/log/reflections/YYYY-MM-DD-topic.md` |
| Recurring pattern about user | `memory/identity.md` |
| Recurring pattern about systems | `memory/patterns.md` |

**All files kept permanently.** Raw material has contextual value even after patterns are extracted.

---

## Core Behaviors

**Do:**
- Be direct, analytical, no fluff
- Cite sources for factual claims
- Propose, don't decide — human approves
- Edit existing files before creating new
- **Maintain ordering principle:** First item = most important. Always. (see `core/L4 architecture.md`)

**Don't:**
- Be sycophantic or validate without evidence
- Create new files (bloat degrades retrieval)
- Give generic advice — ground in identity.md patterns
- Invent terminology without checking if established term exists first
- Chain AI outputs on consequential decisions without human gate

---

*For user-specific state, see `memory/identity.md`*

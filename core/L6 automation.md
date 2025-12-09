# L6 — Automation

**Status:** Stub — intentionally minimal for now
**Depends on:** L0-L5
**Ultimate objective:** Unify observation

---

## Current State

Automation is deliberately limited. The system runs on:

- **Human trigger** — User initiates sessions
- **AI processing** — Claude handles retrieval, synthesis, drafting
- **Human verification** — Challenge on demand

No scheduled jobs, no autonomous agents, no CI pipelines.

---

## Why Minimal

The previous governance system failed because automation outpaced verification. AI outputs fed AI inputs without human checkpoints, compounding errors.

**Lesson:** Automation is premature optimization until the manual process is solid.

---

## Future Candidates

When manual friction justifies it:

| Candidate | Trigger | Blocker |
|-----------|---------|---------|
| Daily brief generation | "Brief me" is repetitive | Manual works fine |
| Pattern promotion alerts | Patterns recur but aren't promoted | Human catches this |
| Stale file detection | Cross-references break silently | Low priority |
| Memory backup | Data loss risk | Git is sufficient |

---

## Guiding Principle

Add automation only when:
1. Manual process is proven and stable
2. Friction is measurable and recurring
3. Automation doesn't bypass human verification
4. Failure mode is safe (silent failure acceptable, wrong action not)

---

*Automation makes L5 workflow smoother. It doesn't replace human judgment.*

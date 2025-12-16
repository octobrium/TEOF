# L6 — Automation

**Status:** Stub — intentionally minimal for now
**Depends on:** 0, L1-L5

---

## Current State

Automation is deliberately limited. The system runs on:

- **Human trigger** — User initiates sessions
- **AI processing** — Claude handles retrieval, synthesis, drafting
- **Human verification** — Challenge on demand

No scheduled jobs, no autonomous agents, no CI pipelines.

---

## Why Currently Minimal

The previous governance system failed because automation outpaced verification. AI outputs fed AI inputs without human checkpoints, compounding errors exponentially.

**Lesson:** Automation is premature optimization until the manual process is solid.

**However:** AI-to-AI chaining is not inherently bad — it's inevitable at scale. The risk is error compounding over long chains, which scales with hallucination rate.

---

## Guiding Principle

Add automation only when:
1. Manual process is proven and stable
2. Friction is measurable and recurring
3. Failure mode is safe (silent failure acceptable, wrong action not)

---

## Future Candidates

Evaluate against guiding principle above. When manual friction justifies it:

| Candidate | Trigger | Blocker |
|-----------|---------|---------|
| Daily brief generation | "Brief me" is repetitive | Manual works fine |
| Pattern promotion alerts | Patterns recur but aren't promoted | Human catches this |
| Stale file detection | Cross-references break silently | Low priority |
| Memory backup | Data loss risk | Git is sufficient |

---

## Human Oversight Scaling

Human intervention should scale with error risk, not step count.

**Intervention triggers:**
- Confidence < threshold (calibrated per domain)
- High disagreement between agents
- Consequential decisions (financial, health, irreversible)
- Periodic random audits

**No intervention needed when:**
- High confidence + low stakes
- Multiple agents agree
- Outputs are reversible
- Within validated accuracy domain

**Mathematical frame:**
- If hallucination rate = h, chain length = n: expected accuracy ≈ (1-h)^n
- At h=1%, n=5: ~95% accuracy (acceptable)
- At h=1%, n=100: ~37% accuracy (unacceptable)
- Human gates inserted at intervals proportional to 1/h

**Principle:** Human gate on consequential decisions. Automated verification for routine chains.

---

*Automation makes L5 workflow smoother. Human judgment gates consequential decisions.*

# TEOF Tier 1: Evaluate (5 minutes)

> **Every decision should be traceable. TEOF makes that automatic. Run one command, get proof.**

## What is TEOF?

TEOF is an alignment framework that automatically creates audit trails for every action. Whether you're a solo developer or coordinating with AI agents, TEOF ensures your decisions are:

- **Traceable** — every step leaves evidence
- **Reversible** — you can always roll back
- **Auditable** — anyone can verify what happened

Think of it as **Git for decisions, but deeper**: Git tracks *what files changed*. TEOF tracks *why they changed* — the decision, execution context, and provenance chain that produced those changes.

## See it in action (2 minutes)

Run this single command from the repository root:

```bash
python -m teof up --eval
# Legacy wrapper: bin/teof-eval-PROTOTYPE.sh
```

> _Prototype note_: `teof up --eval` is the canonical CLI. The `bin/teof-eval-PROTOTYPE.sh` shim simply invokes it for convenience.

This will:
1. Install TEOF (takes ~30 seconds)
2. Run a brief analysis on sample documents
3. Generate receipts automatically

**Watch for these files being created** (the script prints the actual UTC timestamp; `artifacts/systemic_out/latest/` always points to that run):
```
artifacts/systemic_out/latest/          # symlink → artifacts/systemic_out/<UTC stamp>/
  ├── brief.json          # Summary with 10 sample inputs and generated ensembles
  ├── score.txt           # Quick metrics (e.g., ensemble_count=10)
  └── *.ensemble.json     # 10 ensemble files (one per input document)

_report/usage/onboarding/
  └── tier1-evaluation-<UTC stamp>.json  # Execution receipt (what ran, when, how)
```

## The Key Insight (1 minute)

**Those files ARE the point.**

- `brief.json` — shows what happened (analysis processed 10 sample documents and generated ensembles)
- `score.txt` — quick metrics to sanity-check the run (e.g., ensemble_count=10)
- `*.ensemble.json` — 10 individual ensemble files, one per input document
- `tier1-evaluation-*.json` — records the entire execution (what was run, what changed, success/failure)

### Why this matters

When you run TEOF:
- You don't just get outputs — you get **proof of how they were created**
- Changes aren't just tracked — they're **reversible by design**
- Decisions aren't just made — they're **auditable forever**

This is TEOF's core value: **automatic accountability**.

No extra commands. No manual logging. No "I think I ran this with those settings." Just deterministic, verifiable evidence.

## Real-world scenarios (30 seconds)

**Solo developer**: "Did this bug exist before my refactor?" → Check receipts from last week.

**AI agent**: "What did the previous agent change?" → Read its receipts, reproduce its exact environment.

**Team**: "Who decided to use this approach?" → Trace back through the receipt chain.

**When things go wrong**: "The agent reverted my work—what did it use?" → The receipt shows the exact inputs, version, and timestamp so you can roll back with confidence.

**Auditor**: "Prove this output matches the claimed inputs." → Here's the timestamped receipt with hashes.

## What you just experienced

- ✅ **Observation primacy** (L0): Every action produces evidence before anything else happens
- ✅ **Determinism** (L1): Same inputs → same outputs → same receipts
- ✅ **Auditability** (L1): Receipts are structured, timestamped, and hash-linked

These aren't features you configure — they're **built-in guarantees**. TEOF's foundational rules enforce them automatically in every workflow.

**Want to donate compute next?**
```bash
python -m teof up --contribute \
  --contributor-id <slug> \
  --workload tier1-eval
```
This records a contribution receipt under `_report/usage/contributors/<slug>/`.
See [`docs/onboarding/contributor-flow.md`](contributor-flow.md) for details.

## Next steps

### Ready to build with TEOF?
→ **[Tier 2: Solo Developer Path](tier2-solo-dev-PROTOTYPE.md)** (30 minutes)

Learn how to:
- Place your code in the right locations
- Create plans and track work
- Generate custom receipts for your projects

### Want to coordinate multiple agents?
→ **[Tier 3: Multi-Agent Coordination](README.md)** (60 minutes)

Set up:
- Agent manifests and identity
- Coordination bus for communication
- Claim system for work assignment

### Just exploring?

You've seen the core. TEOF ensures **every decision is traceable**. If that resonates, dive into Tier 2. If not, you understand what makes TEOF different.

---

**What you skipped** (available in higher tiers):
- How TEOF's architecture works internally
- How to write code that integrates with TEOF
- How agents coordinate through the bus system
- How systemic axes (S1-S10) and layers (L0-L6) structure work

You don't need any of that to understand the value. But it's there when you're ready.

---

**Questions?**
- See issues/discussions at https://github.com/octobrium/TEOF
- Full documentation: [docs/](../)

**One-line summary**: TEOF turns "trust me, I ran the tests" into "here's the timestamped receipt with hashes."

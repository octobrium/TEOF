# Decision Hierarchy Reference

Status: working draft (update with each governance cycle)

TEOF decisions follow a cascading tree so higher-order conditions are settled before downstream choices become actionable. Treat this as a companion to the architectural fractal pattern: every branch maps to the same OCERS checklist, but you only descend once upstream gates are satisfied.

```
Observation (L0)
└── Principles (L1)
    └── Objectives (L2)
        └── Properties (L3)
            └── Architecture (L4)
                └── Workflow (L5)
                    └── Automation (L6)
```

## Using the hierarchy

1. **Start at the root.** Document the observation prompting the change (failure report, consensus note, audit receipt). Without a recorded L0 trigger, the branch is blocked.
2. **Affirm principles.** Check the relevant governance principle (safety, reversibility, receipts). If it isn’t satisfied, pause and resolve the policy gap before continuing.
3. **Define objectives.** State the OCERS trait and target (e.g., “Evidence↑ by enforcing consensus receipts”). This unlocks the remaining levels.
4. **Map properties.** Capture measurable properties (deterministic receipt path, CI guard) that fulfil the objective.
5. **Design architecture.** Document the artefacts that implement those properties (bindings, modules, doc sections).
6. **Plan workflow.** Write steps/queues that wield the architecture safely. Link to `_plans/…` and bus assignments.
7. **Automate last.** Only once the above exist do we hook in scripts/CI/cron. Automation receipts must point back up-tree so reviewers can audit the chain.

## Decision journals

For steady state, each branch should keep a short journal:

- **Observation receipt:** link to bus message or memory log entry.
- **Principle reference:** cite governance/policy clause.
- **Objective ticket:** queue item or plan summary stating the OCERS delta.
- **Property checklist:** bullet list of measurable traits with links to tests/bindings.
- **Architecture diff:** pointer to the code/doc change.
- **Workflow receipt:** plan status / manager-report note.
- **Automation receipt:** stable `_report/.../summary-latest.json` or CI artifact.

Maintaining this pattern lets humans and agents “zoom” between levels quickly and keeps the cognitive load flat even as the system grows.

## System themes in practice

We prioritise work that compounds across five recurring themes:

- **Fractals:** repeat the OCERS contract at every layer. The directive-pointer guard is a good example—helper, docs, CI, and tests all enforce the same mirror. Upcoming consensus automation must follow the same pattern (docs → plan → guard → receipts).
- **Hierarchies:** never skip levels. Capture the observation and principle before implementing properties/automation. The decision tree above is the living checklist; use it before approving new guards or release flows.
- **Compounding:** favour changes that permanently raise the floor (stable receipts, automated checks). Track these in `_plans/` so compounded improvements are auditable.
- **Acceleration:** only accelerate after the pattern holds. Automate consensus CI once the receipts and docs exist so humans can move faster without sacrificing oversight.
- **Evolution:** log deltas (`memory/log.jsonl`, `_report/.../summary-latest.json`) and revisit the bindings matrix when the hierarchy shifts. Every guard should feed back into governance when it exposes new information.

Document what *worked* and *what still needs refinement* in each decision journal. Amplify the former by cloning the pattern elsewhere; route the latter back to governance before shipping more automation.

## Fractal conformance receipts

- Run `python3 -m tools.fractal.conformance --pretty --out _report/fractal/conformance/latest.json` to capture a receipt of OCERS + coordinate coverage across queue items, plans, and memory.
- Treat missing OCERS targets or `S#:L#` coordinates as blockers before promoting automation; `--strict` exits non-zero when gaps exist, making it safe to plug into CI or local preflight.
- Link the emitted `_report/fractal/conformance/latest.json` in decision journals so reviewers can inspect the organism’s health from leaves to trunk.
- Baseline allowances live in `docs/fractal/baseline.json`; lower the numbers as you backfill metadata so CI ratchets toward full coverage.
- Use `python3 tools/fractal/backfill_plans.py --apply` when plans link to queue items but lack OCERS or coordinates; the helper mirrors queue metadata into the plan documents.

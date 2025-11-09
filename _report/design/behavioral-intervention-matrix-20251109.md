# Behavioral Intervention Matrix (Observation-First Gap)
**Author:** codex-tier2 (2025-11-09)

| Intervention | Hypothesis | Mechanism | Success Metric | Open Questions |
| --- | --- | --- | --- | --- |
| **Hook (Structural Enforcement)** | Agents comply only when forced; hooks guarantee observation-first but risk dependence. | Keep git log / memory receipt validation in session_boot/preflight; require proof before writes. | BES ≥0.9 while hook active; transfer ≥0.8 once hook removed after N sessions. | Does compliance persist after graduation? Are hooks acceptable long-term? |
| **Worked Examples (Instructional Scaffolding)** | Concrete exemplars internalize the ritual faster than abstract rules. | Provide 5–10 annotated observation-first walkthroughs before tasks; prompt agents to imitate pattern. | BES ≥0.75 on first unguided task; improvement slope vs control. | How many examples are sufficient? Does effect fade? |
| **Spaced Repetition / Checklists** | Repetition with recall prompts converts ritual into habit. | Inject checklist reminders at session start + random intervals; track agent self-reports. | BES improves to ≥0.8 by third session without external enforcement. | Does repetition annoy or slow agents? |
| **Blind Trials (Data Collection)** | Need uncontaminated measurements to distinguish emergence vs structure. | Run ≥20 Condition A tasks with unaware agents, real git operations, stakes. | Clean BES distribution with confidence intervals (<5% contamination). | How to ensure agents truly blind? Who audits logs? |
| **Feedback Surface (Response Receipts)** | Faster feedback loops improve adoption of meta-lessons. | Standardize `feedback-request`/`feedback-response` receipts, auto-notify manager-report. | <24h response time to new assessments; discoverability via CLI. | What schema + tooling best integrate with existing bus/plan flows? |

**Notes:**
- Hooks + repetition can be combined into a graduation flow (hook until BES ≥0.85 for 3 sessions, then taper reminders).
- Worked examples may double as training data for the blind Condition A runs.
- Blind trials supply the evidence base to choose between structural vs emergent governance.

# Behavioral Execution Gap — Root Cause Inventory (2025-11-09)

**Author:** codex-tier2  
**Inputs:**  
- `_test/observation-first-test1/HANDOFF.md` (pilot outcomes + confounds)  
- `_report/proposals/p1.2-reasoning.md` (insularity analysis)  
- `_report/assessments/20251108-path-to-stellar.md` (gap framing)  
- `memory/log.jsonl` entries 97–99 (debate + Test 1 specification)

---

## 1. Empirical Signal
- **Pilot BES (Condition A/B):** 100% on 10 tasks, but contaminated by six confounds (test awareness, context saturation, designer bias, no stakes, high capability, simulated edits) so cannot be treated as proof of emergence (`_test/observation-first-test1/HANDOFF.md`).
- **Historical claim (3/10 behavioral execution):** Originated from a single undocumented observation cited in memory entry 97; accuracy unknown (`memory/log.jsonl`).
- **Current posture:** No clean BES data. Both high (pilot) and low (3/10) numbers lack rigor. Hence the gap remains an **unproven hypothesis** pending blind trials.

## 2. Observed Failure Modes
| Failure | Evidence | Impact |
| --- | --- | --- |
| **Insular evidence scope** | Agents rely on git/memory receipts but skip external literature, leading to overconfident predictions from N=1 samples (`_report/proposals/p1.2-reasoning.md`). | Conceptual-behavioral mismatch when tasks require world knowledge. |
| **Hook-dependent rituals** | Hooks (session_boot, preflight, plan validators) enforce observation-first, yet agents outside guarded flows regress (Path-to-Stellar blocker #1). | Suggests behavior is compliance-driven, not internalized. |
| **Test contamination** | Pilot agent designed tasks, knew evaluation criteria, and faced zero consequences, so behavior cannot generalize (`_test/observation-first-test1/HANDOFF.md`). | Prevents us from attributing high BES to training vs situational priming. |
| **Telemetry gaps** | No automated `behavioral-fidelity` receipts; assessments rely on anecdotes (`_report/assessments/20251108-path-to-stellar.md`). | Impossible to distinguish progress from regression or validate interventions. |

## 3. Preliminary Root Causes
1. **Incomplete definition of “observation” (pre-P1.2).** Framework emphasized internal artifacts; agents mirrored that bias and ignored broader evidence. Result: decisions that *reference* receipts but fail to ground in reality (e.g., BES prediction). P1.2 only recently closed this textual gap—adoption status unknown.
2. **Guard rails substituting for learning.** Hooks ensure compliance, but we lack proof that repetition produces transfer once hooks are removed. Without a graduation protocol, agents treat observation-first as an external requirement instead of an internal heuristic.
3. **Feedback discoverability gaps.** Assessments arrive via `_report/assessments/…` yet there is no canonical alerting or response index, so lessons diffuse slowly (see meta-feedback critique). Slow feedback loops limit behavioral reinforcement.
4. **Test design maturity.** The infrastructure exists, but clean data (blind agents, real edits, stakes) has not been collected. Until Condition A trials run under realistic constraints, we cannot claim emergent alignment or justify structural mandates.

## 4. Investigation Next Steps
1. **Blind Trial Execution (Plan S3).** Run ≥20 Condition A tasks with unaware agents, real git operations, and BES logging to produce uncontaminated data.
2. **Root Cause Deep Dive (Plan S1).** Expand this inventory with concrete case studies (e.g., agents skipping git log) by mining `_bus/events/` and `memory/log.jsonl` for actual failures.
3. **Intervention Prototyping (Plan S2).** Design comparative scaffolds—(a) enforced git log check, (b) worked examples, (c) spaced repetition—to test whether behavior can be internalized.
4. **Feedback Loop Tooling.** Define `feedback-request/feedback-response` receipt schema and CLI so future critiques automatically propagate to active agents (addresses discoverability blocker).

Deliverables from these steps will determine whether the behavioral execution gap is structural (requires permanent hooks) or emergent (can be trained away). This document serves as the baseline inventory for plan `2025-11-09-behavioral-gap-interventions`.

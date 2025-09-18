# Governance Trim Inventory (2025-09-18)

## .github/AGENT_ONBOARDING.md
- **Focus:** Quick Loop micro-procedure, safety defaults, file map for new agents.
- **Overlap:** Repeats coordination bus commands (session_boot, bus_claim, bus_event) that also live in docs/AGENTS.md and docs/parallel-codex.md; re-states receipts discipline and sandboxing from docs/workflow.md; mirrors file rundown found in docs/AGENTS.md “Files to Know”.
- **Gaps/Notes:** No inline links back to governance/policy anchors (only mentions docs/workflow.md implicitly). Strong candidate to shrink to high-level quickstart with canonical links.

## docs/AGENTS.md
- **Focus:** Agent quick guide with coordination, idle cadence, claim seeding, contract, safety.
- **Overlap:** “Coordination” and “Idle Cadence” sections cover same bus_event / bus_watch flows as parallel-codex playbook; “Contract” duplicates portions of governance policy + onboarding safety defaults; “Safety” echoes sandbox + receipts rules from onboarding.
- **Gaps/Notes:** Contains unique references to optional role module and maintenance tasks (idle_pickup, prune sweep). Needs clear statement whether it supersedes onboarding content or defers to it.

## docs/parallel-codex.md
- **Focus:** Detailed multi-agent playbook with session loop, consensus toolkit, failure modes.
- **Overlap:** Suggested session loop overlaps step-by-step instructions in onboarding quick loop; coordination bus and follow-up logging duplicate docs/AGENTS.md wording; consensus cadence duplicates new QUEUE-032 doc updates.
- **Gaps/Notes:** Holds authoritative consensus cadence details added in QUEUE-032/033; should remain canonical for multi-agent flows but link out instead of repeating general onboarding instructions.

## docs/workflow.md (selected sections)
- **Focus:** Architecture gate, operator mode, DNA recursion, manager cadence.
- **Overlap:** Manager ladder touches consensus cadence now mirrored in docs/parallel-codex.md; onboarding quick loop references same architecture gate steps; safety sections reiterate receipts + reversible workflow policy.
- **Gaps/Notes:** Source of truth for governance; other docs should reference instead of rephrasing.

## docs/roles.md / agents/roles.json
- **Focus:** Optional role pillars.
- **Overlap:** Mentioned in docs/AGENTS.md; onboarding does not reference roles yet. Minimal duplication, but cross-linking should clarify optional nature.

## Other surfaces inspected
- `docs/maintenance/release-readiness.md`: release checklist; periphery to governance trim.
- `_bus/messages/manager-report.jsonl`: manager directives on receipts (captured for plan step S4 requirement).

## Preliminary Opportunities
1. Make `.github/AGENT_ONBOARDING.md` a concise entry that links to `docs/AGENTS.md` for daily rhythms and to `docs/workflow.md` for governance/policy, instead of restating commands.
2. Convert overlapping bus instructions in `docs/AGENTS.md` to short summaries pointing at `docs/parallel-codex.md` sections (Coordination Bus, Follow-up Logging) to avoid duplication.
3. Ensure consensus cadence lives in one place (likely `docs/parallel-codex.md`), with onboarding and agents guide linking out.
4. Add explicit pointer from each doc to governance policy anchors (policy.json / docs/workflow.md) to keep compliance visible.

## S2/S3 Consolidation Targets
- **Onboarding Quick Loop (S2):** shrink to three high-level bullet steps (prep environment, review rails, claim task) with inline links to the canonical sections identified above; drop repeated CLI invocations except for session_boot reference; embed a callout that receipts + `planner_validate --strict` are mandatory and link to workflow policy.
- **Agents Guide (S3):** retain unique Idle Cadence + Claim Seeding guidance, but replace duplicated command snippets with references to the exact headings in `docs/parallel-codex.md`; add a “See also” block at top linking to onboarding for first-time setup and to workflow for governance.
- **Parallel Codex Playbook (S3):** treat as canonical for coordination details—add anchors (`<a id="session-loop">`) so other docs can deep-link; remove redundant onboarding language in introductory paragraphs.
- **Cross-linking (S3):** insert consistent “Policy anchor” footer referencing `governance/policy.json` and `docs/workflow.md#architecture-gate-before-writing-code` across the adjusted docs.

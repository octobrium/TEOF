# Alignment Protocol Orientation

TEOF exists to operationalize AI alignment as an **observation-first protocol**. Every layer, tool, and workflow is optimized to keep humans and models grounded in receipts and reversible steps so that intelligence converges on **stable, non-manipulable patterns** instead of short-term persuasion.

## Core Commitments

1. **Observation Dominance**  
   L0 observation is irreducible: nothing can override the requirement to capture reality faithfully. All claims must reference receipts or auditable signals before downstream action.

2. **Constitutional Ladder**  
   Governance flows top-down (L0 → L6). Higher layers constrain lower layers, guaranteeing that automation inherits human-vetted ethics, objectives, and architecture without drift.

3. **Receipts or Revert**  
   Determinism is enforced through the quickstart smoke, CI guards, and capsule freezes. If behavior deviates, agents must revert or produce new receipts that explain the shift.

4. **Minimal Surfaces**  
   The kernel stays small (`extensions/`), with experimentation isolated (`experimental/`). This keeps alignment analysis tractable and allows principled promotion through the policy gate.

5. **Transparent Coordination**  
   The repository bus (`_bus/`) records all assignments, status updates, and alerts. Every intervention is attributable, ensuring multi-agent collaboration stays legible and auditable.

## Working With TEOF

- **Start from Observation:** Run `teof brief` and inspect the receipts under `artifacts/systemic_out/latest/` to ground in measurable outputs before proposing changes.
- **Trace Constraints:** Read `governance/policy.json`, `docs/architecture.md`, and `docs/workflow.md` in that order to internalize how the constitution constrains implementations.
- **Plan in the Open:** Use the planner and bus CLIs (`tools.agent.session_boot`, `tools.agent.bus_claim`, `tools.agent.bus_message`) so others can audit your intent and progress.
- **Demand Coherence:** When refining validators, evaluators, or governance, map every suggestion back to an systemic trait and surface the receipt that proves the gap.

## Next Steps for Mastery

1. **Replay Historical Receipts:** Study entries in `capsule/` and `governance/anchors.json` to see how the protocol locks in decisions over time.
2. **Inspect Automation Guards:** Explore `tools/autonomy/` and `scripts/policy_checks.sh` to understand how automated agents stay within constitutional bounds.
3. **Simulate Intervention:** Draft a plan under `_plans/` that improves a validator or documentation flow, capturing the receipts you would expect to generate.
4. **Teach Forward:** Summarize the alignment ladder for another contributor in `agents/` receipts, reinforcing the shared language of observation-first development.

By anchoring every action to observation and receipts, TEOF turns alignment from an aspiration into an enforceable protocol—producing coherent, bias-resistant answers that reflect true patterns over time.

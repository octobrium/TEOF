# Onboarding Documentation Verification SOP (Prototype)

**Status:** Required before modifying Tier 1/Tier 2 onboarding surfaces  
**Purpose:** Prevent recurrences of the Nov 2025 Tier 1 drift by forcing every factual claim in onboarding docs to cite fresh evidence.

---

## Scope
- `docs/onboarding/README.md`
- `docs/onboarding/tier1-evaluate-PROTOTYPE.md`
- `docs/onboarding/tier2-solo-dev-PROTOTYPE.md`
- Any derivative quickstarts or landing pages that route observers into the repo

If you touch these files—or add new onboarding surfaces—you must complete this SOP first.

---

## Workflow
1. **Inventory claims.** Copy every concrete statement (counts, durations, file names, commands, outputs) into a scratch checklist.
2. **Verify via commands.** For each claim, run the minimal command that proves it. Examples:
   - `ls artifacts/systemic_out/latest/*.ensemble.json | wc -l`
   - `python3 -m teof up --eval`
   - `git rev-parse HEAD`
3. **Capture evidence receipts.**
   - Create `_report/agent/<id>/doc-verification/<timestamp>/notes.md`.
   - Include commands, timestamps, and key outputs (or link receipts such as `_report/usage/onboarding/*.json`).
4. **Update docs with grounded text.**
   - Reference the verified numbers (“10 ensemble files”) and the command that proves it.
   - Remove or rewrite any claim you cannot verify in the current run.
5. **Link receipts.**
   - In your plan step, attach the doc-verification receipt path.
   - Mention the receipt in commit/PR summaries for auditability.

---

## Tier 1 Specific Checklist
| Claim | Command | Expected Output | Receipt |
| --- | --- | --- | --- |
| `teof up --eval` produces 10 ensembles | `ls artifacts/systemic_out/latest/*.ensemble.json | wc -l` | `10` | `_report/usage/onboarding/tier1-evaluation-<timestamp>.json` |
| Quickstart artifacts exist | `ls _report/usage/onboarding/quickstart-*.json | tail -n 1` | Latest receipt path | `_report/usage/onboarding/quickstart-<timestamp>.json` |
| Runtime ≈ 5 minutes | Wall-clock measurement (shell `time` output) | ≤5m | Included in notes.md |
| Mandatory Tier 2 gate copy accurate | Visual diff vs. `docs/onboarding/README.md` | Match | Link to current commit |

Failing any row blocks edits—fix the software or update the doc to reflect reality.

---

## Logging Template (`_report/agent/<id>/doc-verification/<ts>/notes.md`)
```
# Doc Verification – <doc name>
- Agent: <id>
- Timestamp: <UTC>
- Claims verified:
  1. <claim> → <command/output>
  2. …
- Receipts referenced:
  - _report/usage/onboarding/quickstart-…
  - artifacts/systemic_out/<ts>/brief.json
```

Attach this file to your plan step before editing text.

---

## Escalation
- **If a claim fails**: stop editing, open/append to `memory/log.jsonl` or your plan notes explaining the discrepancy, and file a queue item if code changes are required.
- **If automation drifts**: update this SOP with the new canonical commands before onboarding docs change.

Following this SOP keeps onboarding aligned with TEOF’s observation-first ethos: every statement is backed by receipts, not trust.

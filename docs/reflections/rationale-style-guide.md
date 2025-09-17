# Rationale Style Guide (Draft)

Purpose: help humans and agents capture concise, evidence-linked explanations that teach future nodes.

## Structural Checklist

1. **Claim → Evidence → Intent.** Start with the decision, cite receipts or observations, state how it advances Observation/Commandments.
2. **Link receipts explicitly.** Reference `_report/...` or plan steps so auditors can replay.
3. **Call out risk & fallback.** Include the confidence level and the contingency if wrong.
4. **Close the loop.** Say what evidence will be gathered to check the decision later.

## Example Template

```
Decision: Enable autoupdate of ledger after autocollab.
Evidence: _report/autocollab/20250917T170236Z (risk<=0.2); ledger tail receipt _report/runner/...-c5a82a16.json.
Intent: Supports Commandment 2 (append-only memory) and accelerates low-risk paths.
Risk: Low — failure mode limited to ledger append; fallback = revert hook + manual run.
Follow-up: Verify ledger row via tools/runner in <24h> and log in memory.
```

## Tone Guidelines

- **Curious:** note open questions or assumptions.
- **Auditable:** avoid vague phrases; cite files + lines when possible.
- **Compact:** 3–5 sentences, or a short bullet block.
- **Accessible:** plain language first; add deep links for context.

## When to Use

- Plan updates (`tools/planner.cli step set ... --note`).
- Memory log entries describing lessons learned.
- Pull request / branch rationales (autoprops or manual).

## Optional Enhancements

- Tag commandment ID (e.g., `CMD-2`) for quick filtering.
- Include expected calibration: “Confidence 0.7 because similar change on 20250917T163219Z succeeded.”

Iterate over time: as we observe what explanations help reconciliation, feed new patterns back into this guide.

# Consensus Push Checklist (Multi-Agent)

Use this sequence whenever work is ready to land on `main`. The checklist keeps
receipts, bus messages, and peer acknowledgements in sync so parallel seats can
cross-audit before a push.

## Prerequisites
- Working tree clean (planned commits staged).
- All relevant tests/linters run locally.
- Plans/queues updated (or explicitly noted as unchanged).

## Steps
1. **Summarise the diff** — capture scope (docs, tools, receipts) in a plan
   note or reflection; run `git status -s` + `git diff --stat` to confirm
   nothing unexpected is pending.
2. **Run guardrails** — execute key checks (`pytest`, `tools.planner.validate`,
   etc.) so the audit trail points to passing runs.
3. **Generate a consensus receipt** — e.g.
   ```bash
   python3 -m tools.consensus.ledger --format jsonl \
     --limit 20 \
     --output _report/consensus/push-<slug>-<UTC>.jsonl
   ```
   Add a short summary of what was validated in the receipt body.
4. **Post to manager-report** —
   ```bash
   python3 -m tools.agent.bus_message --task manager-report --type status \
     --summary "<agent>: consensus snapshot ready" \
     --receipt _report/consensus/push-<slug>-<UTC>.jsonl \
     --meta scope=<slug> --meta status=await-ack
   ```
   Attach additional receipts (tests, docs) as needed.
5. **Request peer audit** — tag the relevant agents or leave a note specifying
   who should acknowledge the snapshot.
6. **Collect acknowledgements** — wait for at least one peer to reply on the bus
   (`--type consensus` or `status`) confirming review. Escalate if no response in
   the agreed window.
7. **Push** — once acknowledgements arrive, run `git push origin main`. If a
   rebase/merge is required, return to step 1.
8. **Post-push update** — log a follow-up status message with
   `--meta status=pushed` and note the commit hash in the plan/reflection.

## References
- `docs/parallel-codex.md` — coordination playbook.
- `docs/workflow.md` — master workflow / ladders.
- `tools.consensus.ledger`, `tools.consensus.receipts`, `tools.consensus.dashboard`
  — existing consensus utilities.

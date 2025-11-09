# Push Coordination Difficulties — 2025-11-09

## Observed issues
- Working tree contains hundreds of unrelated plan/doc/CLI changes from multiple agents (`git status` spans >300 files), so any push would accidentally mix other work.
- Unable to reach consensus on the bus: no shared note describing who owns the dirty changes and when they will be landed.
- Session guard kept expiring (>1h old) which blocks bus_event logging.
- Authenticity remediation receipts were refreshed, but the AUTH tasks still appear open because no guard verification receipt yet shows them green; without that evidence reviewers will block the push.
- `python3 -m teof operator verify --strict-plan` fails because the new November 9 automation plans reference untracked docs/receipts (confidence calibration, cold storage, impact bridge, receipts index streaming, etc.), so CI treats the tree as non-pushable.

## Impact
- Cannot safely run `python3 -m teof status`/`scan` receipts for a push that includes other agents' edits.
- Coordination friction: every attempt to "push to main" or "improve TEOF" is stalled on the dirty tree, wasting time.
- Risk of merging unreviewed plan/governance edits if someone forces a push to clear the backlog.

## Proposed remediation
1. Assign a short task (e.g., `QUEUE-9999`) to clean/sync the working tree. Each agent either lands or stashes their edits so the tree only contains the current change.
2. Add a guardrail (maybe a simple `python -m tools.autonomy.build_guard` variant) that alerts when `git status` exceeds N files before allowing `teof status --out docs/status.md` to proceed.
3. When a push is requested, require a bus thread summarizing outstanding edits + ownership so new agents know whether to proceed or defer.
4. Schedule a quick authenticity follow-up run to close `AUTH-PRIMARY_TRUTH-*` and `AUTH-UNASSIGNED-*` once guard receipts turn green, then release those claims.
5. Finish tracking the automation docs/receipts/CLIs that the November 9 plans cite so `python3 -m teof operator verify --strict-plan` passes before attempting another push.

Documented by codex-tier2 while trying to coordinate the push on 2025-11-09.

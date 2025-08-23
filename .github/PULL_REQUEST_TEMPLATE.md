## What & Why
Explain the change in terms of **Concept (goal)** and **Architecture (how/where)**.

- Area: `area/<seed|trunk|roots|bark|branches|leaves|fruit|bundles>`
- Closes: #<issue-number>

## How to test (offline)

python3 -m teof.cli validate examples_hello.json
if capsule changed:
teof freeze


## Checklist
- [ ] Links a tracked issue and applies labels (area/*, type/*, P0/P1/P2).
- [ ] No imports from `experimental/` or `archive/` into `extensions/`.
- [ ] Offline demo passes (`validate` on example).
- [ ] If capsule contents changed, ran `teof freeze` and updated `capsule/current/hashes.json`.
- [ ] Receipt schema respected (or updated in `docs/receipt.schema.json` with reason).
- [ ] Updated docs (concept/architecture/workflow) if behavior or contracts changed.

## Notes
Anything risky, migration steps, or follow-ups.

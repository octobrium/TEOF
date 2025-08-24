## Title
<TEP-#### or exploratory-spike>: <short title>

## Summary
**What** changed  
**Why** (link TEP id or mark `exploratory-spike`)  
**How** (smallest viable diff)

## Validation
- [ ] Ran `teof status`
- [ ] Ran `teof tasks --format json` and chose the top `todo`
- [ ] `teof brief` produced/updated artifacts (if applicable)
- [ ] Tests: `pytest -q` (if tests exist) / added a minimal golden
- [ ] No placeholders (`…`, `<TODO`, `PASS  # TODO`) remain
- [ ] Capsule symlink intact (`capsule/current -> v1.5`)

## Status delta
Paste ~10 lines from `docs/STATUS.md` after your change.

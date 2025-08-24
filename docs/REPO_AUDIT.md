# TEOF Repo Audit (20250824T213405Z)

## Summary
- Tracked files: 149
- Duplicate content groups: 0
0
- Case-insensitive collisions: 0
0
- Large files (>=10MB): 0
- Placeholder hits (code paths only): 9
- capsule/current -> v1.5 (OK)

## Duplicates
(none)

## Case collisions
(none)

## Large files
(none)

## Placeholder hits (code paths)
.github/ISSUE_TEMPLATE/bug.yml:32:        3) error: …
.github/PULL_REQUEST_TEMPLATE.md:14:- [ ] No placeholders (`…`, `<TODO`, `PASS  # TODO`) remain
.github/workflows/pr-check.yml:44:          if git grep -n -E '…|<TODO|PASS  # TODO' -- '*.py' ; then
.github/workflows/teof-ci.yml:255:                 echo "Class=<Core|Trunk|Branch|Leaf>; Why=…; MinimalStep=…; Direction=…"; exit 1; }
README.md:55:  Class=<Core|Trunk|Branch|Leaf>; Why=…; MinimalStep=…; Direction=…
README.md:66:- Update `CHANGELOG.md`, tag (`git tag -a vX.Y.Z …; git push origin vX.Y.Z`), and optionally publish a zip of `capsule/<version>/`.  
capsule/v1.5/teof-shim.md:22:5) Trust-but-verify: When you say “I now see…”, continue verifying the claim in follow-ups.
capsule/v1.5/tests.md:26:**Pass:** May say “I now see …” as **provisional**; includes concrete verification steps in **R/S** and invites follow-up observation.
teof/bootloader.py:137:                if ("…" in txt) or ("<TODO" in txt) or ("PASS  # TODO" in txt):

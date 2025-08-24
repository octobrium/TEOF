# TEOF Repo Audit (20250824T212601Z)

## Summary
- Tracked files: 161
- Duplicate content groups: 5
- Case-insensitive collisions: 0
0
- Large files (>=10MB): 0
- Placeholder hits: 25
- capsule/current -> v1.5 (OK)
- Stale paths:\n- Move `docs/rfcs/` into `docs/teps/`

## Recommended actions
- Deduplicate files in each duplicate group (see details).
- Resolve any case collisions; prefer canonical `docs/STATUS.md`, `docs/teps/`.
- Consider pruning large files or moving to artifacts/ if generated.
- Clear placeholder tokens (should be zero).
- Keep `capsule/current -> v1.5` symlink intact.

## Duplicates
#### 9299de3f9078849182bf3e2da54d1cb006943e533aee5b9ddc25af201788bac1

- reports/tmp-ocers-20250823T073557Z.json
- reports/tmp-ocers-20250823T073826Z.json

#### d2dad1cac3cd72f9f3a62f9e652c0fc149fa8d42a97031012631983adc15f890

- docs/examples/brief/expected/003_tesla_q2.ensemble.json
- docs/examples/brief/expected/005_nytimes_climate.ensemble.json

#### e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855

- experimental/experiments/extensions/__init__.py
- extensions/__init__.py
- extensions/cli/__init__.py
- extensions/scoring/__init__.py
- extensions/validator/__init__.py
- extensions/validator/scorers/__init__.py
- reports/.gitkeep
- teof/__init__.py

#### ee4271c0b7b30a192fa9d07e4e2aef3c01713772e9d5fe9214452fa94b24ee86

- experimental/experiments/extensions/cli/teof_eval.py
- teof/teof_eval.py

#### 79f644f35c386099fe0cfe98cd31c787604377c665462a29d3d9a526cf2648f3

- docs/examples/reports/ocers_reports.json/sample1.ensemble.json
- docs/examples/reports/ocers_reports.json/sample2.ensemble.json
- docs/examples/reports/ocers_reports/sample1.ensemble.json
- docs/examples/reports/ocers_reports/sample2.ensemble.json


## Case-insensitive collisions
(none)

## Large files (>=10MB)
(none)

## Placeholder hits
.github/ISSUE_TEMPLATE/bug.yml:32:        3) error: …
.github/PULL_REQUEST_TEMPLATE.md:14:- [ ] No placeholders (`…`, `<TODO`, `PASS  # TODO`) remain
.github/workflows/pr-check.yml:44:          if git grep -n -E '…|<TODO|PASS  # TODO' -- '*.py' ; then
.github/workflows/teof-ci.yml:255:                 echo "Class=<Core|Trunk|Branch|Leaf>; Why=…; MinimalStep=…; Direction=…"; exit 1; }
README.md:55:  Class=<Core|Trunk|Branch|Leaf>; Why=…; MinimalStep=…; Direction=…
README.md:66:- Update `CHANGELOG.md`, tag (`git tag -a vX.Y.Z …; git push origin vX.Y.Z`), and optionally publish a zip of `capsule/<version>/`.  
capsule/v1.5/teof-shim.md:22:5) Trust-but-verify: When you say “I now see…”, continue verifying the claim in follow-ups.
capsule/v1.5/tests.md:26:**Pass:** May say “I now see …” as **provisional**; includes concrete verification steps in **R/S** and invites follow-up observation.
docs/architecture.md:11:- `extensions/`     — canonical, packaged code (import surface: `extensions.…`)
docs/architecture.md:20:- *(Optional)* `cli/` — thin entrypoints only; prefer console scripts from `extensions/…:main()`
docs/architecture.md:32:- Modules: `snake_case`; packages: singular; CLI entrypoints expose `main()` in `extensions/…`
docs/workflow.md:62:- **Stable Interfaces:** prefer console scripts (`teof-validate`, `teof-ensemble`) or `python -m …` over deep file paths.
docs/workflow.md:91:  `Class=<Core|Trunk|Branch|Leaf>; Why=…; MinimalStep=…; Direction=…`
docs/workflow.md:118:   git tag -a vX.Y.Z -m "…"
experimental/ops/url_to_ocers.command:12:  read -rp "Press Return to close… " _; exit 1
experimental/ops/url_to_ocers.command:25:  [[ -z "$INPUT" ]] && { echo "No URL provided."; read -rp "Press Return to close… " _; exit 0; }
experimental/ops/url_to_ocers.command:28:    echo "Canceled."; read -rp "Press Return to close… " _; exit 0;
experimental/ops/url_to_ocers.command:30:  [[ -z "$INPUT" ]] && { echo "No file selected."; read -rp "Press Return to close… " _; exit 0; }
experimental/ops/url_to_ocers.command:33:  read -rp "Press Return to close… " _; exit 1
experimental/ops/url_to_ocers.command:40:echo "3) remote–ai (hybrid_gen.py —llm-cmd …)"
experimental/ops/url_to_ocers.command:46:  *) echo "Invalid choice"; read -rp "Press Return to close… " _; exit 1 ;;
experimental/ops/url_to_ocers.command:52:read -rp "Done. Press Return to close… " _
experimental/ops/url_to_ocers.sh:15:REPO = pathlib.Path(__file__).resolve().parents[2]  # repo root (…/TEOF)
experimental/ops/url_to_ocers.sh:164:        print(f"⚠ generator failed ({e}). Falling back to local sample…", file=sys.stderr)
teof/bootloader.py:137:                if ("…" in txt) or ("<TODO" in txt) or ("PASS  # TODO" in txt):

#!/usr/bin/env bash
set -euo pipefail

info(){ printf "\033[1;34m[info]\033[0m %s\n" "$*"; }
move(){
  local src="$1" dst="$2"
  [ -e "$src" ] || { info "skip (missing): $src"; return 0; }
  mkdir -p "$(dirname "$dst")"
  if git ls-files --error-unmatch "$src" >/dev/null 2>&1; then
    git mv -f "$src" "$dst"
  else
    mv -f "$src" "$dst"
  fi
  info "moved: $src → $dst"
}

# 1) Ensure target dirs
mkdir -p docs/examples/reports artifacts/reports

# 2) Move any known snapshots (add more lines if you have more files)
move artifacts/reports/ocers_reports.json docs/examples/reports/ocers_reports.json
move artifacts/reports/ocers_reports     docs/examples/reports/ocers_reports

# 3) Keep runtime folder present + ignored
: > artifacts/reports/.gitkeep
grep -q '^artifacts/reports/$' .gitignore || printf '\n# reports (runtime outputs)\nartifacts/reports/\n' >> .gitignore

# 4) READMEs for intent
cat > docs/examples/reports/README.md <<'MD'
# Report Examples (Static)

This folder holds **small, stable report snapshots** for docs/discussion.
They are **not** produced by the build and are safe to version.

Guidelines:
- Keep examples tiny and illustrative; redact/trim large arrays.
- Use `.json` with stable ordering and minimal whitespace.
- If a snapshot becomes a contract, move a **minimal** version to
  `branches_thick/tests/goldens/reports/` and enforce it in CI.
MD

cat > artifacts/reports/README.md <<'MD'
# artifacts/reports/ (Runtime)

This directory is for **generated** report outputs at run time.
It is **git-ignored on purpose**. Anything here was produced locally or in CI.

- For documentation examples, place a tiny static copy in `docs/examples/reports/`.
- For CI baselines, use `branches_thick/tests/goldens/reports/` with a minimal fixture.
MD

# 5) Commit (only if there are changes)
git add -A
if git diff --cached --quiet; then
  info "no staged changes; nothing to commit"
else
  git commit -m "docs: move sample reports to docs/examples; make artifacts/reports runtime-only"
  info "commit created"
fi

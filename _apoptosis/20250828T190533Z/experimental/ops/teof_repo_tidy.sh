#!/usr/bin/env bash
# teof_repo_tidy.sh — consolidate repo cleanups into a single script
set -euo pipefail

# -------------------------
# Flags
# -------------------------
DO_COMMIT=0
DO_VERIFY=0

for arg in "$@"; do
  case "$arg" in
    --commit) DO_COMMIT=1 ;;
    --verify) DO_VERIFY=1 ;;
    -h|--help)
      cat <<'USAGE'
Usage: bash teof_repo_tidy.sh [--commit] [--verify]

Actions:
  • Move ops scripts to legacy/ops/
  • Move APERTURE-GUIDELINE.md → docs/roots/
  • Move scripts/teof_cli.py → branches_thick/cli/ (remove scripts/ if empty)
  • Update Makefile to use branches_thick/cli/teof_cli.py
  • Ensure artifacts/.gitkeep
  • Archive stray --out/ → artifacts/_legacy_out/<timestamp>/
  • Remove *.egg-info from version control
  • Add standard .gitignore rules

Options:
  --commit  Create a single "chore: tidy repo layout" commit at the end.
  --verify  Run "make brief && make open_brief" to validate runtime.

This script is idempotent: safe to re-run.
USAGE
      exit 0 ;;
    *)
      echo "Unknown flag: $arg" >&2
      exit 1 ;;
  esac
done

# -------------------------
# Helpers
# -------------------------
info(){ printf "\033[1;34m[info]\033[0m %s\n" "$*"; }
warn(){ printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
err(){  printf "\033[1;31m[err]\033[0m %s\n"  "$*" >&2; }

in_git_repo() { git rev-parse --is-inside-work-tree >/dev/null 2>&1; }
is_tracked()  { git ls-files --error-unmatch "$1" >/dev/null 2>&1; }

mv_git_or_fs(){
  local src="$1"
  local dst="$2"
  [ -e "$src" ] || { warn "skip (missing): $src"; return 0; }
  mkdir -p "$(dirname "$dst")"
  if in_git_repo && is_tracked "$src"; then
    git mv -f "$src" "$dst"
  else
    mv -f "$src" "$dst"
  fi
  info "moved: $src → $dst"
}

rm_cached_if_tracked(){
  local p="$1"
  if in_git_repo && is_tracked "$p"; then
    git rm -r --cached "$p" || true
    info "untracked (kept on disk): $p"
  fi
}

portable_sed_inplace(){
  # Usage: portable_sed_inplace 's#old#new#g' file
  if sed --version >/dev/null 2>&1; then
    sed -i "$1" "$2"                 # GNU sed
  else
    sed -i '' "$1" "$2"              # BSD sed (macOS)
  fi
}

# -------------------------
# Sanity checks
# -------------------------
[ -f "Makefile" ] || warn "Makefile not found at repo root (ok if not using make)."
[ -d "trunk" ]    || warn "trunk/ not found (structure may differ; continuing)."
in_git_repo || warn "Not in a git repo; operations will be filesystem-only."

if in_git_repo; then
  if ! git diff --quiet || ! git diff --cached --quiet; then
    warn "You have uncommitted changes. Consider committing/stashing before running."
  fi
fi

# -------------------------
# 0) Archive any stray --out/ directory (old outputs)
# -------------------------
if [ -d "--out" ]; then
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  dst="artifacts/_legacy_out/$ts"
  mkdir -p "$(dirname "$dst")"
  mv "--out" "$dst"
  info "archived legacy --out/ → $dst"
fi

# -------------------------
# 1) Ops scripts → legacy/ops
# -------------------------
mkdir -p legacy/ops
for s in teof_finalize.sh teof_finalize_fix.sh teof_insta_reorg.sh teof_mop_up.sh; do
  if [ -e "$s" ]; then
    mv_git_or_fs "$s" "legacy/ops/$s"
  fi
done

# -------------------------
# 2) Aperture doc → docs/roots
# -------------------------
if [ -e "APERTURE-GUIDELINE.md" ]; then
  mkdir -p docs/roots
  mv_git_or_fs "APERTURE-GUIDELINE.md" "docs/roots/APERTURE-GUIDELINE.md"
fi

# -------------------------
# 3) scripts/teof_cli.py → branches_thick/cli
# -------------------------
if [ -e "scripts/teof_cli.py" ]; then
  mkdir -p branches_thick/cli
  mv_git_or_fs "scripts/teof_cli.py" "branches_thick/cli/teof_cli.py"
fi

# remove scripts/ if empty
if [ -d "scripts" ] && [ -z "$(ls -A scripts 2>/dev/null || true)" ]; then
  rmdir scripts || true
  info "removed empty: scripts/"
fi

# Update Makefile invocations (portable sed)
if [ -f Makefile ]; then
  portable_sed_inplace 's#scripts/teof_cli\.py#branches_thick/cli/teof_cli.py#g' Makefile
  info "updated Makefile to use branches_thick/cli/teof_cli.py"
fi

# -------------------------
# 4) Ensure artifacts/.gitkeep
# -------------------------
mkdir -p artifacts
if [ ! -f artifacts/.gitkeep ]; then
  : > artifacts/.gitkeep
  in_git_repo && git add artifacts/.gitkeep >/dev/null 2>&1 || true
  info "created: artifacts/.gitkeep"
fi

# -------------------------
# 5) Remove *.egg-info from version control + ignore
# -------------------------
if [ -d "teof.egg-info" ]; then
  rm_cached_if_tracked "teof.egg-info"
  rm -rf teof.egg-info || true
  info "deleted teof.egg-info on disk"
fi

# If any other egg-info dirs are present and tracked, untrack them.
if in_git_repo; then
  while IFS= read -r tracked; do
    case "$tracked" in
      *.egg-info/*|*.egg-info)
        git rm -r --cached "$tracked" || true
        info "untracked egg-info: $tracked"
        ;;
    esac
  done < <(git ls-files | grep -E '\.egg-info($|/)') || true
fi

# Add standard ignores
GITIGNORE=.gitignore
[ -f "$GITIGNORE" ] || : > "$GITIGNORE"
if ! grep -q '### TEOF standard ignores ###' "$GITIGNORE"; then
  cat >> "$GITIGNORE" <<'EOF'
### TEOF standard ignores ###
dist/
build/
*.egg-info/
.venv/
__pycache__/
*.pyc
artifacts/systemic_out/
EOF
  info "updated .gitignore with standard ignores"
fi

# -------------------------
# 6) Optional verify
# -------------------------
if [ "$DO_VERIFY" -eq 1 ]; then
  if command -v make >/dev/null 2>&1; then
    info "running: make brief && make open_brief"
    make brief && make open_brief
  else
    warn "'make' not found; skipping verify"
  fi
fi

# -------------------------
# 7) Optional single commit
# -------------------------
if [ "$DO_COMMIT" -eq 1 ] && in_git_repo; then
  git add -A
  if git diff --cached --quiet; then
    info "no staged changes to commit"
  else
    git commit -m "chore: tidy repo layout (ops→legacy/ops, aperture doc→docs/roots, cli→branches_thick/cli, Makefile update, archive --out, ignore egg-info, ensure artifacts/.gitkeep)"
    info "commit created"
  fi
fi

info "Done. You can re-run this script safely (idempotent)."

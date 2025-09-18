#!/usr/bin/env bash
set -euo pipefail

BASE=${1:-origin/main}
fail=0
# Hard-fail sections should set fail=1 via err(); warn-only sections print via warn().
err(){ printf '%s\n' "$@" >&2; fail=1; }
warn(){ printf '%s\n' "$@" >&2; }

# Limit scans to non-archive files
git_non_archive() { git ls-files -z | grep -zvE '^archive/'; }

# --- Capsule invariants (HARD FAIL) ---
CAP="capsule/v1.5"
req=( OGS-spec.md PROVENANCE.md README.md RELEASE.md TEOF-FUTURE.md
      calibration.md canonical-teof.md capsule-handshake.txt capsule.txt
      core-teof.md reconstruction.json teof-shim.md tests.md volatile-data-protocol.md
      hashes.json )
for f in "${req[@]}"; do
  [[ -f "$CAP/$f" ]] || err "Missing: $CAP/$f"
done

# No deprecated capsule extras outside archive (HARD FAIL)
if git_non_archive | tr '\0' '\n' | grep -E '^capsule/.*/capsule-(mini|selfreconstructing)\.txt$' >/dev/null; then
  err "Deprecated capsule extras present (capsule-mini / capsule-selfreconstructing)"
fi

# No renames/moves of capsule files vs BASE (HARD FAIL)
if git diff --name-status --diff-filter=R "$BASE"...HEAD -- "$CAP" | grep . >/dev/null; then
  err "Capsule files were renamed/moved between $BASE and HEAD — not allowed."
fi

# --- Top-level hygiene (WARN for now) ---
# Allowlist of top-level dirs/files currently present
allow_dirs=( archive capsule docs extensions experimental .github .githooks scripts bin
             governance memory reports teof tests tools _plans _bus _apoptosis _report agents queue )
allow_files=( README.md LICENSE .gitignore .editorconfig .gitattributes
              .markdownlint-cli2.jsonc .markdownlint.jsonc .markdownlintignore
              CHANGELOG.md CODE_OF_CONDUCT.md CONTRIBUTING.md NOTICE SECURITY.md TRADEMARKS.md
              pyproject.toml quickstart.md examples_hello.json
              AGENT_MANIFEST.json AGENT_MANIFEST.example.json )

# unexpected top-level directories
while IFS= read -r d; do
  [[ -z "$d" ]] && continue
  [[ "$d" == "." ]] && continue
  case " ${allow_dirs[*]} " in *" $d "*) : ;; *)
    # ignore nested paths; only top-level
    [[ "$d" == */* ]] || warn "Unexpected top–level dir: $d"
  esac
done < <(git ls-tree -d --name-only HEAD)

# unexpected top-level files
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  case " ${allow_files[*]} " in *" $f "*) : ;; *)
    warn "Unexpected file at repo root: $f"
  esac
done < <(git ls-files | awk -F/ 'NF==1')

# --- Junk globs anywhere outside archive (HARD FAIL) ---
if git_non_archive | grep -zE '(\.bak$|\.save$|(^|/)\.DS_Store$)' >/dev/null; then
  printf '%s\n' "Junk files matched (.bak, .save, .DS_Store). Run: bin/clean-duplicates --apply" >&2
  fail=1
fi

# --- UPPERCASE docs filename policy (warn by default; fail if STRICT_CAPS=1) ---
if [ -d "docs" ]; then
  upper_docs="$(git ls-files docs | grep -E 'docs/.*/.*[A-Z].*\.md$' || true)"
  if [ -n "$upper_docs" ]; then
    echo "WARN: Uppercase letters in docs filenames detected:"
    echo "$upper_docs"
    if [ "${STRICT_CAPS:-0}" = "1" ]; then
      echo "ERROR: STRICT_CAPS=1 — refusing uppercase docs filenames."
      exit 1
    fi
  fi
fi

# --- Symlink policy (warn-only) ---
if [ ! -L "capsule/current" ]; then
  echo "WARN: capsule/current is not a symlink (prefer symlink -> version dir)"
fi

exit $fail

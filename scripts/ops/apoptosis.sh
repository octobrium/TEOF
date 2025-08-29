#!/usr/bin/env bash
set -euo pipefail
APPLY="${APPLY:-0}"; NUKE="${NUKE_BRANCHES:-0}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

# Canonical top-level we KEEP (expanded to avoid trashing useful OSS meta)
KEEP_TOP=(
  ".github" "bin" "capsule" "cli" "docs" "extensions" "governance" "scripts" "tools" "tests" "queue"
  "LICENSE" "NOTICE" "README.md" "SECURITY.md" "CONTRIBUTING.md" "CODE_OF_CONDUCT.md" "CHANGELOG.md"
  "Makefile" ".gitignore" ".editorconfig" ".gitattributes" ".pre-commit-config.yaml" ".markdownlint.yml" "pyproject.toml"
)

in_keep(){ for k in "${KEEP_TOP[@]}"; do [[ "$1" == "$k" ]] && return 0; done; return 1; }
say(){ printf ">> %s\n" "$*"; }

# 1) Consolidate duplicated extensions trees → top-level extensions/
if [ -d experimental/experiments/extensions ]; then
  say "would merge experimental/experiments/extensions -> extensions/"
  if [ "$APPLY" = "1" ]; then
    mkdir -p extensions
    rsync -a --ignore-existing experimental/experiments/extensions/ extensions/ 2>/dev/null || \
      { (cd experimental/experiments && tar cf - extensions) | (cd . && tar xpf -); }
  fi
fi

# 2) Soft-archive unexpected top-level entries (reversible)
for p in * .*; do
  [[ "$p" =~ ^(\.|\.\.|\.git|_apoptosis|_report|\.bak)$ ]] && continue
  in_keep "$p" && continue
  say "would move '$p' -> _apoptosis/$STAMP/$p"
  if [ "$APPLY" = "1" ]; then
    mkdir -p "_apoptosis/$STAMP"
    git mv -k "$p" "_apoptosis/$STAMP/$p" 2>/dev/null || mv "$p" "_apoptosis/$STAMP/$p"
  fi
done

# 3) Normalize scripts into buckets (ci/dev/ops) without overwriting
mkdir -p scripts/ci scripts/dev scripts/ops
for f in $(git ls-files | grep -E '^scripts/[^/]+\.sh$' || true); do
  b="$(basename "$f")"; dest="scripts/dev/$b"
  [[ "$b" =~ (ci|check|lint|verify|guard|policy) ]] && dest="scripts/ci/$b"
  [[ "$b" =~ (deploy|ops|apoptosis|tidy) ]] && dest="scripts/ops/$b"
  [ "$f" = "$dest" ] && continue
  say "would place $f -> $dest (if missing)"
  if [ "$APPLY" = "1" ] && [ ! -e "$dest" ]; then
    git mv -k "$f" "$dest" 2>/dev/null || { mkdir -p "$(dirname "$dest")"; mv "$f" "$dest"; }
  fi
done

# 4) Install guard + .gitignore entries ONLY on APPLY
if [ "$APPLY" = "1" ]; then
  cat > scripts/ci/guard_apoptosis.sh <<'GA'
#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "❌ $*"; exit 1; }
[ -d extensions ] || fail "missing top-level 'extensions/'"
dupes=$(git ls-files | grep -E '/extensions/' | grep -v '^extensions/' || true)
[ -z "$dupes" ] || fail "found secondary 'extensions/' trees:\n$dupes"
for d in scripts scripts/ci scripts/dev scripts/ops; do [ -d "$d" ] || fail "missing: $d"; done
[ -L capsule/current ] || fail "capsule/current must be a symlink"
ver="$(readlink capsule/current || true)"; [ -n "$ver" ] || fail "capsule/current is empty"
for f in count files root; do [ -f "capsule/$ver/$f" ] || fail "missing capsule/$ver/$f"; done
echo "✅ apoptosis guard OK"
GA
  chmod +x scripts/ci/guard_apoptosis.sh

  if [ -f bin/preflight ] && ! grep -q 'guard_apoptosis.sh' bin/preflight; then
    printf '\n# apoptosis guard\nscripts/ci/guard_apoptosis.sh\n' >> bin/preflight
  fi
  if ! grep -q '^_apoptosis/' .gitignore 2>/dev/null; then
    { echo "_apoptosis/"; echo "_report/"; } >> .gitignore
  fi
fi

# 5) Optionally prune local branches already merged into main
if [ "$APPLY" = "1" ] && [ "$NUKE" = "1" ]; then
  current="$(git rev-parse --abbrev-ref HEAD)"
  git branch --merged main | sed 's/* //g' | sed 's/^ *//g' | grep -vE "^(main|$current)$" | xargs -r -n1 git branch -d
fi

printf "=== DONE (APPLY=%s, NUKE_BRANCHES=%s) ===\n" "$APPLY" "$NUKE"

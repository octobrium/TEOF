#!/usr/bin/env bash
set -euo pipefail
stamp=$(date -u +%Y%m%dT%H%M%SZ)
archive_root="archive/cleanup-$stamp"
mkdir -p "$archive_root"

echo "==> Move backup artifacts (*.bak*, *.save)"
find . -type f \( -name "*.bak*" -o -name "*.save" \) | while read -r f; do
  dest="$archive_root/$(dirname "$f")"
  mkdir -p "$dest"
  git mv "$f" "$dest/" 2>/dev/null || mv "$f" "$dest/"
done

echo "==> Move experimental/packages/ocers"
if [ -d experimental/packages/ocers ]; then
  mkdir -p "$archive_root/experimental/packages"
  git mv experimental/packages/ocers "$archive_root/experimental/packages/" 2>/dev/null || \
  mv experimental/packages/ocers "$archive_root/experimental/packages/"
fi

echo "==> Move capsule duplicates"
for f in capsule/v1.5/capsule-mini.txt capsule/v1.5/capsule-selfreconstructing.txt; do
  [ -f "$f" ] || continue
  mkdir -p "$archive_root/capsule/v1.5"
  git mv "$f" "$archive_root/capsule/v1.5/" 2>/dev/null || \
  mv "$f" "$archive_root/capsule/v1.5/"
done

echo "==> Commit"
git add -A
git commit -m "cleanup: backups, experimental ocers, capsule duplicates -> $archive_root" || true
echo "==> Done"

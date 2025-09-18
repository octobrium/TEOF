#!/usr/bin/env bash
# Install repo-managed git hooks.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
HOOK_DIR="$ROOT/.git/hooks"
HOOK_PATH="$HOOK_DIR/pre-push"
SOURCE="$ROOT/tools/hooks/pre_push.sh"

if [ ! -d "$HOOK_DIR" ]; then
  mkdir -p "$HOOK_DIR"
fi

if [ -e "$HOOK_PATH" ] && [ ! -L "$HOOK_PATH" ]; then
  mv "$HOOK_PATH" "${HOOK_PATH}.backup"
  echo "Existing pre-push hook backed up to ${HOOK_PATH}.backup"
fi

ln -sf "$SOURCE" "$HOOK_PATH"
chmod +x "$SOURCE"
echo "Installed pre-push hook → $SOURCE"

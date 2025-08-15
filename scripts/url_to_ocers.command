#!/bin/bash
set -euo pipefail

# --- auto-detect TEOF root by walking up until we find 'capsule' ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEOF_ROOT="$SCRIPT_DIR"
while [ ! -d "$TEOF_ROOT/capsule" ] && [ "$TEOF_ROOT" != "/" ]; do
  TEOF_ROOT="$(dirname "$TEOF_ROOT")"
done
if [ ! -d "$TEOF_ROOT/capsule" ]; then
  echo "❌ Could not find TEOF root (missing 'capsule' folder)."
  read -rp "Press Return to close… " _; exit 1
fi
echo "📂 TEOF root detected at: $TEOF_ROOT"

# --- input type ---
echo "Select input type:"
echo "1) URL"
echo "2) File"
read -rp "Enter 1 or 2: " choice

INPUT=""
if [[ "$choice" == "1" ]]; then
  read -rp "Enter the URL: " INPUT
  [[ -z "$INPUT" ]] && { echo "No URL provided."; read -rp "Press Return to close… " _; exit 0; }
elif [[ "$choice" == "2" ]]; then
  INPUT="$(/usr/bin/osascript -e 'POSIX path of (choose file with prompt "Select a file to convert to OCERS:")')" || {
    echo "Canceled."; read -rp "Press Return to close… " _; exit 0;
  }
  [[ -z "$INPUT" ]] && { echo "No file selected."; read -rp "Press Return to close… " _; exit 0; }
else
  echo "Invalid choice."
  read -rp "Press Return to close… " _; exit 1
fi

# --- generator menu ---
echo "Select generator:"
select GENERATOR in "local-sample" "local-advanced" "remote-ai"; do
  case "$REPLY" in
    1|2|3) break ;;
    *) echo "Enter 1, 2, or 3." ;;
  esac
done

# --- call the real worker ---
export TEOF_REPO="$TEOF_ROOT"
/bin/bash "$TEOF_ROOT/scripts/url_to_ocers.sh" "$INPUT" "$GENERATOR"

read -rp "Done. Press Return to close… " _

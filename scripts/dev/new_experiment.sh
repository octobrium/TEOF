#!/usr/bin/env bash
set -euo pipefail
[ $# -ge 1 ] || { echo "Usage: $0 <experiment-name-kebab> [YYYY-MM-DD]"; exit 1; }
NAME="$1"; DATE="${2:-$(date +%Y-%m-%d)}"
DIR="experiments/${DATE}-${NAME}"
mkdir -p "$DIR"
cat > "$DIR/EXPERIMENT.md" <<EOM
# Title: ${NAME//-/ }
State: ACTIVE
Intent: <what you’re testing>
Outcome: <fill when DONE>
Links: <PRs/commits/docs>
EOM
echo "created $DIR/EXPERIMENT.md"

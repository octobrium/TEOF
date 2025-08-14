#!/usr/bin/env bash
set -euo pipefail
# Usage: ./teof-validate.sh "<prompt>" model_id runner_digest commit_sha
PROMPT="$1"; MODEL="$2"; RUNNER="$3"; COMMIT="$4"

tmp="$(mktemp -d)"
for i in 1 2 3; do
  # Replace this block with your model call; must force temp=0 and shortest-valid.
  # Save raw output to $tmp/out$i.txt and a minimal runmeta$i.json
  echo "$PROMPT" > "$tmp/prompt.txt"
  # --- BEGIN: user-integrator should swap this for their runtime ----
  # Simulate a model call by reading a file or echo (placeholder)
  cp ./sample_outputs/ocers_ok.json "$tmp/out$i.txt"
  # --- END -----------------------------------------------------------
  cat > "$tmp/runmeta$i.json" <<JSON
{"model":"$MODEL","runner_digest":"$RUNNER","temp":"0"}
JSON
done

# Compare outputs for byte-identical determinism
if ! cmp -s "$tmp/out1.txt" "$tmp/out2.txt" || ! cmp -s "$tmp/out2.txt" "$tmp/out3.txt"; then
  echo "Determinism check: outputs differ across temp=0 runs"
  DET="WARN"
else
  DET="OK"
fi

# Validate one of them (identical or first)
python3 validator/teof_validator.py --input "$tmp/out1.txt" --runmeta "$tmp/runmeta1.json" --commit "$COMMIT"
code=$?
echo "determinism=$DET"
rm -rf "$tmp"
exit $code

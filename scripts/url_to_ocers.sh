#!/bin/bash
# URL/File → OCERS → Validate → Score (macOS, venv-first)

set -euo pipefail

# ---------------------------------------
# 0) Locate TEOF repo root (TEOF_REPO > walk-up > choose-folder)
# ---------------------------------------
if [ -n "${TEOF_REPO:-}" ] && [ -d "$TEOF_REPO" ]; then
  REPO="$TEOF_REPO"
else
  HERE="$(cd "$(dirname "$0")" && pwd)"
  PROBE="$HERE"
  while [ "$PROBE" != "/" ] && [ ! -d "$PROBE/capsule" ]; do
    PROBE="$(dirname "$PROBE")"
  done
  if [ -d "$PROBE/capsule" ]; then
    REPO="$PROBE"
  else
    REPO="$(/usr/bin/osascript -e 'POSIX path of (choose folder with prompt "Select your TEOF repository folder (root):")')" || { echo "Canceled."; exit 0; }
  fi
fi
cd "$REPO" || { echo "Invalid repo path: $REPO"; exit 1; }

# ---------------------------------------
# 1) Python resolver: venv > HB 3.11 > system
#    Auto-bootstraps venv with baseline deps for URL mode.
# ---------------------------------------
ensure_venv() {
  if [ ! -x ".venv/bin/python" ]; then
    if [ -x "/opt/homebrew/bin/python3.11" ]; then
      /opt/homebrew/bin/python3.11 -m venv .venv
    else
      python3 -m venv .venv
    fi
    ./.venv/bin/python -m pip install -U pip >/dev/null
    if [ -f "extensions/requirements.txt" ]; then
      ./.venv/bin/pip install -r extensions/requirements.txt >/dev/null
    else
      ./.venv/bin/pip install requests beautifulsoup4 >/dev/null
    fi
  fi
}

if [ -d ".venv" ]; then
  ensure_venv
  PY="./.venv/bin/python"
elif [ -x "/opt/homebrew/bin/python3.11" ]; then
  PY="/opt/homebrew/bin/python3.11"
else
  PY="python3"
fi

# ---------------------------------------
# 2) Inputs (CLI args optional)
#    $1 = input (URL or file path), $2 = generator hint or command
# ---------------------------------------
ARG_INPUT="${1:-}"
ARG_GEN="${2:-}"

if [[ -z "$ARG_INPUT" ]]; then
  echo "Select input type:"
  echo "1) URL"
  echo "2) File"
  read -r -p "Enter 1 or 2: " CHOICE
  if [[ "$CHOICE" == "1" ]]; then
    read -r -p "Enter the URL: " ARG_INPUT
    [[ -z "$ARG_INPUT" ]] && { echo "No URL provided."; exit 0; }
  elif [[ "$CHOICE" == "2" ]]; then
    ARG_INPUT="$(/usr/bin/osascript -e 'POSIX path of (choose file with prompt "Select a source file (text will be extracted and turned into OCERS):")')" || { echo "Canceled."; exit 0; }
    [[ -z "$ARG_INPUT" ]] && { echo "No file selected."; exit 0; }
  else
    echo "Invalid choice."; exit 1
  fi
fi

if [[ -z "$ARG_GEN" ]]; then
  echo "Select generator:"
  select ARG_GEN in "local-sample" "local-advanced" "remote-ai"; do
    case "$REPLY" in 1|2|3) break ;; *) echo "Enter 1, 2, or 3." ;; esac
  done
fi

# ---------------------------------------
# 3) Paths & helpers
# ---------------------------------------
TS="$(date -u +"%Y%m%dT%H%M%SZ")"
OUT_DIR="extensions/scoring/out"
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/ocers_${TS}.json"
COMMIT_SHA="$("$PY" - <<'PY' 2>/dev/null || echo local
import subprocess, sys
try:
    print(subprocess.check_output(["git","rev-parse","--short","HEAD"], stderr=subprocess.DEVNULL).decode().strip())
except Exception:
    print("local")
PY
)"

EVAL_CLI="extensions/cli/teof_eval.py"
VALIDATOR_PY="validator/teof_validator.py"
SCORER_PY="scoring/teof_score.py"

have_eval_cli() { [ -f "$EVAL_CLI" ]; }
have_validator() { [ -f "$VALIDATOR_PY" ]; }
have_scorer()    { [ -f "$SCORER_PY" ]; }

run_validate_and_score_with_cli () {
  "$PY" "$EVAL_CLI" validate --input "$OUT" --commit "$COMMIT_SHA"
  "$PY" "$EVAL_CLI" score    --input "$OUT" --commit "$COMMIT_SHA"
}

run_validate_and_score_fallback () {
  if ! have_validator || ! have_scorer; then
    echo "Missing validator or scorer:"
    echo "  validator: $VALIDATOR_PY (exists: $(have_validator && echo yes || echo no))"
    echo "  scorer   : $SCORER_PY   (exists: $(have_scorer && echo yes || echo no))"
    exit 1
  fi
  "$PY" "$VALIDATOR_PY" --input "$OUT" --runmeta /dev/null --commit "$COMMIT_SHA" || true
  "$PY" "$SCORER_PY"    --input "$OUT" --commit "$COMMIT_SHA"
}

resolve_gen_cmd () {
  local hint="$1"
  # If looks like a concrete command, use as-is
  if [[ "$hint" == *"python"* || "$hint" == *"ollama"* || "$hint" == *" "*
     ]]; then echo "$hint"; return; fi
  case "$hint" in
    local-sample|local-advanced|remote-ai)
      if [ -f "extensions/cli/generators/hybrid_gen.py" ]; then
        echo "\"$PY\" extensions/cli/generators/hybrid_gen.py --profile \"$hint\""
      else
        cat <<'PY'
python - <<PY
import sys, json, re
text=sys.stdin.read()
paras=[p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
O=paras[0][:400] if paras else ""
C="\n".join(paras[1:3])[:800] if len(paras)>1 else ""
nums=re.findall(r"\b\d[\d,\.%]*\b", text)
links=re.findall(r"https?://\S+", text)
quotes=re.findall(r"[“\"' ]([^”\"']{12,280})[”\"' ]", text)
E=[]
if nums: E.append("numbers: "+", ".join(nums[:6]))
if links: E.append("links:\n- " + "\n- ".join(links[:5]))
if quotes: E.append("quotes:\n- " + "\n- ".join(quotes[:4]))
E="\n".join(E)[:1200]
R="Assumptions/biases not fully extracted; verify sources; note missing counterpoints."
S="1) Verify key facts from ≥2 sources.\n2) Extract core numbers/dates.\n3) Summarize risks and next steps."
print(json.dumps({"O":O,"C":C,"E":E,"R":R,"S":S}, indent=2))
PY
PY
      fi
      ;;
    *) echo "$hint" ;;
  esac
}

GEN_CMD="$(resolve_gen_cmd "$ARG_GEN")"

# ---------------------------------------
# 4) Build OCERS from URL or File
# ---------------------------------------
if [[ "$ARG_INPUT" =~ ^https?:// ]]; then
  if have_eval_cli; then
    "$PY" "$EVAL_CLI" from-url \
      --url "$ARG_INPUT" \
      --output "$OUT" \
      --commit "$COMMIT_SHA" \
      --generator-cmd "$GEN_CMD"
    run_validate_and_score_with_cli
  else
    # Ensure deps exist for URL fallback
    "$PY" - <<'PY' || { echo "Install deps in venv or extensions/requirements.txt"; exit 1; }
try:
    import requests, bs4  # type: ignore
except Exception:
    raise SystemExit(1)
print("deps-ok")
PY
    PAGE_TXT="$("$PY" - <<PY
import sys, requests, bs4
url = sys.argv[1]
r = requests.get(url, timeout=20)
r.raise_for_status()
soup = bs4.BeautifulSoup(r.text, 'html.parser')
for t in soup(['script','style','noscript']): t.extract()
print(soup.get_text(' ', strip=True))
PY
"$ARG_INPUT"
)"
    /bin/bash -lc 'cat <<TXT | '"$GEN_CMD"' > '"$OUT"'
'"$PAGE_TXT"'
TXT'
    run_validate_and_score_fallback
  fi
else
  FILE_PATH="$ARG_INPUT"
  if [ ! -f "$FILE_PATH" ]; then echo "File not found: $FILE_PATH"; exit 1; fi
  if file -b "$FILE_PATH" | grep -qi 'text'; then
    CONTENT_CMD=(/bin/cat "$FILE_PATH")
  else
    if command -v textutil >/dev/null 2>&1; then
      TMPTXT="$(mktemp)"; textutil -convert txt -stdout "$FILE_PATH" > "$TMPTXT" || true
      CONTENT_CMD=(/bin/cat "$TMPTXT")
    else
      CONTENT_CMD=(/bin/cat "$FILE_PATH")
    fi
  fi
  "${CONTENT_CMD[@]}" | /bin/bash -lc "$GEN_CMD" > "$OUT"
  echo "Wrote OCERS to $OUT"
  if have_eval_cli; then run_validate_and_score_with_cli; else run_validate_and_score_fallback; fi
fi

echo
echo "✓ Finished."
echo "Output OCERS: $OUT"
if have_eval_cli; then
  echo "Re-run scoring: \"$PY\" $EVAL_CLI score --input \"$OUT\" --commit \"$COMMIT_SHA\""
else
  echo "Re-run scoring: \"$PY\" $SCORER_PY --input \"$OUT\" --commit \"$COMMIT_SHA\""
fi

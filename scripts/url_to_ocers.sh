#!/bin/bash
# URL/File → OCERS → Validate → Score

set -euo pipefail

# ---- locate TEOF root by walking up until 'capsule' exists ----
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEOF_ROOT="$SCRIPT_DIR"
while [ ! -d "$TEOF_ROOT/capsule" ] && [ "$TEOF_ROOT" != "/" ]; do
  TEOF_ROOT="$(dirname "$TEOF_ROOT")"
done
if [ ! -d "$TEOF_ROOT/capsule" ]; then
  echo "❌ Could not find TEOF root (missing 'capsule' folder)."
  exit 1
fi

# ---- pick python ----
PY="$TEOF_ROOT/.venv/bin/python"
if [ ! -x "$PY" ]; then PY="$(command -v python3 || true)"; fi
if [ -z "${PY:-}" ]; then echo "❌ python3 not found"; exit 1; fi

# ---- args ----
INPUT="${1:-}"
GENERATOR="${2:-local-sample}"  # local-sample | local-advanced | remote-ai

# If the user’s wrapper ever passes args in reverse, fix it:
if [[ -z "${INPUT}" && "${GENERATOR:-}" =~ ^https?:// ]]; then
  INPUT="$GENERATOR"
  GENERATOR="local-sample"
fi

MODE="file"
if [[ "${INPUT}" =~ ^https?:// ]]; then MODE="url"; fi

TS="$(date -u +"%Y%m%dT%H%M%SZ")"
OUT_DIR="$TEOF_ROOT/extensions/scoring/out"
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/ocers_${TS}.json"

echo "→ Repo:    $TEOF_ROOT"
echo "→ Python:  $PY"
echo "→ Mode:    $MODE  | Generator: $GENERATOR"
echo "→ Output:  $OUT"

TMP="$(mktemp -d)"
RAW_TXT="$TMP/raw.txt"
RUNMETA="$TMP/runmeta.json"

# ---- get raw text ----
if [ "$MODE" = "url" ]; then
  # require requests/bs4
  if ! "$PY" - <<'PY' >/dev/null 2>&1
try:
    import requests, bs4  # type: ignore
except Exception:
    raise SystemExit(1)
PY
  then
    echo "❌ URL mode needs requests + beautifulsoup4"
    echo "   $TEOF_ROOT/.venv/bin/pip install requests beautifulsoup4"
    exit 1
  fi

  # NOTE: pass the URL as argv[1] to the heredoc by using `python - "$INPUT"`
  "$PY" - "$INPUT" <<'PY' > "$RAW_TXT"
import sys, re
import requests
from bs4 import BeautifulSoup

url = sys.argv[1] if len(sys.argv) > 1 else ""
if not url:
    sys.exit("no url")

try:
    resp = requests.get(url, timeout=20, headers={"User-Agent":"Mozilla/5.0"})
    resp.raise_for_status()
except Exception as e:
    sys.exit(f"fetch error: {e}")

soup = BeautifulSoup(resp.text, "html.parser")
for t in soup(["script","style","noscript"]): t.decompose()
text = soup.get_text("\n")
text = re.sub(r'\n{3,}', '\n\n', text).strip()
print(text)
PY

else
  # file path
  if [ ! -f "$INPUT" ]; then
    echo "Error reading url. The file doesn’t exist."
    rm -rf "$TMP"; exit 1
  fi
  if file -b "$INPUT" | grep -qi 'text'; then
    cat "$INPUT" > "$RAW_TXT"
  elif command -v textutil >/dev/null 2>&1; then
    textutil -convert txt -stdout "$INPUT" > "$RAW_TXT" || cp "$INPUT" "$RAW_TXT"
  else
    cat "$INPUT" > "$RAW_TXT"
  fi
fi

# ---- generators ----
gen_local_sample () {
  "$PY" - <<'PY'
import sys, json, re
text = sys.stdin.read()
paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
O = paras[0][:400] if paras else ""
C = "\n".join(paras[1:3])[:800] if len(paras) > 1 else ""
nums   = re.findall(r"\b\d[\d,.\%]*\b", text)
links  = re.findall(r"https?://\S+", text)
quotes = re.findall(r"[\"“']([^\"”']{12,280})[\"”']", text)
E_parts = []
if nums:   E_parts.append("numbers: " + ", ".join(nums[:6]))
if links:  E_parts.append("links:\n- " + "\n- ".join(links[:5]))
if quotes: E_parts.append("quotes:\n- " + "\n- ".join(quotes[:4]))
E = "\n".join(E_parts)[:1200]
R = "Assumptions/biases may be present; verify sources; note counterpoints."
S = "1) Verify key facts from ≥2 sources.\n2) Extract core numbers/dates.\n3) Summarize risks and next steps."
print(json.dumps({"O":O,"C":C,"E":E,"R":R,"S":S}, indent=2))
PY
}

gen_local_advanced () {
  if [ -f "$TEOF_ROOT/extensions/cli/generators/hybrid_gen.py" ]; then
    "$PY" "$TEOF_ROOT/extensions/cli/generators/hybrid_gen.py" || return 1
  else
    return 1
  fi
}

gen_remote_ai () {
  if [ -f "$TEOF_ROOT/extensions/cli/generators/hybrid_gen.py" ]; then
    "$PY" "$TEOF_ROOT/extensions/cli/generators/hybrid_gen.py" --llm-cmd "ollama run llama3.1" || return 1
  else
    return 1
  fi
}

GEN_OK=0
case "$GENERATOR" in
  local-sample)   cat "$RAW_TXT" | gen_local_sample   > "$OUT" || GEN_OK=1 ;;
  local-advanced) cat "$RAW_TXT" | gen_local_advanced > "$OUT" || GEN_OK=1 ;;
  remote-ai)      cat "$RAW_TXT" | gen_remote_ai      > "$OUT" || GEN_OK=1 ;;
  *) echo "unknown generator '$GENERATOR'"; GEN_OK=1 ;;
esac

if [ $GEN_OK -ne 0 ]; then
  echo "⚠️generator failed — falling back to local-sample heuristic…"
  cat "$RAW_TXT" | gen_local_sample > "$OUT"
fi

echo "ok"

# ---- validate + score ----
cat > "$RUNMETA" <<JSON
{"model":"$GENERATOR","runner_digest":"cli","temp":"0"}
JSON

VAL="$TEOF_ROOT/extensions/validator/teof_validator.py"
if [ ! -f "$VAL" ]; then VAL="$TEOF_ROOT/validator/teof_validator.py"; fi
COMMIT_SHA="$(git -C "$TEOF_ROOT" rev-parse --short HEAD 2>/dev/null || echo local)"

"$PY" "$VAL" --input "$OUT" --runmeta "$RUNMETA" --commit "$COMMIT_SHA" || true

SCORE="$TEOF_ROOT/extensions/scoring/teof_score.py"
if [ -f "$SCORE" ]; then
  "$PY" "$SCORE" --input "$OUT" --commit "$COMMIT_SHA" || true
fi

rm -rf "$TMP"

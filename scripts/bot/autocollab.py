#!/usr/bin/env python3
import os, sys, re, json, subprocess, textwrap, random, datetime, glob, shlex
from pathlib import Path, PurePosixPath

try:
    import yaml, requests  # pip install pyyaml requests
except Exception:
    print("Deps missing: pip install pyyaml requests", file=sys.stderr); sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "scripts" / "bot" / "tasks.yaml"
FITNESS = ROOT / "governance" / "teof_fitness.yaml"

LLM_BASE  = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_KEY   = os.getenv("LLM_API_KEY", "")
DRY_RUN   = os.getenv("DRY_RUN", "0") == "1"
TASK_ID   = os.getenv("TASK_ID", "")

# budgets (soft caps)
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS","0") or "0")
LLM_PRICE_PER_1K_CENTS = int(os.getenv("LLM_PRICE_PER_1K_CENTS","0") or "0")
LLM_MAX_CENTS = int(os.getenv("LLM_MAX_CENTS","0") or "0")
LLM_EXPECTED_OUTPUT_TOKENS = int(os.getenv("LLM_EXPECTED_OUTPUT_TOKENS","800") or "800")

LEDGER_COMMIT = os.getenv("LEDGER_COMMIT","0") == "1"

def run(cmd, check=True, capture=False, env=None):
    if capture:
        return subprocess.run(cmd, check=check, text=True, capture_output=True, env=env).stdout
    subprocess.run(cmd, check=check, env=env); return ""

def git(*args, capture=False): return run(["git", *args], capture=capture)

# config
cfg = yaml.safe_load(TASKS.read_text(encoding="utf-8"))
fit = yaml.safe_load(FITNESS.read_text(encoding="utf-8"))
MAX_LINES = int(cfg.get("max_lines", 120))
ALLOW = cfg.get("allow_globs", [])
TASKS_LIST = cfg.get("tasks", [])

# choose task (deterministic per day unless TASK_ID given)
if TASK_ID:
    task = next((t for t in TASKS_LIST if t["id"] == TASK_ID), None)
else:
    seed = datetime.date.today().isoformat()
    task = random.Random(seed).choice(TASKS_LIST) if TASKS_LIST else None
if not task: sys.exit(0)

# context (docs-only)
def sample_context(globs, max_chars=4000):
    files = []
    for g in globs:
        for p in glob.glob(str(ROOT / g), recursive=True):
            pp = Path(p)
            if pp.is_file() and pp.stat().st_size < 200_000:
                files.append(pp)
    chunks, total = [], 0
    for fp in sorted(files)[:20]:
        try: txt = fp.read_text(encoding="utf-8")
        except Exception: continue
        block = f"\n===== FILE:{fp.relative_to(ROOT)} =====\n{txt}"
        if total + len(block) > max_chars: break
        chunks.append(block); total += len(block)
    return "\n".join(chunks)

SYSTEM = f"""You are a cautious editor.
Output ONLY a unified diff in a ```diff fenced block``` that:
- Modifies files ONLY matching: {ALLOW}
- Total changed lines ≤ {MAX_LINES}
- No renames, moves, or deletions; only in-place edits.
- No code semantics; docs clarity/hygiene only.
"""
USER = textwrap.dedent(f"""Task: {task['id']} — {task['name']}
Description:
{task['description']}
Guidance:
{task.get('guidance','')}
Context:
{sample_context(ALLOW)}
""")

# budget estimate (very rough: ~4 chars/token)
def est_tokens(s: str) -> int: return max(1, (len(s) + 3) // 4)
est_input = est_tokens(SYSTEM) + est_tokens(USER)
est_total = est_input + LLM_EXPECTED_OUTPUT_TOKENS
if LLM_MAX_TOKENS and est_total > LLM_MAX_TOKENS:
    print(f"Budget: est_total_tokens={est_total} > cap={LLM_MAX_TOKENS}; exiting."); sys.exit(0)
if LLM_PRICE_PER_1K_CENTS and LLM_MAX_CENTS:
    est_cents = (est_total * LLM_PRICE_PER_1K_CENTS + 999) // 1000
    if est_cents > LLM_MAX_CENTS:
        print(f"Budget: est_cents≈{est_cents} > cap={LLM_MAX_CENTS}; exiting."); sys.exit(0)

# OpenAI-compatible call
def call_llm(system, user):
    if not LLM_KEY: return ""
    url = LLM_BASE.rstrip("/") + "/chat/completions"
    payload = {"model": LLM_MODEL, "temperature": 0.2,
               "messages":[{"role":"system","content":system},
                           {"role":"user","content":user}]}
    r = requests.post(url, headers={"Authorization":f"Bearer {LLM_KEY}","Content-Type":"application/json"},
                      data=json.dumps(payload), timeout=90)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

raw = call_llm(SYSTEM, USER)
if not raw: sys.exit(0)

# extract diff (handle CRLF)
m = re.search(r"```(?:diff|patch)?\r?\n(.*?)```", raw, re.S)
if not m: sys.exit(0)
patch = m.group(1).strip()
if not re.search(r"^diff --git ", patch, re.M): sys.exit(0)

# apply on temp branch
branch = f"autocollab/{datetime.date.today().isoformat()}-{task['id']}"
git("fetch", "origin")
try: git("checkout", "-B", branch)
except Exception: git("checkout", "-b", branch)

tmp = ROOT / "_tmp.patch"
tmp.write_text(patch, encoding="utf-8")
try: run(["git", "apply", "--3way", "--index", str(tmp)])
except subprocess.CalledProcessError:
    git("reset", "--hard"); sys.exit(0)

# reject renames/deletes; allowlist + size
name_status = git("diff", "--staged", "--name-status", capture=True).splitlines()
for ln in name_status:
    status, path = ln.split("\t", 1)
    if status != "M":
        git("reset", "--hard"); sys.exit(0)

numstat = git("diff", "--staged", "--numstat", capture=True).splitlines()
changed, total = [], 0
for ln in numstat:
    a,b,p = ln.split("\t")
    a = 0 if a == "-" else int(a)
    b = 0 if b == "-" else int(b)
    total += a + b
    rp = PurePosixPath(p).as_posix()
    if any(PurePosixPath(rp).match(g.replace("\\","/")) for g in ALLOW):
        changed.append(rp)
    else:
        git("reset","--hard"); sys.exit(0)

if total > MAX_LINES:
    git("reset","--hard"); sys.exit(0)

# fitness (doctor proxy via hints)
weights = fit.get("weights", {}); threshold = int(fit.get("threshold", 75))
small = int(fit.get("hints", {}).get("small_lines", 80))
score = 0
score += weights.get("diff_small", 0) if total <= small else int(weights.get("diff_small", 0) * 0.4)
score += weights.get("path_respect", 0)

ci_ok = False
for cmd in fit.get("hints", {}).get("ci_cmds", []):
    parts = shlex.split(cmd); exe = parts[0]
    if Path(exe).exists():
        try:
            if os.access(exe, os.X_OK): run(parts)
            else: run(["bash", *parts])
            ci_ok = True; break
        except Exception: pass
if ci_ok: score += weights.get("ci_green", 0)

# commit identity in CI
if os.getenv("CI"):
    run(["git","config","user.email","teof-bot@users.noreply.github.com"])
    run(["git","config","user.name","teof-bot"])
run(["git","commit","-m", f"bot: {task['id']} — {task['name']}"])

# decide outcome
outcome = "skipped"
if DRY_RUN and os.getenv("CI"):
    git("reset","--hard"); outcome = "dry_run"
elif score < threshold:
    git("reset","--hard"); outcome = "score_below_threshold"
else:
    run(["git","push","-u","origin",branch]); outcome = "pushed"
    try:
        run(["gh","pr","create",
             "--title", f"bot: {task['id']} — {task['name']}",
             "--body",  f"Model: {LLM_MODEL}\nLines: {total}\nFiles: {len(changed)}\n",
             "--label", "bot:autocollab"], check=True)
    except Exception:
        repo = os.getenv("GITHUB_REPOSITORY"); token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        if repo and token:
            pr = requests.post(f"https://api.github.com/repos/{repo}/pulls",
                               headers={"Authorization":f"token {token}",
                                        "Accept":"application/vnd.github+json"},
                               json={"title": f"bot: {task['id']} — {task['name']}",
                                     "body":  f"Model: {LLM_MODEL}\nLines: {total}\nFiles: {len(changed)}\n",
                                     "head": branch, "base":"main"}, timeout=60)
            if pr.ok:
                num = pr.json().get("number")
                try:
                    requests.post(f"https://api.github.com/repos/{repo}/issues/{num}/labels",
                                  headers={"Authorization":f"token {token}",
                                           "Accept":"application/vnd.github+json"},
                                  json={"labels":["bot:autocollab"]}, timeout=60)
                except Exception: pass

# ledger
from datetime import datetime, timezone
entry = {
    "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "task_id": task["id"], "task_name": task["name"],
    "model": LLM_MODEL, "est_tokens": est_total,
    "score": score, "threshold": threshold,
    "changed_files": len(changed), "paths": changed, "outcome": outcome
}
(ROOT/"_report").mkdir(parents=True, exist_ok=True)
with (ROOT/"_report/ledger.jsonl").open("a", encoding="utf-8") as f:
    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

if LEDGER_COMMIT:
    with (ROOT/"governance/ledger.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    try:
        run(["git","add","governance/ledger.jsonl"])
        run(["git","commit","-m","governance: append ledger entry"])
    except Exception:
        pass

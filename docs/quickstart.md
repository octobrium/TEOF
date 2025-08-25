# Quickstart

## 0) Clone
```bash
git clone https://github.com/octobrium/TEOF.git
cd TEOF
```

## 1) First-time setup (repo health)
Run the one-shot bootstrap, which normalizes line endings, fixes TABs in Makefiles, ensures scripts are executable, installs the pre-commit doctor, and runs basic checks.

```bash
tools/bootstrap.sh
```

You should see ✅ messages. From now on, every `git commit` will run the doctor automatically (you can bypass in emergencies with `SKIP_DOCTOR=1 git commit ...`).

## 2) Install (editable)
Use your preferred environment (venv/conda/pipx). Example with venv:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 3) Run the brief pipeline
```bash
teof brief
```

Artifacts appear in:
```
artifacts/ocers_out/<UTCSTAMP>/
artifacts/ocers_out/latest/
```

---

### Notes
- If you cloned before adding bootstrap/doctor, just run `tools/bootstrap.sh` once in your existing checkout.
- Pre-commit doctor runs fast and only checks the few invariants that bite most often (line endings, Makefile TABs, script executability, etc.).

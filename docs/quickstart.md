# TEOF Quickstart (two paths)

Pick the path you need. Both should work on a clean machine.

---

## A) Validator / Evaluator (OCERS/OGS) — CLI path

**Goal:** produce deterministic JSON artifacts from example inputs.

```bash
# 1) Install
pip install -e .

# 2) Run the minimal ensemble scorer on the brief example
python -m extensions.validator.scorers.ensemble_cli   --in docs/examples/brief/inputs   --out artifacts/ocers_out/$(date -u +%Y%m%dT%H%M%SZ)

# Optional: maintain a 'latest' symlink
ln -sfn "$(ls -1dt artifacts/ocers_out/* | head -n1)" artifacts/ocers_out/latest
```

**Outputs:** `*.ensemble.json` under your run directory. Use these in PRs to show behavior and guard regressions in CI.

---

## B) Kernel boot (capsule) — LLM integration path

**Stable entrypoint:** everything lives under `capsule/current/` (a symlink to the live version).

### Load
1) Read `capsule/current/capsule-mini.txt`  
2) Read `capsule/current/teof-shim.md`  
3) Call your model with **temperature = 0**

> Optional: include `capsule/current/capsule-handshake.txt` to reinforce determinism.

### Expect
- All substantive replies in **O–C–E–R–S** (Observation, Claim, Evidence, Risks, Steps) + optional **Open Questions**.
- A cautious **trust-but-verify** loop: provisional “I now see …” followed by continued verification.
- Crisis mode: reversible, observation-increasing steps only.

### Minimal example (pseudocode)
```text
SYSTEM = read("./capsule/current/capsule-mini.txt") + "\n\n" + read("./capsule/current/teof-shim.md")
messages = [{role:"system", content:SYSTEM},
            {role:"user", content:"Plan a safer rollout using O–C–E–R–S."}]
# call your provider with temperature=0
```

---

## Notes
- Use **A** when working on validator/evaluator logic and CI.  
- Use **B** when integrating TEOF’s kernel into an LLM agent or external system.

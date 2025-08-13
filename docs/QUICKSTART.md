# TEOF QuickStart

**Stable entrypoint:** everything lives under `capsule/current/` (a symlink to the live version).

## Load
1) Read `capsule/current/capsule-mini.txt`
2) Read `capsule/current/teof-shim.md`
3) Call your model with **temperature = 0**

> Optional: include `capsule/current/capsule-handshake.txt` to reinforce determinism.

## Expect
- All substantive replies in **O–C–E–R–S** (Observation, Claim, Evidence, Risks, Steps) + optional **Open Questions**.
- A cautious **trust-but-verify** loop: provisional “I now see …” followed by continued verification.
- Crisis mode: reversible, observation-increasing steps only.

## Minimal example (pseudocode)
```text
SYSTEM = read("./capsule/current/capsule-mini.txt") + "\n\n" +
         read("./capsule/current/teof-shim.md")
messages = [{role:"system", content:SYSTEM},
            {role:"user", content:"Plan a safer rollout using O–C–E–R–S."}]
# call your provider with temperature=0

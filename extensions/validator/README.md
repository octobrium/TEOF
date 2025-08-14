# TEOF OCERS Validator (v0.1, minimal)

Purpose: verify that an output conforms to the OCERS shape and is deterministic under three temp=0 runs (if provided). This is an **extension** of TEOF, not part of the immutable core.

## What it checks (core)
- OCERS presence with required non-empty fields: `O, C, E, R, S`
- Accepts JSON form:
  ```json
  {"O": "...", "C": "...", "E": "...", "R": "...", "S": "..."}
  ```
- Accepts headed text form:
  ```
  O: ...
  C: ...
  E: ...
  R: ...
  S: ...
  ```
- Optional field: `OpenQuestions`

## What it does NOT do (by design, v0.1)
- No doctrinal validation (no axiom quoting checks)
- No semantic alignment scoring
- No model calls (SAMPLE mode only, out of the box)

## Quick start
```bash
chmod +x validator/teof-validate.sh

# SAMPLE mode uses bundled examples, no API calls
MODE=SAMPLE ./validator/teof-validate.sh "Test prompt" local-sample runner-abc $(git rev-parse --short HEAD)
```

**Expected output (SAMPLE mode):**
```
OCERS-VALIDATOR v0.1 | verdict=PASS | commit=<sha> | model=local-sample | runner=runner-abc | ocers_json=1 | out_sha256=<...> | utc=<...>
determinism=OK
```
Exit code: `0`

## Direct Python usage
```bash
python3 validator/teof_validator.py \
  --input validator/sample_outputs/ocers_ok.json \
  --runmeta validator/sample_outputs/runmeta.json \
  --commit $(git rev-parse --short HEAD) \
  --receipt-json validator/receipt.json
```

### Exit codes
- `0` = PASS
- `1` = FAIL (shape/parse)
- `3` = internal error

### Optional flags (non-blocking)
- `--receipt-json <path>`: write a machine-readable result
- `--schema <path>`: (reserved for future) custom schema path

## Determinism check (harness)
The shell harness runs three outputs and compares them. In `SAMPLE` mode, it copies the same file thrice (deterministic). In a future `MODEL` mode, integrators can plug a real model call at temp=0 (shortest-valid).

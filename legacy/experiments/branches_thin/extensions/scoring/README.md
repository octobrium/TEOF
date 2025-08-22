# TEOF Scoring System (v0.1, minimal)

Purpose: turn validated OCERS into a simple, comparable **TEOF Score (0–100)** with per-field diagnostics.  
Scope: **non-doctrinal**, **non-semantic** beyond basic signal checks; designed to pair with the OCERS validator.

## What it scores
Each section gets up to **20 points**:
- **O (Observation)** — concise, faithful summary signal (length window)
- **C (Coherence)** — clarity/structure signal (length window)
- **E (Evidence)** — specificity signal (numbers, years, links, quotes)
- **R (Risk)** — risk-awareness signal (keywords)
- **S (Steps)** — actionability signal (imperatives, lists)

Total = O + C + E + R + S (max 100)

> Assumes OCERS is present. For best reliability, run the **validator** first.

## Quick start
```bash
python3 scoring/teof_score.py \
  --input validator/sample_outputs/ocers_ok.json \
  --commit abc123
```

**Output (example):**
```
TEOF-SCORE v0.1 | score=86/100 | O=16 C=16 E=18 R=16 S=20 | commit=abc123 | ocers_json=1 | utc=2025-08-14T00:00:00Z | notes="Good evidence specificity; solid steps"
```

### Exit codes
- `0` = ran successfully (score printed)
- `3` = internal error (couldn’t read/parse input)

## Notes
- This scorer is deliberately minimal; it’s a **baseline** signal to enable comparisons and prompt iteration.
- Keep it paired with the **OCERS Validator** for structural guarantees and determinism checks.

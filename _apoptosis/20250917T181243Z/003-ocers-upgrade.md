# Task: OCERS scorer v0.2 (weights + simple signals)
Goal: Replace binary stub with weighted signals (e.g., presence of sunset/fallback, references, determinism).
OCERS Target: Coherence↑ Evidence↑ Safety↑
Sunset: Revert if mis-scores >20% on sampled human labels.
Fallback: Use current stub.
Acceptance: `teof/eval/ocers_min.py` outputs per-dimension subscores and a weighted total.

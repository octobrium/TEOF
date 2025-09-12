2) L1 objectives (what “mitigated by observation” means, measurably)

Add 5 concrete fitness signals you can tune as the system grows:

Ambiguity catch rate: % of PRs that properly flag “intent unclear” before a human does. (Higher is better until noise rises.)

Observation resolution rate: % of flagged PRs that are resolved via observation evidence without human override.

Calibration delta: Brier/log-loss improvement on your “oracle” tests month-over-month (system gets more intelligent/robust).

Receipt quality score: Fraction of decisions carrying testable predictions + artifacts (hashes, logs).

Safe default adherence: % of cases below confidence threshold that chose the safe path (no-merge).

These let you see the system becoming more intelligent, robust, aligned with observation over time.
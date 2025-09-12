Unity — coherence under observation

Signals: reproducible state (% deterministic builds); config/link integrity (%).

Guard: single source of truth; no merge if determinism < floor.

Energy — internal function/communication

Signals: time-to-seed (p50); internal latency/throughput per resource.

Guard: budget ceilings on run/seed cost.

Propagation — growth/portability

Signals: cold-start success on clean env (%); doc task completeness.

Guard: portability checklist passes before “scale” work.

Defense — adapt & protect

Signals: rollback success (%); MTTR; security test coverage.

Guard: reversible change required for risky diffs; fail if missing.


3) L2 contracts (make “consult observation” enforceable)

Introduce three normative, checkable contracts:

L2-A.1 Observation Consult Protocol (OCP).
Before acting on ambiguous intent, an agent MUST produce an Observation Consult Record (OCR) containing:

Question of record (what is unclear)

Hypotheses considered (H1, H2…)

Observable claims & tests (what would be seen if H1 vs H2)

Evidence gathered (receipts: logs/hashes/data-of-record)

Result & confidence (with calibration note)

SPEC IDs & knobs referenced

L2-A.2 Prediction-First Decisions.
Every non-trivial decision SHALL include at least one verifiable prediction tied to a near-term check (even if trivial, e.g., “lint passes / hash equals …”). No prediction → no merge.

L2-A.3 Disagreement Harness.
For high-impact changes, run paired agents with different priors; select the plan whose predictions best match observation on a small, deterministic test. (This lets intelligence improve without guessing intent.)
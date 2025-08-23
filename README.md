# The Eternal Observer Framework (TEOF)

**Author:** Observation • **License:** [MIT](LICENSE)

TEOF is a minimal, substrate‑neutral alignment kernel. It gives humans and agents a deterministic, auditable way to move from **Observation → Coherence → Ethics → Reproducibility → Self‑repair** before taking action.

> **Start here**
> - Repo map: [`docs/architecture.md`](docs/architecture.md)  
> - Promotion rules: [`docs/promotion-policy.md`](docs/promotion-policy.md)  
> - Workflow (priority ladder): [`docs/workflow.md`](docs/workflow.md#architecture-gate-before-writing-code)  
> - Operator mode (LLM quick brief): [`docs/workflow.md#operator-mode-llm-quick-brief`](docs/workflow.md#operator-mode-llm-quick-brief)  
> - Quickstart (one command → artifacts): [`docs/quickstart.md`](docs/quickstart.md)

---

## What’s in this repo

- **Kernel code** in `extensions/` (canonical, packaged).  
- **Candidates** in `experimental/` (promoted via policy).  
- **Capsule** baselines and hashes in `capsule/` with `capsule/current` as a pointer.  
- **Governance** anchors (append‑only) in `governance/`.  
- **Docs** (this README, quickstart, architecture, promotion policy, examples) in `docs/`.  
- **Scripts** like the import policy guard and freeze helper in `scripts/`.  
- **Foundation texts** (conceptual bedrock) under `docs/foundation/` – e.g. [Aperture Guideline](docs/foundation/APERTURE-GUIDELINE.md).

See the full map in [`docs/architecture.md`](docs/architecture.md).

---

## Quickstart

From a clean checkout:

```bash
# 1) Install
pip install -e .

# 2) Run the minimal ensemble scorer on the brief example
python -m extensions.validator.scorers.ensemble_cli   --in docs/examples/brief/inputs   --out artifacts/ocers_out/$(date -u +%Y%m%dT%H%M%SZ)
```

This writes `*.ensemble.json` artifacts. For details and optional CLI entrypoints (`teof-validate`, `teof-ensemble`) see [`docs/quickstart.md`](docs/quickstart.md).

---

## Contributing (function‑first)

Before writing code, follow the **Architecture Gate** in [`docs/workflow.md`](docs/workflow.md):

- Place work per `docs/architecture.md` (kernel → `extensions/`, prototypes → `experimental/`, etc.).  
- Kernel code **must not** import from `experimental/` or `archive/` (enforced by `scripts/policy_checks.sh`).  
- If validator/evaluator logic or reasoning rules change, update goldens in `docs/examples/**/expected/` and explain the rationale.  
- Use the PR **Objective line**:
  ```
  Class=<Core|Trunk|Branch|Leaf>; Why=…; MinimalStep=…; Direction=…
  ```
- If you need to refine the DNA (architecture/workflow/promotion policy), follow the **DNA Recursion** section in `docs/workflow.md`.

Promotion from `experimental/` → `extensions/` must meet the criteria in [`docs/promotion-policy.md`](docs/promotion-policy.md).

---

## Releases & provenance

- Freeze the capsule (`capsule/<version>/hashes.json`) and append an anchors event in `governance/anchors.json` (append‑only, includes `prev_content_hash`).  
- Update `CHANGELOG.md`, tag (`git tag -a vX.Y.Z …; git push origin vX.Y.Z`), and optionally publish a zip of `capsule/<version>/`.  
- See the **Lean release block** in [`docs/workflow.md`](docs/workflow.md).

---

## Why TEOF

- **Deterministic**: same inputs → same outputs; CI checks shapes (and later exactness).  
- **Minimal**: small import surface; text‑first formats; few dependencies.  
- **Auditable**: append‑only governance + hashed baselines enable trustless verification.  
- **Composable**: the kernel stays tiny; applications (e.g., TEOF Score™, web demos) live in separate repos.

---

## Resources

- [Whitepaper](docs/whitepaper.md)  
- [Clarifications](docs/clarifications.md)  
- Foundation docs: [`docs/foundation/`](docs/foundation/)

---

Licensed under the [MIT License](LICENSE).

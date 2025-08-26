<!-- markdownlint-disable MD013 -->
# Promotion Policy (experimental → extensions)

**Goal:** Keep the kernel tiny, deterministic, and auditable. Promote only proven modules from `experimental/` into `extensions/`.

## Scope
This policy governs code that aspires to become canonical (packaged and exported). Everything else stays in `experimental/` or moves to `archive/`.

## Criteria (ALL required)
1. **Determinism** — Same inputs → identical outputs across 3 clean runs. Document reproduction commands.
2. **Spec alignment** — Matches current OCERS/OGS shapes. If rules changed, update goldens in `docs/examples/**/expected/` and include a 1–2 sentence rationale.
3. **CI coverage** — Examples in `docs/examples/**` exercise the behavior. Regressions fail CI (shape now; exact match when ready).
4. **Minimal surface** — Clear `main()` (or console entrypoint); minimal dependencies; no hidden state.
5. **Provenance** — Append an event in `governance/anchors.json` with `prev_content_hash` for any promoted logic.
6. **Docs updated** — Quickstart and/or module README show exact, runnable commands.

## Process
1. Open a PR moving/adding code under `experimental/` with intent to promote (link a short plan or TEP if needed).
2. Prove determinism (triple-run), update goldens, and add/refresh docs.
3. Append an anchors event (provenance) and update `CHANGELOG.md` if behavior changed.
4. Reviewer checks:
   - Placement aligns with `docs/ARCHITECTURE.md`
   - Import policy guard passes (no `extensions/` imports from `experimental/`/`archive/`)
   - Criteria above are satisfied
5. Promote by moving to `extensions/` (use `git mv` to preserve history).

## De‑promotion / Freezing
If a canonical module no longer meets criteria or is superseded, move it to `archive/` with a note “frozen as of `<tag>`/`<date>`”. Update docs to redirect references.

## Packaging rule
Only `extensions/` is packaged and exposed via console scripts. Packaged code must not import from `experimental/` or `archive/` (enforced by `scripts/policy_checks.sh`).

## PR helper checklist
- [ ] Determinism proven (3 runs identical)
- [ ] Examples/goldens updated
- [ ] CI green on examples
- [ ] Anchors event appended (with `prev_content_hash`)
- [ ] Docs + Quickstart updated
- [ ] `CHANGELOG.md` updated (if behavior changed)

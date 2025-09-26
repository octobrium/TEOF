# Memory Layer Blueprint (v0)

Purpose: give TEOF agents a thin, deterministic memory stack that captures
every run, promotes trustworthy facts, and indexes artifacts for replay.

## Artifacts

- `memory/log.jsonl` – append-only event log (already exists). Each entry:
  ```json
  {
    "ts": "2025-09-26T17:21:50Z",
    "run_id": "20250926T172150Z-abc123",
    "parent_run_id": null,
    "layer": "L5",
    "systemic_scale": 4,
    "task": "2025-09-25-memory-layer:S1",
    "inputs": {"plan": "2025-09-25-memory-layer.plan.json"},
    "tool_calls": ["python3", "teof tasks"],
    "outputs": {"summary": "Defined memory schema."},
    "exit_status": 0,
    "output_sha256": "…",
    "derived_facts": ["memory-schema-defined"],
    "next_actions": ["implement-api"],
    "receipts": ["docs/automation/memory-layer.md"],
    "hash_prev": "…",
    "hash_self": "…"
  }
  ```
  - Promote hash chaining once API lands (`hash_prev` = previous entry hash).
  - `layer`/`systemic_scale` mirror backlog rubric for downstream sorting.

- `memory/state.json` – curated facts the system currently trusts.
  ```json
  {
    "version": 0,
    "last_updated": "2025-09-25T20:00:00Z",
    "facts": [
      {
        "id": "memory-schema-defined",
        "layer": "L4",
        "confidence": 0.9,
        "statement": "Memory schema v0 recorded in docs/automation/memory-layer.md",
        "source_run": "20250926T172150Z-abc123",
        "evidence": ["docs/automation/memory-layer.md"],
        "expires_at": null
      }
    ]
  }
  ```
  - Facts promote via `promote_fact` (confidence threshold).
  - Expiry optional for volatile truths.

- `memory/artifacts.json` – index from task → outputs with hashes.
  ```json
  {
    "version": 0,
    "artifacts": {
      "2025-09-25-memory-layer:S1": [
        {
          "path": "docs/automation/memory-layer.md",
          "sha256": "…",
          "run_id": "20250926T172150Z-abc123"
        }
      ]
    }
  }
  ```
  - Dedup by hash before appending.

- `memory/runs/<run_id>/` – raw capsule for each execution.
  - Files:
    - `context.json` (prompt, plan snapshot, environment vars).
    - `inputs/` – raw input payloads.
    - `outputs/` – stdout, stderr, produced files (copies or symlinks).
    - `meta.json` – same summary as log event for quick access.
  - Directory name uses UTC timestamp + short uuid (`20250926T172150Z-abc123`).

## Promotion rules

1. Every run **must** write a log entry before exit (append-only, hash-linked).
2. Facts only move `log → state.json` after review or automated confidence ≥ threshold.
3. Artifacts only index tracked files (no gitignored paths).
4. `runs/<id>/` is immutable once written (only new runs appear).
5. Planner CLI enforces capture: creating a plan auto-prompts layer/systemic/impact; execution wrappers populate run metadata.
6. State promotions must cite their receipts. `scripts/ci/check_memory_state.py` blocks edits to `memory/state.json` unless the referenced run capsule (via `source_run` or `derived_facts`) appears in the appended `memory/log.jsonl` entries.

## API surface (planned for S2)

- `write_log(event: dict) -> str` – returns run_id; handles hash chaining.
- `promote_fact(fact: dict) -> None` – inserts/updates entries in `state.json`.
- `recall(query: str, *, limit=5) -> list` – searches log/state/artifacts by tag/task.

## Diagnostics (planned for S3)

- `python -m tools.memory.doctor` – verify hash chain, missing runs, stale facts.
- `python -m tools.memory.timeline [--task <id>]` – render compact history.
- `python -m tools.memory.diff --run <id> --against <id|latest>` – compare outputs.

This schema anchors the implementation work in `2025-09-25-memory-layer`. Receipts:
- `docs/automation/memory-layer.md` (this document).

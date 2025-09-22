# External Steward Profiles

Purpose: capture canonical metadata for each steward responsible for external feeds so automation can reason about capabilities, obligations, and default trust baselines.

Each profile should include:

- `id`: canonical handle aligning with hello packets / automation IDs.
- `display_name`: human-readable label.
- `capabilities`: short list of verbs the steward automates (e.g., `external_adapter`, `summary_refresh`).
- `obligations`: promises the steward is accountable for (e.g., `refresh_registry_post_run`).
- `trust_baseline`: float 0–1 reflecting vetted reliability before live trust metrics are applied.
- Optional: `contact`, `notes`, `last_reviewed`.

Profiles feed into `docs/adoption/external-feed-registry.config.json` and the automated trust metrics under `_report/usage/external-summary.json`.


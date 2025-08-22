# Report Examples (Static)

This folder holds **small, stable report snapshots** for docs/discussion.
They are **not** produced by the build and are safe to version.

Guidelines:
- Keep examples tiny and illustrative; redact/trim large arrays.
- Use `.json` with stable ordering and minimal whitespace.
- If a snapshot becomes a contract, move a **minimal** version to
  `docs/examples/brief/goldens/reports/` and enforce it in CI.

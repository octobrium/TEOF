# Contributing

## Developer Certificate of Origin (DCO)
By contributing, you agree to the DCO. Sign commits with:

Signed-off-by: Your Name <you@example.com>

## How to contribute
1. Run `teof status` and `teof tasks --format json`.
2. Make the smallest change that satisfies the top task (one-shot).
3. If changing `extensions/**`, reference a `TEP-####` in the PR title/body.
4. Ensure tests pass (`pytest -q`) and no placeholder tokens remain.
5. Open a PR. CI will upload brief artifacts and run checks.

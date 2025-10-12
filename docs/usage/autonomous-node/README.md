# Autonomous Node Runner

Run the local workflow autonomously (no human approvals) with:

```bash
scripts/run-autonomous-node.sh 10
```

This executes:
- `teof status --out … --quiet`
- `teof scan --format json --out …`
- `teof ideas evaluate --format json`

Receipts land under `docs/usage/autonomous-node/<UTCSTAMP>/` with a `summary.json` capturing hashes for status, scan payload, and idea ranking.

Schedule via cron/systemd to “mine” continuously. Example cron entry:

```
*/30 * * * * cd /path/to/TEOF && scripts/run-autonomous-node.sh 5 >/tmp/teof-node.log 2>&1
```

Each run is sandboxed to the repo workspace; extend tooling once incentives are in place.

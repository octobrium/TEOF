# VDP Golden Fixtures

These JSON fixtures exercise the Volatile Data Protocol guard. CI loads them via
`scripts/ci/check_vdp.py` to confirm that volatile observations without
`timestamp_utc` or `source` fail, stale data must be labeled, invalid timestamps
are rejected, and both future-dated quotes and non-volatile context lines remain
permitted. Tickers (BTC, NVDA, IBIT, PLTR, MSTR) are synthetic and exist purely
to stress the evaluator — swap them freely if another label is clearer.

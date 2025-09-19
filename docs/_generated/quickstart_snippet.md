<!-- generated: quickstart snippet -->
Run this smoke test on a fresh checkout:
```bash
python3 -m pip install -e .
teof brief
ls artifacts/ocers_out/latest
cat artifacts/ocers_out/latest/brief.json
```

- Install exposes the teof console script.
- teof brief scores docs/examples/brief/inputs/ and writes receipts under artifacts/ocers_out/<UTC>.

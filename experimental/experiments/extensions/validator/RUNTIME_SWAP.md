# Runtime Swap (minimal)

This explains how to replace the sample copy step in `validator/teof-validate.sh` with a **real model call** that returns OCERS in JSON or headed form. Keep **temp=0** and prefer **shortest valid** decoding.

## Contract
- Input: a prompt (see `prompt_ocers.txt`)
- Output (strict): either
  1) JSON
     ```json
     {"O":"...", "C":"...", "E":"...", "R":"...", "S":"...", "OpenQuestions":""}
     ```
  2) Headed text
     ```
     O: ...
     C: ...
     E: ...
     R: ...
     S: ...
     ```

## Swap point
In `validator/teof-validate.sh`, replace the sample line:
```bash
cp validator/sample_outputs/ocers_ok.json "$tmp/out$i.txt"
```
with your model call, writing **raw** output to `$tmp/out$i.txt` and run metadata to `$tmp/runmeta$i.json`.

## Example: HTTP API (curl)
```bash
# inside the for i in 1 2 3 loop
resp="$(curl -sS -X POST https://YOUR_API/generate \
  -H 'content-type: application/json' \
  -d '{
        "model":"YOUR_MODEL_ID",
        "temperature":0,
        "max_tokens":800,
        "prompt": '"$(jq -Rs . < "$tmp/prompt.txt")"',
        "decode":"shortest_valid"
      }')"

# write raw text output to out$i.txt
echo "$resp" | jq -r '.text' > "$tmp/out$i.txt"

# write minimal runmeta
cat > "$tmp/runmeta$i.json" <<JSON
{"model":"YOUR_MODEL_ID","runner_digest":"$RUNNER","temp":"0"}
JSON
```

## Example: local CLI
```bash
# inside the loop
out="$(your_model_cli --model YOUR_MODEL_ID --temp 0 --decode shortest < "$tmp/prompt.txt")"
printf "%s" "$out" > "$tmp/out$i.txt"
cat > "$tmp/runmeta$i.json" <<JSON
{"model":"YOUR_MODEL_ID","runner_digest":"$RUNNER","temp":"0"}
JSON
```

## Notes
- Keep temperature **exactly 0** (or the closest available).
- If “shortest valid” isn’t available, use greedy decoding.
- Do not wrap output with prose; emit **OCERS only**.
- Determinism is checked byte-for-byte across 3 runs.

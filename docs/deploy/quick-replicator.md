# TEOF Replica Quickstart

This guide helps a decentralized operator bring up a fresh replica of the TEOF repo, generate observational artifacts, and confirm health without relying on central infrastructure.

## 1. Bootstrap the repository

```bash
# Clone and enter the repo
git clone https://github.com/octobrium/TEOF.git teof-replica
cd teof-replica

# Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

## 2. Run the built-in smoke flow

```bash
# Produce the brief artifacts and link the latest run
python -m teof.cli brief

# Inspect the latest outputs
ls artifacts/ocers_out/latest
```

The run writes:

- `*.ensemble.json` ensemble scores for each bundled input
- `brief.json` summary with timestamp + file list
- `score.txt` count of generated artifacts

Keep these artifacts as a local receipt; they are not added to capsule canon.

## 3. Optional: doctor & pytest

```bash
# Non-blocking health check
bash tools/doctor.sh

# Minimal test suite
pytest -q
```

## 4. Share receipts (optional)

To advertise availability without exposing internal data, append a short note to a Git-ignored scratch file (e.g. `_report/teof-replica-smoke.txt`) and share it out-of-band. Do not publish private keys, secrets, or sensitive logs.

## 5. Staying in sync

Pull changes periodically and re-run the smoke flow:

```bash
git pull --ff-only
python -m teof.cli brief
```

Use signed attestations (threshold ≥2 signers) if you publish capsule promotions or governance modifications.

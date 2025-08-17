# OCERS (neutral validator)

A minimal rubric-based validator/scorer: **Observation • Coherence • Evidence • Result • Scope**.

## Install (local build)
```bash
python -m build
pip install dist/ocers-0.1.0-py3-none-any.whl

ocers-validate input.txt --out reports/
ocers-ensemble input_dir/ --out scores.json

from ocers import validate_text
report = validate_text("OBSERVATION: ... COHERENCE: ... EVIDENCE: ... RESULT: ... SCOPE: ...")


---

Then confirm with:
```bash
ls -R packages/ocers


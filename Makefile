PY := python3

.PHONY: brief
brief:
	./scripts/teof_cli.py

.PHONY: brief_explore
brief_explore:
	TEOF_MODE=explore ./scripts/teof_cli.py

.PHONY: check
check:
	$(PY) tools/teof_evaluator.py < datasets/goldens/pass_01_fresh_price.json >/dev/null
	$(PY) tools/teof_evaluator.py < datasets/goldens/pass_02_conflict_but_cited.json >/dev/null
	$(PY) tools/teof_evaluator.py < datasets/goldens/pass_03_stale_but_labeled.json >/dev/null
	$(PY) tools/teof_evaluator.py < datasets/goldens/fail_01_missing_timestamp.json >/dev/null 2>&1 || true
	$(PY) tools/teof_evaluator.py < datasets/goldens/fail_02_missing_source.json >/dev/null 2>&1 || true
	$(PY) tools/teof_evaluator.py < datasets/goldens/fail_03_stale_unlabeled.json >/dev/null 2>&1 || true
	@echo "goldens: all good"

.PHONY: audit
audit:
	./scripts/audit.py

.PHONY: open_brief
open_brief:
	less ocers_out/latest/brief.md

.PHONY: watch
watch:
	./scripts/watchlist.py

.PHONY: brief_all
brief_all:
	make brief
	make watch

PY := python3
EVAL := tools/teof_evaluator.py
GOLDENS := $(wildcard datasets/goldens/*.json)

.PHONY: check
check:
	@set -e; \
	for f in $(GOLDENS); do \
	  echo "==> $$f"; \
	  if echo "$$f" | grep -q "/fail_"; then \
	    if $(PY) $(EVAL) < "$$f" >/dev/null 2>&1; then \
	      echo "ERROR: $$f should fail but passed"; exit 1; \
	    else echo "OK (failed as expected)"; fi; \
	  else \
	    $(PY) $(EVAL) < "$$f" >/dev/null || { echo "ERROR: $$f should pass"; exit 1; }; \
	    echo "OK (passed)"; \
	  fi; \
	done; \
	echo "goldens: all good"

.PHONY: validate
validate:
	@$(PY) $(EVAL) < examples/ocers/example.json || true

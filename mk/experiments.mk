SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

.PHONY: new-exp archive-exp finish-exp finish-exp!

# make new-exp name=<kebab> [date=YYYY-MM-DD]
new-exp:
	@test -n "$(name)" || (echo "Usage: make new-exp name=<kebab> [date=YYYY-MM-DD]"; exit 1)
	@./scripts/new_experiment.sh "$(name)" "$(date)"

# make archive-exp exp=YYYY-MM-DD-<kebab>
archive-exp:
	@test -n "$(exp)" || (echo "Usage: make archive-exp exp=YYYY-MM-DD-<kebab>"; exit 1)
	@test -f "experiments/$(exp)/EXPERIMENT.md" || (echo "No such experiment: experiments/$(exp)"; exit 1)
	@grep -E "^State:[[:space:]]*(DONE|ABANDONED)[[:space:]]*$$" "experiments/$(exp)/EXPERIMENT.md" >/dev/null \
	 || (echo "State must be DONE or ABANDONED"; exit 1)
	@git mv "experiments/$(exp)" "archive/experiments/$(exp)" 2>/dev/null || mv "experiments/$(exp)" "archive/experiments/$(exp)"
	@echo "Archived: $(exp)"

# make finish-exp exp=YYYY-MM-DD-<kebab>
finish-exp:
	@test -n "$(exp)" || (echo "Usage: make finish-exp exp=YYYY-MM-DD-<kebab>"; exit 1)
	@test -f "experiments/$(exp)/EXPERIMENT.md" || (echo "No such experiment: experiments/$(exp)"; exit 1)
	@perl -0777 -pe 's/^State:\s*ACTIVE/State: DONE/m' -i "experiments/$(exp)/EXPERIMENT.md"
	@$(MAKE) -f mk/experiments.mk archive-exp exp="$(exp)"

# make finish-exp! exp=YYYY-MM-DD-<kebab> [FORCE=1]
finish-exp!:
	@test -n "$(exp)" || (echo "Usage: make finish-exp! exp=YYYY-MM-DD-<kebab> [FORCE=1]"; exit 1)
	@test -f "experiments/$(exp)/EXPERIMENT.md" || (echo "No such experiment: experiments/$(exp)"; exit 1)
	@if [[ "${FORCE:-0}" != "1" ]]; then \
		grep -E "^Outcome:[[:space:]]*(?!<fill)" "experiments/$(exp)/EXPERIMENT.md" >/dev/null || { echo "Fill Outcome: or FORCE=1"; exit 1; }; \
		grep -E "^Links:[[:space:]]*(?!<PRs/commits/docs>)" "experiments/$(exp)/EXPERIMENT.md" >/dev/null || { echo "Fill Links: or FORCE=1"; exit 1; }; \
	fi
	@perl -0777 -pe 's/^State:\s*(ACTIVE|PAUSED)/State: DONE/m' -i "experiments/$(exp)/EXPERIMENT.md"
	@$(MAKE) -f mk/experiments.mk archive-exp exp="$(exp)"

help::
	@echo "Experiment lifecycle:"
	@echo "  make new-exp name=<kebab> [date=YYYY-MM-DD]"
	@echo "  make finish-exp exp=YYYY-MM-DD-<kebab>"
	@echo "  make finish-exp! exp=YYYY-MM-DD-<kebab> [FORCE=1]"
	@echo "  make archive-exp exp=YYYY-MM-DD-<kebab>"

SHELL := /bin/bash
PYTHON ?= $(shell command -v python3 || command -v python)
OUT := artifacts/ocers_out

.PHONY: brief brief_all open_brief audit clean help show_latest

help:
	@echo ""
	@echo "Targets:"
	@echo "  make brief        - Run the CLI (it writes files and updates 'latest')"
	@echo "  make open_brief   - Open ocers_out/latest/brief.md (robust guard)"
	@echo "  make audit        - Show ocers_out/latest/score.txt (first 120 lines)"
	@echo "  make show_latest  - Inspect the latest folder and files"
	@echo "  make brief_all    - Run brief, then open_brief"
	@echo "  make clean        - Remove all outputs in ocers_out/"
	@echo ""

brief:
	@echo ">>> Generating brief..."
	@$(PYTHON) cli/teof_cli.py

# Helpful inspector to avoid mystery: lists the symlink and the files it points to.
show_latest:
	@echo ">>> Inspecting $(OUT)/latest"
	@ls -l $(OUT) || true
	@echo "----"
	@if [[ -L "$(OUT)/latest" ]]; then \
		echo ">>> latest is a symlink to: $$(readlink $(OUT)/latest)"; \
		echo ">>> contents of that folder:"; \
		ls -l "$$(readlink $(OUT)/latest)" || true; \
	else \
		echo ">>> $(OUT)/latest is missing or not a symlink"; \
	fi

open_brief:
	@file="$(OUT)/latest/brief.md"; \
	if [[ ! -e "$$file" ]]; then \
		echo ">>> ERROR: $$file not found."; \
		echo ">>> Running show_latest for context..."; \
		$(MAKE) -s show_latest; \
		echo ">>> Tip: run 'make brief' again if you interrupted the generator."; \
		exit 1; \
	fi; \
	less "$$file"

audit:
	@file="$(OUT)/latest/score.txt"; \
	if [[ ! -e "$$file" ]]; then \
		echo ">>> ERROR: $$file not found."; \
		echo ">>> Running show_latest for context..."; \
		$(MAKE) -s show_latest; \
		exit 1; \
	fi; \
	echo ">>> Showing score (first 120 lines):"; \
	sed -n '1,120p' "$$file"

brief_all: brief open_brief

clean:
	@rm -rf "$(OUT)"
	@echo ">>> Cleaned $(OUT)/"

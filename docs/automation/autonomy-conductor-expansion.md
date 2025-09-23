# Autonomy Conductor — External Prompt Loop Brainstorm

2025-09-23 — Session notes on extending the conductor into a
continuous Codex/self-prompting loop without modifying TEOF’s canonical
automation surface.

## Motivation

- Operator wants repeat `proceed` behaviour: Codex should keep receiving prompts
  as if a human were typing, so TEOF can grow unattended.
- Needed for future multi-agent / multi-LLM scenarios where conductor prompts
  feed different participants (humans, LLMs, external services).

## Current Constraints

- `tools.autonomy.conductor` collects guardrails, authenticity/CI snapshots, and
  emits JSON receipts. It does not submit prompts to Codex.
- Codex CLI session is outside the repo sandbox; repository code cannot inject
  keystrokes directly into the terminal.
- Any “keep pressing enter” loop requires an external controller with OS-level
  automation permissions or an API bridge.

## Proposed Architecture (out of tree)

1. **Prompt surface:** run `teof-conductor --watch --dry-run --max-iterations 0`
   to continually emit prompts with guardrails/metadata under
   `_report/usage/autonomy-conductor/`.
2. **Watcher:** external script tails the receipt directory, extracts
   `payload["prompt"]`, and decides when/what to dispatch.
3. **Dispatcher options:**
   - **UI automation (macOS):** AppleScript/`osascript` + Accessibility
     permissions; focus Codex terminal, paste prompt, hit Return.
   - **UI automation (Linux):** `xdotool` or `pyautogui` to send keystrokes.
   - **UI automation (Windows):** `pywinauto`, PowerShell, or AutoHotkey.
   - **HTTP path:** call an LLM API directly (OpenAI, local model) and store the
     response as a new receipt or backlog item.
4. **Executor:** after sending the prompt, optionally trigger automation (tests,
   hygiene) and log results as receipts.

## Safeguards / Governance

- Respect `docs/automation/autonomy-consent.json` flags (`auto_enabled`,
  `continuous`, `allow_apply`). External script should halt if consent flips or
  authenticity trust drops (monitor `_report/usage/external-authenticity.json`).
- Provide a kill switch (toggle file, hotkey, etc.) so the operator can stop the
  loop instantly.
- Keep audit trail: archive prompts, responses, and actions under `_report/` to
  maintain TEOF’s provenance expectations.

## Implementation Notes

- Store the watcher/dispatcher scripts outside the repo (e.g.,
  `~/teof-autonomy-playground/`) so canonical users aren’t forced to install UI
  automation tooling.
- Use background services (`launchd`, `systemd --user`, or `tmux`) to run the
  watcher.
- Scripting example (macOS sketch):

  ```bash
  #!/usr/bin/env bash
  receipt=$(ls -t _report/usage/autonomy-conductor/conductor-*.json | head -n 1)
  prompt=$(python3 - <<'PY'
import json, sys
payload = json.load(open(sys.argv[1]))
print(payload["prompt"])
PY
"$receipt")

  /usr/bin/osascript <<OS
  tell application "Terminal"
    activate
    tell application "System Events"
      keystroke "$prompt"
      key code 36
    end tell
  end tell
  OS
  ```

- Future path: same receipts can be fed to human reviewers or other LLMs,
  enabling multi-agent orchestration with minimal changes to TEOF’s core.


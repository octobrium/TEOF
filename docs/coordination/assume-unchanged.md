# Clearing `assume-unchanged` Flags

When multiple agents take turns on the same worktree, stray `git update-index --assume-unchanged` flags can prevent later pushes from including important files. Use the helper below before you start staging changes or when a teammate hands the repo back to you:

```bash
python -m tools.agent.reset_assume_unchanged list
python -m tools.agent.reset_assume_unchanged clear
```

- `list` shows any tracked files currently marked as assume-unchanged.
- `clear` removes the flag from every file so future staging behaves normally.

Run this helper alongside `git status -sb` as part of the standard session handoff. It keeps multi-agent pushes deterministic without touching anyone else’s uncommitted edits.

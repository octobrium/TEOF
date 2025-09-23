# Reflection Intake Template

Use this structure when capturing personal observations before they enter the
backlog. Fill the sections and then run `teof-reflection-intake` (or
`python3 -m tools.autonomy.reflection_intake`) to record the reflection and
optionally emit a backlog suggestion.

```
Title: <short human-readable label>
Layers: <comma-separated layer tags, e.g., L0, L2>
Summary:
  <What did you observe or learn?>

Signals:
  <Evidence, triggers, or sources that prompted the reflection>

Actions:
  <Optional next steps, experiments, or backlog candidates>

Tags: <comma-separated free-form tags>
PlanSuggestion: <optional plan id>
Notes:
  <Additional context you want to keep with the record>
```

Example CLI invocation:

```bash
teof-reflection-intake \
  --title "Morning insight" \
  --layer L0 \
  --summary "Observed a recurring pattern in decision making." \
  --signals "Weekly journaling notes" \
  --actions "Schedule a dedicated review block" \
  --tag mindset \
  --plan-suggestion 2025-09-23-autonomy-roadmap \
  --emit-backlog
```

This writes `memory/reflections/reflection-<timestamp>.json` and prints a
backlog suggestion that can be pasted into `_plans/next-development.todo.json`
after review.

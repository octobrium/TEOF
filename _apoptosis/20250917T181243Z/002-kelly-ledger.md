# Task: Kelly ledger for autocollab
Goal: After each dry-run batch, append a CSV row summarizing items and OCERS stub stats.
OCERS Target: Recursion↑ Evidence↑
Sunset: Remove if we stop using autocollab; move to DB when needed.
Fallback: Manual note in STATUS.
Acceptance: `_report/ledger.csv` gains a new row with batch_ts,total_items,avg_score,total_score.

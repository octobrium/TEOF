# Distribution Cadence — Evangelism Kit

Status: Active (2025-10-03). Owner: codex-4 (codex-5 support welcomed).

## Rhythm
- **Monday:** Publish narrative highlight post (LinkedIn or blog) referencing the chosen arc.
- **Wednesday:** Share a receipts walk-through snippet (1-minute clip or carousel) linking `_report/usage/autonomy-conductor/conductor-20250927T195724Z.json`.
- **Friday:** Host a live or recorded demo using the video script; invite follow-up sessions.

Each event produces a receipt under `_report/usage/evangelism/` (use the `log_event` CLI to generate `event-<timestamp>.json`). Include the audience, asset used, link, and follow-up notes.

Recent receipts logged 2025-09-29 → 2025-10-03 illustrate the pattern below.

## Upcoming Cycles
| Date | Channel | Arc | Asset | Status | Receipt |
| --- | --- | --- | --- | --- | --- |
| 2025-09-29 | Blog | Arc A | One-pager | published | `_report/usage/evangelism/event-20251003T022842Z.json` |
| 2025-10-01 | Social | Arc C | Slide deck | sent | `_report/usage/evangelism/event-20251003T022850Z.json` |
| 2025-10-03 | Webinar | Arc B | Demo video | scheduled | `_report/usage/evangelism/event-20251003T022859Z.json` |
| 2025-10-08 | Newsletter | Arc D | One-pager | scheduled | `_report/usage/evangelism/cadence-20251003T022920Z.json` |

Update the table after each touch, attach actual receipts, and broadcast a `bus_event` so the manager dashboard mirrors progress.

Use `python3 -m tools.receipts.log_event evangelism` to capture each touch; receipts are linked above.

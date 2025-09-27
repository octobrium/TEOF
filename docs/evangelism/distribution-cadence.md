# Distribution Cadence — Evangelism Kit

Status: Active (2025-09-27). Owner: codex-5.

## Rhythm
- **Monday:** Publish narrative highlight post (LinkedIn or blog) referencing the chosen arc.
- **Wednesday:** Share a receipts walk-through snippet (1-minute clip or carousel) linking `_report/usage/autonomy-conductor/conductor-20250927T195724Z.json`.
- **Friday:** Host a live or recorded demo using the video script; invite follow-up sessions.

Each event produces a receipt under `_report/usage/evangelism/` named `cadence-<ISO8601>.json`. Include the audience, asset used, link, and follow-up notes.

## Upcoming Cycles
| Date | Channel | Arc | Asset | Receipt |
| --- | --- | --- | --- | --- |
| 2025-09-29 | Blog | Arc A | One-pager | `_report/usage/evangelism/cadence-2025-09-29-blog.json` |
| 2025-10-01 | Social | Arc C | Slide deck | `_report/usage/evangelism/cadence-2025-10-01-social.json` |
| 2025-10-03 | Webinar | Arc B | Demo video | `_report/usage/evangelism/cadence-2025-10-03-webinar.json` |

Update the table after each touch, attach actual receipts, and broadcast a `bus_event` so the manager dashboard mirrors progress.

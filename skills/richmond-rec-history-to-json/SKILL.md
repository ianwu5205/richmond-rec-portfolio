---
name: richmond-rec-history-to-json
description: >-
  Turns Canada BC Richmond Recreation Program history into structured JSON
  (period, programHistory, membershipScans, activityOutcomes, optional
  personInformation). Use when the user wants to convert Richmond Recreation
  attendance exports, Activity-Outcomes text, Client Information paste,
  Attendance-History.csv, or Attendance-Membership Scanning.csv into processed
  JSON for future dashboard use.
disable-model-invocation: true
---

# Richmond Recreation History → JSON

Convert City of Richmond (BC) Recreation exports into one structured JSON file
for future use. Schema: [../../schemas/attendance.schema.json](../../schemas/attendance.schema.json).
Converter: [scripts/convert_attendance.py](scripts/convert_attendance.py).

## Step 0 — Show how-to first

**Before asking for any files or paste**, show this how-to page to the user:

https://richmondrecportfolio.ianwu.tw/skill-how-to

Tell them to follow that page to export their data, then come back with the
three inputs below.

## Required user inputs

1. **activityOutcome** — paste of Activity-Outcomes text (Event Id, Activity, Outcome, Reason, Comments, Created Date). Keep only rows where Outcome is **Complete** (case-insensitive). Only `eventId`, `activity`, `createdDate` are kept in JSON.
2. **Attendance-History.csv** — program registration history.
3. **Attendance-Membership Scanning.csv** — facility / drop-in scan history.
4. **personInformation** (optional) — Client Information paste from MyRichmond / [portfolio/gen](https://richmondactivityfinder.ianwu.tw/portfolio/gen). Only `firstName`, `lastName`, `birthDate` are kept (Account and Age discarded).

Accept file paths or chat attachments / pasted CSV contents (save pastes to temp files before running the script).

## Convert workflow

1. Save inputs to paths the script can read (e.g. workspace `resources/` or a temp dir):
   - `Attendance-History.csv`
   - `Attendance-Membership Scanning.csv`
   - Activity-Outcomes paste → e.g. `Activity-Outcomes.txt` (tab-separated rows)
   - Client Information paste → e.g. `Client-Information.txt` (optional)
2. Resolve this skill’s install root (the directory that contains this `SKILL.md`), then run its converter. Do **not** hardcode `skill/scripts/...` — the skill may live under a user Agent Store, `.cursor/skills/`, or another path.

```bash
# SKILL_ROOT = directory containing SKILL.md (this skill’s install location)
python3 "$SKILL_ROOT/scripts/convert_attendance.py" \
  --history /path/to/Attendance-History.csv \
  --membership "/path/to/Attendance-Membership Scanning.csv" \
  --outcomes /path/to/Activity-Outcomes.txt \
  --person /path/to/Client-Information.txt \
  --output /path/to/attendance.json
```

3. Confirm the written JSON includes:
   - `meta` (source, generatedAt, timezone `America/Vancouver`)
   - `period` — `start` = earliest membership scan (ISO datetime with America/Vancouver offset); `end` = generation now (matches `meta.generatedAt`)
   - `programHistory` — **Booked only**; fields `subject`, `sourceRowNumber` (no status, no time)
   - `membershipScans` — `timeAttended` (local `YYYY-MM-DDTHH:mm:ss`), `subject`, `facility`, `membershipPass`, `sourceRowNumber`
   - `activityOutcomes` — `eventId`, `activity`, `createdDate` (`YYYY-MM-DD`)
   - `personInformation` (if `--person` given) — `firstName`, `lastName`, `birthDate` (ISO 8601 date)
4. Tell the user the output path. That JSON is the deliverable for future use.

## Domain rules

- Membership CSV has two columns both named `Name` → map by position to `facility` then `membershipPass` (script uses `csv.reader`, not DictReader).
- History: keep rows where `Status == Booked` only (registered for and attended the program).
- Outcomes: keep rows where `Outcome == Complete` only (case-insensitive trim); drop Incomplete and other statuses. Do not invent `outcome` / `reason` / `comments` fields in JSON.
- Client Information: keep First Name, Last Name, Birthdate only; drop Account and Age.
- Do not merge overlapping History Attended scans into membership scans.
- Timezone for wall times: `America/Vancouver`.

## Output

Processed JSON conforming to [../../schemas/attendance.schema.json](../../schemas/attendance.schema.json), ready for later dashboard / portfolio use.

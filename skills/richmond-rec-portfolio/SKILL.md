---
name: richmond-rec-portfolio
description: >-
  Use processed attendance.json from richmond-rec-history-to-json to generate
  a portfolio website. Use when the user wants a Richmond Recreation portfolio
  site from existing processed attendance JSON (not when converting CSVs).
disable-model-invocation: true
dependencies:
  - local: ../richmond-rec-history-to-json
---

# Richmond Rec Portfolio → Web

Generate a portfolio website from processed Richmond Recreation attendance JSON.
This skill reads `attendance.json` produced by `/richmond-rec-history-to-json`.
It does **not** invoke that skill or run the converter.

Layout reference: [references/portfolio-layout.md](references/portfolio-layout.md).
Extraction prompt: [references/portfolio-extraction-prompt.md](references/portfolio-extraction-prompt.md).
Generator: [scripts/generate_portfolio.py](scripts/generate_portfolio.py).

## Preconditions

1. Locate the input JSON:
   - If the user provides a path, use that
   - Otherwise search the workspace for `attendance.json` / `resources/attendance.json`
2. If it is missing, **do not run the conversion yourself**. Tell the user:
   > Processed JSON not found. Please run `/richmond-rec-history-to-json` first.
   > See how to export: https://richmondrecportfolio.ianwu.tw/skill-how-to
3. If found, validate it against `$SKILL_ROOT/../../schemas/attendance.schema.json`

## Extract portfolio data (LLM)

Before generating HTML, run LLM extraction per
[references/portfolio-extraction-prompt.md](references/portfolio-extraction-prompt.md):

1. Read the validated `attendance.json`
2. Call `set_portfolio_data` **once** to categorize `programHistory` subjects into
   `attendance` category arrays (see tool schema in the prompt doc)
3. Save the tool arguments as `portfolio-data.json` (workspace or next to the output HTML)
4. Do **not** invoke `/richmond-rec-history-to-json`

Category display headings: [references/attendance-category-labels.json](references/attendance-category-labels.json).

## Generate the site

Resolve this skill’s install root (the directory that contains this `SKILL.md`),
then run the generator. Do **not** hardcode skill paths — use `$SKILL_ROOT`.

```bash
# SKILL_ROOT = directory containing SKILL.md
python3 "$SKILL_ROOT/scripts/generate_portfolio.py" \
  --input /path/to/attendance.json \
  --portfolio-data /path/to/portfolio-data.json \
  --output /path/to/portfolio.html
```

Optional: `--schema /path/to/attendance.schema.json` (defaults to
`$SKILL_ROOT/../../schemas/attendance.schema.json`).

Semantics:

- `membershipScans` (from attendance.json) = facility entry / drop-in records — computed in the script
- `programHistory` categorization = LLM extraction → `portfolio-data.json` → **Attended Program**

The script maps:

- `clientInformation` / `personInformation` → profile header (portfolio-data preferred)
- `period` (`start` / `end` from attendance.json) → **Period** under the profile header (readable date range)
- `activityOutcomes` → Recent Achievements (portfolio-data preferred)
- `membershipScans` → **Drop in count** (always from attendance.json)
- `attendance` category arrays → **Attended Program** (from portfolio-data.json)

Tell the user the absolute path of the written HTML file (e.g. `portfolio.html`).
Open it in a browser; it is a standalone page with Tailwind via CDN.

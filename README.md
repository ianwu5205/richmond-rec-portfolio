# richmond-rec-portfolio

Agent skill suite for **City of Richmond (BC) Recreation**: export history → structured JSON → portfolio HTML.

## Two-step UX

Both skills are **user-invoked** (`disable-model-invocation: true`). Skill `richmond-rec-portfolio` does not invoke skill `richmond-rec-history-to-json` — it only reads `attendance.json` (data dependency).

1. **`/richmond-rec-history-to-json`** — convert History / Membership / Activity-Outcomes / Client Information exports into `attendance.json`
2. **`/richmond-rec-portfolio`** — generate a portfolio web page from that JSON (plus LLM-extracted `portfolio-data.json`)

Export how-to: https://richmondrecportfolio.ianwu.tw/how-to

## Layout

```
.
├── .claude-plugin/
│   └── marketplace.json                # plugin marketplace listing
├── .gitignore                          # ignore caches / OS junk
├── LICENSE                             # MIT
├── README.md
├── schemas/
│   └── attendance.schema.json          # shared attendance JSON Schema
└── skills/
    ├── richmond-rec-history-to-json/   # exports → attendance.json
    │   ├── SKILL.md
    │   └── scripts/
    │       └── convert_attendance.py   # CSV/text → JSON converter
    └── richmond-rec-portfolio/         # attendance.json → portfolio.html
        ├── SKILL.md
        ├── scripts/
        │   └── generate_portfolio.py   # portfolio HTML generator
        └── references/
            ├── attendance-category-labels.json  # category key → display heading
            ├── portfolio-extraction-prompt.md   # LLM + set_portfolio_data prompt
            ├── portfolio-layout.md              # HTML section layout notes
            └── fixtures/                        # synthetic smoke-test samples
                ├── README.md
                ├── sample-attendance.json
                └── sample-portfolio-data.json
```

## Install

Add this repo as a Claude/Cursor plugin marketplace source. Plugins are listed in [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json):

- `richmond-rec-history-to-json` → `./skills/richmond-rec-history-to-json`
- `richmond-rec-portfolio` → `./skills/richmond-rec-portfolio`

Requires **Python 3** (stdlib only).

## Step 1 — Convert exports → JSON

```bash
SKILL_A=skills/richmond-rec-history-to-json
python3 "$SKILL_A/scripts/convert_attendance.py" \
  --history /path/to/Attendance-History.csv \
  --membership "/path/to/Attendance-Membership Scanning.csv" \
  --outcomes /path/to/Activity-Outcomes.txt \
  --person /path/to/Client-Information.txt \
  --output /path/to/attendance.json
```

`--outcomes` and `--person` are optional. Activity-Outcomes keep rows where **Outcome is Complete** only (case-insensitive); Incomplete and other statuses are dropped.

Schema: [`schemas/attendance.schema.json`](schemas/attendance.schema.json).

## Step 2 — Generate portfolio HTML

After `attendance.json` exists, the agent categorizes `programHistory` via the LLM `set_portfolio_data` tool ([extraction prompt](skills/richmond-rec-portfolio/references/portfolio-extraction-prompt.md)) and saves `portfolio-data.json`. Then:

```bash
SKILL_B=skills/richmond-rec-portfolio
python3 "$SKILL_B/scripts/generate_portfolio.py" \
  --input /path/to/attendance.json \
  --portfolio-data /path/to/portfolio-data.json \
  --output /path/to/portfolio.html
```

Fixtures for a dry run: `skills/richmond-rec-portfolio/references/fixtures/`.

## License

MIT — see [LICENSE](LICENSE).

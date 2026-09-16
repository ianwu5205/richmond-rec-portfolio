# richmond-rec-portfolio

Monorepo suite for City of Richmond (BC) Recreation attendance → processed JSON → portfolio website.

## Skills (two-step UX)

Both skills are **user-invoked** (`disable-model-invocation: true`). Skill b does **not** call skill a; it only reads `attendance.json`.

1. **`/richmond-rec-history-to-json`** — convert History / Membership / Outcomes / Client Information exports into `attendance.json`
2. **`/richmond-rec-portfolio`** — use that JSON to generate a portfolio website (scaffold; generator coming later)

Export how-to: https://richmondrecportfolio.ianwu.tw/how-to

## Layout

```
.
├── .claude-plugin/marketplace.json
├── schemas/attendance.schema.json          # shared schema
├── skills/
│   ├── richmond-rec-history-to-json/       # step 1
│   │   ├── SKILL.md
│   │   └── scripts/convert_attendance.py
│   └── richmond-rec-portfolio/             # step 2 (scaffold)
│       └── SKILL.md
├── LICENSE
└── README.md
```

## Requirements

- Python 3 (stdlib only for the converter)

## Install

Clone or add this repo as a Claude/Cursor plugin marketplace source. Plugins are listed in [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json).

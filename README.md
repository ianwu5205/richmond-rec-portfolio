# richmond-rec-portfolio

Agent skill suite for **City of Richmond (BC) Recreation**: export history → structured JSON → portfolio HTML.

## Install

```bash
npx skills add https://github.com/ianwu5205/richmond-rec-portfolio/
```

Requires **Python 3** (stdlib only). Plugins are also listed in [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) if you add this repo as a marketplace source.

## Prepare data

Before you generate your portfolio, sign in to the MyRichmond portal and export your recreation history data.

Export how-to: https://richmondrecportfolio.ianwu.tw/skill-how-to

## Use

```
/richmond-rec-portfolio
```

If you do not already have `attendance.json`, run step 1 first:

```
/richmond-rec-history-to-json
```

Then invoke `/richmond-rec-portfolio` to generate the portfolio HTML.

## Skills

There are two skills in this suite:

1. **`/richmond-rec-history-to-json`** — convert History / Membership / Activity-Outcomes / Client Information exports into `attendance.json`
2. **`/richmond-rec-portfolio`** — generate a portfolio web page from that JSON (plus LLM-extracted `portfolio-data.json`)

### Advanced use

If you do not like the pre-set portfolio HTML, run `/richmond-rec-history-to-json` to export into `attendance.json`, then use that structured data to build your own portfolio with your AI tool.

## Schema

Shared JSON Schema for the suite’s attendance / history structured data: [`schemas/attendance.schema.json`](schemas/attendance.schema.json).

It covers program registration history, membership / facility drop-in scans, activity outcomes, and optional person information from City of Richmond Recreation exports.

## License

MIT — see [LICENSE](LICENSE).

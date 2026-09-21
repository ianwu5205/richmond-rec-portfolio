#!/usr/bin/env python3
"""Generate a standalone Richmond Rec portfolio HTML from attendance.json + portfolio-data.json."""

from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

VANCOUVER = ZoneInfo("America/Vancouver")

ATTENDANCE_META_KEYS = frozenset({"dropInCount"})


def e(text: Any) -> str:
    return html.escape("" if text is None else str(text), quote=True)


def parse_iso_datetime(value: str) -> datetime | None:
    raw = value.strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def format_readable_date(value: str) -> str:
    """Format an ISO datetime as a short readable calendar date in Vancouver time."""
    dt = parse_iso_datetime(value)
    if dt is None:
        return value.strip()
    local = dt.astimezone(VANCOUVER) if dt.tzinfo is not None else dt
    return f"{local.strftime('%b')} {local.day}, {local.year}"


def format_period_range(period: Any) -> str:
    """Return 'Mon D, YYYY → Mon D, YYYY' from attendance period, or empty if unavailable."""
    if not isinstance(period, dict):
        return ""
    start = period.get("start")
    end = period.get("end")
    if not start or not end:
        return ""
    return f"{format_readable_date(str(start))} → {format_readable_date(str(end))}"


def compute_age(birth_date: date, today: date) -> int:
    years = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


def initials(first: str, last: str) -> str:
    parts = []
    if first.strip():
        parts.append(first.strip()[0].upper())
    if last.strip():
        parts.append(last.strip()[0].upper())
    return "".join(parts) or "?"


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Input JSON must be an object")
    return data


def default_schema_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent / "schemas" / "attendance.schema.json"


def default_category_labels_path() -> Path:
    return Path(__file__).resolve().parent.parent / "references" / "attendance-category-labels.json"


def load_category_labels(path: Path) -> dict[str, str]:
    labels = load_json(path)
    if not isinstance(labels, dict) or not labels:
        raise ValueError("attendance-category-labels.json must be a non-empty object")
    return {str(k): str(v) for k, v in labels.items()}


def validate_attendance(data: dict[str, Any], schema_path: Path | None) -> list[str]:
    """Light structural checks aligned with attendance.schema.json (stdlib only)."""
    errors: list[str] = []
    for key in ("meta", "period", "programHistory", "membershipScans", "activityOutcomes"):
        if key not in data:
            errors.append(f"missing required field: {key}")
    meta = data.get("meta")
    if isinstance(meta, dict):
        for key in ("source", "generatedAt", "timezone"):
            if key not in meta:
                errors.append(f"missing meta.{key}")
    elif "meta" in data:
        errors.append("meta must be an object")

    period = data.get("period")
    if isinstance(period, dict):
        for key in ("start", "end"):
            if key not in period:
                errors.append(f"missing period.{key}")
    elif "period" in data:
        errors.append("period must be an object")

    for key in ("programHistory", "membershipScans", "activityOutcomes"):
        if key in data and not isinstance(data[key], list):
            errors.append(f"{key} must be an array")

    if schema_path is not None and not schema_path.is_file():
        errors.append(f"schema file not found: {schema_path}")

    return errors


def validate_portfolio_data(data: dict[str, Any], category_labels: dict[str, str]) -> list[str]:
    errors: list[str] = []
    if "activityOutcomes" not in data:
        errors.append("missing required field: activityOutcomes")
    elif not isinstance(data["activityOutcomes"], list):
        errors.append("activityOutcomes must be an array")

    attendance = data.get("attendance")
    if attendance is None:
        errors.append("missing required field: attendance")
    elif not isinstance(attendance, dict):
        errors.append("attendance must be an object")
    else:
        unknown = set(attendance) - set(category_labels) - ATTENDANCE_META_KEYS
        if unknown:
            errors.append(f"unknown attendance keys: {', '.join(sorted(unknown))}")
        for key, value in attendance.items():
            if key in ATTENDANCE_META_KEYS:
                continue
            if not isinstance(value, list):
                errors.append(f"attendance.{key} must be an array")

    client = data.get("clientInformation")
    if client is not None and not isinstance(client, dict):
        errors.append("clientInformation must be an object")

    return errors


def resolve_client(
    portfolio_data: dict[str, Any], attendance_data: dict[str, Any]
) -> dict[str, str]:
    client = portfolio_data.get("clientInformation") or {}
    person = attendance_data.get("personInformation") or {}
    return {
        "firstName": str(client.get("firstName") or person.get("firstName") or "").strip(),
        "lastName": str(client.get("lastName") or person.get("lastName") or "").strip(),
        "birthDate": str(client.get("birthDate") or person.get("birthDate") or "").strip(),
    }


def resolve_outcomes(
    portfolio_data: dict[str, Any], attendance_data: dict[str, Any]
) -> list[dict[str, Any]]:
    outcomes = portfolio_data.get("activityOutcomes")
    if isinstance(outcomes, list) and outcomes:
        return outcomes
    fallback = attendance_data.get("activityOutcomes")
    return fallback if isinstance(fallback, list) else []


def facility_visit_counts(
    membership_scans: list[dict[str, Any]],
) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for item in membership_scans:
        facility = (item.get("facility") or "").strip()
        if not facility:
            continue
        counts[facility] = counts.get(facility, 0) + 1
    return sorted(counts.items(), key=lambda pair: (-pair[1], pair[0].lower()))


def render_drop_in_count(membership_scans: list[dict[str, Any]]) -> str:
    rows = facility_visit_counts(membership_scans)
    total = sum(count for _, count in rows)
    if not rows:
        return """
    <section class="mt-10">
      <h2 class="mb-4 text-lg font-semibold text-slate-900">Drop in count</h2>
      <p class="text-sm text-slate-500">No facility entry records.</p>
    </section>"""

    facility_rows = "".join(
        f"""
          <div class="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3">
            <span class="font-medium text-slate-800">{e(facility)}</span>
            <span class="tabular-nums text-slate-600">{count}</span>
          </div>"""
        for facility, count in rows
    )

    return f"""
    <section class="mt-10">
      <h2 class="mb-4 text-lg font-semibold text-slate-900">Drop in count</h2>
      <p class="mb-3 text-sm text-slate-500">
        Facility entry records from drop-in visits (pool, gym, and other locations).
      </p>
      <div class="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div class="flex items-stretch gap-4">
          <div class="flex min-w-[5rem] shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-white px-4 py-3">
            <span class="text-4xl font-bold tabular-nums text-slate-900">{total}</span>
          </div>
          <div class="flex min-w-0 flex-1 flex-col gap-2">
            {facility_rows}
          </div>
        </div>
      </div>
    </section>"""


def render_achievements(outcomes: list[dict[str, Any]]) -> str:
    if not outcomes:
        return '<p class="text-slate-500 text-sm">No recent achievements recorded.</p>'
    cards = []
    for item in outcomes:
        activity = e(item.get("activity", "Activity"))
        created = e(item.get("createdDate", ""))
        cards.append(
            f"""
            <div class="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-cyan-50 text-cyan-700 text-lg" aria-hidden="true">🌊</div>
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-center gap-2">
                  <h3 class="font-semibold text-slate-900">{activity}</h3>
                  <span class="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-800">Completed</span>
                </div>
                <p class="mt-1 text-sm text-slate-500">{created}</p>
              </div>
            </div>"""
        )
    return '<div class="space-y-3">' + "".join(cards) + "</div>"


def render_attended_program(
    attendance: dict[str, Any], category_labels: dict[str, str]
) -> str:
    blocks: list[str] = []
    for key, heading in category_labels.items():
        subjects = attendance.get(key)
        if not isinstance(subjects, list) or not subjects:
            continue
        unique = []
        seen: set[str] = set()
        for subject in subjects:
            text = str(subject).strip()
            if text and text not in seen:
                seen.add(text)
                unique.append(text)
        if not unique:
            continue
        cards = "".join(
            f"""
            <div class="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-800 shadow-sm">
              {e(subject)}
            </div>"""
            for subject in unique
        )
        blocks.append(
            f"""
            <div class="border-l-4 border-green-600 pl-4">
              <h3 class="mb-3 text-base font-semibold text-slate-900">{e(heading)}</h3>
              <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {cards}
              </div>
            </div>"""
        )
    if not blocks:
        return '<p class="text-slate-500 text-sm">No registered programs in history.</p>'
    return '<div class="space-y-8">' + "".join(blocks) + "</div>"


def build_html(
    attendance_data: dict[str, Any],
    portfolio_data: dict[str, Any],
    category_labels: dict[str, str],
) -> str:
    client = resolve_client(portfolio_data, attendance_data)
    first = client["firstName"]
    last = client["lastName"]
    birth_raw = client["birthDate"]

    has_person = bool(first or last)
    display_name = f"{first} {last}".strip() if has_person else "Portfolio"
    badge = initials(first, last) if has_person else "P"

    today = datetime.now(VANCOUVER).date()
    age_html = ""
    birth_html = ""
    if birth_raw:
        try:
            birth = date.fromisoformat(birth_raw)
            age = compute_age(birth, today)
            age_html = f'<span class="text-slate-600">Age {age}</span>'
            birth_html = f'<span class="text-slate-600">Birthdate {e(birth_raw)}</span>'
        except ValueError:
            birth_html = f'<span class="text-slate-600">Birthdate {e(birth_raw)}</span>'

    meta_bits = " · ".join(x for x in (age_html, birth_html) if x)
    if not meta_bits and not has_person:
        meta_bits = '<span class="text-slate-500">Person details not provided</span>'

    period_text = format_period_range(attendance_data.get("period"))
    period_html = ""
    if period_text:
        period_html = (
            f'<p class="mt-5 flex w-fit items-center gap-2 rounded-full border '
            f'border-emerald-100 bg-emerald-50 px-3 py-1.5 text-xs font-medium '
            f'text-emerald-950 shadow-sm sm:ml-auto">'
            f'<span class="uppercase tracking-wider text-emerald-700">Period</span>'
            f'<span class="tabular-nums">{e(period_text)}</span>'
            f"</p>"
        )

    outcomes = resolve_outcomes(portfolio_data, attendance_data)
    scans = attendance_data.get("membershipScans") or []
    attendance = portfolio_data.get("attendance") or {}

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{e(display_name)} — Activity Portfolio</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-slate-100 text-slate-900 antialiased">
  <div class="mx-auto max-w-3xl px-4 py-6 sm:px-6 sm:py-10">
    <div class="mb-4 flex items-center justify-end print:hidden">
      <button type="button" onclick="window.print()"
        class="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50">
        Print
      </button>
    </div>

    <section class="overflow-hidden rounded-2xl bg-white shadow-md">
      <div class="h-28 bg-gradient-to-r from-green-600 to-blue-600 sm:h-32"></div>
      <div class="relative px-6 pb-8 pt-0">
        <div class="-mt-10 mb-4 flex h-20 w-20 items-center justify-center rounded-full border-4 border-white bg-slate-800 text-2xl font-bold text-white shadow-md">
          {e(badge)}
        </div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">{e(display_name)}</h1>
        <p class="mt-1 text-slate-500">Activity Portfolio &amp; Progress</p>
        <p class="mt-3 text-sm">{meta_bits}</p>
        {period_html}
      </div>
    </section>

    <section class="mt-8">
      <h2 class="mb-4 text-lg font-semibold text-slate-900">Recent Achievements</h2>
      {render_achievements(outcomes)}
    </section>

    {render_drop_in_count(scans)}

    <section class="mt-10">
      <h2 class="mb-3 text-lg font-semibold text-slate-900">Attended Program</h2>
      <p class="mb-4 text-sm text-slate-500">
        Registered and attended programs from extracted portfolio data.
      </p>
      {render_attended_program(attendance, category_labels)}
    </section>

    <footer class="mt-12 border-t border-slate-200 pt-6 text-center text-xs text-slate-500">
      Generated by Richmond Rec Portfolio
    </footer>
  </div>
</body>
</html>
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate portfolio HTML from attendance.json and portfolio-data.json"
    )
    parser.add_argument("--input", required=True, type=Path, help="Path to attendance.json")
    parser.add_argument(
        "--portfolio-data",
        required=True,
        type=Path,
        help="Path to portfolio-data.json from set_portfolio_data extraction",
    )
    parser.add_argument("--output", required=True, type=Path, help="Path to write portfolio.html")
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Path to attendance.schema.json (default: repo schemas/attendance.schema.json)",
    )
    parser.add_argument(
        "--category-labels",
        type=Path,
        default=None,
        help="Path to attendance-category-labels.json (default: skill references/)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    schema_path = args.schema if args.schema is not None else default_schema_path()
    labels_path = args.category_labels if args.category_labels is not None else default_category_labels_path()

    if not args.input.is_file():
        print(f"error: input not found: {args.input}", file=sys.stderr)
        return 1
    if not args.portfolio_data.is_file():
        print(f"error: portfolio-data not found: {args.portfolio_data}", file=sys.stderr)
        return 1

    try:
        attendance_data = load_json(args.input)
        portfolio_data = load_json(args.portfolio_data)
        category_labels = load_category_labels(labels_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: failed to read input: {exc}", file=sys.stderr)
        return 1

    errors = validate_attendance(attendance_data, schema_path)
    errors.extend(validate_portfolio_data(portfolio_data, category_labels))
    if errors:
        print("error: validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    html_out = build_html(attendance_data, portfolio_data, category_labels)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html_out, encoding="utf-8")
    print(f"Wrote {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

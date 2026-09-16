#!/usr/bin/env python3
"""Convert Richmond Recreation exports into one structured JSON document.

Inputs:
  - Attendance-History.csv (Booked rows only → programHistory)
  - Attendance-Membership Scanning.csv (→ membershipScans)
  - Activity-Outcomes text (optional → activityOutcomes)
  - Client Information paste (optional → personInformation)
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

CSV_TIME_FORMAT = "%m/%d/%y %I:%M %p"
ISO_LOCAL_FORMAT = "%Y-%m-%dT%H:%M:%S"
DATE_FORMAT = "%m/%d/%y"

# Tab-separated Activity-Outcomes data line:
# EventId \t Activity \t Outcome \t Reason \t Comments \t CreatedDate
OUTCOME_LINE = re.compile(
    r"^(?P<event_id>\d+)\t"
    r"(?P<activity>[^\t]+)\t"
    r"(?P<outcome>[^\t]*)\t"
    r"(?P<reason>[^\t]*)\t"
    r"(?P<comments>[^\t]*)\t"
    r"(?P<created_date>\d{1,2}/\d{1,2}/\d{2})\s*$"
)


def parse_local_time(value: str) -> str:
    """Parse M/D/YY h:mm AM/PM into local ISO wall time (no offset)."""
    return datetime.strptime(value.strip(), CSV_TIME_FORMAT).strftime(
        ISO_LOCAL_FORMAT
    )


def parse_local_date(value: str) -> str:
    """Parse M/D/YY into ISO 8601 date (YYYY-MM-DD)."""
    return datetime.strptime(value.strip(), DATE_FORMAT).date().isoformat()


def load_program_history(path: Path) -> list[dict]:
    """Keep only Booked rows (registered for and attended the program)."""
    items: list[dict] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Status"].strip() != "Booked":
                continue
            items.append(
                {
                    "subject": row["Subject"].strip(),
                    "sourceRowNumber": int(row["RowNumber"]),
                }
            )
    return items


def load_membership_scans(path: Path) -> list[dict]:
    """Use csv.reader so duplicate Name columns are not collapsed."""
    items: list[dict] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        expected = ["Time Attended", "Subject", "Name", "Name", "RowNumber"]
        if header != expected:
            raise ValueError(
                f"Unexpected membership CSV header in {path}: {header!r} "
                f"(expected {expected!r})"
            )
        for row in reader:
            if not row or all(not cell.strip() for cell in row):
                continue
            time_attended, subject, facility, membership_pass, row_number = row
            items.append(
                {
                    "timeAttended": parse_local_time(time_attended),
                    "subject": subject.strip(),
                    "facility": facility.strip(),
                    "membershipPass": membership_pass.strip(),
                    "sourceRowNumber": int(row_number),
                }
            )
    return items


def labeled_value(text: str, label: str) -> str:
    """Take 'Label: value' from a MyRichmond field dump (ignore bare 'Label:')."""
    match = re.search(rf"^{re.escape(label)}:[ \t]+(.+)$", text, re.M)
    if not match:
        raise ValueError(f"Missing {label!r} in Client Information paste")
    return match.group(1).strip()


def load_person_information(path: Path) -> dict:
    """Keep First Name, Last Name, Birthdate only; drop Account and Age."""
    text = path.read_text(encoding="utf-8-sig")
    birth_raw = labeled_value(text, "Birthdate")
    try:
        birth_date = datetime.strptime(birth_raw, CSV_TIME_FORMAT).date()
    except ValueError:
        birth_date = datetime.strptime(birth_raw.split()[0], DATE_FORMAT).date()
    return {
        "firstName": labeled_value(text, "First Name"),
        "lastName": labeled_value(text, "Last Name"),
        "birthDate": birth_date.isoformat(),
    }


def load_activity_outcomes(path: Path) -> list[dict]:
    """Parse pasted Activity-Outcomes text; keep eventId, activity, createdDate."""
    text = path.read_text(encoding="utf-8-sig")
    items: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("Event Id"):
            continue
        match = OUTCOME_LINE.match(line)
        if not match:
            # Skip header leftovers / blank noise; fail on numeric-looking junk
            if re.match(r"^\d+", line):
                raise ValueError(f"Unrecognized activity outcome line: {line!r}")
            continue
        items.append(
            {
                "eventId": match.group("event_id"),
                "activity": match.group("activity").strip(),
                "createdDate": parse_local_date(match.group("created_date")),
            }
        )
    return items


def convert(
    history_path: Path,
    membership_path: Path,
    output_path: Path,
    outcomes_path: Path | None = None,
    person_path: Path | None = None,
) -> dict:
    document: dict = {
        "meta": {
            "source": "City of Richmond Recreation",
            "generatedAt": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
            "timezone": "America/Vancouver",
        },
        "programHistory": load_program_history(history_path),
        "membershipScans": load_membership_scans(membership_path),
    }
    if outcomes_path is not None:
        document["activityOutcomes"] = load_activity_outcomes(outcomes_path)
    if person_path is not None:
        document["personInformation"] = load_person_information(person_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return document


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Richmond attendance CSVs (+ optional outcomes text) to JSON."
    )
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--membership", type=Path, required=True)
    parser.add_argument(
        "--outcomes",
        type=Path,
        default=None,
        help="Activity-Outcomes pasted text file",
    )
    parser.add_argument(
        "--person",
        type=Path,
        default=None,
        help="Client Information pasted text file",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    document = convert(
        args.history,
        args.membership,
        args.output,
        args.outcomes,
        args.person,
    )
    outcomes_n = len(document.get("activityOutcomes", []))
    person = "yes" if "personInformation" in document else "no"
    print(
        f"Wrote {args.output} "
        f"({len(document['programHistory'])} programHistory, "
        f"{len(document['membershipScans'])} membershipScans, "
        f"{outcomes_n} activityOutcomes, personInformation={person})"
    )


if __name__ == "__main__":
    main()

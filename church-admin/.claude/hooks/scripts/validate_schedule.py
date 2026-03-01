#!/usr/bin/env python3
"""
P1 Deterministic Validation — schedule.yaml (S1-S6)

Rules:
  S1: ID uniqueness and format across 3 types (SVC-*, EVT-*, FAC-*)
  S2: Time format HH:MM 24-hour
  S3: Recurrence and day_of_week enum validation
  S4: Status enum (services N/A, events: planned/confirmed/completed/cancelled,
      bookings: pending/confirmed/cancelled)
  S5: Facility booking time-overlap detection (no two confirmed bookings
      for same facility on same date overlap)
  S6: Facility and location non-empty (all location/facility fields must be
      non-empty strings)

Exit codes: 0 = completed (check 'valid' field), 1 = fatal error.
"""

import argparse
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from church_data_utils import (
    SVC_ID_RE,
    EVT_ID_RE,
    FAC_ID_RE,
    TIME_RE,
    RECURRENCE_ENUM,
    DAY_ENUM,
    EVENT_STATUS_ENUM,
    BOOKING_STATUS_ENUM,
    load_yaml,
    make_check_result,
    build_output,
    print_and_exit,
    fatal_error,
)

SCRIPT_NAME = "validate_schedule.py"
DATA_FILE = "data/schedule.yaml"


# ---------------------------------------------------------------------------
# Check Functions
# ---------------------------------------------------------------------------
def check_s1(data):
    """S1: All service/event/booking IDs unique and match format."""
    errors = []
    all_ids = []

    for s in data.get("regular_services", []):
        sid = s.get("id")
        if sid is None or not SVC_ID_RE.match(str(sid)):
            errors.append(f"S1: Invalid service ID format: {sid!r} (expected SVC-ABC[-N])")
        all_ids.append(sid)

    for e in data.get("special_events", []):
        eid = e.get("id")
        if eid is None or not EVT_ID_RE.match(str(eid)):
            errors.append(f"S1: Invalid event ID format: {eid!r} (expected EVT-YYYY-NNN+)")
        all_ids.append(eid)

    for f in data.get("facility_bookings", []):
        fid = f.get("id")
        if fid is None or not FAC_ID_RE.match(str(fid)):
            errors.append(f"S1: Invalid booking ID format: {fid!r} (expected FAC-YYYY-NNN+)")
        all_ids.append(fid)

    seen = set()
    for sid in all_ids:
        if sid is not None and sid in seen:
            errors.append(f"S1: Duplicate schedule ID: {sid}")
        if sid is not None:
            seen.add(sid)

    return make_check_result(
        "S1", "ID Uniqueness and Format", errors,
        f"All {len(all_ids)} schedule IDs valid and unique",
    )


def check_s2(data):
    """S2: Time fields match HH:MM 24-hour format."""
    errors = []

    for s in data.get("regular_services", []):
        t = s.get("time")
        if t is None or not TIME_RE.match(str(t)):
            errors.append(
                f"S2: Service {s.get('id')} time '{t}' is not HH:MM 24h format"
            )

    for e in data.get("special_events", []):
        t = e.get("time")
        if t is None or not TIME_RE.match(str(t)):
            errors.append(
                f"S2: Event {e.get('id')} time '{t}' is not HH:MM 24h format"
            )

    for f in data.get("facility_bookings", []):
        for field in ("time_start", "time_end"):
            t = f.get(field)
            if t is None or not TIME_RE.match(str(t)):
                errors.append(
                    f"S2: Booking {f.get('id')} {field} '{t}' is not HH:MM 24h format"
                )

    return make_check_result(
        "S2", "Time Format Validation", errors,
        "All time fields valid",
    )


def check_s3(data):
    """S3: recurrence and day_of_week are valid enum values."""
    errors = []
    for s in data.get("regular_services", []):
        sid = s.get("id", "UNKNOWN")
        rec = s.get("recurrence")
        if rec not in RECURRENCE_ENUM:
            errors.append(
                f"S3: Service {sid} recurrence '{rec}' not in {sorted(RECURRENCE_ENUM)}"
            )
        dow = s.get("day_of_week")
        if dow not in DAY_ENUM:
            errors.append(
                f"S3: Service {sid} day_of_week '{dow}' not in {sorted(DAY_ENUM)}"
            )

    return make_check_result(
        "S3", "Recurrence and Day-of-Week Validation", errors,
        "All recurrence and day_of_week values valid",
    )


def check_s4(data):
    """S4: event status and booking status in valid enum sets."""
    errors = []
    for e in data.get("special_events", []):
        eid = e.get("id", "UNKNOWN")
        st = e.get("status")
        if st not in EVENT_STATUS_ENUM:
            errors.append(
                f"S4: Event {eid} status '{st}' not in {sorted(EVENT_STATUS_ENUM)}"
            )

    for f in data.get("facility_bookings", []):
        fid = f.get("id", "UNKNOWN")
        st = f.get("status")
        if st not in BOOKING_STATUS_ENUM:
            errors.append(
                f"S4: Booking {fid} status '{st}' not in {sorted(BOOKING_STATUS_ENUM)}"
            )

    return make_check_result(
        "S4", "Event and Booking Status Enum", errors,
        "All status values valid",
    )


def check_s5(data):
    """S5: time_end > time_start; no overlaps for same facility on same date."""
    errors = []
    bookings = data.get("facility_bookings", [])

    # Time range validity
    for b in bookings:
        bid = b.get("id", "UNKNOWN")
        ts = str(b.get("time_start", ""))
        te = str(b.get("time_end", ""))
        if ts and te and ts >= te:
            errors.append(
                f"S5: Booking {bid} time_end '{te}' is not after time_start '{ts}'"
            )

    # Overlap detection: group by (facility, date), skip cancelled
    facility_date_groups = defaultdict(list)
    for b in bookings:
        if b.get("status") == "cancelled":
            continue
        key = (str(b.get("facility", "")), str(b.get("date", "")))
        facility_date_groups[key].append(b)

    for key, group in facility_date_groups.items():
        if len(group) < 2:
            continue
        sorted_group = sorted(group, key=lambda x: str(x.get("time_start", "")))
        for i in range(len(sorted_group) - 1):
            a = sorted_group[i]
            b_next = sorted_group[i + 1]
            if str(a.get("time_end", "")) > str(b_next.get("time_start", "")):
                errors.append(
                    f"S5: Facility conflict on {key[1]} at '{key[0]}': "
                    f"{a.get('id')} ({a.get('time_start')}-{a.get('time_end')}) "
                    f"overlaps with {b_next.get('id')} "
                    f"({b_next.get('time_start')}-{b_next.get('time_end')})"
                )

    return make_check_result(
        "S5", "Facility Booking Time Range and Conflict Detection", errors,
        "All booking times valid and conflict-free",
    )


def check_s6(data):
    """S6: All location/facility fields are non-empty strings."""
    errors = []

    for s in data.get("regular_services", []):
        sid = s.get("id", "UNKNOWN")
        loc = s.get("location")
        if not loc or not isinstance(loc, str) or not loc.strip():
            errors.append(f"S6: Service {sid} has empty or missing location")

    for e in data.get("special_events", []):
        eid = e.get("id", "UNKNOWN")
        loc = e.get("location")
        if not loc or not isinstance(loc, str) or not loc.strip():
            errors.append(f"S6: Event {eid} has empty or missing location")

    for f in data.get("facility_bookings", []):
        fid = f.get("id", "UNKNOWN")
        fac = f.get("facility")
        if not fac or not isinstance(fac, str) or not fac.strip():
            errors.append(f"S6: Booking {fid} has empty or missing facility")

    return make_check_result(
        "S6", "Location and Facility Non-Empty", errors,
        "All location/facility fields populated",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="P1 Validation for schedule.yaml")
    parser.add_argument("--data-dir", type=str, required=True, help="Path to data/ directory")
    parser.add_argument("--fix", action="store_true", help="(No fixable fields for schedule)")
    args = parser.parse_args()

    schedule_path = os.path.join(args.data_dir, "schedule.yaml")
    try:
        data = load_yaml(schedule_path)
    except (FileNotFoundError, Exception) as e:
        fatal_error(SCRIPT_NAME, str(e))

    checks = [
        check_s1(data),
        check_s2(data),
        check_s3(data),
        check_s4(data),
        check_s5(data),
        check_s6(data),
    ]

    output = build_output(SCRIPT_NAME, DATA_FILE, checks)
    print_and_exit(output)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        fatal_error(SCRIPT_NAME, str(e))

#!/usr/bin/env python3
"""
P1 Deterministic Validation — members.yaml (M1-M7)

Rules:
  M1: ID uniqueness and format (M\\d{3,})
  M2: Required fields non-empty (name, status)
  M3: Phone regex 010-NNNN-NNNN when present
  M4: Status enum (active, inactive, transferred, deceased)
  M5: Family ID cross-reference (family_id groups >= 2 members)
  M6: Date field validity (birth_date, registration_date, baptism_date)
  M7: _stats arithmetic (total_active, total_members match actual)

Exit codes: 0 = completed (check 'valid' field), 1 = fatal error.
"""

import argparse
import json
import os
import sys
from datetime import date, datetime

# Add script directory to path for local import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from church_data_utils import (
    MEMBER_ID_RE,
    MEMBER_STATUS_ENUM,
    FAMILY_ID_RE,
    PHONE_RE,
    DATE_RE,
    load_yaml,
    atomic_write_yaml,
    make_check_result,
    build_output,
    print_and_exit,
    fatal_error,
    parse_date,
)

SCRIPT_NAME = "validate_members.py"
DATA_FILE = "data/members.yaml"


# ---------------------------------------------------------------------------
# Check Functions
# ---------------------------------------------------------------------------
def check_m1(members):
    """M1: All member IDs unique and match M\\d{3,} format."""
    errors = []
    ids = []
    for m in members:
        mid = m.get("id")
        if mid is None or not MEMBER_ID_RE.match(str(mid)):
            errors.append(
                f"M1: Invalid member ID format: {mid!r} (expected M followed by 3+ digits)"
            )
        ids.append(mid)

    seen = set()
    for mid in ids:
        if mid is not None and mid in seen:
            errors.append(f"M1: Duplicate member ID: {mid}")
        if mid is not None:
            seen.add(mid)

    return make_check_result(
        "M1", "ID Uniqueness and Format", errors,
        f"All {len(ids)} member IDs valid and unique",
    )


def check_m2(members):
    """M2: name and status fields non-empty for every record."""
    errors = []
    for m in members:
        mid = m.get("id", "UNKNOWN")
        name_val = m.get("name")
        if not name_val or not isinstance(name_val, str) or not name_val.strip():
            errors.append(f"M2: Member {mid} has empty or missing 'name'")
        status_val = m.get("status")
        if not status_val or not isinstance(status_val, str) or not status_val.strip():
            errors.append(f"M2: Member {mid} has empty or missing 'status'")

    return make_check_result(
        "M2", "Required Fields Non-Empty", errors,
        "All members have non-empty name and status",
    )


def check_m3(members):
    """M3: phone matches 010-NNNN-NNNN Korean mobile format when present."""
    errors = []
    for m in members:
        mid = m.get("id", "UNKNOWN")
        contact = m.get("contact")
        if not isinstance(contact, dict):
            continue
        phone = contact.get("phone")
        if phone is not None and not PHONE_RE.match(str(phone)):
            errors.append(
                f"M3: Member {mid} phone '{phone}' does not match format 010-NNNN-NNNN"
            )

    return make_check_result(
        "M3", "Phone Format Validation", errors,
        "All phone numbers valid",
    )


def check_m4(members):
    """M4: status in {active, inactive, transferred, deceased}."""
    errors = []
    for m in members:
        mid = m.get("id", "UNKNOWN")
        status = m.get("status")
        if status not in MEMBER_STATUS_ENUM:
            errors.append(
                f"M4: Member {mid} has invalid status '{status}'. "
                f"Allowed: {sorted(MEMBER_STATUS_ENUM)}"
            )

    return make_check_result(
        "M4", "Status Enum Validation", errors,
        "All member statuses valid",
    )


def check_m5(members):
    """M5: family_id references valid family group with >= 2 members."""
    errors = []
    family_groups = {}

    for m in members:
        mid = m.get("id", "UNKNOWN")
        family = m.get("family")
        if not isinstance(family, dict):
            continue
        fid = family.get("family_id")
        if fid is None:
            continue
        if not FAMILY_ID_RE.match(str(fid)):
            errors.append(f"M5: Member {mid} has invalid family_id format: '{fid}'")
            continue
        family_groups.setdefault(fid, []).append(mid)

    for fid, member_ids in family_groups.items():
        if len(member_ids) < 2:
            errors.append(
                f"M5: Family {fid} has only {len(member_ids)} member(s): "
                f"{member_ids}. Family groups require >= 2 members."
            )

    return make_check_result(
        "M5", "Family ID Reference Integrity", errors,
        f"All {len(family_groups)} family groups valid (>= 2 members each)",
    )


def check_m6(members):
    """M6: Date field validity — birth_date, registration_date, baptism_date."""
    errors = []
    today = date.today()

    for m in members:
        mid = m.get("id", "UNKNOWN")

        # birth_date (top-level) — must be valid YYYY-MM-DD and in the past
        bd = m.get("birth_date")
        if bd is not None:
            parsed = parse_date(str(bd))
            if parsed is None:
                errors.append(
                    f"M6: Member {mid} birth_date '{bd}' is not valid YYYY-MM-DD"
                )
            elif parsed >= today:
                errors.append(
                    f"M6: Member {mid} birth_date '{bd}' is not in the past"
                )

        # church.registration_date
        church = m.get("church", {})
        if isinstance(church, dict):
            rd = church.get("registration_date")
            if rd is not None:
                if parse_date(str(rd)) is None:
                    errors.append(
                        f"M6: Member {mid} registration_date '{rd}' is not valid YYYY-MM-DD"
                    )

            # church.baptism_date (nullable)
            bpd = church.get("baptism_date")
            if bpd is not None:
                if parse_date(str(bpd)) is None:
                    errors.append(
                        f"M6: Member {mid} baptism_date '{bpd}' is not valid YYYY-MM-DD"
                    )

    return make_check_result(
        "M6", "Date Field Validity", errors,
        "All date fields valid (birth_date in past, registration/baptism dates valid)",
    )


def check_m7(members, stats, fix=False, data=None, data_path=None):
    """M7: _stats arithmetic — total_active and total_members match actual."""
    errors = []
    fixes = []

    actual_active = sum(1 for m in members if m.get("status") == "active")
    actual_total = len(members)

    stats_active = stats.get("total_active", 0)
    stats_total = stats.get("total_members", 0)

    if actual_active != stats_active:
        errors.append(
            f"M7: _stats.total_active={stats_active} but actual active count={actual_active}"
        )
        if fix:
            fixes.append(f"Fixed _stats.total_active: {stats_active} -> {actual_active}")
            stats["total_active"] = actual_active

    if actual_total != stats_total:
        errors.append(
            f"M7: _stats.total_members={stats_total} but actual total count={actual_total}"
        )
        if fix:
            fixes.append(f"Fixed _stats.total_members: {stats_total} -> {actual_total}")
            stats["total_members"] = actual_total

    if fix and fixes and data is not None and data_path is not None:
        stats["last_computed"] = date.today().isoformat()
        data["_stats"] = stats
        atomic_write_yaml(data_path, data)

    result = make_check_result(
        "M7", "Stats Arithmetic Consistency", errors,
        f"_stats match: total_active={actual_active}, total_members={actual_total}",
    )
    if fixes:
        result["fixes"] = fixes
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="P1 Validation for members.yaml")
    parser.add_argument("--data-dir", type=str, required=True, help="Path to data/ directory")
    parser.add_argument("--fix", action="store_true", help="Auto-fix computed fields (_stats)")
    args = parser.parse_args()

    members_path = os.path.join(args.data_dir, "members.yaml")
    try:
        data = load_yaml(members_path)
    except (FileNotFoundError, Exception) as e:
        fatal_error(SCRIPT_NAME, str(e))

    members = data.get("members", [])
    if not isinstance(members, list):
        fatal_error(SCRIPT_NAME, "members field is not a list")

    stats = data.get("_stats", {})
    if not isinstance(stats, dict):
        stats = {}

    checks = [
        check_m1(members),
        check_m2(members),
        check_m3(members),
        check_m4(members),
        check_m5(members),
        check_m6(members),
        check_m7(members, stats, fix=args.fix, data=data, data_path=members_path),
    ]

    output = build_output(SCRIPT_NAME, DATA_FILE, checks)
    print_and_exit(output)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        fatal_error(SCRIPT_NAME, str(e))

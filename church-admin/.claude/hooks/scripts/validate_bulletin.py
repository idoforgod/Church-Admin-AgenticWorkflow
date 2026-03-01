#!/usr/bin/env python3
"""
P1 Deterministic Validation — bulletin-data.yaml (B1-B3)

Rules:
  B1: Date consistency (bulletin date must be valid YYYY-MM-DD, must be a Sunday)
      + issue_number positive integer + required sections present
  B2: Issue number sequence (issue_number > 0, generation_history monotonically
      increasing, no duplicates)
  B3: Member reference integrity (birthday member_ids and anniversary family_ids
      must exist in members.yaml)

Exit codes: 0 = completed (check 'valid' field), 1 = fatal error.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from church_data_utils import (
    MEMBER_ID_RE,
    FAMILY_ID_RE,
    CELEBRATION_TYPE_ENUM,
    load_yaml,
    load_member_ids,
    make_check_result,
    build_output,
    print_and_exit,
    fatal_error,
    parse_date,
    is_sunday,
)

SCRIPT_NAME = "validate_bulletin.py"
DATA_FILE = "data/bulletin-data.yaml"


# ---------------------------------------------------------------------------
# Check Functions
# ---------------------------------------------------------------------------
def check_b1(data):
    """B1: Bulletin date is valid YYYY-MM-DD and is a Sunday.
    Also checks required sections are present."""
    errors = []
    bulletin = data.get("bulletin", {})
    if not isinstance(bulletin, dict):
        errors.append("B1: 'bulletin' key is missing or not a dict")
        return make_check_result("B1", "Date and Structure Consistency", errors)

    # Date validation
    bdate = bulletin.get("date")
    if bdate is None:
        errors.append("B1: Missing required bulletin field: 'date'")
    else:
        parsed = parse_date(str(bdate))
        if parsed is None:
            errors.append(f"B1: Bulletin date '{bdate}' is not valid YYYY-MM-DD")
        elif not is_sunday(parsed):
            day_name = parsed.strftime("%A")
            errors.append(
                f"B1: Bulletin date '{bdate}' is a {day_name}, not a Sunday"
            )

    # Required sections
    required_sections = {
        "issue_number": "Issue number",
        "sermon": "Sermon information",
        "worship_order": "Worship order",
    }
    for key, label in required_sections.items():
        val = bulletin.get(key)
        if val is None:
            errors.append(f"B1: Missing required bulletin section: '{key}' ({label})")
        elif key == "worship_order" and (not isinstance(val, list) or len(val) < 3):
            count = len(val) if isinstance(val, list) else 0
            errors.append(
                f"B1: worship_order must have >= 3 items (found {count})"
            )

    # Required sermon fields
    sermon = bulletin.get("sermon", {})
    if isinstance(sermon, dict):
        for field in ("title", "scripture", "preacher"):
            if not sermon.get(field):
                errors.append(f"B1: Missing required sermon field: '{field}'")

    return make_check_result(
        "B1", "Date and Structure Consistency", errors,
        "Bulletin date is valid Sunday and all required sections present",
    )


def check_b2(data):
    """B2: issue_number is a positive integer; generation_history has
    monotonically increasing issue numbers with no duplicates."""
    errors = []
    bulletin = data.get("bulletin", {})
    current_issue = bulletin.get("issue_number") if isinstance(bulletin, dict) else None

    if not isinstance(current_issue, int) or current_issue <= 0:
        errors.append(
            f"B2: issue_number must be a positive integer (found {current_issue!r})"
        )
        return make_check_result("B2", "Issue Number Sequence", errors)

    history = data.get("generation_history", [])
    if not isinstance(history, list):
        history = []

    history_issues = [h.get("issue") for h in history if isinstance(h, dict) and h.get("issue") is not None]

    # Check for duplicates
    if len(history_issues) != len(set(history_issues)):
        seen = set()
        dupes = set()
        for hi in history_issues:
            if hi in seen:
                dupes.add(hi)
            seen.add(hi)
        errors.append(f"B2: Duplicate issue numbers in generation_history: {sorted(dupes)}")

    # Check monotonicity
    for i in range(len(history_issues) - 1):
        if history_issues[i] >= history_issues[i + 1]:
            errors.append(
                f"B2: generation_history issue numbers not monotonically increasing: "
                f"{history_issues[i]} >= {history_issues[i + 1]}"
            )

    return make_check_result(
        "B2", "Issue Number Sequence", errors,
        f"Issue number {current_issue} valid; generation_history monotonically increasing",
    )


def check_b3(data, member_ids, family_ids):
    """B3: All member_id and family_id references in celebrations exist in members.yaml."""
    errors = []
    warnings = []

    if not member_ids and not family_ids:
        warnings.append(
            "B3: members.yaml not available — cross-reference checks skipped, format-only validation"
        )

    bulletin = data.get("bulletin", {})
    if not isinstance(bulletin, dict):
        return make_check_result("B3", "Member Reference Integrity", errors,
                                 "No bulletin section to validate")

    celebrations = bulletin.get("celebrations", {})
    if not isinstance(celebrations, dict):
        return make_check_result("B3", "Member Reference Integrity", errors,
                                 "No celebrations section to validate")

    # Validate celebration type keys
    for key in celebrations:
        if key not in CELEBRATION_TYPE_ENUM:
            errors.append(
                f"B3: Unknown celebration type '{key}' — expected one of {sorted(CELEBRATION_TYPE_ENUM)}"
            )

    # Birthday member_id checks
    for bday in celebrations.get("birthday", []):
        if not isinstance(bday, dict):
            continue
        mid = bday.get("member_id")
        if mid is not None:
            if not MEMBER_ID_RE.match(str(mid)):
                errors.append(f"B3: Birthday member_id '{mid}' has invalid format")
            elif member_ids and mid not in member_ids:
                errors.append(f"B3: Birthday member_id '{mid}' not found in members.yaml")

    # Wedding anniversary family_id checks
    for anniv in celebrations.get("wedding_anniversary", []):
        if not isinstance(anniv, dict):
            continue
        fid = anniv.get("family_id")
        if fid is not None:
            if not FAMILY_ID_RE.match(str(fid)):
                errors.append(f"B3: Anniversary family_id '{fid}' has invalid format")
            elif family_ids and fid not in family_ids:
                errors.append(
                    f"B3: Anniversary family_id '{fid}' not found in members.yaml families"
                )

    result = make_check_result(
        "B3", "Member Reference Integrity", errors,
        "All celebration references valid",
    )
    if warnings:
        result["warnings"] = warnings
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="P1 Validation for bulletin-data.yaml")
    parser.add_argument("--data-dir", type=str, required=True, help="Path to data/ directory")
    parser.add_argument("--members-file", type=str, default=None,
                        help="Override path to members.yaml for cross-reference checks")
    parser.add_argument("--fix", action="store_true", help="(No fixable fields for bulletin)")
    args = parser.parse_args()

    bulletin_path = os.path.join(args.data_dir, "bulletin-data.yaml")
    try:
        data = load_yaml(bulletin_path)
    except (FileNotFoundError, Exception) as e:
        fatal_error(SCRIPT_NAME, str(e))

    # Load member IDs for cross-reference checks (B3)
    member_ids, family_ids = load_member_ids(args.data_dir, args.members_file)

    all_warnings = []

    b3_result = check_b3(data, member_ids, family_ids)
    if "warnings" in b3_result:
        all_warnings.extend(b3_result.pop("warnings"))

    checks = [
        check_b1(data),
        check_b2(data),
        b3_result,
    ]

    output = build_output(SCRIPT_NAME, DATA_FILE, checks, warnings=all_warnings)
    print_and_exit(output)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        fatal_error(SCRIPT_NAME, str(e))

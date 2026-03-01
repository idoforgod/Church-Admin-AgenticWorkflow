#!/usr/bin/env python3
"""
P1 Deterministic Validation — newcomers.yaml (N1-N6)

Rules:
  N1: ID uniqueness and format (N\\d{3,})
  N2: Journey stage enum + milestone prerequisite validation
  N3: Date format YYYY-MM-DD
  N4: Member reference integrity (assigned_to, referred_by in members.yaml)
  N5: Settlement consistency (settled <-> settled_as_member + settled_date)
  N6: _stats arithmetic (total_active, by_stage match actual)

Exit codes: 0 = completed (check 'valid' field), 1 = fatal error.
"""

import argparse
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from church_data_utils import (
    NEWCOMER_ID_RE,
    MEMBER_ID_RE,
    JOURNEY_STAGE_SET,
    STAGE_TO_REQUIRED_MILESTONES,
    DATE_RE,
    load_yaml,
    atomic_write_yaml,
    load_member_ids,
    make_check_result,
    build_output,
    print_and_exit,
    fatal_error,
    parse_date,
)

SCRIPT_NAME = "validate_newcomers.py"
DATA_FILE = "data/newcomers.yaml"


# ---------------------------------------------------------------------------
# Check Functions
# ---------------------------------------------------------------------------
def check_n1(newcomers):
    """N1: All newcomer IDs unique and match N\\d{3,} format."""
    errors = []
    ids = []
    for n in newcomers:
        nid = n.get("id")
        if nid is None or not NEWCOMER_ID_RE.match(str(nid)):
            errors.append(
                f"N1: Invalid newcomer ID format: {nid!r} (expected N followed by 3+ digits)"
            )
        ids.append(nid)

    seen = set()
    for nid in ids:
        if nid is not None and nid in seen:
            errors.append(f"N1: Duplicate newcomer ID: {nid}")
        if nid is not None:
            seen.add(nid)

    return make_check_result(
        "N1", "ID Uniqueness and Format", errors,
        f"All {len(ids)} newcomer IDs valid and unique",
    )


def check_n2(newcomers):
    """N2: journey_stage valid + all preceding milestones completed."""
    errors = []
    for n in newcomers:
        nid = n.get("id", "UNKNOWN")
        stage = n.get("journey_stage")

        if stage not in JOURNEY_STAGE_SET:
            errors.append(f"N2: Newcomer {nid} has invalid journey_stage '{stage}'")
            continue

        milestones = n.get("journey_milestones", {})
        if not isinstance(milestones, dict):
            milestones = {}
        required = STAGE_TO_REQUIRED_MILESTONES.get(stage, [])

        for req_ms in required:
            ms_data = milestones.get(req_ms, {})
            if not isinstance(ms_data, dict) or not ms_data.get("completed", False):
                errors.append(
                    f"N2: Newcomer {nid} is at stage '{stage}' but "
                    f"prerequisite milestone '{req_ms}' is not completed"
                )

    return make_check_result(
        "N2", "Journey Stage Validity and Sequential Milestone Completion", errors,
        "All journey stages and milestones consistent",
    )


def check_n3(newcomers):
    """N3: first_visit and milestone dates are valid YYYY-MM-DD."""
    errors = []
    for n in newcomers:
        nid = n.get("id", "UNKNOWN")

        fv = n.get("first_visit")
        if fv is not None:
            if parse_date(str(fv)) is None:
                errors.append(
                    f"N3: Newcomer {nid} first_visit '{fv}' is not valid YYYY-MM-DD"
                )

        milestones = n.get("journey_milestones", {})
        if isinstance(milestones, dict):
            for ms_key, ms_data in milestones.items():
                if not isinstance(ms_data, dict):
                    continue
                ms_date = ms_data.get("date")
                if ms_date is not None:
                    if parse_date(str(ms_date)) is None:
                        errors.append(
                            f"N3: Newcomer {nid} milestone '{ms_key}' date "
                            f"'{ms_date}' is not valid YYYY-MM-DD"
                        )

        sd = n.get("settled_date")
        if sd is not None:
            if parse_date(str(sd)) is None:
                errors.append(
                    f"N3: Newcomer {nid} settled_date '{sd}' is not valid YYYY-MM-DD"
                )

    return make_check_result(
        "N3", "Date Format Validation", errors,
        "All date fields valid",
    )


def check_n4(newcomers, member_ids):
    """N4: referred_by and assigned_to reference valid member IDs."""
    errors = []
    warnings = []

    if not member_ids:
        warnings.append(
            "N4: members.yaml not available — cross-reference checks skipped, format-only validation"
        )

    for n in newcomers:
        nid = n.get("id", "UNKNOWN")

        ref = n.get("referred_by")
        if ref is not None:
            if not MEMBER_ID_RE.match(str(ref)):
                errors.append(
                    f"N4: Newcomer {nid} referred_by '{ref}' is not a valid member ID format"
                )
            elif member_ids and ref not in member_ids:
                errors.append(
                    f"N4: Newcomer {nid} referred_by '{ref}' does not exist in members.yaml"
                )

        assigned = n.get("assigned_to")
        if assigned is not None:
            if not MEMBER_ID_RE.match(str(assigned)):
                errors.append(
                    f"N4: Newcomer {nid} assigned_to '{assigned}' is not a valid member ID format"
                )
            elif member_ids and assigned not in member_ids:
                errors.append(
                    f"N4: Newcomer {nid} assigned_to '{assigned}' does not exist in members.yaml"
                )

    result = make_check_result(
        "N4", "Cross-Reference Integrity", errors,
        "All cross-references valid",
    )
    if warnings:
        result["warnings"] = warnings
    return result


def check_n5(newcomers, member_ids):
    """N5: settled_as_member references valid member ID when status is 'settled'."""
    errors = []
    for n in newcomers:
        nid = n.get("id", "UNKNOWN")
        status = n.get("status")
        settled_id = n.get("settled_as_member")
        settled_date = n.get("settled_date")

        if status == "settled":
            if settled_id is None:
                errors.append(
                    f"N5: Newcomer {nid} status is 'settled' but settled_as_member is null"
                )
            elif not MEMBER_ID_RE.match(str(settled_id)):
                errors.append(
                    f"N5: Newcomer {nid} settled_as_member '{settled_id}' has invalid format "
                    f"(expected M followed by 3+ digits)"
                )
            elif member_ids and settled_id not in member_ids:
                errors.append(
                    f"N5: Newcomer {nid} settled_as_member '{settled_id}' not found in members.yaml"
                )
            if settled_date is None:
                errors.append(
                    f"N5: Newcomer {nid} status is 'settled' but settled_date is null"
                )

        if settled_id is not None and status != "settled":
            errors.append(
                f"N5: Newcomer {nid} has settled_as_member='{settled_id}' "
                f"but status is '{status}' (expected 'settled')"
            )

    return make_check_result(
        "N5", "Settlement Consistency", errors,
        "All settlement fields consistent",
    )


def check_n6(newcomers, stats, fix=False, data=None, data_path=None):
    """N6: _stats computed fields match actual record counts."""
    errors = []
    fixes = []

    actual_active = sum(1 for n in newcomers if n.get("status") == "active")
    stats_active = stats.get("total_active", 0)
    if actual_active != stats_active:
        errors.append(
            f"N6: _stats.total_active={stats_active} but actual active count={actual_active}"
        )
        if fix:
            fixes.append(f"Fixed _stats.total_active: {stats_active} -> {actual_active}")
            stats["total_active"] = actual_active

    by_stage = stats.get("by_stage", {})
    stage_counts = {}
    for n in newcomers:
        stage = n.get("journey_stage", "unknown")
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

    for stage_name, expected in by_stage.items():
        actual = stage_counts.get(stage_name, 0)
        if actual != expected:
            errors.append(
                f"N6: _stats.by_stage.{stage_name}={expected} but actual count={actual}"
            )
            if fix:
                fixes.append(f"Fixed _stats.by_stage.{stage_name}: {expected} -> {actual}")
                by_stage[stage_name] = actual

    if fix and fixes and data is not None and data_path is not None:
        stats["last_computed"] = date.today().isoformat()
        data["_stats"] = stats
        atomic_write_yaml(data_path, data)

    result = make_check_result(
        "N6", "Stats Arithmetic Consistency", errors,
        "All computed stats match actual counts",
    )
    if fixes:
        result["fixes"] = fixes
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="P1 Validation for newcomers.yaml")
    parser.add_argument("--data-dir", type=str, required=True, help="Path to data/ directory")
    parser.add_argument("--members-file", type=str, default=None,
                        help="Override path to members.yaml for cross-reference checks")
    parser.add_argument("--fix", action="store_true", help="Auto-fix computed fields (_stats)")
    args = parser.parse_args()

    newcomers_path = os.path.join(args.data_dir, "newcomers.yaml")
    try:
        data = load_yaml(newcomers_path)
    except (FileNotFoundError, Exception) as e:
        fatal_error(SCRIPT_NAME, str(e))

    newcomers = data.get("newcomers", [])
    if not isinstance(newcomers, list):
        fatal_error(SCRIPT_NAME, "newcomers field is not a list")

    stats = data.get("_stats", {})
    if not isinstance(stats, dict):
        stats = {}

    # Load member IDs for cross-reference checks (N4, N5)
    member_ids, _ = load_member_ids(args.data_dir, args.members_file)

    all_warnings = []

    n4_result = check_n4(newcomers, member_ids)
    if "warnings" in n4_result:
        all_warnings.extend(n4_result.pop("warnings"))

    checks = [
        check_n1(newcomers),
        check_n2(newcomers),
        check_n3(newcomers),
        n4_result,
        check_n5(newcomers, member_ids),
        check_n6(newcomers, stats, fix=args.fix, data=data, data_path=newcomers_path),
    ]

    output = build_output(SCRIPT_NAME, DATA_FILE, checks, warnings=all_warnings)
    print_and_exit(output)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        fatal_error(SCRIPT_NAME, str(e))

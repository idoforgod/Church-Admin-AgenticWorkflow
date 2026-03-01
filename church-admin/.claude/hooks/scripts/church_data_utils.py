#!/usr/bin/env python3
"""
Shared utilities for Church Administration P1 validation scripts.

Provides:
- atomic_write_yaml(): fcntl.flock + tempfile + os.rename atomic write
- load_yaml(): safe YAML loading with error handling
- Common constants (ID_PATTERNS, ENUMS, etc.)
- Date parsing helper
"""

import fcntl
import json
import os
import re
import sys
import tempfile
from datetime import date, datetime

import yaml


# ---------------------------------------------------------------------------
# ID Format Patterns
# ---------------------------------------------------------------------------
MEMBER_ID_RE = re.compile(r"^M\d{3,}$")
FAMILY_ID_RE = re.compile(r"^F\d{3,}$")
NEWCOMER_ID_RE = re.compile(r"^N\d{3,}$")
OFFERING_ID_RE = re.compile(r"^OFF-\d{4}-\d{3,}$")
EXPENSE_ID_RE = re.compile(r"^EXP-\d{4}-\d{3,}$")
SVC_ID_RE = re.compile(r"^SVC-[A-Z]+-?\d*$")
EVT_ID_RE = re.compile(r"^EVT-\d{4}-\d{3,}$")
FAC_ID_RE = re.compile(r"^FAC-\d{4}-\d{3,}$")

PHONE_RE = re.compile(r"^010-\d{4}-\d{4}$")
TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# ---------------------------------------------------------------------------
# Enum Sets
# ---------------------------------------------------------------------------
MEMBER_STATUS_ENUM = {"active", "inactive", "transferred", "deceased"}

NEWCOMER_STATUS_ENUM = {"active", "settled", "inactive", "transferred"}

JOURNEY_STAGE_SET = {
    "first_visit", "attending", "small_group",
    "baptism_class", "baptized", "settled",
}

STAGE_TO_REQUIRED_MILESTONES = {
    "first_visit": [],
    "attending": ["first_visit"],
    "small_group": ["first_visit", "welcome_call", "second_visit"],
    "baptism_class": ["first_visit", "welcome_call", "second_visit", "small_group_intro"],
    "baptized": ["first_visit", "welcome_call", "second_visit", "small_group_intro", "baptism_class"],
    "settled": ["first_visit", "welcome_call", "second_visit", "small_group_intro", "baptism_class", "baptism"],
}

RECURRENCE_ENUM = {"weekly", "biweekly", "monthly"}
DAY_ENUM = {"sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"}

EVENT_STATUS_ENUM = {"planned", "confirmed", "completed", "cancelled"}
BOOKING_STATUS_ENUM = {"pending", "confirmed", "cancelled"}

OFFERING_TYPE_ENUM = {
    "sunday_offering", "special_offering", "building_fund",
    "mission_offering", "thanksgiving_offering", "other",
}

CELEBRATION_TYPE_ENUM = {"birthday", "wedding_anniversary"}


# ---------------------------------------------------------------------------
# Date Helpers
# ---------------------------------------------------------------------------
def parse_date(s):
    """Parse YYYY-MM-DD string to date. Returns None on any failure."""
    if not isinstance(s, str) or not DATE_RE.match(s):
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def is_sunday(d):
    """Check if a date object is a Sunday (weekday() == 6)."""
    return d.weekday() == 6


# ---------------------------------------------------------------------------
# YAML I/O
# ---------------------------------------------------------------------------
def load_yaml(filepath):
    """Safely load a YAML file. Raises on error.

    Args:
        filepath: Path to the YAML file.

    Returns:
        Parsed YAML data (dict or list).

    Raises:
        FileNotFoundError: If file does not exist.
        yaml.YAMLError: If YAML parsing fails.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    return data


def atomic_write_yaml(path, data):
    """Write YAML atomically using tempfile + rename.

    Pattern: write to .tmp -> flock -> flush -> fsync -> unlock -> rename
    The os.rename() is atomic on POSIX systems (same filesystem).
    """
    dir_name = os.path.dirname(path) or "."
    tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            yaml.dump(
                data, f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )
            f.flush()
            os.fsync(f.fileno())
            fcntl.flock(f, fcntl.LOCK_UN)
        os.rename(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


# ---------------------------------------------------------------------------
# Member ID loading for cross-reference validation
# ---------------------------------------------------------------------------
def load_member_ids(data_dir, members_file=None):
    """Load member IDs from members.yaml for cross-reference checks.

    Returns:
        Tuple of (member_id_set, family_id_set).
        Both are empty sets if file not found (graceful degradation).
    """
    path = members_file or os.path.join(data_dir, "members.yaml")
    if not os.path.isfile(path):
        return set(), set()
    data = load_yaml(path)
    members = data.get("members", [])
    member_ids = {m.get("id") for m in members if m.get("id")}
    family_ids = set()
    for m in members:
        fid = m.get("family", {}).get("family_id") if isinstance(m.get("family"), dict) else None
        if fid:
            family_ids.add(fid)
    return member_ids, family_ids


# ---------------------------------------------------------------------------
# Output Helpers
# ---------------------------------------------------------------------------
def make_check_result(rule, name, errors, detail_pass=None):
    """Build a standard check result dict."""
    return {
        "rule": rule,
        "name": name,
        "status": "PASS" if not errors else "FAIL",
        "detail": (detail_pass or "OK") if not errors else f"{len(errors)} error(s) found",
        "errors": errors,
    }


def build_output(script_name, data_file, checks, warnings=None):
    """Build the final JSON output dict."""
    all_errors = []
    for c in checks:
        all_errors.extend(c.get("errors", []))

    failed = [c["rule"] for c in checks if c["status"] == "FAIL"]
    passed_count = len(checks) - len(failed)

    summary = f"{passed_count}/{len(checks)} checks passed"
    if failed:
        summary += f", {len(failed)} failed ({', '.join(failed)})"

    return {
        "valid": len(all_errors) == 0,
        "script": script_name,
        "data_file": data_file,
        "checks": checks,
        "errors": all_errors,
        "warnings": warnings or [],
        "summary": summary,
    }


def print_and_exit(output):
    """Print JSON output and exit with code 0."""
    print(json.dumps(output, indent=2, ensure_ascii=False))
    sys.exit(0)


def fatal_error(script_name, error_msg):
    """Print fatal error JSON and exit with code 1."""
    output = {
        "valid": False,
        "script": script_name,
        "error": error_msg,
        "checks": [],
        "errors": [f"Fatal error: {error_msg}"],
        "warnings": [],
        "summary": f"Fatal error: {error_msg}",
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    sys.exit(1)

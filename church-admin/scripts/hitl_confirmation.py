#!/usr/bin/env python3
"""
Human-in-the-Loop (HitL) Confirmation — Staging Review & Data Commit

Reads staging files from inbox/staging/, presents extracted data for human review,
and on approval writes validated records to the target data/*.yaml files using
atomic_write from church_data_utils.py.

This script enforces the principle that NO data reaches data/*.yaml without
explicit human approval.

Workflow:
  1. List all staging files in inbox/staging/
  2. For each file: display summary, records, confidence scores
  3. Accept user action: approve / reject / skip
  4. On approve: merge records into target YAML, move staging to processed
  5. On reject: move staging + source to inbox/errors/ with reason
  6. On skip: leave staging file for later review

Usage:
    # Interactive review of all staging files:
    python3 hitl_confirmation.py --staging-dir ./inbox/staging --data-dir ./data

    # Review a specific staging file:
    python3 hitl_confirmation.py --file ./inbox/staging/tier_a_offering_20260228.json

    # Auto-approve all high-confidence records (>=0.9) — for batch processing:
    python3 hitl_confirmation.py --staging-dir ./inbox/staging --auto-approve 0.9

    # List pending staging files without interactive prompts:
    python3 hitl_confirmation.py --staging-dir ./inbox/staging --list-only

    # Programmatic approve (non-interactive, for agent use):
    python3 hitl_confirmation.py --file <staging.json> --action approve --data-dir ./data
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime

import yaml

# ---------------------------------------------------------------------------
# Import church_data_utils for atomic YAML writes
# ---------------------------------------------------------------------------
# The utils module is in church-admin/.claude/hooks/scripts/
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)
_UTILS_DIR = os.path.join(_PROJECT_DIR, ".claude", "hooks", "scripts")
if _UTILS_DIR not in sys.path:
    sys.path.insert(0, _UTILS_DIR)

try:
    from church_data_utils import atomic_write_yaml, load_yaml
    HAS_UTILS = True
except ImportError:
    HAS_UTILS = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PROCESSED_DIR = "inbox/processed"
ERRORS_DIR = "inbox/errors"

# ID generation patterns (match existing data format)
ID_PATTERNS = {
    "offerings": ("OFF-{year}-{seq:03d}", re.compile(r"^OFF-\d{4}-(\d{3,})$")),
    "expenses": ("EXP-{year}-{seq:03d}", re.compile(r"^EXP-\d{4}-(\d{3,})$")),
    "newcomers": ("N{seq:03d}", re.compile(r"^N(\d{3,})$")),
    "members": ("M{seq:03d}", re.compile(r"^M(\d{3,})$")),
}


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------
def display_staging_summary(staging_data):
    """Print a human-readable summary of a staging file."""
    print("\n" + "=" * 70)
    print(f"  Source:      {staging_data.get('source_file', 'unknown')}")
    print(f"  Tier:        {staging_data.get('parser_tier', '?')}")
    print(f"  Target:      {staging_data.get('target_data_file', '?')} "
          f"[{staging_data.get('target_section', '?')}]")
    print(f"  Records:     {staging_data.get('total_records', 0)}")
    print(f"  Confidence:  {staging_data.get('average_confidence', 0):.0%}")
    print(f"  Parsed at:   {staging_data.get('timestamp', '?')}")

    # Glossary mappings used
    glossary = staging_data.get("glossary_mappings", {})
    if glossary:
        print(f"  Glossary:    {len(glossary)} terms used")
        for k, v in glossary.items():
            print(f"               {k} -> {v}")

    # Warnings
    warnings = staging_data.get("parse_warnings", [])
    if warnings:
        print(f"  Warnings:    {len(warnings)}")
        for w in warnings[:5]:
            print(f"    [!] {w}")
        if len(warnings) > 5:
            print(f"    ... and {len(warnings) - 5} more")

    print("=" * 70)


def display_records(records, max_display=10):
    """Print records in a readable format."""
    for i, record in enumerate(records[:max_display], start=1):
        conf = record.get("confidence", 0)
        conf_marker = "OK" if conf >= 0.8 else "LOW" if conf >= 0.5 else "WARN"
        source_info = record.get("source_row") or record.get("source_block", "?")

        print(f"\n  Record {i} (source: row/block {source_info}, "
              f"confidence: {conf:.0%} [{conf_marker}]):")

        fields = record.get("fields", {})
        for key, value in fields.items():
            if isinstance(value, dict):
                print(f"    {key}:")
                for sk, sv in value.items():
                    print(f"      {sk}: {sv}")
            elif isinstance(value, list):
                if value:
                    print(f"    {key}: {', '.join(str(v) for v in value)}")
                else:
                    print(f"    {key}: []")
            else:
                print(f"    {key}: {value}")

        notes = record.get("notes", [])
        if notes:
            for note in notes:
                print(f"    [note] {note}")

    if len(records) > max_display:
        print(f"\n  ... {len(records) - max_display} more records not shown")


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------
def get_next_id(section, existing_data, year=None):
    """Generate the next sequential ID for a data section.

    Args:
        section: Data section name (e.g., 'offerings', 'newcomers').
        existing_data: Current data dict from the target YAML.
        year: Year for year-based IDs (offerings, expenses).

    Returns:
        Next ID string.
    """
    if year is None:
        year = datetime.now().year

    pattern_info = ID_PATTERNS.get(section)
    if not pattern_info:
        return f"UNKNOWN-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    template, regex = pattern_info

    # Find existing max sequence number
    max_seq = 0
    items = existing_data.get(section, [])
    for item in items:
        item_id = item.get("id", "")
        m = regex.match(item_id)
        if m:
            seq = int(m.group(1))
            if seq > max_seq:
                max_seq = seq

    next_seq = max_seq + 1
    return template.format(year=year, seq=next_seq)


# ---------------------------------------------------------------------------
# Data merge logic
# ---------------------------------------------------------------------------
def merge_offering_records(records, existing_data, year=None):
    """Merge offering records into finance.yaml offerings format.

    Groups records by date into offering entries with item lists.
    """
    if year is None:
        year = datetime.now().year

    # Group records by date
    by_date = {}
    for record in records:
        fields = record.get("fields", {})
        date = fields.get("date")
        if not date:
            continue
        if date not in by_date:
            by_date[date] = {
                "service": fields.get("service", "주일예배 (Sunday Service)"),
                "items": [],
            }
        by_date[date]["items"].append({
            "category": fields.get("category_english")
                        or fields.get("type", "unknown"),
            "amount": fields.get("amount", 0),
        })

    # Create offering entries
    new_entries = []
    for date, info in sorted(by_date.items()):
        entry_id = get_next_id("offerings", existing_data, year)
        total = sum(item["amount"] for item in info["items"])
        entry = {
            "id": entry_id,
            "date": date,
            "service": info["service"],
            "type": "sunday_offering",
            "items": info["items"],
            "total": total,
            "recorded_by": "data-ingestor (inbox pipeline)",
            "verified": False,
            "void": False,
        }
        new_entries.append(entry)
        # Update existing_data so next ID is sequential
        existing_data.setdefault("offerings", []).append(entry)

    return new_entries


def merge_expense_records(records, existing_data, year=None):
    """Merge expense records into finance.yaml expenses format."""
    if year is None:
        year = datetime.now().year

    new_entries = []
    for record in records:
        fields = record.get("fields", {})
        entry_id = get_next_id("expenses", existing_data, year)
        entry = {
            "id": entry_id,
            "date": fields.get("date"),
            "category": fields.get("category", "기타"),
            "subcategory": fields.get("subcategory", ""),
            "amount": fields.get("amount", 0),
            "description": fields.get("description", ""),
            "payment_method": fields.get("payment_method", ""),
            "approved_by": "",
            "receipt": True,
            "void": False,
        }
        new_entries.append(entry)
        existing_data.setdefault("expenses", []).append(entry)

    return new_entries


def merge_newcomer_records(records, existing_data):
    """Merge newcomer records into newcomers.yaml format."""
    new_entries = []
    for record in records:
        fields = record.get("fields", {})
        entry_id = get_next_id("newcomers", existing_data)

        # Build journey milestones template
        milestones = {
            "first_visit": {
                "date": fields.get("first_visit"),
                "completed": bool(fields.get("first_visit")),
            },
            "welcome_call": {"date": None, "completed": False},
            "second_visit": {"date": None, "completed": False},
            "small_group_intro": {"date": None, "completed": False},
            "baptism_class": {"date": None, "completed": False},
            "baptism": {"date": None, "completed": False},
        }

        entry = {
            "id": entry_id,
            "name": fields.get("name"),
            "gender": fields.get("gender"),
            "birth_year": fields.get("birth_year"),
            "contact": fields.get("contact", {"phone": None, "kakao_id": None}),
            "first_visit": fields.get("first_visit"),
            "visit_route": fields.get("visit_route"),
            "referred_by": fields.get("referred_by"),
            "journey_stage": fields.get("journey_stage", "first_visit"),
            "journey_milestones": milestones,
            "assigned_to": None,
            "assigned_department": fields.get("assigned_department"),
            "status": "active",
            "settled_as_member": None,
            "settled_date": None,
        }
        new_entries.append(entry)
        existing_data.setdefault("newcomers", []).append(entry)

    return new_entries


def merge_member_records(records, existing_data):
    """Merge member records into members.yaml format."""
    new_entries = []
    for record in records:
        fields = record.get("fields", {})
        entry_id = get_next_id("members", existing_data)
        entry = {
            "id": entry_id,
            "name": fields.get("name"),
            "gender": fields.get("gender"),
            "birth_date": fields.get("birth_date"),
            "status": "active",
            "contact": fields.get("contact", {"phone": None, "email": None, "address": None}),
            "church": fields.get("church", {
                "registration_date": datetime.now().strftime("%Y-%m-%d"),
                "baptism_date": None,
                "baptism_type": None,
                "department": None,
                "cell_group": None,
                "role": None,
                "serving_area": [],
            }),
            "family": {"family_id": None, "relation": None},
            "history": [{
                "date": datetime.now().strftime("%Y-%m-%d"),
                "event": "registration",
                "note": "Registered via inbox pipeline",
            }],
        }
        new_entries.append(entry)
        existing_data.setdefault("members", []).append(entry)

    return new_entries


def merge_member_visit_records(records, existing_data):
    """Merge visitation (심방일지) records into a data file.

    Appends visit records with date, visitor, visited member, and notes.
    """
    visits = existing_data.get("member_visits", [])
    new_entries = []
    for rec in records:
        fields = rec.get("fields", {})
        entry = {
            "date": fields.get("date", datetime.now().strftime("%Y-%m-%d")),
            "visitor": fields.get("visitor", ""),
            "visited_member": fields.get("visited_member", ""),
            "purpose": fields.get("purpose", "pastoral_care"),
            "notes": fields.get("notes", ""),
        }
        new_entries.append(entry)
    visits.extend(new_entries)
    existing_data["member_visits"] = visits
    return new_entries


def merge_meeting_minutes_records(records, existing_data):
    """Merge meeting minutes (회의록) records into a data file.

    Appends meeting records with date, type, attendees, and decisions.
    """
    minutes = existing_data.get("meeting_minutes", [])
    new_entries = []
    for rec in records:
        fields = rec.get("fields", {})
        entry = {
            "date": fields.get("date", datetime.now().strftime("%Y-%m-%d")),
            "meeting_type": fields.get("meeting_type", "general"),
            "attendees": fields.get("attendees", []),
            "agenda": fields.get("agenda", []),
            "decisions": fields.get("decisions", []),
            "notes": fields.get("notes", ""),
        }
        new_entries.append(entry)
    minutes.extend(new_entries)
    existing_data["meeting_minutes"] = minutes
    return new_entries


# ---------------------------------------------------------------------------
# Approval / rejection actions
# ---------------------------------------------------------------------------
def approve_staging(staging_path, staging_data, data_dir, processed_dir):
    """Approve a staging file: merge records into target YAML.

    Args:
        staging_path: Path to the staging JSON file.
        staging_data: Parsed staging data dict.
        data_dir: Path to data/ directory.
        processed_dir: Path to inbox/processed/ directory.

    Returns:
        dict with result summary.
    """
    if not HAS_UTILS:
        return {
            "error": "church_data_utils not available. "
                     "Cannot perform atomic YAML write."
        }

    target_file = staging_data.get("target_data_file")
    target_section = staging_data.get("target_section")
    records = staging_data.get("records", [])

    if not target_file or target_file == "unknown":
        return {"error": f"Unknown target data file: {target_file}"}

    if not records:
        return {"error": "No records to merge"}

    # Resolve target path
    target_path = os.path.join(
        data_dir, os.path.basename(target_file)
    ) if not os.path.isabs(target_file) else target_file

    # Adjust for relative path stored in staging (e.g., "data/finance.yaml")
    if not os.path.isfile(target_path):
        alt_path = os.path.join(os.path.dirname(data_dir), target_file)
        if os.path.isfile(alt_path):
            target_path = alt_path

    # Load existing data
    try:
        existing_data = load_yaml(target_path)
    except FileNotFoundError:
        return {"error": f"Target data file not found: {target_path}"}

    # Merge based on section type
    merge_fn = {
        "offerings": merge_offering_records,
        "expenses": merge_expense_records,
        "newcomers": merge_newcomer_records,
        "members": merge_member_records,
        "member_visits": merge_member_visit_records,
        "meeting_minutes": merge_meeting_minutes_records,
    }.get(target_section)

    if merge_fn is None:
        return {
            "error": f"No merge function for section '{target_section}'. "
                     "Manual data entry required."
        }

    try:
        new_entries = merge_fn(records, existing_data)
    except Exception as e:
        return {"error": f"Merge failed: {e}"}

    # Update metadata
    existing_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    existing_data["updated_by"] = "data-ingestor"

    # Atomic write
    try:
        atomic_write_yaml(target_path, existing_data)
    except Exception as e:
        return {"error": f"Atomic write failed: {e}"}

    # Move staging file to processed
    os.makedirs(processed_dir, exist_ok=True)
    processed_path = os.path.join(
        processed_dir, os.path.basename(staging_path)
    )
    shutil.move(staging_path, processed_path)

    # Move source file to processed (if it exists and is not already there)
    source_file = staging_data.get("source_file")
    if source_file and os.path.isfile(source_file):
        source_processed = os.path.join(
            processed_dir, os.path.basename(source_file)
        )
        shutil.move(source_file, source_processed)

    return {
        "status": "approved",
        "target_file": target_path,
        "target_section": target_section,
        "records_merged": len(new_entries),
        "new_ids": [e.get("id") for e in new_entries if e.get("id")],
        "staging_moved_to": processed_path,
    }


def reject_staging(staging_path, staging_data, errors_dir, reason=""):
    """Reject a staging file: move to errors directory with reason.

    Args:
        staging_path: Path to the staging JSON file.
        staging_data: Parsed staging data dict.
        errors_dir: Path to inbox/errors/ directory.
        reason: Rejection reason string.

    Returns:
        dict with result summary.
    """
    os.makedirs(errors_dir, exist_ok=True)

    # Move staging file
    error_path = os.path.join(errors_dir, os.path.basename(staging_path))
    shutil.move(staging_path, error_path)

    # Create error report
    error_report = {
        "rejected_at": datetime.now().isoformat(timespec="seconds"),
        "reason": reason or "Rejected by human reviewer",
        "source_file": staging_data.get("source_file"),
        "records_count": staging_data.get("total_records", 0),
        "average_confidence": staging_data.get("average_confidence", 0),
    }

    report_path = error_path.replace(".json", ".error.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(error_report, f, indent=2, ensure_ascii=False)

    # Move source file to errors too
    source_file = staging_data.get("source_file")
    if source_file and os.path.isfile(source_file):
        source_error_path = os.path.join(
            errors_dir, os.path.basename(source_file)
        )
        shutil.move(source_file, source_error_path)

    return {
        "status": "rejected",
        "reason": reason,
        "staging_moved_to": error_path,
        "error_report": report_path,
    }


# ---------------------------------------------------------------------------
# Listing and batch operations
# ---------------------------------------------------------------------------
def list_staging_files(staging_dir):
    """List all pending staging files.

    Returns list of (path, summary_dict) tuples.
    """
    results = []
    if not os.path.isdir(staging_dir):
        return results

    for filename in sorted(os.listdir(staging_dir)):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(staging_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            summary = {
                "file": filename,
                "tier": data.get("parser_tier", "?"),
                "source": data.get("source_file", "?"),
                "target": data.get("target_data_file", "?"),
                "records": data.get("total_records", 0),
                "confidence": data.get("average_confidence", 0),
                "timestamp": data.get("timestamp", "?"),
                "status": data.get("status", "ready"),
            }
            results.append((filepath, summary))
        except (json.JSONDecodeError, OSError) as e:
            results.append((filepath, {"file": filename, "error": str(e)}))

    return results


# ---------------------------------------------------------------------------
# Interactive review
# ---------------------------------------------------------------------------
def interactive_review(staging_dir, data_dir, processed_dir, errors_dir):
    """Run interactive review of all staging files.

    Returns summary dict with counts of approved/rejected/skipped.
    """
    files = list_staging_files(staging_dir)
    if not files:
        print("No staging files to review.")
        return {"approved": 0, "rejected": 0, "skipped": 0}

    print(f"\n{'=' * 70}")
    print(f"  HitL Confirmation — {len(files)} staging file(s) pending")
    print(f"{'=' * 70}")

    counts = {"approved": 0, "rejected": 0, "skipped": 0}

    for filepath, summary in files:
        if "error" in summary:
            print(f"\n  [ERROR] {summary['file']}: {summary['error']}")
            continue

        # Load full staging data
        with open(filepath, "r", encoding="utf-8") as f:
            staging_data = json.load(f)

        # Skip pending_analysis files
        if staging_data.get("status") == "pending_analysis":
            print(f"\n  [SKIP] {summary['file']}: pending multimodal analysis")
            counts["skipped"] += 1
            continue

        display_staging_summary(staging_data)
        display_records(staging_data.get("records", []))

        # Prompt for action
        print("\n  Actions: [a]pprove  [r]eject  [s]kip  [q]uit")
        try:
            action = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  Exiting review.")
            break

        if action in ("a", "approve"):
            result = approve_staging(
                filepath, staging_data, data_dir, processed_dir
            )
            if "error" in result:
                print(f"  [ERROR] {result['error']}")
            else:
                print(f"  [APPROVED] {result['records_merged']} records merged "
                      f"into {result['target_file']}")
                if result.get("new_ids"):
                    print(f"  New IDs: {', '.join(result['new_ids'])}")
                counts["approved"] += 1

        elif action in ("r", "reject"):
            reason = input("  Rejection reason: ").strip()
            result = reject_staging(
                filepath, staging_data, errors_dir, reason
            )
            print(f"  [REJECTED] Moved to {result['staging_moved_to']}")
            counts["rejected"] += 1

        elif action in ("q", "quit"):
            print("  Exiting review.")
            break

        else:
            print("  [SKIPPED]")
            counts["skipped"] += 1

    print(f"\n{'=' * 70}")
    print(f"  Review complete: "
          f"{counts['approved']} approved, "
          f"{counts['rejected']} rejected, "
          f"{counts['skipped']} skipped")
    print(f"{'=' * 70}")

    return counts


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="HitL Confirmation — Review and commit staging data to YAML"
    )
    parser.add_argument(
        "--staging-dir", default="./inbox/staging",
        help="Directory with staging JSON files (default: ./inbox/staging)"
    )
    parser.add_argument(
        "--data-dir", default="./data",
        help="Directory with target data/*.yaml files (default: ./data)"
    )
    parser.add_argument(
        "--file",
        help="Review a specific staging file instead of all"
    )
    parser.add_argument(
        "--action", choices=["approve", "reject", "list"],
        help="Non-interactive action for --file (approve/reject/list)"
    )
    parser.add_argument(
        "--reason", default="",
        help="Rejection reason (used with --action reject)"
    )
    parser.add_argument(
        "--auto-approve", type=float, metavar="THRESHOLD",
        help="Auto-approve records with confidence >= threshold (0.0-1.0)"
    )
    parser.add_argument(
        "--list-only", action="store_true",
        help="List pending staging files without interactive review"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output results as JSON"
    )
    args = parser.parse_args()

    # Resolve directories relative to project
    project_dir = os.path.dirname(_SCRIPT_DIR)
    staging_dir = os.path.join(project_dir, "inbox", "staging") \
        if args.staging_dir == "./inbox/staging" else args.staging_dir
    data_dir = os.path.join(project_dir, "data") \
        if args.data_dir == "./data" else args.data_dir
    processed_dir = os.path.join(project_dir, PROCESSED_DIR)
    errors_dir = os.path.join(project_dir, ERRORS_DIR)

    # List mode
    if args.list_only or args.action == "list":
        files = list_staging_files(staging_dir)
        if not files:
            print("No staging files pending.")
            return
        print(f"\nPending staging files ({len(files)}):\n")
        for filepath, summary in files:
            if "error" in summary:
                print(f"  [ERROR] {summary['file']}: {summary['error']}")
            else:
                conf = summary.get("confidence", 0)
                print(f"  [{summary['tier']}] {summary['file']}")
                print(f"       {summary['records']} records, "
                      f"confidence: {conf:.0%}, "
                      f"target: {summary['target']}")
        return

    # Single file mode
    if args.file:
        if not os.path.isfile(args.file):
            print(f"ERROR: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)

        with open(args.file, "r", encoding="utf-8") as f:
            staging_data = json.load(f)

        if args.action == "approve":
            result = approve_staging(
                args.file, staging_data, data_dir, processed_dir
            )
        elif args.action == "reject":
            result = reject_staging(
                args.file, staging_data, errors_dir, args.reason
            )
        else:
            # Display and wait for interactive input
            display_staging_summary(staging_data)
            display_records(staging_data.get("records", []))
            result = {"status": "displayed"}

        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif "error" in result:
            print(f"ERROR: {result['error']}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"Result: {result.get('status', 'unknown')}")
        return

    # Auto-approve mode
    if args.auto_approve is not None:
        threshold = args.auto_approve
        files = list_staging_files(staging_dir)
        approved = 0
        skipped = 0
        for filepath, summary in files:
            if "error" in summary:
                continue
            conf = summary.get("confidence", 0)
            if conf >= threshold:
                with open(filepath, "r", encoding="utf-8") as f:
                    staging_data = json.load(f)
                result = approve_staging(
                    filepath, staging_data, data_dir, processed_dir
                )
                if "error" not in result:
                    print(f"  [AUTO-APPROVED] {summary['file']} "
                          f"(confidence: {conf:.0%})")
                    approved += 1
                else:
                    print(f"  [ERROR] {summary['file']}: {result['error']}")
            else:
                print(f"  [SKIP] {summary['file']} "
                      f"(confidence: {conf:.0%} < {threshold:.0%})")
                skipped += 1

        print(f"\nAuto-approve complete: {approved} approved, {skipped} skipped")
        return

    # Default: interactive review
    interactive_review(staging_dir, data_dir, processed_dir, errors_dir)


if __name__ == "__main__":
    main()

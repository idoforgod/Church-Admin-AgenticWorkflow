#!/usr/bin/env python3
"""
Inbox Parser — Main entry point for the 3-tier data collection pipeline.

Scans inbox/ subdirectories for new files, routes each file to the appropriate
tier parser based on file extension, and produces JSON staging files.

Tier routing:
  - Tier A (Structured):       .xlsx, .csv  -> tier_a_parser.py
  - Tier B (Semi-structured):  .docx, .pdf  -> tier_b_parser.py
  - Tier C (Unstructured):     .jpg, .png, .jpeg, .heic, .webp -> tier_c_parser.py

Usage:
    # Scan all inbox directories and parse new files:
    python3 inbox_parser.py --inbox-dir ./inbox/ --data-dir ./data/ \\
        --glossary ./data/church-glossary.yaml

    # Scan a specific subdirectory:
    python3 inbox_parser.py --inbox-dir ./inbox/ --scan-dir templates

    # Dry run (show what would be parsed without actually parsing):
    python3 inbox_parser.py --inbox-dir ./inbox/ --dry-run

    # Parse a single file:
    python3 inbox_parser.py --inbox-dir ./inbox/ --file ./inbox/templates/헌금내역.xlsx
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# Import tier parsers (same directory)
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from tier_a_parser import parse_file as tier_a_parse
from tier_b_parser import parse_file as tier_b_parse
from tier_c_parser import create_staging as tier_c_parse


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# Extension -> tier mapping
TIER_ROUTING = {
    # Tier A: Structured
    ".xlsx": "A",
    ".csv": "A",
    ".xls": "A",
    # Tier B: Semi-structured
    ".docx": "B",
    ".pdf": "B",
    # Tier C: Unstructured (images)
    ".jpg": "C",
    ".jpeg": "C",
    ".png": "C",
    ".heic": "C",
    ".webp": "C",
}

# Subdirectories to scan
SCAN_DIRS = ["templates", "documents", "images"]

# Files/patterns to skip
SKIP_PATTERNS = {".DS_Store", "Thumbs.db", ".gitkeep", ".gitignore"}


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------
def discover_files(inbox_dir, scan_dirs=None):
    """Discover parseable files in inbox subdirectories.

    Args:
        inbox_dir: Path to inbox/ directory.
        scan_dirs: List of subdirectory names to scan. Defaults to SCAN_DIRS.

    Returns:
        List of (filepath, extension, tier) tuples, sorted by tier then name.
    """
    if scan_dirs is None:
        scan_dirs = SCAN_DIRS

    discovered = []
    for subdir in scan_dirs:
        subdir_path = os.path.join(inbox_dir, subdir)
        if not os.path.isdir(subdir_path):
            continue

        for filename in sorted(os.listdir(subdir_path)):
            # Skip hidden files and known non-data files
            if filename.startswith(".") or filename in SKIP_PATTERNS:
                continue

            filepath = os.path.join(subdir_path, filename)
            if not os.path.isfile(filepath):
                continue

            ext = os.path.splitext(filename)[1].lower()
            tier = TIER_ROUTING.get(ext)
            if tier:
                discovered.append((filepath, ext, tier))

    # Sort by tier (A, B, C) then filename
    discovered.sort(key=lambda x: (x[2], x[0]))
    return discovered


# ---------------------------------------------------------------------------
# Parse dispatcher
# ---------------------------------------------------------------------------
def parse_single_file(filepath, tier, glossary_path, staging_dir):
    """Route a single file to the appropriate tier parser.

    Args:
        filepath: Path to the file to parse.
        tier: Tier identifier ("A", "B", or "C").
        glossary_path: Path to church-glossary.yaml.
        staging_dir: Path to inbox/staging/ directory.

    Returns:
        dict with parse results (includes 'staging_file' on success,
        'error' key on failure).
    """
    try:
        if tier == "A":
            return tier_a_parse(filepath, glossary_path, staging_dir)
        elif tier == "B":
            return tier_b_parse(filepath, glossary_path, staging_dir)
        elif tier == "C":
            return tier_c_parse(filepath, glossary_path, staging_dir)
        else:
            return {"error": f"Unknown tier: {tier}"}
    except Exception as e:
        return {"error": f"Parser exception for {filepath}: {e}"}


def move_to_errors(filepath, inbox_dir, error_msg):
    """Move a file to inbox/errors/ with an error report.

    Args:
        filepath: Path to the file that failed parsing.
        inbox_dir: Path to inbox/ directory.
        error_msg: Error message string.
    """
    errors_dir = os.path.join(inbox_dir, "errors")
    os.makedirs(errors_dir, exist_ok=True)

    basename = os.path.basename(filepath)
    error_dest = os.path.join(errors_dir, basename)

    # Avoid overwriting existing error files
    if os.path.exists(error_dest):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(basename)
        error_dest = os.path.join(errors_dir, f"{name}_{ts}{ext}")

    try:
        shutil.copy2(filepath, error_dest)
    except OSError:
        pass

    # Write error report
    error_report = {
        "source_file": filepath,
        "error": error_msg,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    report_path = error_dest + ".error.json"
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(error_report, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def move_to_processed(filepath, inbox_dir):
    """Move a successfully parsed file to inbox/processed/.

    Args:
        filepath: Path to the parsed file.
        inbox_dir: Path to inbox/ directory.
    """
    processed_dir = os.path.join(inbox_dir, "processed")
    os.makedirs(processed_dir, exist_ok=True)

    basename = os.path.basename(filepath)
    dest = os.path.join(processed_dir, basename)

    # Avoid overwriting
    if os.path.exists(dest):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(basename)
        dest = os.path.join(processed_dir, f"{name}_{ts}{ext}")

    try:
        shutil.move(filepath, dest)
    except OSError as e:
        print(f"  WARNING: Could not move {filepath} to processed: {e}",
              file=sys.stderr)


# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------
def run_pipeline(inbox_dir, data_dir, glossary_path, scan_dirs=None,
                 dry_run=False, single_file=None):
    """Execute the full inbox parsing pipeline.

    Args:
        inbox_dir: Path to inbox/ directory.
        data_dir: Path to data/ directory.
        glossary_path: Path to church-glossary.yaml.
        scan_dirs: Subdirectories to scan (or all if None).
        dry_run: If True, only list files without parsing.
        single_file: If set, parse only this specific file.

    Returns:
        dict with pipeline results summary.
    """
    staging_dir = os.path.join(inbox_dir, "staging")
    os.makedirs(staging_dir, exist_ok=True)

    results = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "inbox_dir": inbox_dir,
        "files_discovered": 0,
        "files_parsed": 0,
        "files_errored": 0,
        "files_skipped": 0,
        "total_records": 0,
        "staging_files": [],
        "errors": [],
        "by_tier": {"A": 0, "B": 0, "C": 0},
    }

    # Discover files
    if single_file:
        ext = os.path.splitext(single_file)[1].lower()
        tier = TIER_ROUTING.get(ext)
        if tier is None:
            results["errors"].append({
                "file": single_file,
                "error": f"Unsupported file extension: {ext}",
            })
            return results
        files = [(single_file, ext, tier)]
    else:
        files = discover_files(inbox_dir, scan_dirs)

    results["files_discovered"] = len(files)

    if not files:
        print("No parseable files found in inbox.")
        return results

    # Display discovery summary
    print(f"\n{'=' * 60}")
    print(f"  Inbox Pipeline — {len(files)} file(s) discovered")
    print(f"{'=' * 60}")

    tier_counts = {"A": 0, "B": 0, "C": 0}
    for _, _, tier in files:
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    for tier_name, count in sorted(tier_counts.items()):
        tier_labels = {"A": "Structured", "B": "Semi-structured", "C": "Unstructured"}
        if count > 0:
            print(f"  Tier {tier_name} ({tier_labels.get(tier_name, '?')}): {count} file(s)")

    print()

    if dry_run:
        print("  [DRY RUN] Files that would be parsed:\n")
        for filepath, ext, tier in files:
            print(f"    [{tier}] {filepath}")
        return results

    # Parse each file
    for filepath, ext, tier in files:
        basename = os.path.basename(filepath)
        print(f"  [{tier}] Parsing: {basename}")

        result = parse_single_file(filepath, tier, glossary_path, staging_dir)

        if "error" in result:
            print(f"      ERROR: {result['error']}")
            results["files_errored"] += 1
            results["errors"].append({
                "file": filepath,
                "tier": tier,
                "error": result["error"],
            })
            move_to_errors(filepath, inbox_dir, result["error"])
        else:
            record_count = result.get("total_records", 0)
            confidence = result.get("average_confidence", 0)
            staging_file = result.get("staging_file", "?")

            print(f"      {record_count} records extracted "
                  f"(confidence: {confidence:.0%})")
            print(f"      Staging: {os.path.basename(staging_file)}")

            results["files_parsed"] += 1
            results["total_records"] += record_count
            results["by_tier"][tier] += 1
            results["staging_files"].append({
                "file": staging_file,
                "source": filepath,
                "tier": tier,
                "records": record_count,
                "confidence": confidence,
            })

            # Move source to processed
            move_to_processed(filepath, inbox_dir)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  Pipeline complete:")
    print(f"    Parsed:  {results['files_parsed']}")
    print(f"    Errors:  {results['files_errored']}")
    print(f"    Records: {results['total_records']}")
    print(f"    Staging: {len(results['staging_files'])} file(s) in {staging_dir}")
    print(f"{'=' * 60}")

    if results["staging_files"]:
        print(f"\n  Next step: Review staging files with hitl_confirmation.py")
        print(f"    python3 scripts/hitl_confirmation.py --staging-dir {staging_dir} "
              f"--data-dir {data_dir}")

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Inbox Parser — Main entry point for church admin data collection pipeline"
    )
    parser.add_argument(
        "--inbox-dir", default="./inbox/",
        help="Path to inbox/ directory (default: ./inbox/)"
    )
    parser.add_argument(
        "--data-dir", default="./data/",
        help="Path to data/ directory (default: ./data/)"
    )
    parser.add_argument(
        "--glossary", default="./data/church-glossary.yaml",
        help="Path to church-glossary.yaml (default: ./data/church-glossary.yaml)"
    )
    parser.add_argument(
        "--scan-dir", nargs="*",
        help="Specific subdirectories to scan (default: templates documents images)"
    )
    parser.add_argument(
        "--file",
        help="Parse a single file instead of scanning directories"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be parsed without actually parsing"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output results as JSON"
    )
    args = parser.parse_args()

    results = run_pipeline(
        inbox_dir=args.inbox_dir,
        data_dir=args.data_dir,
        glossary_path=args.glossary,
        scan_dirs=args.scan_dir,
        dry_run=args.dry_run,
        single_file=args.file,
    )

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

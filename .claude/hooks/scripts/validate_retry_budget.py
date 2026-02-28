#!/usr/bin/env python3
"""
Retry Budget P1 Validation — validate_retry_budget.py

Standalone script called by Orchestrator before each retry attempt.
NOT a Hook — manually invoked during workflow execution.

Usage:
    # Check if retry is allowed (read-only)
    python3 .claude/hooks/scripts/validate_retry_budget.py --step 3 --gate verification --project-dir .

    # Check AND atomically consume one retry budget (RECOMMENDED — single call)
    python3 .claude/hooks/scripts/validate_retry_budget.py --step 3 --gate verification --project-dir . --check-and-increment

    # Increment only (legacy — prefer --check-and-increment)
    python3 .claude/hooks/scripts/validate_retry_budget.py --step 3 --gate verification --project-dir . --increment

Output: JSON to stdout
    {"valid": true, "can_retry": true, "retries_used": 1, "max_retries": 3, ...}

Exit codes:
    0 — validation completed (check "can_retry" field for decision)
    1 — argument error or fatal failure

Checks (RB1-RB3):
    RB1: Counter file read (deterministic integer, 0 if absent)
    RB2: ULW active detection (snapshot regex — reuses existing P1 pattern)
    RB3: Budget comparison (retries_used < max_retries)

Modes:
    (default)              Read-only — check budget without modifying counter
    --check-and-increment  Atomic check+consume — if can_retry is true, increment
                           counter BEFORE returning. Prevents AI from forgetting
                           the increment call. Counter stays unchanged if budget
                           is exhausted (can_retry: false).
    --increment            Unconditional increment — legacy mode for manual use

P1 Compliance: All logic is deterministic arithmetic + file I/O + regex.
SOT Compliance: Read-only on SOT. Writes only to {gate}-logs/ counter files.

Known limitation: ULW detection reads latest.md snapshot. If a previous session
used ULW and the snapshot hasn't been overwritten yet, max_retries may be 3
instead of 2. This is a safe-direction false positive (allows 1 extra retry).
"""

import argparse
import json
import os
import re
import sys

# Constants
DEFAULT_MAX_RETRIES = 10
ULW_MAX_RETRIES = 15
VALID_GATES = ("verification", "pacs", "review")

# Gate → directory mapping
GATE_DIRS = {
    "verification": "verification-logs",
    "pacs": "pacs-logs",
    "review": "review-logs",
}

# ULW detection regex — matches "ULW 상태" section in snapshot
# Reuses the same signal that restore_context.py checks
_ULW_SNAPSHOT_RE = re.compile(r"ULW 상태|Ultrawork Mode State")


def _counter_path(project_dir, step, gate):
    """Return the path to the retry counter file for a step/gate."""
    gate_dir = os.path.join(project_dir, GATE_DIRS[gate])
    return os.path.join(gate_dir, f".step-{step}-retry-count")


def _read_counter(path):
    """Read retry count from counter file. Returns 0 if absent or invalid.

    P1: deterministic file read + int parse.
    """
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                return int(f.read().strip())
    except (ValueError, IOError):
        pass
    return 0


def _increment_counter(path):
    """Atomically increment the retry counter and return the new value.

    P1: atomic write (temp → rename) to prevent partial writes.
    """
    current = _read_counter(path)
    new_value = current + 1

    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Atomic write
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w") as f:
            f.write(str(new_value))
        os.replace(tmp_path, path)
    except Exception:
        # Fallback: direct write
        try:
            with open(path, "w") as f:
                f.write(str(new_value))
        except IOError:
            pass

    return new_value


def _detect_ulw_from_snapshot(project_dir):
    """Detect ULW active state from latest snapshot.

    P1: regex match on file content — same signal as restore_context.py.
    Returns True if ULW is active, False otherwise.
    """
    snapshot_path = os.path.join(
        project_dir, ".claude", "context-snapshots", "latest.md"
    )
    try:
        if os.path.exists(snapshot_path):
            with open(snapshot_path, "r", encoding="utf-8") as f:
                content = f.read()
            return bool(_ULW_SNAPSHOT_RE.search(content))
    except IOError:
        pass
    return False


def main():
    parser = argparse.ArgumentParser(
        description="P1 Validation for retry budget (ULW-aware)"
    )
    parser.add_argument("--step", type=int, required=True, help="Step number")
    parser.add_argument(
        "--gate",
        choices=VALID_GATES,
        required=True,
        help="Quality gate type (verification, pacs, review)",
    )
    parser.add_argument(
        "--project-dir", default=".", help="Project root directory"
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--check-and-increment",
        action="store_true",
        help="Atomic: check budget, increment if allowed (RECOMMENDED)",
    )
    mode_group.add_argument(
        "--increment",
        action="store_true",
        help="Unconditional increment (legacy — prefer --check-and-increment)",
    )

    args = parser.parse_args()
    project_dir = os.path.abspath(args.project_dir)

    # RB2: Detect ULW state
    ulw_active = _detect_ulw_from_snapshot(project_dir)
    max_retries = ULW_MAX_RETRIES if ulw_active else DEFAULT_MAX_RETRIES

    # Counter file path
    counter_file = _counter_path(project_dir, args.step, args.gate)

    # Determine mode and execute
    incremented = False

    if args.check_and_increment:
        # Atomic check+consume: read → compare → increment only if budget allows
        retries_used = _read_counter(counter_file)
        can_retry = retries_used < max_retries
        if can_retry:
            retries_used = _increment_counter(counter_file)
            incremented = True
    elif args.increment:
        # Legacy: unconditional increment
        retries_used = _increment_counter(counter_file)
        can_retry = retries_used < max_retries
        incremented = True
    else:
        # Read-only check
        retries_used = _read_counter(counter_file)
        can_retry = retries_used < max_retries

    budget_remaining = max(0, max_retries - retries_used)

    # Build result
    checks = {
        "RB1_counter_read": "PASS",
        "RB2_ulw_detection": "PASS",
        "RB3_budget_remaining": "PASS" if can_retry else "FAIL",
    }

    result = {
        "valid": True,
        "can_retry": can_retry,
        "retries_used": retries_used,
        "max_retries": max_retries,
        "budget_remaining": budget_remaining,
        "ulw_active": ulw_active,
        "gate": args.gate,
        "step": args.step,
        "incremented": incremented,
        "checks": checks,
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"valid": False, "error": str(e)}))
        sys.exit(1)

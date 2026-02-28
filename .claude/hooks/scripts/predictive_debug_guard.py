#!/usr/bin/env python3
"""
PreToolUse Hook — Predictive Debugging Guard

Warns Claude about historically error-prone files BEFORE editing.
Does NOT block — exit code 0 always. Warnings via stderr.

Triggered by: PreToolUse with matcher "Edit|Write"
Location: .claude/settings.json (Project)
Path: Direct execution (standalone, NOT through context_guard.py)

P1 Hallucination Prevention:
  - Risk score lookup is deterministic (JSON parse + dict lookup).
  - Path normalization is deterministic (os.path.relpath).
  - Threshold comparison is deterministic (float comparison).
  - No _context_lib.py import — self-contained for fast startup.

Data flow:
  risk-scores.json (pre-computed at SessionStart by restore_context.py)
  → read cache → normalize file path → lookup risk score → warn if high

Design decisions:
  - Self-contained: No imports from _context_lib.py to avoid loading 4,500+ line
    module on every Edit/Write (each PreToolUse spawns a new Python process).
  - Exit 0 always: This is a WARNING hook, not a BLOCKING hook.
    Unlike block_destructive_commands.py (exit 2 = block), this hook only informs.
  - Stderr for Claude: Claude receives stderr as self-correction feedback.
  - Cold start safe: If risk-scores.json doesn't exist or has < 5 sessions,
    exits silently (no false warnings with insufficient data).

ADR: Predictive Debugging in DECISION-LOG.md
"""

import json
import os
import sys

# --- Constants (self-contained — NOT imported from _context_lib.py) ---
# D-7: Intentionally duplicated from _context_lib.py for fast startup.
#      Changing _RISK_SCORE_THRESHOLD or _RISK_MIN_SESSIONS in _context_lib.py
#      REQUIRES updating these values to stay in sync.
RISK_THRESHOLD = 3.0        # Sync: _context_lib.py _RISK_SCORE_THRESHOLD
MIN_SESSIONS = 5            # Sync: _context_lib.py _RISK_MIN_SESSIONS
# Cache file path relative to project's .claude/context-snapshots/
CACHE_FILENAME = "risk-scores.json"
# Maximum age of cache in seconds (2 hours — beyond this, data is stale)
# Trade-off (ADR-036): Cache is generated at SessionStart (clear|compact|resume),
# NOT at startup. First startup after >2h gap has no cache → silent exit (safe).
MAX_CACHE_AGE_SECONDS = 7200


def main():
    """Read PreToolUse JSON from stdin, check file risk score, warn if high."""
    try:
        stdin_data = sys.stdin.read()
        if not stdin_data.strip():
            sys.exit(0)

        payload = json.loads(stdin_data)
        file_path = payload.get("tool_input", {}).get("file_path", "")

        if not file_path:
            sys.exit(0)
    except (json.JSONDecodeError, KeyError, TypeError):
        sys.exit(0)

    # Determine project directory
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        sys.exit(0)

    # Read cached risk scores
    cache_path = os.path.join(
        project_dir, ".claude", "context-snapshots", CACHE_FILENAME
    )
    risk_data = _read_cache(cache_path)
    if not risk_data:
        sys.exit(0)

    # Cold start guard
    if risk_data.get("data_sessions", 0) < MIN_SESSIONS:
        sys.exit(0)

    # Cache freshness check
    if not _is_cache_fresh(cache_path):
        sys.exit(0)

    # Normalize file path to project-relative
    try:
        rel_path = os.path.relpath(file_path, project_dir)
    except ValueError:
        rel_path = file_path

    # Look up risk score — try exact match first, then basename match
    files = risk_data.get("files", {})
    file_risk = files.get(rel_path)

    if not file_risk:
        # Fallback: try matching by basename (error_patterns often store bare names)
        basename = os.path.basename(rel_path)
        for cached_path, cached_risk in files.items():
            if os.path.basename(cached_path) == basename:
                file_risk = cached_risk
                break

    if not file_risk:
        sys.exit(0)

    risk_score = file_risk.get("risk_score", 0)
    if risk_score < RISK_THRESHOLD:
        sys.exit(0)

    # Generate warning for Claude via stderr
    error_types = file_risk.get("error_types", {})
    error_count = file_risk.get("error_count", 0)
    resolution_rate = file_risk.get("resolution_rate", 0)
    last_error = file_risk.get("last_error_session", "unknown")

    types_str = ", ".join(f"{k}:{v}" for k, v in sorted(
        error_types.items(), key=lambda x: x[1], reverse=True
    ))

    print(
        f"PREDICTIVE WARNING: {rel_path} — risk score {risk_score:.1f}\n"
        f"  Past errors: {error_count} ({types_str})\n"
        f"  Resolution rate: {resolution_rate:.0%} | Last error: {last_error}\n"
        f"  Recommendation: Review past error patterns before editing. "
        f"Pay extra attention to {_top_error_type(error_types)} issues.",
        file=sys.stderr,
    )

    # Always exit 0 — warn, don't block
    sys.exit(0)


def _read_cache(cache_path):
    """Read risk-scores.json cache file.

    Returns dict on success, None on any failure.
    """
    if not os.path.exists(cache_path):
        return None
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        return None


def _is_cache_fresh(cache_path):
    """Check if cache file was generated within MAX_CACHE_AGE_SECONDS.

    Returns True if fresh, False if stale or unreadable.
    """
    try:
        import time
        age = time.time() - os.path.getmtime(cache_path)
        return age < MAX_CACHE_AGE_SECONDS
    except OSError:
        return False


def _top_error_type(error_types):
    """Return the most frequent error type name.

    Returns: string (error type name), or "unknown" if empty.
    """
    if not error_types:
        return "unknown"
    return max(error_types, key=error_types.get)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Safety-first: never block Claude on unexpected internal errors
        sys.exit(0)

#!/usr/bin/env python3
"""
PreToolUse Hook — Data File Sole-Writer Guard

Enforces the sole-writer discipline for church-admin data files.
Blocks Edit/Write to data/*.yaml unless the current agent has write permission.

Triggered by: PreToolUse with matcher "Edit|Write"
Location: Parent .claude/settings.json (Project)
Path: Direct execution via `if test -f` guard

Exit codes:
  0 — Allow (not a data file, or no agent context to verify)
  2 — Block (unauthorized write attempt) — Claude receives stderr feedback

Safety-first: Any unexpected error → exit(0) (never block Claude on script failure).

Design notes:
  - The sole-writer map is defined here as a constant. It mirrors the headers in each
    data/*.yaml file and the CLAUDE.md documentation.
  - Agent identity is inferred from CLAUDE_AGENT_NAME env var (set by Claude Code when
    running sub-agents). If not set, we assume the main orchestrator session, which is
    allowed to write (it delegates to agents, but in single-session mode it IS the agent).
  - church-glossary.yaml is append-only by ANY agent — always allowed.
"""

import json
import os
import sys

# ---------------------------------------------------------------------------
# Sole-writer map: data file basename → authorized agent name
# D-7 intentional duplication with CLAUDE.md and data file headers.
# If you change this map, update CLAUDE.md and the data file headers too.
# ---------------------------------------------------------------------------
SOLE_WRITER_MAP = {
    "members.yaml": "member-manager",
    "finance.yaml": "finance-recorder",
    "schedule.yaml": "schedule-manager",
    "newcomers.yaml": "newcomer-tracker",
    "bulletin-data.yaml": "bulletin-generator",
    # church-glossary.yaml: ANY agent can append — not in this map
}

# Files in data/ that are always allowed (append-only or non-restricted)
ALWAYS_ALLOWED = {"church-glossary.yaml"}


def _is_data_file(file_path: str) -> bool:
    """Check if the file path targets a data/*.yaml file."""
    if not file_path:
        return False
    # Normalize path
    parts = file_path.replace("\\", "/").split("/")
    # Look for data/ directory followed by a .yaml file
    for i, part in enumerate(parts):
        if part == "data" and i + 1 < len(parts) and parts[i + 1].endswith(".yaml"):
            return True
    return False


def _get_data_basename(file_path: str) -> str:
    """Extract the basename of a data/*.yaml file."""
    return os.path.basename(file_path)


def main():
    """Read PreToolUse JSON from stdin, check sole-writer discipline."""
    try:
        stdin_data = sys.stdin.read()
        if not stdin_data.strip():
            sys.exit(0)

        payload = json.loads(stdin_data)
        tool_input = payload.get("tool_input", {})

        # Edit tool uses "file_path", Write tool uses "file_path"
        file_path = tool_input.get("file_path", "")

        if not file_path:
            sys.exit(0)

        # Only guard data/*.yaml files
        if not _is_data_file(file_path):
            sys.exit(0)

        basename = _get_data_basename(file_path)

        # Always-allowed files (append-only)
        if basename in ALWAYS_ALLOWED:
            sys.exit(0)

        # Check sole-writer map
        if basename not in SOLE_WRITER_MAP:
            # Unknown data file — allow (don't block on files we don't know about)
            sys.exit(0)

        authorized_agent = SOLE_WRITER_MAP[basename]

        # Get current agent identity
        agent_name = os.environ.get("CLAUDE_AGENT_NAME", "")

        # If no agent name set, assume main orchestrator — allow
        # (The main session may legitimately write data files when not using sub-agents)
        if not agent_name:
            sys.exit(0)

        # Normalize agent name (remove @ prefix if present)
        agent_name = agent_name.lstrip("@").strip()

        # Check authorization
        if agent_name != authorized_agent:
            print(
                f"DATA FILE WRITE BLOCKED: {basename} can only be written by "
                f"'{authorized_agent}' agent. Current agent: '{agent_name}'.\n"
                f"Sole-writer discipline (Absolute Criterion 2) prevents data corruption.\n"
                f"Route this operation through the {authorized_agent} agent instead.",
                file=sys.stderr,
            )
            sys.exit(2)

        # Authorized — allow
        sys.exit(0)

    except (json.JSONDecodeError, KeyError, TypeError, OSError):
        # Malformed input or unexpected error — don't block
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        # Safety-first: never block on unexpected errors
        sys.exit(0)

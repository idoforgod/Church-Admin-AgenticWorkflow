#!/usr/bin/env python3
"""
Context Preservation System — update_work_log.py

Triggered by: PostToolUse (Edit|Write|Bash|Task|NotebookEdit|TeamCreate|SendMessage|TaskCreate|TaskUpdate)

Responsibilities:
  1. Accumulate work log entries (file-locked append to work_log.jsonl)
  2. Multi-signal token estimation from transcript
  3. If >75% threshold: trigger proactive save via save_context.py logic

Architecture:
  - Runs after every Edit, Write, Bash, Task tool use
  - Appends structured log entry with fcntl.flock protection
  - Checks transcript size to estimate token usage
  - Non-blocking: exit 0 always (never blocks Claude)
"""

import os
import sys
import json
from datetime import datetime

# Add script directory to path for shared library import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _context_lib import (
    read_stdin_json,
    get_snapshot_dir,
    append_with_lock,
    estimate_tokens,
    should_skip_save,
    parse_transcript,
    capture_sot,
    load_work_log,
    generate_snapshot_md,
    atomic_write,
    cleanup_snapshots,
    read_autopilot_state,
    sot_paths,
    THRESHOLD_75_TOKENS,
    update_latest_with_guard,
    archive_and_index_session,
)


def main():
    input_data = read_stdin_json()

    # Determine project directory
    project_dir = os.environ.get(
        "CLAUDE_PROJECT_DIR",
        input_data.get("cwd", os.getcwd()),
    )

    snapshot_dir = get_snapshot_dir(project_dir)
    os.makedirs(snapshot_dir, exist_ok=True)

    # Extract tool information
    tool_name = input_data.get("tool_name", "unknown")
    tool_input = input_data.get("tool_input", {})
    tool_response = input_data.get("tool_response", {})
    session_id = input_data.get("session_id", "unknown")
    transcript_path = input_data.get("transcript_path", "")

    # Build work log entry
    log_entry = _build_log_entry(tool_name, tool_input, tool_response, session_id, project_dir)

    # Append to work log with file locking
    work_log_path = os.path.join(snapshot_dir, "work_log.jsonl")
    entry_json = json.dumps(log_entry, ensure_ascii=False) + "\n"
    append_with_lock(work_log_path, entry_json)

    # Estimate tokens and check threshold
    estimated_tokens, signals = estimate_tokens(transcript_path)

    if signals.get("over_threshold", False):
        # Token usage exceeds 75% — trigger proactive save
        _trigger_proactive_save(project_dir, snapshot_dir, input_data)


def _build_log_entry(tool_name, tool_input, tool_response, session_id, project_dir=None):
    """Build a structured work log entry."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = {
        "timestamp": now,
        "session_id": session_id,
        "tool_name": tool_name,
        "summary": "",
        "file_path": "",
    }

    if tool_name == "Write":
        path = tool_input.get("file_path", "")
        content = tool_input.get("content", "")
        line_count = len(content.split("\n"))
        entry["file_path"] = path
        entry["summary"] = f"Write {path} ({line_count} lines)"

    elif tool_name == "Edit":
        path = tool_input.get("file_path", "")
        old = tool_input.get("old_string", "")
        new = tool_input.get("new_string", "")
        entry["file_path"] = path
        old_preview = old.split("\n")[0][:60] if old else ""
        new_preview = new.split("\n")[0][:60] if new else ""
        entry["summary"] = f"Edit {path}: '{old_preview}' → '{new_preview}'"

    elif tool_name == "Bash":
        cmd = tool_input.get("command", "")
        desc = tool_input.get("description", "")
        entry["summary"] = f"Bash: {cmd[:150]}" + (f" ({desc})" if desc else "")

    elif tool_name == "Task":
        desc = tool_input.get("description", "")
        agent_type = tool_input.get("subagent_type", "")
        entry["summary"] = f"Task ({agent_type}): {desc}"

    elif tool_name == "NotebookEdit":
        path = tool_input.get("notebook_path", "")
        mode = tool_input.get("edit_mode", "replace")
        entry["file_path"] = path
        entry["summary"] = f"NotebookEdit ({mode}) → {path}"

    elif tool_name == "TeamCreate":
        team = tool_input.get("team_name", "")
        entry["summary"] = f"TeamCreate: {team}"

    elif tool_name == "SendMessage":
        msg_type = tool_input.get("type", "message")
        recipient = tool_input.get("recipient", "broadcast")
        entry["summary"] = f"SendMessage ({msg_type}) → {recipient}"

    elif tool_name == "TaskCreate":
        subject = tool_input.get("subject", "")
        entry["summary"] = f"TaskCreate: {subject[:100]}"

    elif tool_name == "TaskUpdate":
        task_id = tool_input.get("taskId", "")
        status = tool_input.get("status", "")
        entry["summary"] = f"TaskUpdate #{task_id}: {status}"

    else:
        entry["summary"] = f"{tool_name}: {json.dumps(tool_input, ensure_ascii=False)[:150]}"

    # Autopilot tracking fields (conditional — only when active)
    # A-3: Fast path using sot_paths() — skip if no SOT file exists
    if project_dir and any(os.path.exists(p) for p in sot_paths(project_dir)):
        try:
            ap_state = read_autopilot_state(project_dir)
            if ap_state:
                entry["autopilot_active"] = True
                entry["autopilot_step"] = ap_state.get("current_step", 0)
        except Exception:
            pass  # Non-blocking

    return entry


def _trigger_proactive_save(project_dir, snapshot_dir, input_data=None):
    """Trigger a proactive save when token threshold is exceeded.

    Direct function call (no subprocess) to avoid stdin piping issues.
    Uses the same _context_lib functions as save_context.py.
    """
    # Skip if recently saved
    if should_skip_save(snapshot_dir):
        return

    try:
        transcript_path = (input_data or {}).get("transcript_path", "")
        session_id = (input_data or {}).get("session_id", "unknown")

        # Parse transcript directly
        entries = parse_transcript(transcript_path)

        # Load work log
        work_log = load_work_log(snapshot_dir)

        # Capture SOT (read-only)
        sot_content = capture_sot(project_dir)

        # Generate snapshot
        md_content = generate_snapshot_md(
            session_id=session_id,
            trigger="threshold",
            project_dir=project_dir,
            entries=entries,
            work_log=work_log,
            sot_content=sot_content,
        )

        # Atomic write
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(snapshot_dir, f"{timestamp}_threshold.md")
        atomic_write(filepath, md_content)

        # E5: Empty Snapshot Guard — update latest.md with rich content protection
        update_latest_with_guard(snapshot_dir, md_content, entries)

        # Cleanup
        cleanup_snapshots(snapshot_dir)

        # Knowledge Archive: archive + index + cleanup (consolidated)
        archive_and_index_session(
            snapshot_dir, md_content, session_id, "threshold",
            project_dir, entries, transcript_path,
        )

        # C-6: Archive work log (keep last 10 entries) — atomic_write for crash safety
        work_log_path = os.path.join(snapshot_dir, "work_log.jsonl")
        if os.path.exists(work_log_path):
            try:
                with open(work_log_path, "r", encoding="utf-8") as wf:
                    lines = wf.readlines()
                if len(lines) > 10:
                    kept_data = "".join(lines[-10:])
                    atomic_write(work_log_path, kept_data)
            except (OSError, IOError):
                pass

    except Exception:
        pass  # Non-blocking — don't crash on save failure


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Non-blocking: log error but don't crash
        print(f"update_work_log error: {e}", file=sys.stderr)
        sys.exit(0)

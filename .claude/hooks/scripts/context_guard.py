#!/usr/bin/env python3
"""
Context Preservation System — context_guard.py

Unified entry point dispatching Hook events to specialized handlers.
This file is referenced by .claude/settings.json (project hooks).

Dispatch table:
  --mode=stop        → generate_context_summary.py   (Stop hook: incremental snapshot)
  --mode=post-tool   → update_work_log.py            (PostToolUse: work log + threshold)
  --mode=pre-compact → save_context.py --trigger precompact  (PreCompact: full save)
  --mode=restore     → restore_context.py            (SessionStart: RLM pointer restore)

Architecture:
  - Reads stdin JSON once, passes to the target script via subprocess
  - SOT: Read-only (delegates to target scripts which are also read-only)
  - stdout pass-through for restore mode (SessionStart outputs recovery message)
  - exit 0 on any error (never blocks Claude)
"""

import os
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# (script_filename, extra_args)
DISPATCH = {
    "stop":        ("generate_context_summary.py", []),
    "post-tool":   ("update_work_log.py",          []),
    "pre-compact": ("save_context.py",             ["--trigger", "precompact"]),
    "restore":     ("restore_context.py",          []),
}


def main():
    # Parse --mode argument
    mode = None
    argv = sys.argv[1:]
    for i, arg in enumerate(argv):
        if arg.startswith("--mode="):
            mode = arg.split("=", 1)[1]
            break
        elif arg == "--mode" and i + 1 < len(argv):
            mode = argv[i + 1]
            break

    if not mode or mode not in DISPATCH:
        # Unknown mode — exit silently, don't block Claude
        sys.exit(0)

    script_name, extra_args = DISPATCH[mode]
    target = os.path.join(SCRIPT_DIR, script_name)

    if not os.path.isfile(target):
        sys.exit(0)

    # Read stdin once (hook JSON payload from Claude)
    stdin_data = ""
    if not sys.stdin.isatty():
        try:
            stdin_data = sys.stdin.read()
        except Exception:
            pass

    cmd = [sys.executable, target] + extra_args

    try:
        result = subprocess.run(
            cmd,
            input=stdin_data,
            text=True,
            timeout=25,  # Leave buffer within parent hook timeout (30s)
        )
        # B-5: Only propagate exit code 2 (hook blocking signal).
        # All other non-zero codes are treated as non-blocking (exit 0)
        # to maintain hook design principle: hooks should not break the session.
        sys.exit(2 if result.returncode == 2 else 0)
    except subprocess.TimeoutExpired:
        sys.exit(0)
    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()

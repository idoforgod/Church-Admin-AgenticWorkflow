#!/usr/bin/env python3
"""
PostToolUse Hook — YAML Syntax Validator

Validates YAML syntax after every Write to data/*.yaml files.
If the written YAML is malformed, blocks with exit code 2 so Claude
can self-correct before the invalid file persists.

Triggered by: PostToolUse with matcher "Write"
Location: Parent .claude/settings.json (Project)
Path: Direct execution via `if test -f` guard

Exit codes:
  0 — YAML is valid (or file is not a data/*.yaml)
  2 — YAML syntax error — Claude receives stderr with the parse error

Safety-first: Any unexpected error → exit(0) (never block Claude on script failure).

Design notes:
  - Only validates files matching data/*.yaml pattern.
  - Uses PyYAML safe_load for parsing (no arbitrary Python execution).
  - Reports line/column of syntax error for precise Claude self-correction.
"""

import json
import os
import sys

try:
    import yaml
except ImportError:
    # PyYAML not available — can't validate, allow
    sys.exit(0)


def _is_data_yaml(file_path: str) -> bool:
    """Check if the file path targets a data/*.yaml file."""
    if not file_path:
        return False
    parts = file_path.replace("\\", "/").split("/")
    for i, part in enumerate(parts):
        if part == "data" and i + 1 < len(parts) and parts[i + 1].endswith(".yaml"):
            return True
    return False


def main():
    """Read PostToolUse JSON from stdin, validate YAML if applicable."""
    try:
        stdin_data = sys.stdin.read()
        if not stdin_data.strip():
            sys.exit(0)

        payload = json.loads(stdin_data)
        tool_input = payload.get("tool_input", {})

        file_path = tool_input.get("file_path", "")

        if not file_path or not _is_data_yaml(file_path):
            sys.exit(0)

        # Check if the file actually exists on disk
        if not os.path.isfile(file_path):
            # File doesn't exist yet (Write tool may have failed) — allow
            sys.exit(0)

        # Read and parse the file
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            print(
                f"YAML VALIDATION ERROR: {os.path.basename(file_path)} is empty.\n"
                f"Data files must contain valid YAML content.",
                file=sys.stderr,
            )
            sys.exit(2)

        # Attempt to parse YAML
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            error_detail = str(e)
            # Extract line/column info if available
            if hasattr(e, "problem_mark") and e.problem_mark:
                mark = e.problem_mark
                error_detail = (
                    f"Line {mark.line + 1}, Column {mark.column + 1}: "
                    f"{getattr(e, 'problem', 'Unknown error')}"
                )

            print(
                f"YAML SYNTAX ERROR in {os.path.basename(file_path)}:\n"
                f"{error_detail}\n"
                f"Fix the YAML syntax error before proceeding. "
                f"The file must be valid YAML.",
                file=sys.stderr,
            )
            sys.exit(2)

        # Valid YAML — allow
        sys.exit(0)

    except (json.JSONDecodeError, KeyError, TypeError):
        # Malformed hook input — don't block
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        # Safety-first: never block on unexpected errors
        sys.exit(0)

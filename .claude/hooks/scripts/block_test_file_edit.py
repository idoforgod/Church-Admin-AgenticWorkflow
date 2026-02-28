#!/usr/bin/env python3
"""
PreToolUse Hook — TDD Test File Guard

Blocks Edit/Write operations on test files when TDD mode is active.
Forces Claude to fix implementation code instead of modifying tests.

Activation: Create `.tdd-guard` file in the project root.
Deactivation: Remove `.tdd-guard` file.

Triggered by: PreToolUse with matcher "Edit|Write"
Location: .claude/settings.json (Project)
Path: Direct execution (standalone, NOT through context_guard.py)

P1 Hallucination Prevention: Test file detection is deterministic
(regex + string matching). No AI judgment needed.

SOT Compliance: NO ACCESS to SOT (state.yaml).
  Reads only `.tdd-guard` (toggle file) and stdin JSON (hook payload).

Detection tiers:
  Tier 1 — Directory-based: file is under test/, tests/, __tests__/, spec/, specs/
  Tier 2 — Filename-based: common test file naming conventions across languages
           (test_*, *_test.*, *.test.*, *.spec.*, *Test.*, conftest.py, etc.)

Known limitations:
  - CamelCase detection (FooTest.java) uses basename endswith, not regex.
    Acceptable: covers all standard Java/Kotlin/C# conventions.
  - Directories named "test" in non-test contexts (e.g., src/protest/)
    are NOT matched — only exact component matches.

Safety-first: Any unexpected internal error → exit(0) (never block Claude).

ADR-032 in DECISION-LOG.md
"""

import json
import os
import re
import sys
from typing import Optional


# ---------------------------------------------------------------------------
# Test directory patterns — exact match on path components
# ---------------------------------------------------------------------------
TEST_DIR_NAMES = frozenset({
    "test", "tests", "__tests__", "spec", "specs",
})

# ---------------------------------------------------------------------------
# Test filename patterns — regex on filename (case-insensitive)
#
# Each pattern targets a specific language/framework convention.
# Ordered by prevalence (Python/JS first, then Java/Go/Ruby).
# ---------------------------------------------------------------------------
TEST_FILE_PATTERNS = [
    # Python: test_foo.py, conftest.py
    re.compile(r"^test[_.]", re.IGNORECASE),
    # Python/Go/Rust: foo_test.py, foo_test.go
    re.compile(r"_tests?\.", re.IGNORECASE),
    # JS/TS: foo.test.js, foo.test.tsx
    re.compile(r"\.tests?\.", re.IGNORECASE),
    # JS/TS: foo.spec.js, foo.spec.tsx
    re.compile(r"\.specs?\.", re.IGNORECASE),
    # Ruby: foo_spec.rb
    re.compile(r"_spec\.", re.IGNORECASE),
    # Python: conftest.py (pytest fixtures)
    re.compile(r"^conftest\.py$", re.IGNORECASE),
]


def _find_project_dir() -> str:
    """Determine the project root directory.

    Priority: CLAUDE_PROJECT_DIR env var > derive from script path.
    """
    env_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_dir and os.path.isdir(env_dir):
        return env_dir
    # Fallback: script is at .claude/hooks/scripts/ → go up 3 levels
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))


def _is_tdd_mode_active(project_dir: str) -> bool:
    """Check if .tdd-guard file exists in the project root."""
    return os.path.exists(os.path.join(project_dir, ".tdd-guard"))


def is_test_file(file_path: str) -> bool:
    """Determine if a file path refers to a test file.

    Two-tier detection:
      Tier 1: Directory — any path component matches TEST_DIR_NAMES
      Tier 2: Filename — matches common test file naming conventions

    Returns True if the file is a test file, False otherwise.
    """
    normalized = file_path.replace("\\", "/")
    parts = normalized.split("/")

    # Tier 1: Directory-based detection
    # Check all path components EXCEPT the last one (filename)
    for part in parts[:-1]:
        if part.lower() in TEST_DIR_NAMES:
            return True

    # Tier 2: Filename-based detection
    filename = parts[-1] if parts else ""
    if not filename:
        return False

    # Regex patterns for common test file conventions
    for pattern in TEST_FILE_PATTERNS:
        if pattern.search(filename):
            return True

    # CamelCase: FooTest.java, FooTests.java, FooSpec.scala
    basename = filename.rsplit(".", 1)[0] if "." in filename else filename
    if basename.endswith(("Test", "Tests", "Spec", "Specs")):
        return True

    return False


def check_file_path(file_path: str) -> Optional[str]:
    """Check if a file path is a test file that should be blocked.

    Returns block message if blocked, None otherwise.
    """
    if is_test_file(file_path):
        return (
            "Test files are read-only in TDD mode (.tdd-guard active). "
            "Do NOT modify the test. Fix the implementation code to make the test pass."
        )
    return None


def main():
    """Read PreToolUse JSON from stdin, check for test file edits."""
    project_dir = _find_project_dir()

    # Gate: If .tdd-guard doesn't exist, allow everything (fast path)
    if not _is_tdd_mode_active(project_dir):
        sys.exit(0)

    # Read Hook JSON payload from stdin
    # Format: {"tool_name": "Edit|Write", "tool_input": {"file_path": "..."}}
    try:
        stdin_data = sys.stdin.read()
        if not stdin_data.strip():
            sys.exit(0)

        payload = json.loads(stdin_data)
        file_path = payload.get("tool_input", {}).get("file_path", "")

        if not file_path:
            sys.exit(0)
    except (json.JSONDecodeError, KeyError, TypeError):
        # Malformed input — don't block, exit cleanly
        sys.exit(0)

    # Check if file is a test file
    block_message = check_file_path(file_path)

    if block_message:
        # Exit code 2 = Claude Hook blocking signal
        # stderr content is sent to Claude for self-correction
        print(
            f"TEST FILE EDIT BLOCKED: {block_message}\n"
            f"Blocked file: {file_path}",
            file=sys.stderr,
        )
        sys.exit(2)

    # Not a test file — allow operation
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Safety-first: never block Claude on unexpected internal errors
        sys.exit(0)

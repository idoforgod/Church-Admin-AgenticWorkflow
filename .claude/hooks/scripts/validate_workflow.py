#!/usr/bin/env python3
"""
Workflow.md DNA Inheritance P1 Validation — validate_workflow.py

Standalone script called after workflow-generator completes (SKILL.md Step 13).
NOT a Hook — manually invoked during workflow generation.

Usage:
    python3 .claude/hooks/scripts/validate_workflow.py --workflow-path ./workflow.md

Output: JSON to stdout
    {"valid": true, "warnings": [], ...}

Exit codes:
    0 — validation completed (check "valid" field for result)
    1 — argument error or fatal failure

Checks (W1-W8):
    W1: Workflow file exists and is readable
    W2: Minimum file size (≥ 500 bytes)
    W3: Inherited DNA header present
    W4: Inherited Patterns table present (≥ 3 data rows)
    W5: Constitutional Principles section present
    W6: Coding Anchor Points (CAP) reference present
    W7: Cross-step traceability Verification-Validator consistency
    W8: Domain knowledge Verification-Validator consistency

P1 Compliance: All validation is deterministic (delegates to _context_lib).
SOT Compliance: Read-only — no file writes.
"""

import argparse
import json
import os
import sys

# Add script directory to path for shared library import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _context_lib import validate_workflow_md


def main():
    parser = argparse.ArgumentParser(
        description="P1 Validation for generated workflow.md DNA inheritance"
    )
    parser.add_argument(
        "--workflow-path", type=str, required=True,
        help="Path to the generated workflow.md file"
    )
    args = parser.parse_args()

    workflow_path = os.path.abspath(args.workflow_path)
    is_valid, warnings = validate_workflow_md(workflow_path)

    output = {
        "valid": is_valid,
        "workflow_path": workflow_path,
        "warnings": list(warnings),
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_output = {
            "valid": False,
            "error": str(e),
            "warnings": [f"Fatal error: {e}"],
        }
        print(json.dumps(error_output, indent=2, ensure_ascii=False))
        sys.exit(1)

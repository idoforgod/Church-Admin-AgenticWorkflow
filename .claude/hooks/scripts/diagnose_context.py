#!/usr/bin/env python3
"""
Abductive Diagnosis Pre-Analysis — diagnose_context.py

Standalone script called by Orchestrator AFTER a quality gate FAIL
and BEFORE retry. Gathers deterministic evidence for LLM-based diagnosis.
NOT a Hook — manually invoked during workflow execution.

Usage:
    python3 .claude/hooks/scripts/diagnose_context.py --step 3 --gate verification --project-dir .
    python3 .claude/hooks/scripts/diagnose_context.py --step 3 --gate pacs --project-dir .
    python3 .claude/hooks/scripts/diagnose_context.py --step 3 --gate review --project-dir .

Output: JSON to stdout
    {
        "step": 3,
        "gate": "verification",
        "retry_history": {...},
        "upstream_evidence": {...},
        "hypothesis_priority": [...],
        "fast_path": {...},
        "raw_evidence": {...}
    }

Exit codes:
    0 — analysis completed successfully
    1 — argument error or fatal failure

P1 Compliance: All evidence gathering is deterministic (delegates to _context_lib).
SOT Compliance: Read-only — no file writes.
"""

import argparse
import json
import os
import sys

# Add script directory to path for shared library import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _context_lib import diagnose_failure_context


def main():
    parser = argparse.ArgumentParser(
        description="Abductive Diagnosis Pre-Analysis for quality gate failures"
    )
    parser.add_argument(
        "--step", type=int, required=True,
        help="Step number that failed the quality gate"
    )
    parser.add_argument(
        "--gate", type=str, required=True,
        choices=["verification", "pacs", "review"],
        help="Which quality gate failed"
    )
    parser.add_argument(
        "--project-dir", type=str, default=".",
        help="Project root directory (default: current directory)"
    )
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    step = args.step
    gate = args.gate

    # Gather evidence bundle
    context = diagnose_failure_context(project_dir, step, gate)

    print(json.dumps(context, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({
            "error": str(e),
            "valid": False,
        }), file=sys.stdout)
        sys.exit(1)

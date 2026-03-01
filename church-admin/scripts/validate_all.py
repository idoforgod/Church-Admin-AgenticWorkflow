#!/usr/bin/env python3
"""
Aggregated Validator — Run all 5 P1 validation scripts and report combined results.

Usage:
    python3 scripts/validate_all.py [--data-dir DATA_DIR]

Outputs:
    Combined JSON report to stdout with per-validator results and grand totals.
    Exit code 0 if all pass, 1 if any fail.

This script is the single entry point for running all church-admin data validators.
Referenced by: /validate-all slash command, setup_church_admin.py, CLAUDE.md
"""

import json
import os
import subprocess
import sys

# Validators relative to church-admin root
VALIDATORS = [
    {
        "name": "Members",
        "script": ".claude/hooks/scripts/validate_members.py",
        "rules": "M1-M7",
    },
    {
        "name": "Finance",
        "script": ".claude/hooks/scripts/validate_finance.py",
        "rules": "F1-F7",
    },
    {
        "name": "Schedule",
        "script": ".claude/hooks/scripts/validate_schedule.py",
        "rules": "S1-S6",
    },
    {
        "name": "Newcomers",
        "script": ".claude/hooks/scripts/validate_newcomers.py",
        "rules": "N1-N6",
    },
    {
        "name": "Bulletin",
        "script": ".claude/hooks/scripts/validate_bulletin.py",
        "rules": "B1-B3",
    },
]


def _find_church_admin_root() -> str:
    """Find church-admin root directory."""
    # If we're in church-admin/scripts/, go up one
    cwd = os.getcwd()
    if os.path.basename(cwd) == "scripts":
        cwd = os.path.dirname(cwd)
    # Check if data/ exists here
    if os.path.isdir(os.path.join(cwd, "data")):
        return cwd
    # Try parent
    parent = os.path.dirname(cwd)
    if os.path.isdir(os.path.join(parent, "church-admin", "data")):
        return os.path.join(parent, "church-admin")
    return cwd


def main():
    data_dir = None
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--data-dir" and i < len(sys.argv) - 1:
            data_dir = sys.argv[i + 1]

    root = _find_church_admin_root()

    if not data_dir:
        data_dir = os.path.join(root, "data")

    total_passed = 0
    total_failed = 0
    total_checks = 0
    results = []
    all_pass = True

    for v in VALIDATORS:
        script_path = os.path.join(root, v["script"])
        if not os.path.isfile(script_path):
            results.append({
                "name": v["name"],
                "rules": v["rules"],
                "status": "SKIP",
                "reason": f"Script not found: {v['script']}",
            })
            continue

        try:
            proc = subprocess.run(
                [sys.executable, script_path, "--data-dir", data_dir],
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = proc.stdout.strip()
            if output:
                data = json.loads(output)
                summary = data.get("summary", "")
                checks = data.get("checks", [])
                passed = sum(1 for c in checks if c.get("status") == "PASS")
                failed = sum(1 for c in checks if c.get("status") == "FAIL")
                total_passed += passed
                total_failed += failed
                total_checks += passed + failed

                failed_checks = [
                    {"rule": c.get("rule", "?"), "errors": c.get("errors", [])}
                    for c in checks
                    if c.get("status") == "FAIL"
                ]

                result = {
                    "name": v["name"],
                    "rules": v["rules"],
                    "summary": summary,
                    "passed": passed,
                    "failed": failed,
                }
                if failed_checks:
                    result["failed_checks"] = failed_checks
                    all_pass = False
                results.append(result)
            else:
                results.append({
                    "name": v["name"],
                    "rules": v["rules"],
                    "status": "ERROR",
                    "reason": f"No output. stderr: {proc.stderr[:200]}",
                })
                all_pass = False
        except subprocess.TimeoutExpired:
            results.append({
                "name": v["name"],
                "rules": v["rules"],
                "status": "TIMEOUT",
            })
            all_pass = False
        except (json.JSONDecodeError, Exception) as e:
            results.append({
                "name": v["name"],
                "rules": v["rules"],
                "status": "ERROR",
                "reason": str(e)[:200],
            })
            all_pass = False

    report = {
        "total_passed": total_passed,
        "total_failed": total_failed,
        "total_checks": total_checks,
        "all_pass": all_pass,
        "summary": f"{total_passed}/{total_checks} checks passed",
        "validators": results,
    }

    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()

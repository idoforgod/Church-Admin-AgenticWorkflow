#!/usr/bin/env python3
"""
Setup Hook — Church Admin Infrastructure Health Check

Verifies the church-admin system's infrastructure integrity on `claude --init`.
Runs alongside the parent setup_init.py (which checks AgenticWorkflow-level health).

Triggered by: Setup with matcher "init"
Location: Parent .claude/settings.json (Project)
Path: Direct execution via `if test -f` guard

Exit codes:
  0 — All checks passed (stdout: health report)
  1 — Some checks failed (stdout: report with failures marked)

Design notes:
  - This script runs from the parent project root. It resolves church-admin/ relative
    to CLAUDE_PROJECT_DIR or by looking for church-admin/ in the current directory tree.
  - Checks are deterministic — no AI judgment needed.
  - Does NOT modify any files — read-only verification.
"""

import os
import sys

try:
    import yaml
except ImportError:
    print("Church Admin Setup — SKIP: PyYAML not available")
    sys.exit(0)

# ---------------------------------------------------------------------------
# Expected infrastructure
# ---------------------------------------------------------------------------
EXPECTED_DATA_FILES = [
    "members.yaml",
    "finance.yaml",
    "schedule.yaml",
    "newcomers.yaml",
    "bulletin-data.yaml",
    "church-glossary.yaml",
]

EXPECTED_AGENTS = [
    "bulletin-generator.md",
    "data-ingestor.md",
    "document-generator.md",
    "finance-recorder.md",
    "member-manager.md",
    "newcomer-tracker.md",
    "schedule-manager.md",
    "template-scanner.md",
]

EXPECTED_VALIDATORS = [
    "validate_members.py",
    "validate_finance.py",
    "validate_schedule.py",
    "validate_newcomers.py",
    "validate_bulletin.py",
]

EXPECTED_INBOX_DIRS = [
    "documents",
    "errors",
    "images",
    "processed",
    "staging",
    "templates",
]

EXPECTED_SCRIPTS = [
    "inbox_parser.py",
    "tier_a_parser.py",
    "tier_b_parser.py",
    "tier_c_parser.py",
    "template_engine.py",
    "template_scanner.py",
    "hitl_confirmation.py",
    "daily-backup.sh",
]


def _find_church_admin_dir() -> str:
    """Resolve church-admin/ directory path."""
    # Try CLAUDE_PROJECT_DIR first
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir:
        candidate = os.path.join(project_dir, "church-admin")
        if os.path.isdir(candidate):
            return candidate

    # Try current directory
    cwd = os.getcwd()
    if os.path.basename(cwd) == "church-admin":
        return cwd
    candidate = os.path.join(cwd, "church-admin")
    if os.path.isdir(candidate):
        return candidate

    return ""


def _check_files(base_dir: str, subdir: str, expected: list, label: str) -> tuple:
    """Check that expected files exist in base_dir/subdir."""
    target = os.path.join(base_dir, subdir) if subdir else base_dir
    found = []
    missing = []
    for f in expected:
        path = os.path.join(target, f)
        if os.path.exists(path):
            found.append(f)
        else:
            missing.append(f)
    return found, missing


def _check_yaml_parseable(base_dir: str) -> list:
    """Try to parse all data/*.yaml files. Return list of unparseable files."""
    data_dir = os.path.join(base_dir, "data")
    errors = []
    for fname in EXPECTED_DATA_FILES:
        fpath = os.path.join(data_dir, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                yaml.safe_load(f.read())
        except yaml.YAMLError as e:
            errors.append(f"{fname}: {e}")
    return errors


def _check_state_yaml(base_dir: str) -> list:
    """Validate state.yaml basic structure."""
    state_path = os.path.join(base_dir, "state.yaml")
    errors = []
    if not os.path.isfile(state_path):
        errors.append("state.yaml not found")
        return errors
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f.read())
        if not isinstance(data, dict):
            errors.append("state.yaml is not a YAML mapping")
            return errors
        if "church" not in data:
            errors.append("state.yaml missing 'church' top-level key")
        else:
            church = data["church"]
            if "data_paths" not in church:
                errors.append("state.yaml missing 'church.data_paths'")
            if "features" not in church:
                errors.append("state.yaml missing 'church.features'")
    except yaml.YAMLError as e:
        errors.append(f"state.yaml parse error: {e}")
    return errors


def main():
    church_dir = _find_church_admin_dir()
    if not church_dir:
        print("Church Admin Setup — SKIP: church-admin/ directory not found")
        sys.exit(0)

    print("Church Admin Setup — Infrastructure Health Check")
    print(f"  Directory: {church_dir}")
    print()

    total_checks = 0
    total_passed = 0
    total_failed = 0

    # 1. Data files
    found, missing = _check_files(church_dir, "data", EXPECTED_DATA_FILES, "Data files")
    total_checks += 1
    if not missing:
        print(f"  \u2713 Data files: {len(found)}/{len(EXPECTED_DATA_FILES)} present")
        total_passed += 1
    else:
        print(f"  \u2717 Data files: {len(found)}/{len(EXPECTED_DATA_FILES)} — MISSING: {', '.join(missing)}")
        total_failed += 1

    # 2. YAML parseable
    yaml_errors = _check_yaml_parseable(church_dir)
    total_checks += 1
    if not yaml_errors:
        print(f"  \u2713 YAML syntax: All data files parse correctly")
        total_passed += 1
    else:
        print(f"  \u2717 YAML syntax errors:")
        for e in yaml_errors:
            print(f"      {e}")
        total_failed += 1

    # 3. Agent files
    found, missing = _check_files(church_dir, ".claude/agents", EXPECTED_AGENTS, "Agents")
    total_checks += 1
    if not missing:
        print(f"  \u2713 Agents: {len(found)}/{len(EXPECTED_AGENTS)} present")
        total_passed += 1
    else:
        print(f"  \u2717 Agents: {len(found)}/{len(EXPECTED_AGENTS)} — MISSING: {', '.join(missing)}")
        total_failed += 1

    # 4. Validation scripts
    found, missing = _check_files(
        church_dir, ".claude/hooks/scripts", EXPECTED_VALIDATORS, "Validators"
    )
    total_checks += 1
    if not missing:
        print(f"  \u2713 Validators: {len(found)}/{len(EXPECTED_VALIDATORS)} present")
        total_passed += 1
    else:
        print(f"  \u2717 Validators: {len(found)}/{len(EXPECTED_VALIDATORS)} — MISSING: {', '.join(missing)}")
        total_failed += 1

    # 5. Inbox directories
    found, missing = _check_files(church_dir, "inbox", EXPECTED_INBOX_DIRS, "Inbox dirs")
    total_checks += 1
    if not missing:
        print(f"  \u2713 Inbox dirs: {len(found)}/{len(EXPECTED_INBOX_DIRS)} present")
        total_passed += 1
    else:
        print(f"  \u2717 Inbox dirs: {len(found)}/{len(EXPECTED_INBOX_DIRS)} — MISSING: {', '.join(missing)}")
        total_failed += 1

    # 6. Scripts
    found, missing = _check_files(church_dir, "scripts", EXPECTED_SCRIPTS, "Scripts")
    total_checks += 1
    if not missing:
        print(f"  \u2713 Scripts: {len(found)}/{len(EXPECTED_SCRIPTS)} present")
        total_passed += 1
    else:
        print(f"  \u2717 Scripts: {len(found)}/{len(EXPECTED_SCRIPTS)} — MISSING: {', '.join(missing)}")
        total_failed += 1

    # 7. state.yaml
    state_errors = _check_state_yaml(church_dir)
    total_checks += 1
    if not state_errors:
        print(f"  \u2713 state.yaml: Valid structure")
        total_passed += 1
    else:
        print(f"  \u2717 state.yaml issues:")
        for e in state_errors:
            print(f"      {e}")
        total_failed += 1

    # 8. CLAUDE.md exists
    claude_md = os.path.join(church_dir, "CLAUDE.md")
    total_checks += 1
    if os.path.isfile(claude_md):
        print(f"  \u2713 CLAUDE.md: Present")
        total_passed += 1
    else:
        print(f"  \u2717 CLAUDE.md: NOT FOUND — agents lack domain-specific instructions")
        total_failed += 1

    # Summary
    print()
    print(f"  Result: {total_passed}/{total_checks} checks passed")

    if total_failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"Church Admin Setup — ERROR: {e}", file=sys.stderr)
        sys.exit(0)

#!/usr/bin/env python3
"""
P1 Deterministic Validation — finance.yaml (F1-F7)

Rules:
  F1: ID uniqueness and format (OFF-YYYY-NNN, EXP-YYYY-NNN)
  F2: Amount positivity (all amounts > 0, void excluded)
  F3: Offering sum consistency (total == sum(items[].amount))
  F4: Budget arithmetic (total_budget == sum(categories))
  F5: Monthly summary accuracy (income/expense/balance match records)
  F6: Pledged annual member_id cross-reference (must exist in members.yaml)
  F7: Offering type enum validation

Exit codes: 0 = completed (check 'valid' field), 1 = fatal error.
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from church_data_utils import (
    OFFERING_ID_RE,
    EXPENSE_ID_RE,
    MEMBER_ID_RE,
    OFFERING_TYPE_ENUM,
    load_yaml,
    load_member_ids,
    atomic_write_yaml,
    make_check_result,
    build_output,
    print_and_exit,
    fatal_error,
)

SCRIPT_NAME = "validate_finance.py"
DATA_FILE = "data/finance.yaml"


# ---------------------------------------------------------------------------
# Check Functions
# ---------------------------------------------------------------------------
def check_f1(data):
    """F1: All offering/expense IDs unique and match format."""
    errors = []

    # Offering IDs
    off_ids = []
    for o in data.get("offerings", []):
        oid = o.get("id")
        if oid is None or not OFFERING_ID_RE.match(str(oid)):
            errors.append(f"F1: Invalid offering ID format: {oid!r} (expected OFF-YYYY-NNN+)")
        off_ids.append(oid)

    seen = set()
    for oid in off_ids:
        if oid is not None and oid in seen:
            errors.append(f"F1: Duplicate offering ID: {oid}")
        if oid is not None:
            seen.add(oid)

    # Expense IDs
    exp_ids = []
    for e in data.get("expenses", []):
        eid = e.get("id")
        if eid is None or not EXPENSE_ID_RE.match(str(eid)):
            errors.append(f"F1: Invalid expense ID format: {eid!r} (expected EXP-YYYY-NNN+)")
        exp_ids.append(eid)

    seen = set()
    for eid in exp_ids:
        if eid is not None and eid in seen:
            errors.append(f"F1: Duplicate expense ID: {eid}")
        if eid is not None:
            seen.add(eid)

    return make_check_result(
        "F1", "ID Uniqueness and Format", errors,
        f"All {len(off_ids)} offering + {len(exp_ids)} expense IDs valid and unique",
    )


def check_f2(data):
    """F2: All amount fields are positive integers."""
    errors = []

    for o in data.get("offerings", []):
        oid = o.get("id", "UNKNOWN")
        if o.get("void", False):
            continue  # Skip voided records
        for i, item in enumerate(o.get("items", [])):
            amt = item.get("amount")
            if not isinstance(amt, int) or amt <= 0:
                errors.append(
                    f"F2: Offering {oid} item[{i}] amount {amt!r} is not a positive integer"
                )
        total = o.get("total")
        if not isinstance(total, int) or total <= 0:
            errors.append(f"F2: Offering {oid} total {total!r} is not a positive integer")

    for e in data.get("expenses", []):
        eid = e.get("id", "UNKNOWN")
        if e.get("void", False):
            continue  # Skip voided records
        amt = e.get("amount")
        if not isinstance(amt, int) or amt <= 0:
            errors.append(f"F2: Expense {eid} amount {amt!r} is not a positive integer")

    return make_check_result(
        "F2", "Amount Positivity", errors,
        "All amounts are positive integers",
    )


def check_f3(data):
    """F3: offerings[].total == sum(items[].amount) for non-void records."""
    errors = []
    for o in data.get("offerings", []):
        oid = o.get("id", "UNKNOWN")
        if o.get("void", False):
            continue
        items_sum = sum(item.get("amount", 0) for item in o.get("items", []))
        declared_total = o.get("total", 0)
        if items_sum != declared_total:
            errors.append(
                f"F3: Offering {oid} arithmetic mismatch: "
                f"sum(items)={items_sum} != total={declared_total}"
            )

    return make_check_result(
        "F3", "Offering Sum Consistency", errors,
        "All offering sums consistent",
    )


def check_f4(data):
    """F4: budget.total_budget == sum(budget.categories.values())."""
    errors = []
    budget = data.get("budget", {})
    if not isinstance(budget, dict):
        errors.append("F4: budget is not a dict")
        return make_check_result("F4", "Budget Arithmetic", errors)

    categories = budget.get("categories", {})
    declared_total = budget.get("total_budget", 0)

    if not isinstance(categories, dict):
        errors.append("F4: budget.categories is not a dict")
        return make_check_result("F4", "Budget Arithmetic", errors)

    # Verify all category values are positive integers
    for cat_name, cat_val in categories.items():
        if not isinstance(cat_val, int) or cat_val <= 0:
            errors.append(
                f"F4: Budget category '{cat_name}' has non-positive or non-integer value: {cat_val!r}"
            )

    computed_sum = sum(v for v in categories.values() if isinstance(v, int))
    if computed_sum != declared_total:
        errors.append(
            f"F4: Budget arithmetic mismatch: "
            f"sum(categories)={computed_sum} != total_budget={declared_total}"
        )

    return make_check_result(
        "F4", "Budget Arithmetic", errors,
        f"Budget sums to {computed_sum}, matches declared {declared_total}",
    )


def check_f5(data):
    """F5: monthly_summary totals match non-void records for that month."""
    errors = []
    monthly = data.get("monthly_summary", {})
    if not monthly:
        return make_check_result(
            "F5", "Monthly Summary Accuracy", errors,
            "No monthly summary to validate",
        )

    # Compute actual monthly totals from non-void records
    actual_income = defaultdict(int)
    actual_expense = defaultdict(int)

    for o in data.get("offerings", []):
        if o.get("void", False):
            continue
        month_key = str(o.get("date", ""))[:7]  # "2026-01" from "2026-01-05"
        actual_income[month_key] += o.get("total", 0)

    for e in data.get("expenses", []):
        if e.get("void", False):
            continue
        month_key = str(e.get("date", ""))[:7]
        actual_expense[month_key] += e.get("amount", 0)

    for month_key, summary in monthly.items():
        declared_income = summary.get("total_income", 0)
        declared_expense = summary.get("total_expense", 0)
        declared_balance = summary.get("balance", 0)

        if actual_income.get(month_key, 0) != declared_income:
            errors.append(
                f"F5: Month {month_key} income mismatch: "
                f"actual={actual_income.get(month_key, 0)} != declared={declared_income}"
            )
        if actual_expense.get(month_key, 0) != declared_expense:
            errors.append(
                f"F5: Month {month_key} expense mismatch: "
                f"actual={actual_expense.get(month_key, 0)} != declared={declared_expense}"
            )
        if declared_income - declared_expense != declared_balance:
            errors.append(
                f"F5: Month {month_key} balance mismatch: "
                f"{declared_income} - {declared_expense} = {declared_income - declared_expense} "
                f"!= declared balance {declared_balance}"
            )

    return make_check_result(
        "F5", "Monthly Summary Accuracy", errors,
        f"All {len(monthly)} monthly summaries consistent",
    )


def check_f6(data, member_ids):
    """F6: pledged_annual[].member_id format + cross-reference to members.yaml."""
    errors = []
    warnings = []

    pledges = data.get("pledged_annual", [])
    if not isinstance(pledges, list):
        pledges = []

    if not member_ids:
        warnings.append(
            "F6: members.yaml not available — cross-reference checks skipped, format-only validation"
        )

    for p in pledges:
        mid = p.get("member_id")
        if mid is None:
            errors.append("F6: pledged_annual entry missing member_id")
            continue
        if not MEMBER_ID_RE.match(str(mid)):
            errors.append(
                f"F6: pledged_annual member_id '{mid}' has invalid format (expected M followed by 3+ digits)"
            )
        elif member_ids and mid not in member_ids:
            errors.append(
                f"F6: pledged_annual member_id '{mid}' not found in members.yaml"
            )

    result = make_check_result(
        "F6", "Pledged Annual Member Reference", errors,
        f"All {len(pledges)} pledge member references valid",
    )
    if warnings:
        result["warnings"] = warnings
    return result


def check_f7(data):
    """F7: offerings[].type must be a recognized offering type enum."""
    errors = []
    for o in data.get("offerings", []):
        oid = o.get("id", "UNKNOWN")
        otype = o.get("type")
        if otype is not None and otype not in OFFERING_TYPE_ENUM:
            errors.append(
                f"F7: Offering {oid} type '{otype}' not in {sorted(OFFERING_TYPE_ENUM)}"
            )

    return make_check_result(
        "F7", "Offering Type Enum", errors,
        "All offering types valid",
    )


# ---------------------------------------------------------------------------
# --fix mode for monthly summary
# ---------------------------------------------------------------------------
def fix_monthly_summary(data, data_path):
    """Recompute monthly_summary from non-void records and write."""
    actual_income = defaultdict(int)
    actual_expense = defaultdict(int)

    for o in data.get("offerings", []):
        if o.get("void", False):
            continue
        month_key = str(o.get("date", ""))[:7]
        actual_income[month_key] += o.get("total", 0)

    for e in data.get("expenses", []):
        if e.get("void", False):
            continue
        month_key = str(e.get("date", ""))[:7]
        actual_expense[month_key] += e.get("amount", 0)

    all_months = sorted(set(list(actual_income.keys()) + list(actual_expense.keys())))
    new_summary = {}
    for mk in all_months:
        inc = actual_income.get(mk, 0)
        exp = actual_expense.get(mk, 0)
        new_summary[mk] = {
            "total_income": inc,
            "total_expense": exp,
            "balance": inc - exp,
            "computed_at": date.today().isoformat(),
        }

    data["monthly_summary"] = new_summary
    atomic_write_yaml(data_path, data)
    return new_summary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="P1 Validation for finance.yaml")
    parser.add_argument("--data-dir", type=str, required=True, help="Path to data/ directory")
    parser.add_argument("--members-file", type=str, default=None,
                        help="Override path to members.yaml for cross-reference checks")
    parser.add_argument("--fix", action="store_true", help="Auto-fix computed fields (monthly_summary)")
    args = parser.parse_args()

    finance_path = os.path.join(args.data_dir, "finance.yaml")
    try:
        data = load_yaml(finance_path)
    except (FileNotFoundError, Exception) as e:
        fatal_error(SCRIPT_NAME, str(e))

    if args.fix:
        fix_monthly_summary(data, finance_path)
        # Reload after fix
        data = load_yaml(finance_path)

    # Load member IDs for cross-reference checks (F6)
    member_ids, _ = load_member_ids(args.data_dir, args.members_file)

    all_warnings = []

    f6_result = check_f6(data, member_ids)
    if "warnings" in f6_result:
        all_warnings.extend(f6_result.pop("warnings"))

    checks = [
        check_f1(data),
        check_f2(data),
        check_f3(data),
        check_f4(data),
        check_f5(data),
        f6_result,
        check_f7(data),
    ]

    output = build_output(SCRIPT_NAME, DATA_FILE, checks, warnings=all_warnings)
    print_and_exit(output)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        fatal_error(SCRIPT_NAME, str(e))

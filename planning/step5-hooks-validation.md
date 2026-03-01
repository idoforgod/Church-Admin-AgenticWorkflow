# Step 5 — Hook Configuration & P1 Validation Script Specifications

**Version**: 1.0
**Generated**: 2026-02-28
**Source**: Step 4 Data Architecture Spec + Parent AgenticWorkflow Hook Patterns
**Agent**: `@church-hook-designer`
**Purpose**: Complete P1 validation script interfaces, hook configurations, slash command specifications, and shared utilities for the Church Administration AI Agentic Workflow Automation System

---

## Table of Contents

1. [Part A: P1 Validation Script Interface Specifications](#part-a-p1-validation-script-interface-specifications)
2. [Part B: Hook Configuration Design](#part-b-hook-configuration-design)
3. [Part C: Slash Command Specifications](#part-c-slash-command-specifications)
4. [Part D: Shared Utilities](#part-d-shared-utilities)
5. [Verification Report](#verification-report)

---

## Part A: P1 Validation Script Interface Specifications

[trace:step-4:validation-rules]

All 4 P1 validation scripts share a common interface pattern inherited from the parent AgenticWorkflow codebase (reference: `validate_pacs.py`). Every check is deterministic — regex match, arithmetic comparison, set membership, or referential integrity test. No AI judgment is involved.

### Common Interface Contract

**CLI Interface Pattern** (all 4 scripts):

```
python3 church-admin/.claude/hooks/scripts/validate_<domain>.py \
  --data-dir ./church-admin/data/ \
  [--members-file <path>]       # override default members.yaml path (for cross-ref scripts)
  [--fix]                       # auto-fix mode: correct computed fields (_stats), report fixes
```

**JSON Output Schema** (all 4 scripts):

```json
{
  "valid": true,
  "script": "validate_members.py",
  "data_file": "data/members.yaml",
  "checks": [
    {
      "rule": "M1",
      "name": "ID Uniqueness and Format",
      "status": "PASS",
      "detail": "All 251 member IDs unique and match M\\d{3,} format"
    },
    {
      "rule": "M2",
      "name": "Required Fields Non-Empty",
      "status": "FAIL",
      "detail": "2 errors found",
      "errors": [
        "M2: Member M045 has empty or missing 'name'",
        "M2: Member M102 has empty or missing 'status'"
      ]
    }
  ],
  "errors": ["M2: Member M045 has empty or missing 'name'", "..."],
  "warnings": [],
  "summary": "5/6 checks passed, 1 failed (M2)"
}
```

**Exit Codes**:

| Code | Meaning | When |
|------|---------|------|
| 0 | Validation completed | Always — check `valid` field for result |
| 1 | Fatal error | Argument error, file not found, YAML parse failure |

Note: Exit code 2 is NOT used by validation scripts. Exit code 2 is reserved for PreToolUse hooks that block tool calls. Validation scripts always exit 0 and report results via JSON `valid` field.

**Error Handling Pattern** (all scripts):

```python
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_output = {
            "valid": False,
            "script": SCRIPT_NAME,
            "error": str(e),
            "checks": [],
            "errors": [f"Fatal error: {e}"],
            "warnings": [],
            "summary": f"Fatal error: {e}",
        }
        print(json.dumps(error_output, indent=2, ensure_ascii=False))
        sys.exit(1)
```

---

### A1. validate_members.py (M1-M6)

[trace:step-4:schema-specs]

**Target File**: `data/members.yaml`
**Rule Count**: 6 checks (M1-M6)
**Cross-References**: None (members.yaml is the root reference file — other validators reference it)

#### CLI

```
python3 church-admin/.claude/hooks/scripts/validate_members.py --data-dir ./church-admin/data/
python3 church-admin/.claude/hooks/scripts/validate_members.py --data-dir ./church-admin/data/ --fix
```

#### Check-by-Check Detail

**M1 — ID Uniqueness and Format**

- **Condition**: Every `members[].id` matches regex `^M\d{3,}$` AND all IDs are unique within the file.
- **Failure Mode**: Invalid format (e.g., `"member-1"`, `"M01"` with < 3 digits) or duplicate IDs.
- **Implementation**:

```python
import re

_MEMBER_ID_RE = re.compile(r'^M\d{3,}$')

def check_m1(members: list[dict]) -> dict:
    """M1: All member IDs unique and match M\\d{3,} format."""
    errors = []
    ids = []

    for m in members:
        mid = m.get("id")
        if mid is None or not _MEMBER_ID_RE.match(str(mid)):
            errors.append(f"M1: Invalid member ID format: {mid!r} (expected M followed by 3+ digits)")
        ids.append(mid)

    # Uniqueness check
    seen = set()
    for mid in ids:
        if mid in seen:
            errors.append(f"M1: Duplicate member ID: {mid}")
        if mid is not None:
            seen.add(mid)

    return {
        "rule": "M1",
        "name": "ID Uniqueness and Format",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All {len(ids)} member IDs valid and unique" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

**M2 — Required Fields Non-Empty**

- **Condition**: For every member record, `name` is a non-empty string AND `status` is a non-empty string.
- **Failure Mode**: `null`, empty string `""`, whitespace-only, or missing key.
- **Implementation**:

```python
def check_m2(members: list[dict]) -> dict:
    """M2: name and status fields non-empty for every record."""
    errors = []
    for m in members:
        mid = m.get("id", "UNKNOWN")
        if not m.get("name") or not isinstance(m.get("name"), str) or not m["name"].strip():
            errors.append(f"M2: Member {mid} has empty or missing 'name'")
        if not m.get("status") or not isinstance(m.get("status"), str) or not m["status"].strip():
            errors.append(f"M2: Member {mid} has empty or missing 'status'")

    return {
        "rule": "M2",
        "name": "Required Fields Non-Empty",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All members have non-empty name and status" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

**M3 — Phone Format Validation**

- **Condition**: When `members[].contact.phone` is not `null`, it must match regex `^010-\d{4}-\d{4}$` (Korean mobile format).
- **Failure Mode**: Non-null phone that fails regex (e.g., `"010-123-4567"`, `"02-1234-5678"`, `"01012345678"`).
- **`null` handling**: `null` is valid — phone is optional.
- **Implementation**:

```python
_PHONE_RE = re.compile(r'^010-\d{4}-\d{4}$')

def check_m3(members: list[dict]) -> dict:
    """M3: phone matches 010-NNNN-NNNN Korean mobile format when present."""
    errors = []
    for m in members:
        mid = m.get("id", "UNKNOWN")
        phone = m.get("contact", {}).get("phone")
        if phone is not None and not _PHONE_RE.match(str(phone)):
            errors.append(
                f"M3: Member {mid} phone '{phone}' does not match "
                f"format 010-NNNN-NNNN"
            )

    return {
        "rule": "M3",
        "name": "Phone Format Validation",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All phone numbers valid" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

**M4 — Status Enum Validation**

- **Condition**: `members[].status` is one of `{"active", "inactive", "transferred", "deceased"}`.
- **Failure Mode**: Value outside the enum set.
- **Implementation**:

```python
_MEMBER_STATUS_ENUM = {"active", "inactive", "transferred", "deceased"}

def check_m4(members: list[dict]) -> dict:
    """M4: status in {active, inactive, transferred, deceased}."""
    errors = []
    for m in members:
        mid = m.get("id", "UNKNOWN")
        status = m.get("status")
        if status not in _MEMBER_STATUS_ENUM:
            errors.append(
                f"M4: Member {mid} has invalid status '{status}'. "
                f"Allowed: {sorted(_MEMBER_STATUS_ENUM)}"
            )

    return {
        "rule": "M4",
        "name": "Status Enum Validation",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All member statuses valid" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

**M5 — Family ID Reference Integrity**

- **Condition**: When `members[].family.family_id` is not `null`, it matches regex `^F\d{3,}$` AND the family group has >= 2 members sharing that ID.
- **Failure Mode**: Invalid format OR a family_id referenced by only 1 member (orphan family).
- **Implementation**:

```python
_FAMILY_ID_RE = re.compile(r'^F\d{3,}$')

def check_m5(members: list[dict]) -> dict:
    """M5: family_id references valid family group with >= 2 members."""
    errors = []
    family_groups: dict[str, list[str]] = {}

    for m in members:
        mid = m.get("id", "UNKNOWN")
        fid = m.get("family", {}).get("family_id")
        if fid is None:
            continue
        if not _FAMILY_ID_RE.match(str(fid)):
            errors.append(f"M5: Member {mid} has invalid family_id format: '{fid}'")
            continue
        family_groups.setdefault(fid, []).append(mid)

    for fid, member_ids in family_groups.items():
        if len(member_ids) < 2:
            errors.append(
                f"M5: Family {fid} has only {len(member_ids)} member(s): "
                f"{member_ids}. Family groups require >= 2 members."
            )

    return {
        "rule": "M5",
        "name": "Family ID Reference Integrity",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All family groups valid (>= 2 members each)" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

**M6 — Date Field Validity**

- **Condition**: All date fields (`birth_date`, `church.registration_date`, `church.baptism_date`, `history[].date`) match YYYY-MM-DD format AND parse to valid calendar dates. `birth_date` must be in the past (< today).
- **Failure Mode**: Invalid format (e.g., `"2026-13-01"`, `"not-a-date"`), non-existent dates (e.g., `"2026-02-30"`), future birth_date.
- **`null` handling**: `null` values are valid for optional fields (`baptism_date`). Required fields (`birth_date`, `registration_date`) still get checked.
- **Implementation**:

```python
from datetime import date, datetime

_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

def _parse_date(s: str) -> date | None:
    """Parse YYYY-MM-DD string to date. Returns None on any failure."""
    if not isinstance(s, str) or not _DATE_RE.match(s):
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None

def check_m6(members: list[dict]) -> dict:
    """M6: All date fields valid YYYY-MM-DD; birth_date must be in the past."""
    errors = []
    today = date.today()

    for m in members:
        mid = m.get("id", "UNKNOWN")

        # birth_date (top-level, required)
        bd = m.get("birth_date")
        if bd is not None:
            parsed = _parse_date(bd)
            if parsed is None:
                errors.append(f"M6: Member {mid} birth_date '{bd}' is not valid YYYY-MM-DD")
            elif parsed >= today:
                errors.append(f"M6: Member {mid} birth_date '{bd}' is not in the past")

        # church.registration_date (required)
        rd = m.get("church", {}).get("registration_date")
        if rd is not None:
            if _parse_date(rd) is None:
                errors.append(f"M6: Member {mid} registration_date '{rd}' is not valid YYYY-MM-DD")

        # church.baptism_date (nullable)
        bpd = m.get("church", {}).get("baptism_date")
        if bpd is not None:
            if _parse_date(bpd) is None:
                errors.append(f"M6: Member {mid} baptism_date '{bpd}' is not valid YYYY-MM-DD")

        # history[].date
        for i, h in enumerate(m.get("history", [])):
            hd = h.get("date")
            if hd is not None and _parse_date(hd) is None:
                errors.append(f"M6: Member {mid} history[{i}].date '{hd}' is not valid YYYY-MM-DD")

    return {
        "rule": "M6",
        "name": "Date Field Validity",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All date fields valid" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

#### Main Function Structure

```python
def main():
    parser = argparse.ArgumentParser(description="P1 Validation for members.yaml")
    parser.add_argument("--data-dir", type=str, required=True, help="Path to data/ directory")
    parser.add_argument("--fix", action="store_true", help="Auto-fix computed fields (_stats)")
    args = parser.parse_args()

    members_path = os.path.join(args.data_dir, "members.yaml")
    data = load_yaml_safe(members_path)  # shared utility — see Part D

    members = data.get("members", [])
    stats = data.get("_stats", {})

    checks = [
        check_m1(members),
        check_m2(members),
        check_m3(members),
        check_m4(members),
        check_m5(members),
        check_m6(members),
    ]

    all_errors = []
    for c in checks:
        all_errors.extend(c.get("errors", []))

    is_valid = len(all_errors) == 0
    failed = [c["rule"] for c in checks if c["status"] == "FAIL"]

    output = {
        "valid": is_valid,
        "script": "validate_members.py",
        "data_file": "data/members.yaml",
        "checks": checks,
        "errors": all_errors,
        "warnings": [],
        "summary": f"{len(checks) - len(failed)}/{len(checks)} checks passed"
                   + (f", {len(failed)} failed ({', '.join(failed)})" if failed else ""),
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))
```

---

### A2. validate_finance.py (F1-F5)

[trace:step-4:validation-rules]

**Target File**: `data/finance.yaml`
**Rule Count**: 5 checks (F1-F5)
**Cross-References**: Optional — `data/members.yaml` for donor_id validation in F5

#### CLI

```
python3 church-admin/.claude/hooks/scripts/validate_finance.py --data-dir ./church-admin/data/
python3 church-admin/.claude/hooks/scripts/validate_finance.py --data-dir ./church-admin/data/ --fix
```

#### Check-by-Check Detail

**F1 — ID Uniqueness and Format**

- **Condition**: All `offerings[].id` match regex `^OFF-\d{4}-\d{3,}$`. All `expenses[].id` match regex `^EXP-\d{4}-\d{3,}$`. No duplicates within each category.
- **Failure Mode**: Invalid format or duplicate IDs.
- **Implementation**:

```python
_OFF_ID_RE = re.compile(r'^OFF-\d{4}-\d{3,}$')
_EXP_ID_RE = re.compile(r'^EXP-\d{4}-\d{3,}$')

def check_f1(data: dict) -> dict:
    """F1: All offering/expense IDs unique and match format."""
    errors = []

    # Offering IDs
    off_ids = []
    for o in data.get("offerings", []):
        oid = o.get("id")
        if oid is None or not _OFF_ID_RE.match(str(oid)):
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
        if eid is None or not _EXP_ID_RE.match(str(eid)):
            errors.append(f"F1: Invalid expense ID format: {eid!r} (expected EXP-YYYY-NNN+)")
        exp_ids.append(eid)

    seen = set()
    for eid in exp_ids:
        if eid is not None and eid in seen:
            errors.append(f"F1: Duplicate expense ID: {eid}")
        if eid is not None:
            seen.add(eid)

    return {
        "rule": "F1",
        "name": "ID Uniqueness and Format",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All {len(off_ids)} offering + {len(exp_ids)} expense IDs valid" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

**F2 — Amount Positivity**

- **Condition**: All `offerings[].items[].amount`, `offerings[].total`, and `expenses[].amount` are positive integers (`isinstance(amt, int) and amt > 0`).
- **Failure Mode**: Zero, negative, float, string, or null amount.
- **Implementation**:

```python
def check_f2(data: dict) -> dict:
    """F2: All amount fields are positive integers."""
    errors = []

    for o in data.get("offerings", []):
        oid = o.get("id", "UNKNOWN")
        for i, item in enumerate(o.get("items", [])):
            amt = item.get("amount")
            if not isinstance(amt, int) or amt <= 0:
                errors.append(f"F2: Offering {oid} item[{i}] amount {amt!r} is not a positive integer")
        total = o.get("total")
        if not isinstance(total, int) or total <= 0:
            errors.append(f"F2: Offering {oid} total {total!r} is not a positive integer")

    for e in data.get("expenses", []):
        eid = e.get("id", "UNKNOWN")
        amt = e.get("amount")
        if not isinstance(amt, int) or amt <= 0:
            errors.append(f"F2: Expense {eid} amount {amt!r} is not a positive integer")

    return {
        "rule": "F2",
        "name": "Amount Positivity",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All amounts are positive integers" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

**F3 — Offering Sum Consistency**

- **Condition**: For each non-voided offering, `offerings[].total == sum(offerings[].items[].amount)`. Exact integer equality (no tolerance needed since all amounts are integers per F2).
- **Failure Mode**: Arithmetic mismatch.
- **Voided records**: Skipped (voided records are preserved for audit but not validated for sums).
- **Implementation**:

```python
def check_f3(data: dict) -> dict:
    """F3: offerings[].total == sum(items[].amount) for non-void records."""
    errors = []
    for o in data.get("offerings", []):
        oid = o.get("id", "UNKNOWN")
        if o.get("void", False):
            continue  # Skip voided records
        items_sum = sum(item.get("amount", 0) for item in o.get("items", []))
        declared_total = o.get("total", 0)
        if items_sum != declared_total:
            errors.append(
                f"F3: Offering {oid} arithmetic mismatch: "
                f"sum(items)={items_sum} != total={declared_total}"
            )

    return {
        "rule": "F3",
        "name": "Offering Sum Consistency",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All offering sums consistent" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

**F4 — Budget Arithmetic**

- **Condition**: `budget.total_budget == sum(budget.categories.values())`. All category budget values must be positive integers.
- **Failure Mode**: Sum mismatch or non-integer/non-positive budget value.
- **Implementation**:

```python
def check_f4(data: dict) -> dict:
    """F4: budget.total_budget == sum(budget.categories.values())."""
    errors = []
    budget = data.get("budget", {})
    categories = budget.get("categories", {})
    declared_total = budget.get("total_budget", 0)

    if not isinstance(categories, dict):
        errors.append("F4: budget.categories is not a dict")
        return {"rule": "F4", "name": "Budget Arithmetic", "status": "FAIL",
                "detail": "budget.categories is not a dict", "errors": errors}

    # Verify all category values are positive integers
    for cat_name, cat_val in categories.items():
        if not isinstance(cat_val, int) or cat_val <= 0:
            errors.append(f"F4: Budget category '{cat_name}' has non-positive or non-integer value: {cat_val!r}")

    computed_sum = sum(v for v in categories.values() if isinstance(v, int))
    if computed_sum != declared_total:
        errors.append(
            f"F4: Budget arithmetic mismatch: "
            f"sum(categories)={computed_sum} != total_budget={declared_total}"
        )

    return {
        "rule": "F4",
        "name": "Budget Arithmetic",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"Budget sums to {computed_sum}, matches declared {declared_total}" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

**F5 — Monthly Summary Accuracy**

- **Condition**: For each month key in `monthly_summary`, `total_income` equals sum of non-void offerings for that month, `total_expense` equals sum of non-void expenses for that month, and `balance == total_income - total_expense`.
- **Failure Mode**: Income, expense, or balance mismatch.
- **Edge Case**: If `monthly_summary` is empty or absent, check passes (no summary to validate).
- **Implementation**:

```python
from collections import defaultdict

def check_f5(data: dict) -> dict:
    """F5: monthly_summary totals match non-void records for that month."""
    errors = []
    monthly = data.get("monthly_summary", {})
    if not monthly:
        return {"rule": "F5", "name": "Monthly Summary Accuracy", "status": "PASS",
                "detail": "No monthly summary to validate", "errors": []}

    # Compute actual monthly totals from non-void records
    actual_income: dict[str, int] = defaultdict(int)
    actual_expense: dict[str, int] = defaultdict(int)

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

    return {
        "rule": "F5",
        "name": "Monthly Summary Accuracy",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All {len(monthly)} monthly summaries consistent" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

#### --fix Mode Behavior for Finance

When `--fix` is passed, `validate_finance.py` recomputes `monthly_summary` from non-void records and writes the corrected data using `atomic_write_yaml()`. Fix is limited to computed fields only — primary records are never modified.

---

### A3. validate_schedule.py (S1-S5)

[trace:step-4:validation-rules]

**Target File**: `data/schedule.yaml`
**Rule Count**: 5 checks (S1-S5)
**Cross-References**: None

#### CLI

```
python3 church-admin/.claude/hooks/scripts/validate_schedule.py --data-dir ./church-admin/data/
```

#### Check-by-Check Detail

**S1 — ID Uniqueness and Format**

- **Condition**: `regular_services[].id` matches `^SVC-[A-Z]+-?\d*$`. `special_events[].id` matches `^EVT-\d{4}-\d{3,}$`. `facility_bookings[].id` matches `^FAC-\d{4}-\d{3,}$`. All IDs unique across all three collections.
- **Failure Mode**: Invalid format or cross-collection duplicate.
- **Implementation**:

```python
_SVC_ID_RE = re.compile(r'^SVC-[A-Z]+-?\d*$')
_EVT_ID_RE = re.compile(r'^EVT-\d{4}-\d{3,}$')
_FAC_ID_RE = re.compile(r'^FAC-\d{4}-\d{3,}$')

def check_s1(data: dict) -> dict:
    """S1: All service/event/booking IDs unique and match format."""
    errors = []
    all_ids = []

    for s in data.get("regular_services", []):
        sid = s.get("id")
        if sid is None or not _SVC_ID_RE.match(str(sid)):
            errors.append(f"S1: Invalid service ID format: {sid!r} (expected SVC-ABC[-N])")
        all_ids.append(sid)

    for e in data.get("special_events", []):
        eid = e.get("id")
        if eid is None or not _EVT_ID_RE.match(str(eid)):
            errors.append(f"S1: Invalid event ID format: {eid!r} (expected EVT-YYYY-NNN+)")
        all_ids.append(eid)

    for f in data.get("facility_bookings", []):
        fid = f.get("id")
        if fid is None or not _FAC_ID_RE.match(str(fid)):
            errors.append(f"S1: Invalid booking ID format: {fid!r} (expected FAC-YYYY-NNN+)")
        all_ids.append(fid)

    seen = set()
    for sid in all_ids:
        if sid is not None and sid in seen:
            errors.append(f"S1: Duplicate schedule ID: {sid}")
        if sid is not None:
            seen.add(sid)

    return {
        "rule": "S1",
        "name": "ID Uniqueness and Format",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All {len(all_ids)} schedule IDs valid and unique" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

**S2 — Time Format Validation**

- **Condition**: All time fields match regex `^([01]\d|2[0-3]):[0-5]\d$` (HH:MM 24-hour format, 00:00 to 23:59).
- **Fields checked**: `regular_services[].time`, `special_events[].time`, `facility_bookings[].time_start`, `facility_bookings[].time_end`.
- **Implementation**:

```python
_TIME_RE = re.compile(r'^([01]\d|2[0-3]):[0-5]\d$')

def check_s2(data: dict) -> dict:
    """S2: Time fields match HH:MM 24-hour format."""
    errors = []

    for s in data.get("regular_services", []):
        t = s.get("time")
        if t is None or not _TIME_RE.match(str(t)):
            errors.append(f"S2: Service {s.get('id')} time '{t}' is not HH:MM 24h format")

    for e in data.get("special_events", []):
        t = e.get("time")
        if t is None or not _TIME_RE.match(str(t)):
            errors.append(f"S2: Event {e.get('id')} time '{t}' is not HH:MM 24h format")

    for f in data.get("facility_bookings", []):
        for field in ("time_start", "time_end"):
            t = f.get(field)
            if t is None or not _TIME_RE.match(str(t)):
                errors.append(f"S2: Booking {f.get('id')} {field} '{t}' is not HH:MM 24h format")

    return {
        "rule": "S2",
        "name": "Time Format Validation",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All time fields valid" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

**S3 — Recurrence and Day-of-Week Validation**

- **Condition**: `regular_services[].recurrence` is one of `{"weekly", "biweekly", "monthly"}`. `regular_services[].day_of_week` is one of `{"sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"}`.
- **Implementation**:

```python
_RECURRENCE_ENUM = {"weekly", "biweekly", "monthly"}
_DAY_ENUM = {"sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"}

def check_s3(data: dict) -> dict:
    """S3: recurrence and day_of_week are valid enum values."""
    errors = []
    for s in data.get("regular_services", []):
        sid = s.get("id", "UNKNOWN")
        rec = s.get("recurrence")
        if rec not in _RECURRENCE_ENUM:
            errors.append(f"S3: Service {sid} recurrence '{rec}' not in {sorted(_RECURRENCE_ENUM)}")
        dow = s.get("day_of_week")
        if dow not in _DAY_ENUM:
            errors.append(f"S3: Service {sid} day_of_week '{dow}' not in {sorted(_DAY_ENUM)}")

    return {
        "rule": "S3",
        "name": "Recurrence and Day-of-Week Validation",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All recurrence and day_of_week values valid" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

**S4 — Event and Booking Status Enum Validation**

- **Condition**: `special_events[].status` is one of `{"planned", "confirmed", "completed", "cancelled"}`. `facility_bookings[].status` is one of `{"pending", "confirmed", "cancelled"}`.
- **Implementation**:

```python
_EVENT_STATUS_ENUM = {"planned", "confirmed", "completed", "cancelled"}
_BOOKING_STATUS_ENUM = {"pending", "confirmed", "cancelled"}

def check_s4(data: dict) -> dict:
    """S4: event status and booking status in valid enum sets."""
    errors = []
    for e in data.get("special_events", []):
        eid = e.get("id", "UNKNOWN")
        st = e.get("status")
        if st not in _EVENT_STATUS_ENUM:
            errors.append(f"S4: Event {eid} status '{st}' not in {sorted(_EVENT_STATUS_ENUM)}")

    for f in data.get("facility_bookings", []):
        fid = f.get("id", "UNKNOWN")
        st = f.get("status")
        if st not in _BOOKING_STATUS_ENUM:
            errors.append(f"S4: Booking {fid} status '{st}' not in {sorted(_BOOKING_STATUS_ENUM)}")

    return {
        "rule": "S4",
        "name": "Event and Booking Status Enum",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All status values valid" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

**S5 — Facility Booking Time Range and Conflict Detection**

- **Condition**: For each facility booking, `time_end > time_start` (string comparison valid for HH:MM). For bookings on the same date at the same facility (excluding cancelled bookings), no time overlap: booking A's `time_end <= booking B's `time_start` when sorted by `time_start`.
- **Failure Mode**: Inverted time range or overlapping bookings.
- **Implementation**:

```python
from collections import defaultdict

def check_s5(data: dict) -> dict:
    """S5: time_end > time_start; no overlaps for same facility on same date."""
    errors = []
    bookings = data.get("facility_bookings", [])

    # Time range validity
    for b in bookings:
        bid = b.get("id", "UNKNOWN")
        ts = str(b.get("time_start", ""))
        te = str(b.get("time_end", ""))
        if ts and te and ts >= te:
            errors.append(f"S5: Booking {bid} time_end '{te}' is not after time_start '{ts}'")

    # Overlap detection: group by (facility, date), skip cancelled
    facility_date_groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for b in bookings:
        if b.get("status") == "cancelled":
            continue
        key = (str(b.get("facility", "")), str(b.get("date", "")))
        facility_date_groups[key].append(b)

    for key, group in facility_date_groups.items():
        if len(group) < 2:
            continue
        sorted_group = sorted(group, key=lambda x: str(x.get("time_start", "")))
        for i in range(len(sorted_group) - 1):
            a = sorted_group[i]
            b_next = sorted_group[i + 1]
            if str(a.get("time_end", "")) > str(b_next.get("time_start", "")):
                errors.append(
                    f"S5: Facility conflict on {key[1]} at '{key[0]}': "
                    f"{a.get('id')} ({a.get('time_start')}-{a.get('time_end')}) "
                    f"overlaps with {b_next.get('id')} ({b_next.get('time_start')}-{b_next.get('time_end')})"
                )

    return {
        "rule": "S5",
        "name": "Facility Booking Time Range and Conflict Detection",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All booking times valid and conflict-free" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

---

### A4. validate_newcomers.py (N1-N6)

[trace:step-4:validation-rules]

**Target File**: `data/newcomers.yaml`
**Rule Count**: 6 checks (N1-N6)
**Cross-References**: `data/members.yaml` required for N4 and N5

#### CLI

```
python3 church-admin/.claude/hooks/scripts/validate_newcomers.py --data-dir ./church-admin/data/
python3 church-admin/.claude/hooks/scripts/validate_newcomers.py --data-dir ./church-admin/data/ --members-file ./church-admin/data/members.yaml
python3 church-admin/.claude/hooks/scripts/validate_newcomers.py --data-dir ./church-admin/data/ --fix
```

#### Cross-Reference Loading

N4 and N5 require the set of valid member IDs from `members.yaml`. The script loads this file read-only:

```python
def _load_member_ids(data_dir: str, members_file: str | None = None) -> set[str]:
    """Load member IDs from members.yaml for cross-reference checks."""
    path = members_file or os.path.join(data_dir, "members.yaml")
    if not os.path.isfile(path):
        return set()  # If members.yaml doesn't exist, cross-ref checks will report warnings
    data = load_yaml_safe(path)
    return {m.get("id") for m in data.get("members", []) if m.get("id")}
```

#### Check-by-Check Detail

**N1 — ID Uniqueness and Format**

- **Condition**: All `newcomers[].id` match regex `^N\d{3,}$` AND are unique.
- **Implementation**:

```python
_NEWCOMER_ID_RE = re.compile(r'^N\d{3,}$')

def check_n1(newcomers: list[dict]) -> dict:
    """N1: All newcomer IDs unique and match N\\d{3,} format."""
    errors = []
    ids = []
    for n in newcomers:
        nid = n.get("id")
        if nid is None or not _NEWCOMER_ID_RE.match(str(nid)):
            errors.append(f"N1: Invalid newcomer ID format: {nid!r} (expected N followed by 3+ digits)")
        ids.append(nid)

    seen = set()
    for nid in ids:
        if nid is not None and nid in seen:
            errors.append(f"N1: Duplicate newcomer ID: {nid}")
        if nid is not None:
            seen.add(nid)

    return {
        "rule": "N1",
        "name": "ID Uniqueness and Format",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All {len(ids)} newcomer IDs valid and unique" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

**N2 — Journey Stage Validity and Sequential Milestone Completion**

- **Condition**: `journey_stage` is one of `{"first_visit", "attending", "small_group", "baptism_class", "baptized", "settled"}`. For each stage, all prerequisite milestones (as defined in `STAGE_TO_REQUIRED_MILESTONES`) must have `completed: true`.
- **Milestone requirement chain**: `first_visit` requires nothing. `attending` requires `first_visit` completed. `small_group` requires `first_visit`, `welcome_call`, `second_visit`. And so on.
- **Implementation**:

```python
_JOURNEY_STAGE_SET = {"first_visit", "attending", "small_group", "baptism_class", "baptized", "settled"}

_STAGE_TO_REQUIRED_MILESTONES = {
    "first_visit": [],
    "attending": ["first_visit"],
    "small_group": ["first_visit", "welcome_call", "second_visit"],
    "baptism_class": ["first_visit", "welcome_call", "second_visit", "small_group_intro"],
    "baptized": ["first_visit", "welcome_call", "second_visit", "small_group_intro", "baptism_class"],
    "settled": ["first_visit", "welcome_call", "second_visit", "small_group_intro", "baptism_class", "baptism"],
}

def check_n2(newcomers: list[dict]) -> dict:
    """N2: journey_stage valid + all preceding milestones completed."""
    errors = []
    for n in newcomers:
        nid = n.get("id", "UNKNOWN")
        stage = n.get("journey_stage")

        if stage not in _JOURNEY_STAGE_SET:
            errors.append(f"N2: Newcomer {nid} has invalid journey_stage '{stage}'")
            continue

        milestones = n.get("journey_milestones", {})
        required = _STAGE_TO_REQUIRED_MILESTONES.get(stage, [])

        for req_ms in required:
            ms_data = milestones.get(req_ms, {})
            if not isinstance(ms_data, dict) or not ms_data.get("completed", False):
                errors.append(
                    f"N2: Newcomer {nid} is at stage '{stage}' but "
                    f"prerequisite milestone '{req_ms}' is not completed"
                )

    return {
        "rule": "N2",
        "name": "Journey Stage Validity and Sequential Milestone Completion",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All journey stages and milestones consistent" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

**N3 — Date Format Validation**

- **Condition**: `first_visit`, all `journey_milestones.{stage}.date` (when not null), and `settled_date` (when not null) match YYYY-MM-DD format and parse to valid calendar dates.
- **Implementation**:

```python
def check_n3(newcomers: list[dict]) -> dict:
    """N3: first_visit and milestone dates are valid YYYY-MM-DD."""
    errors = []
    for n in newcomers:
        nid = n.get("id", "UNKNOWN")

        fv = n.get("first_visit")
        if fv is not None:
            if _parse_date(str(fv)) is None:
                errors.append(f"N3: Newcomer {nid} first_visit '{fv}' is not valid YYYY-MM-DD")

        for ms_key, ms_data in n.get("journey_milestones", {}).items():
            ms_date = ms_data.get("date") if isinstance(ms_data, dict) else None
            if ms_date is not None:
                if _parse_date(str(ms_date)) is None:
                    errors.append(f"N3: Newcomer {nid} milestone '{ms_key}' date '{ms_date}' is not valid YYYY-MM-DD")

        sd = n.get("settled_date")
        if sd is not None:
            if _parse_date(str(sd)) is None:
                errors.append(f"N3: Newcomer {nid} settled_date '{sd}' is not valid YYYY-MM-DD")

    return {
        "rule": "N3",
        "name": "Date Format Validation",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All date fields valid" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

**N4 — Cross-Reference Integrity (referred_by and assigned_to)**

- **Condition**: When `referred_by` is not null, it matches `^M\d{3,}$` AND exists in `members.yaml`. When `assigned_to` is not null, it matches `^M\d{3,}$` AND exists in `members.yaml`.
- **Dependency**: Requires `member_ids` set loaded from `members.yaml`.
- **Graceful degradation**: If `members.yaml` is unavailable, format-only checks run and a warning is emitted (no cross-reference validation).
- **Implementation**:

```python
_MEMBER_ID_RE = re.compile(r'^M\d{3,}$')

def check_n4(newcomers: list[dict], member_ids: set[str]) -> dict:
    """N4: referred_by and assigned_to reference valid member IDs."""
    errors = []
    warnings = []

    if not member_ids:
        warnings.append("N4: members.yaml not available — cross-reference checks skipped, format-only validation")

    for n in newcomers:
        nid = n.get("id", "UNKNOWN")

        ref = n.get("referred_by")
        if ref is not None:
            if not _MEMBER_ID_RE.match(str(ref)):
                errors.append(f"N4: Newcomer {nid} referred_by '{ref}' is not a valid member ID format")
            elif member_ids and ref not in member_ids:
                errors.append(f"N4: Newcomer {nid} referred_by '{ref}' does not exist in members.yaml")

        assigned = n.get("assigned_to")
        if assigned is not None:
            if not _MEMBER_ID_RE.match(str(assigned)):
                errors.append(f"N4: Newcomer {nid} assigned_to '{assigned}' is not a valid member ID format")
            elif member_ids and assigned not in member_ids:
                errors.append(f"N4: Newcomer {nid} assigned_to '{assigned}' does not exist in members.yaml")

    return {
        "rule": "N4",
        "name": "Cross-Reference Integrity",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All cross-references valid" if not errors else f"{len(errors)} errors found",
        "errors": errors,
        "warnings": warnings,
    }
```

**N5 — Settlement Consistency**

- **Condition**: When `status == "settled"`, `settled_as_member` must not be null AND must reference a valid member ID in `members.yaml`. `settled_date` must not be null. Conversely, when `settled_as_member` is not null, status must be `"settled"`.
- **Implementation**:

```python
def check_n5(newcomers: list[dict], member_ids: set[str]) -> dict:
    """N5: settled_as_member references valid member ID when status is 'settled'."""
    errors = []
    for n in newcomers:
        nid = n.get("id", "UNKNOWN")
        status = n.get("status")
        settled_id = n.get("settled_as_member")
        settled_date = n.get("settled_date")

        if status == "settled":
            if settled_id is None:
                errors.append(f"N5: Newcomer {nid} status is 'settled' but settled_as_member is null")
            elif member_ids and settled_id not in member_ids:
                errors.append(f"N5: Newcomer {nid} settled_as_member '{settled_id}' not found in members.yaml")
            if settled_date is None:
                errors.append(f"N5: Newcomer {nid} status is 'settled' but settled_date is null")

        if settled_id is not None and status != "settled":
            errors.append(
                f"N5: Newcomer {nid} has settled_as_member='{settled_id}' "
                f"but status is '{status}' (expected 'settled')"
            )

    return {
        "rule": "N5",
        "name": "Settlement Consistency",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All settlement fields consistent" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

**N6 — Stats Arithmetic Consistency**

- **Condition**: `_stats.total_active` equals count of records with `status == "active"`. `_stats.by_stage` counts match actual per-stage counts.
- **Implementation**:

```python
def check_n6(newcomers: list[dict], stats: dict) -> dict:
    """N6: _stats computed fields match actual record counts."""
    errors = []

    actual_active = sum(1 for n in newcomers if n.get("status") == "active")
    stats_active = stats.get("total_active", 0)
    if actual_active != stats_active:
        errors.append(f"N6: _stats.total_active={stats_active} but actual active count={actual_active}")

    by_stage = stats.get("by_stage", {})
    stage_counts: dict[str, int] = {}
    for n in newcomers:
        stage = n.get("journey_stage", "unknown")
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

    for stage, expected in by_stage.items():
        actual = stage_counts.get(stage, 0)
        if actual != expected:
            errors.append(f"N6: _stats.by_stage.{stage}={expected} but actual count={actual}")

    return {
        "rule": "N6",
        "name": "Stats Arithmetic Consistency",
        "status": "PASS" if not errors else "FAIL",
        "detail": f"All computed stats match actual counts" if not errors else f"{len(errors)} errors found",
        "errors": errors,
    }
```

---

## Part B: Hook Configuration Design

### B1. guard_data_files.py — Data File Write Protection

**Hook Type**: PreToolUse
**Matcher**: `Edit|Write`
**Purpose**: Prevent unauthorized agents from writing to `data/*.yaml` files. Enforces Layer 1 of the 3-Layer Data Integrity Architecture.
**Pattern Reference**: `block_destructive_commands.py` (same exit code 2 blocking pattern)

[trace:step-4:schema-specs]

#### Write Permission Matrix

```python
# Each data file maps to its sole authorized writer agent.
# The agent identity is determined from the tool_input context.
WRITE_PERMISSIONS = {
    "data/members.yaml":        "member-manager",
    "data/finance.yaml":        "finance-recorder",
    "data/newcomers.yaml":      "newcomer-tracker",
    "data/bulletin-data.yaml":  "bulletin-generator",
    "data/schedule.yaml":       "schedule-manager",
    "church-state.yaml":        "orchestrator",
}

# Append-only files: any agent may add content, but deletions are blocked
APPEND_ONLY_FILES = {"data/church-glossary.yaml"}
```

#### Agent Identity Detection

The hook reads the PreToolUse JSON payload from stdin. The `tool_input` contains the file path being written. Agent identity is inferred from the session context:

```python
def _detect_calling_agent() -> str:
    """Detect the current agent identity.

    Strategy: Check for agent identity markers in the environment or
    tool_input context. In Claude Code, sub-agents set their identity
    via the agent definition file name.

    Fallback: If agent identity cannot be determined, treat as
    'unknown' — which blocks writes to all protected files (safe default).
    """
    # Check environment variable (set by Claude Code agent framework)
    agent = os.environ.get("CLAUDE_AGENT_NAME", "")
    if agent:
        return agent.lower().strip()

    # Fallback: unknown agent — blocked by default (safe)
    return "unknown"
```

#### Exit Code Semantics

| Exit Code | Meaning | Behavior |
|-----------|---------|----------|
| 0 | Authorized | Tool call proceeds normally |
| 2 | Blocked | Tool call is prevented; stderr message sent to Claude for self-correction |

#### Implementation Sketch

```python
#!/usr/bin/env python3
"""
PreToolUse Hook — Data File Write Guard

Blocks unauthorized writes to data/*.yaml files BEFORE execution.
Each data file has exactly one designated writer agent (Layer 1 enforcement).

Exit code 2 = block the tool call + stderr feedback for Claude self-correction
Exit code 0 = allow the tool call to proceed

Safety-first: Unexpected internal errors → exit(0) (never block Claude on bugs).
"""

import json
import os
import sys

WRITE_PERMISSIONS = {
    "data/members.yaml":        "member-manager",
    "data/finance.yaml":        "finance-recorder",
    "data/newcomers.yaml":      "newcomer-tracker",
    "data/bulletin-data.yaml":  "bulletin-generator",
    "data/schedule.yaml":       "schedule-manager",
    "church-state.yaml":        "orchestrator",
}

APPEND_ONLY_FILES = {"data/church-glossary.yaml"}


def _normalize_path(file_path: str) -> str:
    """Normalize file path for matching against permission matrix.

    Handles both absolute and relative paths by extracting the
    relevant suffix (e.g., 'data/members.yaml' from '/full/path/church-admin/data/members.yaml').
    """
    # Try matching against known suffixes
    for known_path in list(WRITE_PERMISSIONS.keys()) + list(APPEND_ONLY_FILES):
        if file_path.endswith(known_path):
            return known_path
    return file_path


def _detect_calling_agent() -> str:
    """Detect the current agent identity from environment."""
    agent = os.environ.get("CLAUDE_AGENT_NAME", "")
    if agent:
        return agent.lower().strip()
    return "unknown"


def _is_deletion_in_glossary(tool_name: str, tool_input: dict) -> bool:
    """Check if a glossary edit removes existing terms (append-only violation).

    For Edit tool: check if old_string contains term entries that are removed.
    For Write tool: would need to compare with existing file — simplified check.
    """
    if tool_name == "Write":
        # Full file write to glossary — potentially destructive
        # Conservative: block full writes, require Edit for appends
        return True
    # Edit tool: allowed (assumed append-only by Claude's self-correction)
    return False


def main():
    try:
        stdin_data = sys.stdin.read()
        if not stdin_data.strip():
            sys.exit(0)

        payload = json.loads(stdin_data)
        tool_name = payload.get("tool_name", "")
        tool_input = payload.get("tool_input", {})

        # Extract file path from tool input
        file_path = tool_input.get("file_path", "") or tool_input.get("path", "")
        if not file_path:
            sys.exit(0)  # No file path — not a data file write

        normalized = _normalize_path(file_path)

    except (json.JSONDecodeError, KeyError, TypeError):
        sys.exit(0)  # Malformed input — don't block

    # Check if this is a protected data file
    if normalized in WRITE_PERMISSIONS:
        agent = _detect_calling_agent()
        authorized_agent = WRITE_PERMISSIONS[normalized]

        if agent != authorized_agent:
            print(
                f"DATA FILE WRITE BLOCKED: {normalized}\n"
                f"Only '{authorized_agent}' agent is authorized to write this file.\n"
                f"Current agent: '{agent}'\n"
                f"Use the designated agent or request the Orchestrator to coordinate the write.",
                file=sys.stderr,
            )
            sys.exit(2)

    elif normalized in APPEND_ONLY_FILES:
        if _is_deletion_in_glossary(tool_name, tool_input):
            print(
                f"GLOSSARY WRITE BLOCKED: {normalized}\n"
                f"church-glossary.yaml is APPEND-ONLY. Use Edit tool to add new terms.\n"
                f"Full file overwrites (Write tool) are blocked to prevent term deletion.",
                file=sys.stderr,
            )
            sys.exit(2)

    # Not a protected file, or authorized — allow
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Safety-first: never block Claude on unexpected internal errors
        sys.exit(0)
```

#### Hook Configuration Entry (.claude/settings.json)

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if test -f \"$CLAUDE_PROJECT_DIR\"/church-admin/.claude/hooks/scripts/guard_data_files.py; then python3 \"$CLAUDE_PROJECT_DIR\"/church-admin/.claude/hooks/scripts/guard_data_files.py; fi",
      "timeout": 10
    }
  ]
}
```

---

### B2. validate_yaml_syntax.py — YAML Syntax Validation

**Hook Type**: PostToolUse
**Matcher**: `Write`
**Purpose**: After any `.yaml` file write, validate YAML syntax using `yaml.safe_load()`. Warning-only (exit code 0 always) — does not block but alerts Claude to fix syntax errors.

#### Exit Code Semantics

| Exit Code | Meaning | Behavior |
|-----------|---------|----------|
| 0 | Always | stderr warning if YAML is invalid; no output if valid |

#### Implementation Sketch

```python
#!/usr/bin/env python3
"""
PostToolUse Hook — YAML Syntax Validator

After any .yaml file write, checks YAML syntax via yaml.safe_load().
Warning-only: exit code 0 always. stderr warning if invalid.

Triggered by: PostToolUse with matcher "Write"
"""

import json
import os
import sys

try:
    import yaml
except ImportError:
    # PyYAML not installed — silently skip
    sys.exit(0)


def main():
    try:
        stdin_data = sys.stdin.read()
        if not stdin_data.strip():
            sys.exit(0)

        payload = json.loads(stdin_data)
        tool_input = payload.get("tool_input", {})
        file_path = tool_input.get("file_path", "") or tool_input.get("path", "")

        if not file_path:
            sys.exit(0)

        # Only check .yaml and .yml files
        if not file_path.endswith((".yaml", ".yml")):
            sys.exit(0)

        # Check if file exists (it should, since this is PostToolUse)
        if not os.path.isfile(file_path):
            sys.exit(0)

        # Attempt to parse
        with open(file_path, "r", encoding="utf-8") as f:
            yaml.safe_load(f)

        # Valid YAML — no output needed
        sys.exit(0)

    except yaml.YAMLError as e:
        print(
            f"YAML SYNTAX WARNING: {file_path}\n"
            f"The file you just wrote has invalid YAML syntax.\n"
            f"Error: {e}\n"
            f"Please fix the YAML syntax to prevent downstream parsing failures.",
            file=sys.stderr,
        )
        sys.exit(0)  # Warning only — don't block

    except Exception:
        # Don't block on unexpected errors
        sys.exit(0)


if __name__ == "__main__":
    main()
```

#### Hook Configuration Entry (.claude/settings.json)

```json
{
  "matcher": "Write",
  "hooks": [
    {
      "type": "command",
      "command": "if test -f \"$CLAUDE_PROJECT_DIR\"/church-admin/.claude/hooks/scripts/validate_yaml_syntax.py; then python3 \"$CLAUDE_PROJECT_DIR\"/church-admin/.claude/hooks/scripts/validate_yaml_syntax.py; fi",
      "timeout": 10
    }
  ]
}
```

---

### B3. setup_church_admin.py — Infrastructure Health Verification

**Hook Type**: Setup
**Matcher**: `init`
**Purpose**: Verify that the church-admin runtime environment is healthy. Reports results via stdout (setup hook pattern).

#### Checks Performed

| Check ID | Description | Severity |
|----------|-------------|----------|
| CA-1 | Python 3.9+ available | FATAL |
| CA-2 | PyYAML importable (`import yaml`) | FATAL |
| CA-3 | `church-admin/data/` directory exists | FATAL |
| CA-4 | All 6 data YAML files exist | ERROR per missing file |
| CA-5 | All data YAML files parse successfully (`yaml.safe_load`) | ERROR per unparseable file |
| CA-6 | 4 validation scripts exist and have no import errors | ERROR per broken script |
| CA-7 | `guard_data_files.py` hook script exists | WARN |
| CA-8 | Runtime directories exist (verification-logs/, pacs-logs/, etc.) | WARN — auto-creates if missing |

#### Implementation Sketch

```python
#!/usr/bin/env python3
"""
Setup Hook — Church Admin Infrastructure Health Verification

Runs on `claude --init` to verify the church-admin runtime environment.
Reports results via stdout (setup hook pattern).

Checks:
  CA-1: Python version >= 3.9
  CA-2: PyYAML available
  CA-3: data/ directory exists
  CA-4: All 6 YAML data files exist
  CA-5: All YAML files parseable
  CA-6: Validation scripts importable
  CA-7: Guard hook exists
  CA-8: Runtime directories (auto-create if missing)
"""

import importlib
import os
import subprocess
import sys


def _check_python_version() -> tuple[str, bool]:
    """CA-1: Python >= 3.9"""
    v = sys.version_info
    ok = v >= (3, 9)
    return (f"CA-1: Python {v.major}.{v.minor}.{v.micro} {'OK' if ok else 'TOO OLD (need 3.9+)'}", ok)


def _check_pyyaml() -> tuple[str, bool]:
    """CA-2: PyYAML importable"""
    try:
        import yaml
        return (f"CA-2: PyYAML {yaml.__version__} OK", True)
    except ImportError:
        return ("CA-2: PyYAML NOT INSTALLED — run: pip install pyyaml", False)


def _check_data_dir(project_dir: str) -> tuple[str, bool]:
    """CA-3: data/ directory exists"""
    data_dir = os.path.join(project_dir, "church-admin", "data")
    exists = os.path.isdir(data_dir)
    return (f"CA-3: data/ directory {'EXISTS' if exists else 'MISSING'}", exists)


def _check_data_files(project_dir: str) -> list[tuple[str, bool]]:
    """CA-4 + CA-5: Data files exist and parse"""
    data_dir = os.path.join(project_dir, "church-admin", "data")
    files = [
        "members.yaml",
        "finance.yaml",
        "schedule.yaml",
        "newcomers.yaml",
        "bulletin-data.yaml",
        "church-glossary.yaml",
    ]
    results = []
    for f in files:
        path = os.path.join(data_dir, f)
        if not os.path.isfile(path):
            results.append((f"CA-4: {f} MISSING", False))
            continue
        results.append((f"CA-4: {f} EXISTS", True))

        # CA-5: Parse check
        try:
            import yaml
            with open(path, "r", encoding="utf-8") as fh:
                yaml.safe_load(fh)
            results.append((f"CA-5: {f} PARSEABLE", True))
        except Exception as e:
            results.append((f"CA-5: {f} PARSE ERROR: {e}", False))

    return results


def _check_validation_scripts(project_dir: str) -> list[tuple[str, bool]]:
    """CA-6: Validation scripts exist and importable"""
    scripts_dir = os.path.join(project_dir, "church-admin", ".claude", "hooks", "scripts")
    scripts = [
        "validate_members.py",
        "validate_finance.py",
        "validate_schedule.py",
        "validate_newcomers.py",
    ]
    results = []
    for s in scripts:
        path = os.path.join(scripts_dir, s)
        if not os.path.isfile(path):
            results.append((f"CA-6: {s} MISSING", False))
            continue
        # Syntax check via py_compile
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import py_compile; py_compile.compile('{path}', doraise=True)"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                results.append((f"CA-6: {s} SYNTAX OK", True))
            else:
                results.append((f"CA-6: {s} SYNTAX ERROR: {result.stderr[:200]}", False))
        except Exception as e:
            results.append((f"CA-6: {s} CHECK FAILED: {e}", False))

    return results


def _check_runtime_dirs(project_dir: str) -> list[tuple[str, bool]]:
    """CA-8: Runtime directories — auto-create if missing"""
    dirs = [
        "verification-logs",
        "pacs-logs",
        "review-logs",
        "autopilot-logs",
        "translations",
        "diagnosis-logs",
    ]
    results = []
    for d in dirs:
        path = os.path.join(project_dir, d)
        if os.path.isdir(path):
            results.append((f"CA-8: {d}/ EXISTS", True))
        else:
            try:
                os.makedirs(path, exist_ok=True)
                results.append((f"CA-8: {d}/ CREATED", True))
            except OSError as e:
                results.append((f"CA-8: {d}/ CREATE FAILED: {e}", False))

    return results


def main():
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    print("=" * 60)
    print("Church Admin Infrastructure Health Check")
    print("=" * 60)

    all_results = []

    # CA-1, CA-2
    r1 = _check_python_version()
    r2 = _check_pyyaml()
    all_results.extend([r1, r2])

    # CA-3
    r3 = _check_data_dir(project_dir)
    all_results.append(r3)

    # CA-4 + CA-5
    all_results.extend(_check_data_files(project_dir))

    # CA-6
    all_results.extend(_check_validation_scripts(project_dir))

    # CA-7: Guard hook
    guard_path = os.path.join(project_dir, "church-admin", ".claude", "hooks", "scripts", "guard_data_files.py")
    all_results.append((f"CA-7: guard_data_files.py {'EXISTS' if os.path.isfile(guard_path) else 'MISSING'}", os.path.isfile(guard_path)))

    # CA-8: Runtime dirs
    all_results.extend(_check_runtime_dirs(project_dir))

    # Report
    fatal_count = 0
    error_count = 0
    for msg, ok in all_results:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {msg}")
        if not ok:
            if "FATAL" in msg or msg.startswith("CA-1") or msg.startswith("CA-2"):
                fatal_count += 1
            else:
                error_count += 1

    print(f"\nResults: {sum(1 for _, ok in all_results if ok)} passed, "
          f"{sum(1 for _, ok in all_results if not ok)} failed "
          f"({fatal_count} fatal, {error_count} errors)")
    print("=" * 60)

    if fatal_count > 0:
        print("FATAL errors detected — church-admin system cannot operate.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Setup check failed with error: {e}", file=sys.stderr)
        sys.exit(1)
```

#### Hook Configuration Entry (.claude/settings.json)

```json
{
  "matcher": "init",
  "hooks": [
    {
      "type": "command",
      "command": "if test -f \"$CLAUDE_PROJECT_DIR\"/church-admin/.claude/hooks/scripts/setup_church_admin.py; then python3 \"$CLAUDE_PROJECT_DIR\"/church-admin/.claude/hooks/scripts/setup_church_admin.py; fi",
      "timeout": 30
    }
  ]
}
```

---

### B4. Complete .claude/settings.json Hook Integration

The following shows how the 3 new church-admin hooks integrate into the existing `.claude/settings.json` structure. The existing parent AgenticWorkflow hooks remain unchanged.

**New entries** (added to the existing configuration):

```json
{
  "hooks": {
    "PreToolUse": [
      // ... existing entries (block_destructive_commands.py, block_test_file_edit.py, predictive_debug_guard.py) ...
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "if test -f \"$CLAUDE_PROJECT_DIR\"/church-admin/.claude/hooks/scripts/guard_data_files.py; then python3 \"$CLAUDE_PROJECT_DIR\"/church-admin/.claude/hooks/scripts/guard_data_files.py; fi",
            "timeout": 10
          }
        ]
      }
    ],
    "PostToolUse": [
      // ... existing entry (context_guard.py --mode=post-tool) ...
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "if test -f \"$CLAUDE_PROJECT_DIR\"/church-admin/.claude/hooks/scripts/validate_yaml_syntax.py; then python3 \"$CLAUDE_PROJECT_DIR\"/church-admin/.claude/hooks/scripts/validate_yaml_syntax.py; fi",
            "timeout": 10
          }
        ]
      }
    ],
    "Setup": [
      // ... existing entries (setup_init.py, setup_maintenance.py) ...
      {
        "matcher": "init",
        "hooks": [
          {
            "type": "command",
            "command": "if test -f \"$CLAUDE_PROJECT_DIR\"/church-admin/.claude/hooks/scripts/setup_church_admin.py; then python3 \"$CLAUDE_PROJECT_DIR\"/church-admin/.claude/hooks/scripts/setup_church_admin.py; fi",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**Design Notes**:

1. All church-admin hooks use the `if test -f; then; fi` pattern consistent with parent hooks. This prevents errors when the church-admin subsystem is not yet initialized (Step 7).
2. `guard_data_files.py` is a PreToolUse hook with exit code 2 blocking capability, run independently (not through `context_guard.py`) — same pattern as `block_destructive_commands.py`.
3. `validate_yaml_syntax.py` is a PostToolUse hook with exit code 0 only (warning) — it never blocks.
4. `setup_church_admin.py` is a Setup init hook — runs alongside the parent `setup_init.py` on `claude --init`.

---

## Part C: Slash Command Specifications

### C1. /review-research (Step 3 Gate)

**File**: `church-admin/.claude/commands/review-research.md`
**Triggered at**: Step 3 `(human)` checkpoint
**Autopilot Default**: Approve all research findings

#### Behavior

1. **Read and display** `research/domain-analysis.md` summary:
   - Total entity count (target: >= 15 entities)
   - Total relation count (target: >= 10 relations)
   - Total constraint count (target: >= 8 constraints)
   - Key finding highlights (first 500 chars of each major section)

2. **Read and display** `research/template-analysis.md` summary:
   - Number of document types analyzed (target: 7)
   - List of each type with fixed/variable region count

3. **Read and display** `domain-knowledge.yaml` statistics:
   - Entity count, relation count, constraint count
   - Any DKS validation warnings (from previous P1 check)

4. **Decision prompt**: Ask user for one of:
   - **Approve**: Accept research and proceed to Planning phase
   - **Feedback**: Provide specific corrections (user types feedback)
   - **Reject**: Redo research step with revised instructions

#### Command File Content

```markdown
---
description: "Review domain analysis and template analysis research findings"
---
Display research outputs from Steps 1-2 for review:
1. Show `research/domain-analysis.md` summary (key findings, entity count, terminology count)
2. Show `research/template-analysis.md` summary (7 document types, layout structures)
3. Show `domain-knowledge.yaml` statistics (entities, relations, constraints)
4. Ask for approval or specific feedback on domain accuracy
$ARGUMENTS
```

---

### C2. /approve-architecture (Step 6 Gate)

**File**: `church-admin/.claude/commands/approve-architecture.md`
**Triggered at**: Step 6 `(human)` checkpoint
**Autopilot Default**: Approve architecture

#### Behavior

1. **Read and display** `planning/data-architecture-spec.md` summary:
   - 6 schema names + field count per schema
   - Validation rule count (M1-M6, F1-F5, S1-S5, N1-N6, B1-B3 = 25 total)
   - 3-layer data integrity architecture status

2. **Read and display** `planning/system-architecture.md` key sections:
   - Agent inventory: name, model, purpose (table format)
   - Feature workflow blueprint list with HitL gate classification
   - Inbox pipeline design summary (3 tiers)
   - Hook and validation configuration summary

3. **Read and display** Step 5 pACS and review results (if available):
   - pACS score and weak dimension
   - Reviewer verdict (PASS/FAIL) and issue count

4. **Decision prompt**: Ask user for one of:
   - **Approve**: Accept architecture and proceed to Implementation phase
   - **Feedback**: Provide specific design change requests
   - **Reject**: Redo planning with revised architecture direction

#### Command File Content

```markdown
---
description: "Review and approve system architecture design for implementation"
---
Display architecture outputs from Steps 4-5 for approval:
1. Show data schema overview from `planning/data-architecture-spec.md` (6 schemas + validation rules)
2. Show agent inventory and model selections from `planning/system-architecture.md`
3. Show feature workflow blueprint list with HitL gate classifications
4. Show inbox/ pipeline and scan-and-replicate design summary
5. Ask for approval or specific design change requests
$ARGUMENTS
```

---

### C3. /review-m1 (Step 10 Gate)

**File**: `church-admin/.claude/commands/review-m1.md`
**Triggered at**: Step 10 `(human)` checkpoint
**Autopilot Default**: Approve M1 core features

#### Behavior

1. **List all M1 output files** with sizes:
   - Feature workflows (weekly-bulletin.md, newcomer-pipeline.md, etc.)
   - Agent definition files (.claude/agents/*.md)
   - Validation scripts (.claude/hooks/scripts/validate_*.py)
   - Data files (data/*.yaml)
   - Bulletin output samples (bulletins/*.md)

2. **Run all 4 P1 validation scripts** against current data:
   ```bash
   python3 church-admin/.claude/hooks/scripts/validate_members.py --data-dir ./church-admin/data/
   python3 church-admin/.claude/hooks/scripts/validate_finance.py --data-dir ./church-admin/data/
   python3 church-admin/.claude/hooks/scripts/validate_schedule.py --data-dir ./church-admin/data/
   python3 church-admin/.claude/hooks/scripts/validate_newcomers.py --data-dir ./church-admin/data/
   ```
   Display pass/fail for each validation rule (M1-M6, F1-F5, S1-S5, N1-N6).

3. **Show bulletin generation test result**: Generate a sample bulletin from seed data and display it.

4. **Show newcomer pipeline test**: Walk through stage transition logic (first_visit -> attending -> ... -> settled).

5. **Show inbox/ parsing test**: Run sample Excel/CSV/image parsing if sample files exist.

6. **Report issues** with severity classification:
   - **Blocking**: P1 validation failures, missing critical files
   - **Warning**: Minor issues, incomplete optional features
   - **Info**: Notes for future improvement

7. **Decision prompt**: Ask user for one of:
   - **Approve**: Accept M1 and proceed to M2 implementation
   - **Feedback**: Provide specific bug reports or corrections
   - **Fix and Re-review**: Request fixes then re-run /review-m1

#### Command File Content

```markdown
---
description: "Review and test M1 core features (bulletin, newcomer, inbox/, scan-and-replicate)"
---
Run M1 integration verification:
1. List all M1 output files with sizes (workflows, agents, scripts, data files)
2. Run all 4 P1 validation scripts against current data — report pass/fail
3. Show bulletin generation test result (sample bulletin from seed data)
4. Show newcomer pipeline stage transition test
5. Show inbox/ parsing test results (Excel, image)
6. Report any issues found with severity classification
$ARGUMENTS
```

---

### C4. /final-review (Step 14 Gate)

**File**: `church-admin/.claude/commands/final-review.md`
**Triggered at**: Step 14 `(human)` checkpoint
**Autopilot Default**: Approve complete system

#### Behavior

1. **List ALL output files** across M1 and M2 with sizes:
   - Complete file tree of `church-admin/` with byte sizes
   - Categorized by: data, agents, hooks, workflows, outputs, docs

2. **Run all 4 P1 validation scripts** — full report:
   - Per-rule pass/fail status
   - Error details for any failures
   - Overall system data integrity status

3. **Run DNA Inheritance P1 validation** on all feature workflows:
   ```bash
   python3 .claude/hooks/scripts/validate_workflow.py --workflow church-admin/workflows/weekly-bulletin.md --project-dir .
   # ... for each feature workflow
   ```
   Verify all generated workflows inherit parent DNA correctly.

4. **Show integration test report** summary:
   - Test pass/fail counts from `testing/integration-results.md`
   - Any test failures with error messages

5. **Verify finance workflow safety**:
   - Confirm `monthly-finance-report.md` has `Autopilot: disabled`
   - Confirm all finance writes require human approval

6. **List IT volunteer documentation** files:
   - Check `docs/` directory for onboarding guide, quick reference card, FAQ
   - Completeness check: all expected files present and non-empty

7. **Report overall system readiness**:
   - **READY**: All checks pass, all features operational
   - **READY WITH WARNINGS**: Minor issues that don't block deployment
   - **NOT READY**: Blocking issues that must be resolved

8. **Decision prompt**: Ask user for one of:
   - **Approve**: Accept complete system as production-ready
   - **Feedback**: Provide specific issues to fix
   - **Defer**: Mark specific features for future iteration

#### Command File Content

```markdown
---
description: "Final system acceptance review for complete M1+M2 church admin system"
---
Run complete system verification:
1. List ALL output files across M1 and M2 with sizes
2. Run all 4 P1 validation scripts — full report
3. Run DNA Inheritance P1 validation on all 5+ feature workflows
4. Show integration test report summary (pass/fail counts)
5. Verify finance workflow header has Autopilot: disabled
6. List IT volunteer documentation files and completeness check
7. Report overall system readiness status with any blocking issues
$ARGUMENTS
```

---

## Part D: Shared Utilities

### D1. Atomic Write Helper — safe_yaml_write()

[trace:step-4:schema-specs]

This function implements the Layer 3 atomic write pattern from the parent AgenticWorkflow codebase. It is used by all agent scripts that write to `data/*.yaml` files.

#### Function Specification

```python
import fcntl
import os
import tempfile
from typing import Any

import yaml


def atomic_write_yaml(path: str, data: Any) -> None:
    """Write YAML data atomically using tempfile + flock + rename.

    Pattern: write to .tmp -> flock -> flush -> fsync -> unlock -> rename
    The os.rename() is atomic on POSIX systems (same filesystem).

    Layer 3 of the 3-Layer Data Integrity Architecture:
    - Layer 1 (Write Permission Separation) prevents cross-agent races
    - Layer 2 (P1 Validation) ensures data correctness
    - Layer 3 (this function) prevents partial/corrupt writes

    Args:
        path: Absolute path to the target YAML file.
        data: Python dict/list to serialize as YAML.

    Raises:
        OSError: If filesystem operations fail.
        yaml.YAMLError: If data is not YAML-serializable.

    Note: The flock guards the write phase of the temp file.
    Cross-writer races on the final target are prevented by
    Layer 1 (single writer per data file), not by flock alone.
    """
    dir_name = os.path.dirname(os.path.abspath(path))

    # Ensure directory exists
    os.makedirs(dir_name, exist_ok=True)

    tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            yaml.dump(
                data, f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )
            f.flush()
            os.fsync(f.fileno())
            fcntl.flock(f, fcntl.LOCK_UN)
        os.rename(tmp_path, path)  # Atomic on POSIX (same filesystem)
    except Exception:
        # Clean up temp file on any failure
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
```

#### Integration with guard_data_files.py

The atomic write helper is called AFTER the PreToolUse hook has verified write permission. The flow is:

```
Agent calls Write tool on data/members.yaml
    → PreToolUse: guard_data_files.py checks agent == "member-manager"
        → If unauthorized: exit(2) → Write blocked
        → If authorized: exit(0) → Write proceeds
    → Agent code uses atomic_write_yaml("data/members.yaml", updated_data)
    → PostToolUse: validate_yaml_syntax.py checks YAML syntax
        → If invalid: stderr warning (agent self-corrects)
```

#### Usage in Agent Scripts

```python
from church_data_utils import atomic_write_yaml, load_yaml_safe

# Load existing data
data = load_yaml_safe("data/members.yaml")

# Modify data
data["members"].append(new_member)
data["_stats"]["total_members"] += 1

# Write atomically
atomic_write_yaml("data/members.yaml", data)
```

---

### D2. Common Utilities Module — church_data_utils.py

**Location**: `church-admin/.claude/hooks/scripts/church_data_utils.py`
**Purpose**: Shared helper functions used by all 4 validation scripts and agent scripts.

#### YAML Loading with Error Handling

```python
import os
import yaml


def load_yaml_safe(path: str) -> dict:
    """Load a YAML file with comprehensive error handling.

    Returns the parsed YAML data as a dict. Raises descriptive
    exceptions on file-not-found, permission errors, or parse errors.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed YAML data (dict or list).

    Raises:
        FileNotFoundError: File does not exist.
        PermissionError: File is not readable.
        yaml.YAMLError: File contains invalid YAML.
        ValueError: File is empty or parses to None.
    """
    abs_path = os.path.abspath(path)

    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"YAML file not found: {abs_path}")

    with open(abs_path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML in {abs_path}: {e}") from e

    if data is None:
        raise ValueError(f"YAML file is empty or parses to None: {abs_path}")

    return data
```

#### Cross-File Member ID Lookup

```python
def load_member_ids(data_dir: str, members_file: str | None = None) -> set[str]:
    """Load the set of all member IDs from members.yaml.

    Used by validate_newcomers.py (N4, N5) and validate_bulletin.py (B3)
    for cross-reference integrity checks.

    Args:
        data_dir: Path to the data/ directory.
        members_file: Override path to members.yaml (optional).

    Returns:
        Set of member ID strings (e.g., {"M001", "M002", ...}).
        Returns empty set if members.yaml is unavailable.
    """
    path = members_file or os.path.join(data_dir, "members.yaml")
    if not os.path.isfile(path):
        return set()
    try:
        data = load_yaml_safe(path)
        return {m.get("id") for m in data.get("members", []) if m.get("id")}
    except Exception:
        return set()


def load_family_ids(data_dir: str, members_file: str | None = None) -> set[str]:
    """Load the set of all family IDs from members.yaml.

    Used by validate_bulletin.py (B3) for wedding anniversary cross-reference.

    Args:
        data_dir: Path to the data/ directory.
        members_file: Override path to members.yaml (optional).

    Returns:
        Set of family ID strings (e.g., {"F042", "F012", ...}).
        Returns empty set if members.yaml is unavailable.
    """
    path = members_file or os.path.join(data_dir, "members.yaml")
    if not os.path.isfile(path):
        return set()
    try:
        data = load_yaml_safe(path)
        ids = set()
        for m in data.get("members", []):
            fid = m.get("family", {}).get("family_id")
            if fid:
                ids.add(fid)
        return ids
    except Exception:
        return set()
```

#### Date Validation Helper

```python
import re
from datetime import date, datetime

_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def parse_date(s: str) -> date | None:
    """Parse a YYYY-MM-DD string to a date object.

    Returns None on any failure (format mismatch, invalid date like 2026-02-30).

    Args:
        s: Date string to parse.

    Returns:
        date object, or None if parsing fails.
    """
    if not isinstance(s, str) or not _DATE_RE.match(s):
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def is_valid_date(s: str) -> bool:
    """Check if a string is a valid YYYY-MM-DD date."""
    return parse_date(s) is not None


def is_past_date(s: str) -> bool:
    """Check if a string is a valid YYYY-MM-DD date in the past."""
    d = parse_date(s)
    return d is not None and d < date.today()
```

#### Phone Validation Helper

```python
_PHONE_RE = re.compile(r'^010-\d{4}-\d{4}$')


def is_valid_korean_phone(phone: str | None) -> bool:
    """Check if phone matches Korean mobile format 010-NNNN-NNNN.

    Returns True if phone is None (nullable field).
    Returns True if phone matches the format.
    Returns False otherwise.
    """
    if phone is None:
        return True
    return bool(_PHONE_RE.match(str(phone)))
```

#### ID Format Validators

```python
_MEMBER_ID_RE = re.compile(r'^M\d{3,}$')
_FAMILY_ID_RE = re.compile(r'^F\d{3,}$')
_NEWCOMER_ID_RE = re.compile(r'^N\d{3,}$')
_OFFERING_ID_RE = re.compile(r'^OFF-\d{4}-\d{3,}$')
_EXPENSE_ID_RE = re.compile(r'^EXP-\d{4}-\d{3,}$')
_SERVICE_ID_RE = re.compile(r'^SVC-[A-Z]+-?\d*$')
_EVENT_ID_RE = re.compile(r'^EVT-\d{4}-\d{3,}$')
_FACILITY_ID_RE = re.compile(r'^FAC-\d{4}-\d{3,}$')


def is_valid_id(value: str, id_type: str) -> bool:
    """Check if an ID matches the expected format for its type.

    Args:
        value: The ID string to validate.
        id_type: One of 'member', 'family', 'newcomer', 'offering',
                 'expense', 'service', 'event', 'facility'.

    Returns:
        True if format matches, False otherwise.
    """
    patterns = {
        "member": _MEMBER_ID_RE,
        "family": _FAMILY_ID_RE,
        "newcomer": _NEWCOMER_ID_RE,
        "offering": _OFFERING_ID_RE,
        "expense": _EXPENSE_ID_RE,
        "service": _SERVICE_ID_RE,
        "event": _EVENT_ID_RE,
        "facility": _FACILITY_ID_RE,
    }
    pattern = patterns.get(id_type)
    if pattern is None:
        return False
    return bool(pattern.match(str(value)))
```

---

### D3. Script File Locations Summary

| Script | Path | Type | Purpose |
|--------|------|------|---------|
| `validate_members.py` | `church-admin/.claude/hooks/scripts/` | Standalone P1 validator | M1-M6 checks |
| `validate_finance.py` | `church-admin/.claude/hooks/scripts/` | Standalone P1 validator | F1-F5 checks |
| `validate_schedule.py` | `church-admin/.claude/hooks/scripts/` | Standalone P1 validator | S1-S5 checks |
| `validate_newcomers.py` | `church-admin/.claude/hooks/scripts/` | Standalone P1 validator | N1-N6 checks |
| `guard_data_files.py` | `church-admin/.claude/hooks/scripts/` | PreToolUse hook | Write permission guard |
| `validate_yaml_syntax.py` | `church-admin/.claude/hooks/scripts/` | PostToolUse hook | YAML syntax check |
| `setup_church_admin.py` | `church-admin/.claude/hooks/scripts/` | Setup hook | Infrastructure health |
| `church_data_utils.py` | `church-admin/.claude/hooks/scripts/` | Shared library | Common helpers |

---

## Verification Report

### Self-Verification Against Agent Verification Criteria

| Criterion | Status | Evidence |
|-----------|--------|----------|
| All 4 validation scripts fully specified with check-by-check detail | **PASS** | Part A covers validate_members.py (M1-M6, 6 checks), validate_finance.py (F1-F5, 5 checks), validate_schedule.py (S1-S5, 5 checks), validate_newcomers.py (N1-N6, 6 checks) — all with Python implementation sketches |
| Each check has deterministic pass/fail condition | **PASS** | Every check uses regex, arithmetic, set membership, or referential integrity — no AI judgment. All return `"status": "PASS"` or `"status": "FAIL"` |
| JSON output format defined for all scripts | **PASS** | Common JSON schema defined at top of Part A with `valid`, `script`, `data_file`, `checks`, `errors`, `warnings`, `summary` fields. Each check returns structured dict |
| 3 hook configurations specified with exit code semantics | **PASS** | Part B covers guard_data_files.py (exit 0/2), validate_yaml_syntax.py (exit 0 always), setup_church_admin.py (exit 0/1). Exit code tables provided for each |
| 4 slash commands specified with exact behavior | **PASS** | Part C covers /review-research, /approve-architecture, /review-m1, /final-review with numbered step lists, decision criteria, and autopilot defaults |
| Atomic write helper pattern specified | **PASS** | Part D1 provides complete `atomic_write_yaml()` function with fcntl.flock + tempfile + os.rename pattern, integration diagram, and usage examples |
| Integration with guard_data_files.py hook documented | **PASS** | Part D1 includes flow diagram: PreToolUse guard -> Agent write -> PostToolUse syntax check. Part B1 includes complete write permission matrix |
| Exit code conventions match parent AgenticWorkflow (0=pass, 2=block) | **PASS** | Validation scripts: exit 0 always (check `valid` field). PreToolUse hooks: exit 0 (allow) / exit 2 (block). PostToolUse hooks: exit 0 always. Setup hooks: exit 0 (healthy) / exit 1 (fatal) |

### Cross-Step Traceability Summary

| Trace Marker | References | Location in Document |
|-------------|-----------|---------------------|
| `[trace:step-4:validation-rules]` | Step 4 validation rule catalog M1-M6, F1-F5, S1-S5, N1-N6 | Part A header, A1-A4 headers |
| `[trace:step-4:schema-specs]` | Step 4 field definitions and data types | Part A1 header, Part B1, Part D1 |

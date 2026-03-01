# Data Architecture Specification — Church Administration System

**Version**: 1.0
**Generated**: 2026-02-28
**Source Step**: Step 1 Domain Analysis + Research Documents
**Purpose**: Complete data schema definitions, validation rules, and integrity architecture for the Church Administration AI Agentic Workflow Automation System

---

## 1. Architecture Overview

### 1.1 3-Layer Data Integrity Architecture

[trace:step-1:entity-relationship-model]

The system enforces data integrity through three independent, complementary layers. Each layer addresses a distinct failure mode, and all three must pass before any data write is considered committed.

**Layer 1 — Write Permission Separation (Structural Guard)**

Each data file has exactly one designated writer agent. This is enforced by a `guard_data_files.py` PreToolUse hook that intercepts Edit/Write tool calls and checks the target file against the calling agent's allowed-write list.

| Data File | Designated Writer Agent | Read Access |
|-----------|------------------------|-------------|
| `church-state.yaml` | Orchestrator / Team Lead only | All agents (read-only) |
| `data/members.yaml` | `member-manager` agent | All agents (read-only) |
| `data/finance.yaml` | `finance-recorder` agent | All agents (read-only) |
| `data/schedule.yaml` | Orchestrator | All agents (read-only) |
| `data/newcomers.yaml` | `newcomer-tracker` agent | All agents (read-only) |
| `data/bulletin-data.yaml` | `bulletin-generator` agent | All agents (read-only) |
| `data/church-glossary.yaml` | Any agent (append-only) | All agents (read-only) |

Hook enforcement specification:

```python
# guard_data_files.py — PreToolUse hook (Edit|Write matcher)
# Exit code 2 = block the tool call + stderr feedback for Claude self-correction

WRITE_PERMISSIONS = {
    "data/members.yaml": "member-manager",
    "data/finance.yaml": "finance-recorder",
    "data/newcomers.yaml": "newcomer-tracker",
    "data/bulletin-data.yaml": "bulletin-generator",
    "church-state.yaml": "orchestrator",
}

# church-glossary.yaml: any agent may append, but deletions are blocked
APPEND_ONLY_FILES = {"data/church-glossary.yaml"}
```

**Layer 2 — P1 Deterministic Validation (Correctness Guard)**

Each data file has a corresponding `validate_*.py` script that performs deterministic, Python-implementable checks. These scripts output JSON to stdout (`{"valid": true/false, "errors": [...], "warnings": [...]}`). No AI judgment is involved — every check is a regex match, arithmetic comparison, or set membership test.

| Validator Script | Target File | Rule IDs |
|-----------------|-------------|----------|
| `validate_members.py` | `data/members.yaml` | M1-M6 |
| `validate_finance.py` | `data/finance.yaml` | F1-F5 |
| `validate_schedule.py` | `data/schedule.yaml` | S1-S5 |
| `validate_newcomers.py` | `data/newcomers.yaml` | N1-N6 |
| `validate_bulletin.py` | `data/bulletin-data.yaml` | B1-B3 |

**Layer 3 — Atomic Writes via File Locking (Corruption Guard)**

All data writes use the `fcntl.flock()` + tempfile + `os.rename()` pattern inherited from the parent AgenticWorkflow codebase (`_context_lib.py`). This prevents partial writes: each write is atomic because `os.rename()` is atomic on POSIX (same filesystem). Note: the flock guards the write phase of the temp file; cross-writer races on the final target are prevented by Layer 1 write-permission separation (single writer per data file), not by Layer 3 alone.

```python
import fcntl, tempfile, os, yaml

def atomic_write_yaml(path: str, data: dict) -> None:
    """Write YAML atomically using tempfile + rename.

    Pattern: write to .tmp → flock → flush → fsync → unlock → rename
    The os.rename() is atomic on POSIX systems (same filesystem).
    """
    dir_name = os.path.dirname(path)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                      sort_keys=False)
            f.flush()
            os.fsync(f.fileno())
            fcntl.flock(f, fcntl.LOCK_UN)
        os.rename(tmp_path, path)  # atomic on POSIX (same filesystem)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
```

### 1.2 Schema Extension Rules

[trace:step-1:extensibility-architecture]

When adding new fields to any shared data file (e.g., adding a `volunteer` section to `members.yaml` for a new workflow), the following three rules are mandatory to preserve backward compatibility:

**Rule 1 — No Field Deletion or Rename**

Existing fields must never be deleted or renamed. Existing workflows reference these fields by exact name; removing them causes immediate breakage.

```yaml
# FORBIDDEN: renaming 'cell_group' to 'small_group'
# FORBIDDEN: deleting 'baptism_type' field
```

**Rule 2 — New Fields Are Always Optional**

Any newly added field must have a safe default (typically `null` or empty list). Existing records that lack the new field must remain valid.

```yaml
# CORRECT: adding an optional field with null default
members:
  - id: "M001"
    name: "Kim Chulsoo (김철수)"
    volunteer_preferences: null  # new field — optional, null default
```

**Rule 3 — Defensive `.get()` Access Pattern**

All code that reads YAML data must use `.get(key, default)` rather than direct key access. This prevents `KeyError` when a field is absent in older records.

```python
# CORRECT — defensive access
serving = member.get("serving_area", [])
volunteer_prefs = member.get("volunteer_preferences", {})

# FORBIDDEN — direct access (breaks on older records)
serving = member["serving_area"]  # KeyError if field missing
```

### 1.3 Data Sensitivity Classification

[trace:step-1:data-integrity]

Data files are classified into three sensitivity levels. Sensitive files are excluded from version control via `.gitignore` and require separate encrypted backup.

| Sensitivity | Files | Reason | `.gitignore` |
|-------------|-------|--------|-------------|
| **HIGH** (PII + Financial) | `data/members.yaml` | Personal contact info, addresses, family relationships | Yes |
| **HIGH** (Financial) | `data/finance.yaml` | Individual offering amounts, expense details | Yes |
| **HIGH** (PII) | `data/newcomers.yaml` | Visitor contact info, personal notes | Yes |
| **LOW** (Operational) | `data/schedule.yaml` | Public service times, event schedules | No |
| **LOW** (Operational) | `data/bulletin-data.yaml` | Public bulletin content | No |
| **LOW** (Reference) | `data/church-glossary.yaml` | Church terminology dictionary | No |
| **MEDIUM** (Config) | `church-state.yaml` | System configuration, file paths | No |

Required `.gitignore` entries:

```gitignore
# Sensitive church data — personal information and financial records
# These files must be backed up separately with encryption
data/members.yaml
data/finance.yaml
data/newcomers.yaml
```

---

## 2. Data Schemas

### 2.1 members.yaml — Church Member Registry (교인 명부)

[trace:step-1:entity-members]

#### File Header

```yaml
# data/members.yaml
# Writer: member-manager agent (sole writer — Layer 1 enforced)
# Validator: validate_members.py (M1-M6)
# Sensitivity: HIGH (PII — .gitignore'd)
# Deletion policy: SOFT-DELETE ONLY (status: "inactive") — never remove records
# NEVER remove existing members — use status: "inactive" to preserve history (교적 보존)

schema_version: "1.0"
last_updated: "2026-03-01"
updated_by: "member-manager"
```

#### Field Definitions

| Field Path | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `schema_version` | string | yes | semver (e.g., "1.0") | Schema version for migration |
| `last_updated` | string | yes | YYYY-MM-DD format | Last modification date |
| `updated_by` | string | yes | non-empty | Agent that performed last write |
| `members` | list[object] | yes | non-empty list | List of member records |
| `members[].id` | string | yes | unique, regex `^M\d{3,}$`, immutable | Member ID (e.g., M001, M1234) |
| `members[].name` | string | yes | non-empty | Full name in Korean (본명) |
| `members[].gender` | enum | yes | `male` or `female` | Gender |
| `members[].birth_date` | string | yes | YYYY-MM-DD, must be past date | Date of birth |
| `members[].status` | enum | yes | `active`, `inactive`, `transferred`, `deceased` | Membership status |
| `members[].contact.phone` | string | no | regex `^010-\d{4}-\d{4}$` or null | Korean mobile phone |
| `members[].contact.email` | string | no | valid email format or null | Email address |
| `members[].contact.address` | string | no | free-text or null | Residential address |
| `members[].church.registration_date` | string | yes | YYYY-MM-DD | Church registration date |
| `members[].church.baptism_date` | string | no | YYYY-MM-DD or null | Baptism date (null if unbaptized) |
| `members[].church.baptism_type` | enum | no | `adult`, `infant`, or null | Baptism type |
| `members[].church.department` | string | no | non-empty or null | Department (e.g., 장년부, 청년부, 유년부) |
| `members[].church.cell_group` | string | no | non-empty or null | Small group / district (구역) name |
| `members[].church.role` | enum | no | `목사`, `장로`, `집사`, `권사`, `성도`, or null | Church office/title (직분) |
| `members[].church.serving_area` | list[string] | no | each item non-empty; empty list if none | Ministry service areas (봉사 영역) |
| `members[].family.family_id` | string | no | regex `^F\d{3,}$` or null | Family group ID |
| `members[].family.relation` | enum | no | `household_head`, `spouse`, `child`, `etc` | Relation within family unit |
| `members[].history` | list[object] | no | append-only, each has `date` + `event` + `note` | Membership event history |
| `members[].history[].date` | string | yes | YYYY-MM-DD | Event date |
| `members[].history[].event` | string | yes | non-empty (e.g., `transfer_in`, `role_change`, `baptism`) | Event type |
| `members[].history[].note` | string | no | free-text | Event description |
| `_stats.total_active` | integer | computed | must equal count of `status == "active"` | Active member count |
| `_stats.total_members` | integer | computed | must equal total count of all members | Total member count |
| `_stats.last_computed` | string | computed | YYYY-MM-DD | Last computation date |

#### Validation Rules (M1-M6)

**M1 — ID Uniqueness and Format**
```python
import re

def check_m1(members: list[dict]) -> tuple[bool, list[str]]:
    """M1: All member IDs unique and match M\\d{3,} format."""
    ID_RE = re.compile(r'^M\d{3,}$')
    errors = []
    ids = [m.get("id") for m in members]

    # Check format
    for mid in ids:
        if mid is None or not ID_RE.match(mid):
            errors.append(f"M1: Invalid member ID format: {mid!r} (expected M followed by 3+ digits)")

    # Check uniqueness
    seen = set()
    for mid in ids:
        if mid in seen:
            errors.append(f"M1: Duplicate member ID: {mid}")
        seen.add(mid)

    return (len(errors) == 0, errors)
```

**M2 — Required Fields Non-Empty**
```python
def check_m2(members: list[dict]) -> tuple[bool, list[str]]:
    """M2: name and status fields non-empty for every record."""
    errors = []
    for m in members:
        mid = m.get("id", "UNKNOWN")
        if not m.get("name") or not isinstance(m.get("name"), str) or not m["name"].strip():
            errors.append(f"M2: Member {mid} has empty or missing 'name'")
        if not m.get("status") or not isinstance(m.get("status"), str) or not m["status"].strip():
            errors.append(f"M2: Member {mid} has empty or missing 'status'")
    return (len(errors) == 0, errors)
```

**M3 — Phone Format Validation**
```python
import re

def check_m3(members: list[dict]) -> tuple[bool, list[str]]:
    """M3: phone matches 010-NNNN-NNNN Korean mobile format when present."""
    PHONE_RE = re.compile(r'^010-\d{4}-\d{4}$')
    errors = []
    for m in members:
        mid = m.get("id", "UNKNOWN")
        phone = m.get("contact", {}).get("phone")
        if phone is not None and not PHONE_RE.match(phone):
            errors.append(
                f"M3: Member {mid} phone '{phone}' does not match "
                f"format 010-NNNN-NNNN"
            )
    return (len(errors) == 0, errors)
```

**M4 — Status Enum Validation**
```python
MEMBER_STATUS_ENUM = {"active", "inactive", "transferred", "deceased"}

def check_m4(members: list[dict]) -> tuple[bool, list[str]]:
    """M4: status in {active, inactive, transferred, deceased}."""
    errors = []
    for m in members:
        mid = m.get("id", "UNKNOWN")
        status = m.get("status")
        if status not in MEMBER_STATUS_ENUM:
            errors.append(
                f"M4: Member {mid} has invalid status '{status}'. "
                f"Allowed: {sorted(MEMBER_STATUS_ENUM)}"
            )
    return (len(errors) == 0, errors)
```

**M5 — Family ID Reference Integrity**
```python
import re

def check_m5(members: list[dict]) -> tuple[bool, list[str]]:
    """M5: family_id references valid family group with >= 2 members."""
    FAMILY_ID_RE = re.compile(r'^F\d{3,}$')
    errors = []

    # Collect all family_ids
    family_groups: dict[str, list[str]] = {}
    for m in members:
        mid = m.get("id", "UNKNOWN")
        fid = m.get("family", {}).get("family_id")
        if fid is None:
            continue
        if not FAMILY_ID_RE.match(fid):
            errors.append(f"M5: Member {mid} has invalid family_id format: '{fid}'")
            continue
        family_groups.setdefault(fid, []).append(mid)

    # Each family_id must have >= 2 members
    for fid, member_ids in family_groups.items():
        if len(member_ids) < 2:
            errors.append(
                f"M5: Family {fid} has only {len(member_ids)} member(s): "
                f"{member_ids}. Family groups require >= 2 members."
            )

    return (len(errors) == 0, errors)
```

**M6 — Date Field Validity**
```python
from datetime import date, datetime
import re

DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

def _parse_date(s: str) -> date | None:
    if not DATE_RE.match(s):
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None

def check_m6(members: list[dict]) -> tuple[bool, list[str]]:
    """M6: All date fields valid YYYY-MM-DD; birth_date must be in the past."""
    errors = []
    today = date.today()

    DATE_FIELDS = [
        ("birth_date", True),   # (field_path, must_be_past)
        ("church.registration_date", False),
        ("church.baptism_date", False),
    ]

    for m in members:
        mid = m.get("id", "UNKNOWN")

        # birth_date (top-level)
        bd = m.get("birth_date")
        if bd is not None:
            parsed = _parse_date(bd)
            if parsed is None:
                errors.append(f"M6: Member {mid} birth_date '{bd}' is not valid YYYY-MM-DD")
            elif parsed >= today:
                errors.append(f"M6: Member {mid} birth_date '{bd}' is not in the past")

        # church.registration_date
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

    return (len(errors) == 0, errors)
```

#### Example Records

```yaml
members:
  - id: "M001"
    name: "김철수"
    gender: "male"
    birth_date: "1975-03-15"
    status: "active"
    contact:
      phone: "010-1234-5678"
      email: "kim.cs@example.com"
      address: "서울시 마포구 합정동 123-4"
    church:
      registration_date: "2015-06-01"
      baptism_date: "2010-04-05"
      baptism_type: "adult"
      department: "장년부"
      cell_group: "합정1구역"
      role: "집사"
      serving_area:
        - "찬양팀"
        - "주차봉사"
    family:
      family_id: "F042"
      relation: "household_head"
    history:
      - date: "2015-06-01"
        event: "transfer_in"
        note: "○○교회에서 이명 (Transfer from XX Church)"
      - date: "2023-07-01"
        event: "role_change"
        note: "성도 → 집사 임직 (Ordained as Deacon)"

  - id: "M002"
    name: "이영희"
    gender: "female"
    birth_date: "1978-11-22"
    status: "active"
    contact:
      phone: "010-9876-5432"
      email: null
      address: "서울시 마포구 합정동 123-4"
    church:
      registration_date: "2015-06-01"
      baptism_date: "2008-12-25"
      baptism_type: "adult"
      department: "장년부"
      cell_group: "합정1구역"
      role: "집사"
      serving_area:
        - "교회학교 교사"
    family:
      family_id: "F042"
      relation: "spouse"
    history: []

  - id: "M003"
    name: "박성민"
    gender: "male"
    birth_date: "2005-08-10"
    status: "active"
    contact:
      phone: null
      email: null
      address: "서울시 마포구 합정동 123-4"
    church:
      registration_date: "2015-06-01"
      baptism_date: null
      baptism_type: null
      department: "청년부"
      cell_group: null
      role: null
      serving_area: []
    family:
      family_id: "F042"
      relation: "child"
    history: []

_stats:
  total_active: 237
  total_members: 251
  last_computed: "2026-03-01"
```

#### Cross-References

| This Field | References | Validation |
|-----------|-----------|------------|
| `members[].id` | Referenced by `newcomers[].referred_by` | N4 checks existence |
| `members[].id` | Referenced by `newcomers[].assigned_to` | N4 checks existence |
| `members[].id` | Referenced by `newcomers[].settled_as_member` | N5 checks existence |
| `members[].id` | Referenced by `bulletin.celebrations.birthday[].member_id` | B3 checks existence |
| `members[].family.family_id` | Referenced by `bulletin.celebrations.wedding_anniversary[].family_id` | B3 checks existence |
| `members[].id` | Referenced by `finance.offerings[].donor_id` (optional) | F5 checks if present |

---

### 2.2 finance.yaml — Financial Records (재정 데이터)

[trace:step-1:entity-finance]

#### File Header

```yaml
# data/finance.yaml
# Writer: finance-recorder agent (sole writer — Layer 1 enforced)
# Validator: validate_finance.py (F1-F5)
# Sensitivity: HIGH (Financial — .gitignore'd)
# Deletion policy: VOID-ONLY (void: true) — never delete records
# Autopilot: PERMANENTLY DISABLED — all writes require human approval
# Currency: KRW (Korean Won), integer amounts only (no decimals)

schema_version: "1.0"
year: 2026
currency: "KRW"
last_updated: "2026-03-01"
updated_by: "finance-recorder"
```

#### Field Definitions

| Field Path | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `schema_version` | string | yes | semver | Schema version |
| `year` | integer | yes | 4-digit year | Fiscal year |
| `currency` | string | yes | always "KRW" | Currency code |
| `last_updated` | string | yes | YYYY-MM-DD | Last modification date |
| `updated_by` | string | yes | non-empty | Agent that last updated |
| `offerings` | list[object] | yes | list of offering records | All offering entries |
| `offerings[].id` | string | yes | unique, regex `^OFF-\d{4}-\d{3,}$` | Offering record ID |
| `offerings[].date` | string | yes | YYYY-MM-DD | Offering date |
| `offerings[].service` | string | yes | non-empty | Service name (e.g., 주일예배 1부) |
| `offerings[].type` | enum | yes | `sunday_offering`, `tithe`, `thanksgiving`, `special`, `mission`, `pledged_annual`, `building_fund` | Offering type |
| `offerings[].items` | list[object] | yes | >= 1 item | Individual offering categories |
| `offerings[].items[].category` | string | yes | non-empty | Category name |
| `offerings[].items[].amount` | integer | yes | > 0 | Amount in KRW |
| `offerings[].items[].donor_id` | string | no | regex `^M\d{3,}$` or null | Donor member ID (optional, for tracked giving) |
| `offerings[].total` | integer | yes | must equal sum of items[].amount | Total for this offering record |
| `offerings[].recorded_by` | string | yes | non-empty | Person who recorded |
| `offerings[].verified` | boolean | yes | true or false | Whether verified by approver |
| `offerings[].void` | boolean | yes | default false | Voided record marker |
| `offerings[].void_reason` | string | no | non-empty if void is true | Reason for voiding |
| `expenses` | list[object] | yes | list of expense records | All expense entries |
| `expenses[].id` | string | yes | unique, regex `^EXP-\d{4}-\d{3,}$` | Expense record ID |
| `expenses[].date` | string | yes | YYYY-MM-DD | Expense date |
| `expenses[].category` | enum | yes | `관리비`, `인건비`, `사역비`, `선교비`, `교육비`, `기타` | Expense category |
| `expenses[].subcategory` | string | no | non-empty or null | Detailed subcategory |
| `expenses[].amount` | integer | yes | > 0 | Amount in KRW |
| `expenses[].description` | string | yes | non-empty | Expense description |
| `expenses[].payment_method` | string | yes | non-empty | Payment method (e.g., 계좌이체, 현금, 카드) |
| `expenses[].approved_by` | string | yes | non-empty | Approver name or role |
| `expenses[].receipt` | boolean | yes | true or false | Whether receipt is on file |
| `expenses[].void` | boolean | yes | default false | Voided record marker |
| `expenses[].void_reason` | string | no | non-empty if void is true | Reason for voiding |
| `pledged_annual` | list[object] | no | list of annual pledge records | Pledged annual offerings (주정헌금) |
| `pledged_annual[].member_id` | string | yes | regex `^M\d{3,}$` | Pledging member ID |
| `pledged_annual[].year` | integer | yes | 4-digit year | Pledge year |
| `pledged_annual[].pledged_amount` | integer | yes | > 0 | Annual pledged amount in KRW |
| `pledged_annual[].paid_to_date` | integer | yes | >= 0 | Amount paid so far |
| `pledged_annual[].status` | enum | yes | `active`, `completed`, `cancelled` | Pledge status |
| `budget` | object | yes | annual budget record | Fiscal year budget |
| `budget.fiscal_year` | integer | yes | 4-digit year | Budget year |
| `budget.approved_date` | string | yes | YYYY-MM-DD | Budget approval date |
| `budget.categories` | object | yes | keys are category names, values are integers > 0 | Budget per category |
| `budget.total_budget` | integer | yes | must equal sum of categories values | Total annual budget |
| `monthly_summary` | object | no | keys are YYYY-MM strings | Monthly summaries (computed) |
| `monthly_summary[YYYY-MM].total_income` | integer | computed | sum of non-void offerings for that month | Monthly income total |
| `monthly_summary[YYYY-MM].total_expense` | integer | computed | sum of non-void expenses for that month | Monthly expense total |
| `monthly_summary[YYYY-MM].balance` | integer | computed | income - expense | Monthly balance |
| `monthly_summary[YYYY-MM].computed_at` | string | computed | YYYY-MM-DD | Computation date |

**Note on offering types**: `sunday_offering` (주일헌금, weekly Sunday offering) and `pledged_annual` (주정헌금, pledged annual offering) are explicitly separated. `pledged_annual` has its own top-level section for tracking pledge fulfillment across the year, while `sunday_offering` is recorded per-service in the `offerings` list. [trace:step-1:finance-offerings]

#### Validation Rules (F1-F5)

**F1 — ID Uniqueness and Format**
```python
import re

OFF_ID_RE = re.compile(r'^OFF-\d{4}-\d{3,}$')
EXP_ID_RE = re.compile(r'^EXP-\d{4}-\d{3,}$')

def check_f1(data: dict) -> tuple[bool, list[str]]:
    """F1: All offering/expense IDs unique and match format."""
    errors = []

    off_ids = []
    for o in data.get("offerings", []):
        oid = o.get("id")
        if oid is None or not OFF_ID_RE.match(oid):
            errors.append(f"F1: Invalid offering ID format: {oid!r}")
        off_ids.append(oid)
    if len(off_ids) != len(set(off_ids)):
        dupes = [x for x in off_ids if off_ids.count(x) > 1]
        errors.append(f"F1: Duplicate offering IDs: {set(dupes)}")

    exp_ids = []
    for e in data.get("expenses", []):
        eid = e.get("id")
        if eid is None or not EXP_ID_RE.match(eid):
            errors.append(f"F1: Invalid expense ID format: {eid!r}")
        exp_ids.append(eid)
    if len(exp_ids) != len(set(exp_ids)):
        dupes = [x for x in exp_ids if exp_ids.count(x) > 1]
        errors.append(f"F1: Duplicate expense IDs: {set(dupes)}")

    return (len(errors) == 0, errors)
```

**F2 — Amount Positivity**
```python
def check_f2(data: dict) -> tuple[bool, list[str]]:
    """F2: All amount fields are positive integers."""
    errors = []

    for o in data.get("offerings", []):
        oid = o.get("id", "UNKNOWN")
        for i, item in enumerate(o.get("items", [])):
            amt = item.get("amount")
            if not isinstance(amt, int) or amt <= 0:
                errors.append(f"F2: Offering {oid} item[{i}] amount {amt} is not a positive integer")
        total = o.get("total")
        if not isinstance(total, int) or total <= 0:
            errors.append(f"F2: Offering {oid} total {total} is not a positive integer")

    for e in data.get("expenses", []):
        eid = e.get("id", "UNKNOWN")
        amt = e.get("amount")
        if not isinstance(amt, int) or amt <= 0:
            errors.append(f"F2: Expense {eid} amount {amt} is not a positive integer")

    return (len(errors) == 0, errors)
```

**F3 — Offering Sum Consistency**
```python
def check_f3(data: dict) -> tuple[bool, list[str]]:
    """F3: offerings[].total == sum(items[].amount) with tolerance < 1."""
    errors = []
    for o in data.get("offerings", []):
        oid = o.get("id", "UNKNOWN")
        if o.get("void", False):
            continue  # Skip voided records
        items_sum = sum(item.get("amount", 0) for item in o.get("items", []))
        declared_total = o.get("total", 0)
        if abs(items_sum - declared_total) >= 1:
            errors.append(
                f"F3: Offering {oid} arithmetic mismatch: "
                f"sum(items)={items_sum} != total={declared_total}"
            )
    return (len(errors) == 0, errors)
```

**F4 — Budget Arithmetic**
```python
def check_f4(data: dict) -> tuple[bool, list[str]]:
    """F4: budget.total_budget == sum(budget.categories.values())."""
    errors = []
    budget = data.get("budget", {})
    categories = budget.get("categories", {})
    declared_total = budget.get("total_budget", 0)

    if not isinstance(categories, dict):
        errors.append("F4: budget.categories is not a dict")
        return (False, errors)

    computed_sum = sum(categories.values())
    if abs(computed_sum - declared_total) >= 1:
        errors.append(
            f"F4: Budget arithmetic mismatch: "
            f"sum(categories)={computed_sum} != total_budget={declared_total}"
        )

    return (len(errors) == 0, errors)
```

**F5 — Monthly Summary Accuracy**
```python
from collections import defaultdict

def check_f5(data: dict) -> tuple[bool, list[str]]:
    """F5: monthly_summary totals match non-void records for that month."""
    errors = []
    monthly = data.get("monthly_summary", {})
    if not monthly:
        return (True, [])  # No summary to validate

    # Compute actual monthly totals from non-void records
    actual_income: dict[str, int] = defaultdict(int)
    actual_expense: dict[str, int] = defaultdict(int)

    for o in data.get("offerings", []):
        if o.get("void", False):
            continue
        month_key = o.get("date", "")[:7]  # "2026-01" from "2026-01-05"
        actual_income[month_key] += o.get("total", 0)

    for e in data.get("expenses", []):
        if e.get("void", False):
            continue
        month_key = e.get("date", "")[:7]
        actual_expense[month_key] += e.get("amount", 0)

    for month_key, summary in monthly.items():
        declared_income = summary.get("total_income", 0)
        declared_expense = summary.get("total_expense", 0)
        declared_balance = summary.get("balance", 0)

        if abs(actual_income.get(month_key, 0) - declared_income) >= 1:
            errors.append(
                f"F5: Month {month_key} income mismatch: "
                f"actual={actual_income.get(month_key, 0)} != declared={declared_income}"
            )
        if abs(actual_expense.get(month_key, 0) - declared_expense) >= 1:
            errors.append(
                f"F5: Month {month_key} expense mismatch: "
                f"actual={actual_expense.get(month_key, 0)} != declared={declared_expense}"
            )
        if abs(declared_income - declared_expense - declared_balance) >= 1:
            errors.append(
                f"F5: Month {month_key} balance mismatch: "
                f"{declared_income} - {declared_expense} != {declared_balance}"
            )

    return (len(errors) == 0, errors)
```

#### Example Records

```yaml
offerings:
  - id: "OFF-2026-001"
    date: "2026-01-05"
    service: "주일예배 1부 (Sunday Service 1st)"
    type: "sunday_offering"
    items:
      - category: "십일조 (Tithe)"
        amount: 3850000
      - category: "주일헌금 (Sunday Offering)"
        amount: 1240000
      - category: "감사헌금 (Thanksgiving)"
        amount: 580000
    total: 5670000
    recorded_by: "재정담당집사 (Finance Deacon)"
    verified: true
    void: false

  - id: "OFF-2026-002"
    date: "2026-01-12"
    service: "주일예배 1부 (Sunday Service 1st)"
    type: "sunday_offering"
    items:
      - category: "십일조 (Tithe)"
        amount: 4120000
      - category: "주일헌금 (Sunday Offering)"
        amount: 1380000
    total: 5500000
    recorded_by: "재정담당집사 (Finance Deacon)"
    verified: true
    void: false

expenses:
  - id: "EXP-2026-001"
    date: "2026-01-10"
    category: "관리비"
    subcategory: "전기요금 (Electricity)"
    amount: 245000
    description: "1월 전기요금 (January electricity bill)"
    payment_method: "계좌이체 (Bank transfer)"
    approved_by: "담임목사 (Senior Pastor)"
    receipt: true
    void: false

  - id: "EXP-2026-002"
    date: "2026-01-15"
    category: "인건비"
    subcategory: "교역자사례비 (Pastoral Compensation)"
    amount: 2500000
    description: "1월 사례비 (January pastoral compensation)"
    payment_method: "계좌이체 (Bank transfer)"
    approved_by: "장로회 (Elder Board)"
    receipt: false
    void: false

pledged_annual:
  - member_id: "M001"
    year: 2026
    pledged_amount: 12000000
    paid_to_date: 3000000
    status: "active"

  - member_id: "M015"
    year: 2026
    pledged_amount: 6000000
    paid_to_date: 1500000
    status: "active"

budget:
  fiscal_year: 2026
  approved_date: "2025-12-28"
  categories:
    관리비: 3500000
    인건비: 35000000
    사역비: 12000000
    선교비: 8000000
    교육비: 5000000
    기타: 2000000
  total_budget: 65500000

monthly_summary:
  "2026-01":
    total_income: 11170000
    total_expense: 2745000
    balance: 8425000
    computed_at: "2026-02-01"
```

#### Cross-References

| This Field | References | Direction |
|-----------|-----------|-----------|
| `offerings[].items[].donor_id` | `members[].id` | finance -> members (optional donor tracking) |
| `expenses[].approved_by` | Member with approval authority (role-based, not ID-linked) | Semantic reference |
| `pledged_annual[].member_id` | `members[].id` | finance -> members (pledge tracking) |
| `monthly_summary` | Derived from `offerings[]` and `expenses[]` | Internal self-reference |

---

### 2.3 schedule.yaml — Worship & Event Schedule (예배/행사 일정)

[trace:step-1:entity-schedule]

#### File Header

```yaml
# data/schedule.yaml
# Writer: Orchestrator (sole writer — Layer 1 enforced)
# Validator: validate_schedule.py (S1-S5)
# Sensitivity: LOW (public schedule information)
# Deletion policy: status → "cancelled" for events; remove completed past events annually

schema_version: "1.0"
last_updated: "2026-03-01"
updated_by: "orchestrator"
```

#### Field Definitions

| Field Path | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `schema_version` | string | yes | semver | Schema version |
| `last_updated` | string | yes | YYYY-MM-DD | Last modification date |
| `updated_by` | string | yes | non-empty | Last updater |
| `regular_services` | list[object] | yes | list of recurring services | Weekly/recurring services |
| `regular_services[].id` | string | yes | unique, regex `^SVC-[A-Z]+-?\d*$` | Service ID |
| `regular_services[].name` | string | yes | non-empty | Service name |
| `regular_services[].recurrence` | enum | yes | `weekly`, `biweekly`, `monthly` | Recurrence pattern |
| `regular_services[].day_of_week` | enum | yes | `sunday`, `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday` | Day of week |
| `regular_services[].time` | string | yes | regex `^([01]\d|2[0-3]):[0-5]\d$` (HH:MM 24h) | Start time |
| `regular_services[].duration_minutes` | integer | yes | > 0, <= 300 | Duration in minutes |
| `regular_services[].location` | string | yes | non-empty | Venue/room name |
| `regular_services[].preacher_rotation` | list[string] | no | each non-empty | Preacher rotation list |
| `regular_services[].worship_leader` | string | no | non-empty or null | Worship leader/team |
| `special_events` | list[object] | no | list of one-off events | Special/non-recurring events |
| `special_events[].id` | string | yes | unique, regex `^EVT-\d{4}-\d{3,}$` | Event ID |
| `special_events[].name` | string | yes | non-empty | Event name |
| `special_events[].date` | string | yes | YYYY-MM-DD | Event date |
| `special_events[].time` | string | yes | HH:MM 24h format | Start time |
| `special_events[].duration_minutes` | integer | yes | > 0, <= 720 | Duration in minutes |
| `special_events[].location` | string | yes | non-empty | Venue/room |
| `special_events[].preacher` | string | no | non-empty or null | Speaker/preacher |
| `special_events[].description` | string | no | free-text | Event description |
| `special_events[].attendance_expected` | integer | no | > 0 or null | Expected attendance |
| `special_events[].preparation` | list[string] | no | preparation tasks | Preparation checklist |
| `special_events[].status` | enum | yes | `planned`, `confirmed`, `completed`, `cancelled` | Event status |
| `facility_bookings` | list[object] | no | facility reservations | Room/facility bookings |
| `facility_bookings[].id` | string | yes | unique, regex `^FAC-\d{4}-\d{3,}$` | Booking ID |
| `facility_bookings[].facility` | string | yes | non-empty | Facility/room name |
| `facility_bookings[].date` | string | yes | YYYY-MM-DD | Booking date |
| `facility_bookings[].time_start` | string | yes | HH:MM 24h format | Start time |
| `facility_bookings[].time_end` | string | yes | HH:MM 24h format, must be > time_start | End time |
| `facility_bookings[].purpose` | string | yes | non-empty | Booking purpose |
| `facility_bookings[].booked_by` | string | yes | non-empty | Person who booked |
| `facility_bookings[].status` | enum | yes | `pending`, `confirmed`, `cancelled` | Booking status |

#### Validation Rules (S1-S5)

**S1 — ID Uniqueness**
```python
import re

SVC_ID_RE = re.compile(r'^SVC-[A-Z]+-?\d*$')
EVT_ID_RE = re.compile(r'^EVT-\d{4}-\d{3,}$')
FAC_ID_RE = re.compile(r'^FAC-\d{4}-\d{3,}$')

def check_s1(data: dict) -> tuple[bool, list[str]]:
    """S1: All service/event/booking IDs unique and match format."""
    errors = []
    all_ids = []

    for s in data.get("regular_services", []):
        sid = s.get("id")
        if sid is None or not SVC_ID_RE.match(sid):
            errors.append(f"S1: Invalid service ID format: {sid!r}")
        all_ids.append(sid)

    for e in data.get("special_events", []):
        eid = e.get("id")
        if eid is None or not EVT_ID_RE.match(eid):
            errors.append(f"S1: Invalid event ID format: {eid!r}")
        all_ids.append(eid)

    for f in data.get("facility_bookings", []):
        fid = f.get("id")
        if fid is None or not FAC_ID_RE.match(fid):
            errors.append(f"S1: Invalid booking ID format: {fid!r}")
        all_ids.append(fid)

    seen = set()
    for sid in all_ids:
        if sid in seen:
            errors.append(f"S1: Duplicate schedule ID: {sid}")
        seen.add(sid)

    return (len(errors) == 0, errors)
```

**S2 — Time Format**
```python
import re

TIME_RE = re.compile(r'^([01]\d|2[0-3]):[0-5]\d$')

def check_s2(data: dict) -> tuple[bool, list[str]]:
    """S2: Time fields match HH:MM 24-hour format."""
    errors = []

    for s in data.get("regular_services", []):
        t = s.get("time")
        if t is None or not TIME_RE.match(t):
            errors.append(f"S2: Service {s.get('id')} time '{t}' is not HH:MM 24h format")

    for e in data.get("special_events", []):
        t = e.get("time")
        if t is None or not TIME_RE.match(t):
            errors.append(f"S2: Event {e.get('id')} time '{t}' is not HH:MM 24h format")

    for f in data.get("facility_bookings", []):
        for field in ("time_start", "time_end"):
            t = f.get(field)
            if t is None or not TIME_RE.match(t):
                errors.append(f"S2: Booking {f.get('id')} {field} '{t}' is not HH:MM 24h format")

    return (len(errors) == 0, errors)
```

**S3 — Recurrence Validity**
```python
RECURRENCE_ENUM = {"weekly", "biweekly", "monthly"}
DAY_ENUM = {"sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"}

def check_s3(data: dict) -> tuple[bool, list[str]]:
    """S3: recurrence in {weekly, biweekly, monthly} and day_of_week valid."""
    errors = []
    for s in data.get("regular_services", []):
        sid = s.get("id", "UNKNOWN")
        rec = s.get("recurrence")
        if rec not in RECURRENCE_ENUM:
            errors.append(f"S3: Service {sid} recurrence '{rec}' not in {sorted(RECURRENCE_ENUM)}")
        dow = s.get("day_of_week")
        if dow not in DAY_ENUM:
            errors.append(f"S3: Service {sid} day_of_week '{dow}' not in {sorted(DAY_ENUM)}")
    return (len(errors) == 0, errors)
```

**S4 — Event Status Enum**
```python
EVENT_STATUS_ENUM = {"planned", "confirmed", "completed", "cancelled"}
BOOKING_STATUS_ENUM = {"pending", "confirmed", "cancelled"}

def check_s4(data: dict) -> tuple[bool, list[str]]:
    """S4: event status and booking status in valid enum sets."""
    errors = []
    for e in data.get("special_events", []):
        eid = e.get("id", "UNKNOWN")
        st = e.get("status")
        if st not in EVENT_STATUS_ENUM:
            errors.append(f"S4: Event {eid} status '{st}' not in {sorted(EVENT_STATUS_ENUM)}")
    for f in data.get("facility_bookings", []):
        fid = f.get("id", "UNKNOWN")
        st = f.get("status")
        if st not in BOOKING_STATUS_ENUM:
            errors.append(f"S4: Booking {fid} status '{st}' not in {sorted(BOOKING_STATUS_ENUM)}")
    return (len(errors) == 0, errors)
```

**S5 — Facility Booking Time Range and Conflict Detection**
```python
from datetime import datetime

def check_s5(data: dict) -> tuple[bool, list[str]]:
    """S5: facility_bookings time_end > time_start; no overlaps for same facility on same date."""
    errors = []
    bookings = data.get("facility_bookings", [])

    for b in bookings:
        bid = b.get("id", "UNKNOWN")
        ts = b.get("time_start", "")
        te = b.get("time_end", "")
        if ts and te and ts >= te:
            errors.append(f"S5: Booking {bid} time_end '{te}' is not after time_start '{ts}'")

    # Check for overlaps: same facility + same date
    from collections import defaultdict
    facility_date_bookings: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for b in bookings:
        if b.get("status") == "cancelled":
            continue
        key = (b.get("facility", ""), b.get("date", ""))
        facility_date_bookings[key].append(b)

    for key, group in facility_date_bookings.items():
        if len(group) < 2:
            continue
        # Sort by time_start
        sorted_group = sorted(group, key=lambda x: x.get("time_start", ""))
        for i in range(len(sorted_group) - 1):
            a = sorted_group[i]
            b = sorted_group[i + 1]
            if a.get("time_end", "") > b.get("time_start", ""):
                errors.append(
                    f"S5: Facility conflict on {key[1]} at '{key[0]}': "
                    f"{a.get('id')} ({a.get('time_start')}-{a.get('time_end')}) "
                    f"overlaps with {b.get('id')} ({b.get('time_start')}-{b.get('time_end')})"
                )

    return (len(errors) == 0, errors)
```

#### Example Records

```yaml
regular_services:
  - id: "SVC-SUN-1"
    name: "주일예배 1부 (Sunday Service 1st)"
    recurrence: "weekly"
    day_of_week: "sunday"
    time: "09:00"
    duration_minutes: 70
    location: "본당 (Main Sanctuary)"
    preacher_rotation:
      - "담임목사 (Senior Pastor)"
      - "부목사1 (Associate Pastor 1)"
    worship_leader: "찬양팀A (Worship Team A)"

  - id: "SVC-SUN-2"
    name: "주일예배 2부 (Sunday Service 2nd)"
    recurrence: "weekly"
    day_of_week: "sunday"
    time: "11:00"
    duration_minutes: 70
    location: "본당 (Main Sanctuary)"
    preacher_rotation:
      - "담임목사 (Senior Pastor)"
    worship_leader: "찬양팀B (Worship Team B)"

  - id: "SVC-WED"
    name: "수요예배 (Wednesday Service)"
    recurrence: "weekly"
    day_of_week: "wednesday"
    time: "19:30"
    duration_minutes: 60
    location: "본당 (Main Sanctuary)"
    preacher_rotation:
      - "담임목사 (Senior Pastor)"
      - "부목사1 (Associate Pastor 1)"
      - "부목사2 (Associate Pastor 2)"
    worship_leader: null

special_events:
  - id: "EVT-2026-001"
    name: "2026년 신년감사예배 (New Year Thanksgiving Service)"
    date: "2026-01-04"
    time: "11:00"
    duration_minutes: 120
    location: "본당 (Main Sanctuary)"
    preacher: "담임목사 (Senior Pastor)"
    description: "New Year thanksgiving worship service"
    attendance_expected: 350
    preparation:
      - "현수막 제작 (Banner production)"
      - "특별 찬양팀 섭외 (Special worship team arrangement)"
      - "식사 준비 250인분 (Meal preparation for 250)"
    status: "completed"

  - id: "EVT-2026-015"
    name: "부활절 연합예배 (Easter Joint Service)"
    date: "2026-04-05"
    time: "10:00"
    duration_minutes: 90
    location: "본당 (Main Sanctuary)"
    preacher: "담임목사 (Senior Pastor)"
    description: "Easter celebration service"
    attendance_expected: 400
    preparation:
      - "꽃 장식 준비 (Floral decoration)"
      - "달걀 나눔 행사 (Egg sharing event)"
    status: "planned"

facility_bookings:
  - id: "FAC-2026-001"
    facility: "교육관 3층 (Education Building 3F)"
    date: "2026-02-15"
    time_start: "14:00"
    time_end: "17:00"
    purpose: "청년부 수련회 준비 모임 (Youth retreat planning meeting)"
    booked_by: "청년부 간사 (Youth Ministry Staff)"
    status: "confirmed"

  - id: "FAC-2026-002"
    facility: "소예배실 (Small Chapel)"
    date: "2026-03-05"
    time_start: "10:00"
    time_end: "12:00"
    purpose: "구역장 모임 (Cell Group Leaders Meeting)"
    booked_by: "교구장 (District Pastor)"
    status: "pending"
```

#### Cross-References

| This Field | References | Direction |
|-----------|-----------|-----------|
| `regular_services[].id` | Referenced by `bulletin.worship_order` derivation | schedule -> bulletin |
| `special_events[].date` | Used by bulletin for announcements | schedule -> bulletin |
| `facility_bookings[].facility` | Must match known facility names in church | Self-referencing |

---

### 2.4 newcomers.yaml — Newcomer Tracking Pipeline (새신자 추적)

[trace:step-1:entity-newcomers]

#### File Header

```yaml
# data/newcomers.yaml
# Writer: newcomer-tracker agent (sole writer — Layer 1 enforced)
# Validator: validate_newcomers.py (N1-N6)
# Sensitivity: HIGH (PII — .gitignore'd)
# Deletion policy: SOFT-DELETE ONLY (status: "inactive") — never remove records
# Journey: first_visit → attending → small_group → baptism_class → baptized → settled

schema_version: "1.0"
last_updated: "2026-03-01"
updated_by: "newcomer-tracker"
```

#### Field Definitions

| Field Path | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `schema_version` | string | yes | semver | Schema version |
| `last_updated` | string | yes | YYYY-MM-DD | Last modification date |
| `updated_by` | string | yes | non-empty | Last updater |
| `newcomers` | list[object] | yes | list of newcomer records | All newcomer entries |
| `newcomers[].id` | string | yes | unique, regex `^N\d{3,}$` | Newcomer ID |
| `newcomers[].name` | string | yes | non-empty | Full name |
| `newcomers[].gender` | enum | yes | `male`, `female` | Gender |
| `newcomers[].birth_year` | integer | no | 4-digit year, reasonable range (1920-current) | Birth year (less specific than full DOB for privacy) |
| `newcomers[].contact.phone` | string | yes | regex `^010-\d{4}-\d{4}$` | Korean mobile phone |
| `newcomers[].contact.kakao_id` | string | no | non-empty or null | KakaoTalk ID |
| `newcomers[].first_visit` | string | yes | YYYY-MM-DD | First visit date |
| `newcomers[].visit_route` | enum | yes | `지인 초청` (friend), `전도` (evangelism), `온라인 검색` (online), `지역사회 행사` (community event), `기타` (other) | How they found the church |
| `newcomers[].referred_by` | string | no | regex `^M\d{3,}$` or null | Referring member ID |
| `newcomers[].journey_stage` | enum | yes | `first_visit`, `attending`, `small_group`, `baptism_class`, `baptized`, `settled` | Current stage in newcomer journey |
| `newcomers[].journey_milestones` | object | yes | keys are stage names | Milestone tracking per stage |
| `newcomers[].journey_milestones.{stage}.date` | string | no | YYYY-MM-DD or null | Date milestone was reached |
| `newcomers[].journey_milestones.{stage}.completed` | boolean | yes | true or false | Whether milestone is completed |
| `newcomers[].journey_milestones.{stage}.notes` | string | no | free-text | Notes about this milestone |
| `newcomers[].assigned_to` | string | yes | regex `^M\d{3,}$` | Assigned shepherd member ID |
| `newcomers[].assigned_department` | string | no | non-empty or null | Target department |
| `newcomers[].status` | enum | yes | `active`, `settled`, `inactive`, `transferred` | Newcomer tracking status |
| `newcomers[].settled_as_member` | string | no | regex `^M\d{3,}$` or null | Member ID after settlement |
| `newcomers[].settled_date` | string | no | YYYY-MM-DD or null | Settlement date |
| `_stats.total_active` | integer | computed | count of active newcomers | Active newcomer count |
| `_stats.by_stage` | object | computed | counts per journey stage | Stage distribution |
| `_stats.last_computed` | string | computed | YYYY-MM-DD | Last computation date |

#### Validation Rules (N1-N6)

**N1 — ID Uniqueness and Format**
```python
import re

NEWCOMER_ID_RE = re.compile(r'^N\d{3,}$')

def check_n1(newcomers: list[dict]) -> tuple[bool, list[str]]:
    """N1: All newcomer IDs unique and match N\\d{3,} format."""
    errors = []
    ids = []
    for n in newcomers:
        nid = n.get("id")
        if nid is None or not NEWCOMER_ID_RE.match(nid):
            errors.append(f"N1: Invalid newcomer ID format: {nid!r}")
        ids.append(nid)
    if len(ids) != len(set(ids)):
        dupes = [x for x in ids if ids.count(x) > 1]
        errors.append(f"N1: Duplicate newcomer IDs: {set(dupes)}")
    return (len(errors) == 0, errors)
```

**N2 — Journey Stage Validity and Sequential Milestone Completion**
```python
JOURNEY_STAGES = [
    "first_visit", "attending", "small_group",
    "baptism_class", "baptized", "settled"
]
JOURNEY_STAGE_SET = set(JOURNEY_STAGES)

# Milestone keys that must be completed before each stage
MILESTONE_KEYS = [
    "first_visit", "welcome_call", "second_visit",
    "small_group_intro", "baptism_class", "baptism"
]

# Mapping: journey_stage requires all milestones up to this index completed
STAGE_TO_REQUIRED_MILESTONES = {
    "first_visit": [],
    "attending": ["first_visit"],
    "small_group": ["first_visit", "welcome_call", "second_visit"],
    "baptism_class": ["first_visit", "welcome_call", "second_visit", "small_group_intro"],
    "baptized": ["first_visit", "welcome_call", "second_visit", "small_group_intro", "baptism_class"],
    "settled": ["first_visit", "welcome_call", "second_visit", "small_group_intro", "baptism_class", "baptism"],
}

def check_n2(newcomers: list[dict]) -> tuple[bool, list[str]]:
    """N2: journey_stage valid + all preceding milestones completed."""
    errors = []
    for n in newcomers:
        nid = n.get("id", "UNKNOWN")
        stage = n.get("journey_stage")

        if stage not in JOURNEY_STAGE_SET:
            errors.append(f"N2: Newcomer {nid} has invalid journey_stage '{stage}'")
            continue

        milestones = n.get("journey_milestones", {})
        required = STAGE_TO_REQUIRED_MILESTONES.get(stage, [])

        for req_ms in required:
            ms_data = milestones.get(req_ms, {})
            if not ms_data.get("completed", False):
                errors.append(
                    f"N2: Newcomer {nid} is at stage '{stage}' but "
                    f"prerequisite milestone '{req_ms}' is not completed"
                )

    return (len(errors) == 0, errors)
```

**N3 — Date Format Validation**
```python
import re
from datetime import datetime, date

DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

def check_n3(newcomers: list[dict]) -> tuple[bool, list[str]]:
    """N3: first_visit and milestone dates are valid YYYY-MM-DD."""
    errors = []
    for n in newcomers:
        nid = n.get("id", "UNKNOWN")

        fv = n.get("first_visit")
        if fv is not None:
            if not DATE_RE.match(fv):
                errors.append(f"N3: Newcomer {nid} first_visit '{fv}' is not YYYY-MM-DD")
            else:
                try:
                    datetime.strptime(fv, "%Y-%m-%d")
                except ValueError:
                    errors.append(f"N3: Newcomer {nid} first_visit '{fv}' is not a valid date")

        for ms_key, ms_data in n.get("journey_milestones", {}).items():
            ms_date = ms_data.get("date") if isinstance(ms_data, dict) else None
            if ms_date is not None:
                if not DATE_RE.match(ms_date):
                    errors.append(f"N3: Newcomer {nid} milestone '{ms_key}' date '{ms_date}' is not YYYY-MM-DD")

        sd = n.get("settled_date")
        if sd is not None:
            if not DATE_RE.match(sd):
                errors.append(f"N3: Newcomer {nid} settled_date '{sd}' is not YYYY-MM-DD")

    return (len(errors) == 0, errors)
```

**N4 — Cross-Reference Integrity (referred_by and assigned_to)**
```python
import re

MEMBER_ID_RE = re.compile(r'^M\d{3,}$')

def check_n4(newcomers: list[dict], member_ids: set[str]) -> tuple[bool, list[str]]:
    """N4: referred_by and assigned_to reference valid member IDs in members.yaml."""
    errors = []
    for n in newcomers:
        nid = n.get("id", "UNKNOWN")

        ref = n.get("referred_by")
        if ref is not None:
            if not MEMBER_ID_RE.match(ref):
                errors.append(f"N4: Newcomer {nid} referred_by '{ref}' is not a valid member ID format")
            elif ref not in member_ids:
                errors.append(f"N4: Newcomer {nid} referred_by '{ref}' does not exist in members.yaml")

        assigned = n.get("assigned_to")
        if assigned is not None:
            if not MEMBER_ID_RE.match(assigned):
                errors.append(f"N4: Newcomer {nid} assigned_to '{assigned}' is not a valid member ID format")
            elif assigned not in member_ids:
                errors.append(f"N4: Newcomer {nid} assigned_to '{assigned}' does not exist in members.yaml")

    return (len(errors) == 0, errors)
```

**N5 — Settlement Consistency**
```python
def check_n5(newcomers: list[dict], member_ids: set[str]) -> tuple[bool, list[str]]:
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
            elif settled_id not in member_ids:
                errors.append(f"N5: Newcomer {nid} settled_as_member '{settled_id}' not found in members.yaml")
            if settled_date is None:
                errors.append(f"N5: Newcomer {nid} status is 'settled' but settled_date is null")

        if settled_id is not None and status != "settled":
            errors.append(
                f"N5: Newcomer {nid} has settled_as_member='{settled_id}' "
                f"but status is '{status}' (expected 'settled')"
            )

    return (len(errors) == 0, errors)
```

**N6 — Stats Arithmetic Consistency**

```python
def check_n6(newcomers: list[dict], stats: dict) -> tuple[bool, list[str]]:
    """N6: _stats computed fields match actual record counts."""
    errors = []

    # Count active records
    actual_active = sum(1 for n in newcomers if n.get("status") == "active")
    stats_active = stats.get("total_active", 0)
    if actual_active != stats_active:
        errors.append(
            f"N6: _stats.total_active={stats_active} but actual active count={actual_active}"
        )

    # Count by journey stage
    by_stage = stats.get("by_stage", {})
    stage_counts: dict[str, int] = {}
    for n in newcomers:
        stage = n.get("journey_stage", "unknown")
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

    for stage, expected in by_stage.items():
        actual = stage_counts.get(stage, 0)
        if actual != expected:
            errors.append(
                f"N6: _stats.by_stage.{stage}={expected} but actual count={actual}"
            )

    return (len(errors) == 0, errors)
```

#### Example Records

```yaml
newcomers:
  - id: "N001"
    name: "박민준"
    gender: "male"
    birth_year: 1992
    contact:
      phone: "010-1111-2222"
      kakao_id: "pmj1992"
    first_visit: "2026-02-02"
    visit_route: "지인 초청"
    referred_by: "M001"
    journey_stage: "attending"
    journey_milestones:
      first_visit:
        date: "2026-02-02"
        completed: true
      welcome_call:
        date: "2026-02-03"
        completed: true
        notes: "반갑게 통화, 다음 주 방문 의사 있음 (Positive call, plans to return)"
      second_visit:
        date: "2026-02-09"
        completed: true
      small_group_intro:
        date: null
        completed: false
      baptism_class:
        date: null
        completed: false
      baptism:
        date: null
        completed: false
    assigned_to: "M023"
    assigned_department: "청년부 (Youth)"
    status: "active"
    settled_as_member: null
    settled_date: null

  - id: "N002"
    name: "최수진"
    gender: "female"
    birth_year: 1988
    contact:
      phone: "010-3333-4444"
      kakao_id: null
    first_visit: "2026-01-19"
    visit_route: "전도"
    referred_by: null
    journey_stage: "small_group"
    journey_milestones:
      first_visit:
        date: "2026-01-19"
        completed: true
      welcome_call:
        date: "2026-01-20"
        completed: true
        notes: "세 자녀 있음. 주일학교 관심 (Has 3 children, interested in Sunday School)"
      second_visit:
        date: "2026-01-26"
        completed: true
      small_group_intro:
        date: "2026-02-05"
        completed: true
      baptism_class:
        date: null
        completed: false
      baptism:
        date: null
        completed: false
    assigned_to: "M056"
    assigned_department: "장년부 (Adult)"
    status: "active"
    settled_as_member: null
    settled_date: null

  - id: "N003"
    name: "정하늘"
    gender: "male"
    birth_year: 1995
    contact:
      phone: "010-5555-6666"
      kakao_id: "haneul95"
    first_visit: "2025-10-12"
    visit_route: "온라인 검색"
    referred_by: null
    journey_stage: "settled"
    journey_milestones:
      first_visit:
        date: "2025-10-12"
        completed: true
      welcome_call:
        date: "2025-10-13"
        completed: true
        notes: null
      second_visit:
        date: "2025-10-19"
        completed: true
      small_group_intro:
        date: "2025-11-02"
        completed: true
      baptism_class:
        date: "2025-11-15"
        completed: true
      baptism:
        date: "2025-12-25"
        completed: true
    assigned_to: "M012"
    assigned_department: "청년부 (Youth)"
    status: "settled"
    settled_as_member: "M252"
    settled_date: "2026-01-05"

_stats:
  total_active: 11
  by_stage:
    first_visit: 2
    attending: 4
    small_group: 3
    baptism_class: 2
    baptized: 0
    settled: 1
  last_computed: "2026-03-01"
```

#### Cross-References

| This Field | References | Direction |
|-----------|-----------|-----------|
| `newcomers[].referred_by` | `members[].id` | newcomers -> members |
| `newcomers[].assigned_to` | `members[].id` | newcomers -> members |
| `newcomers[].settled_as_member` | `members[].id` (new member created upon settlement) | newcomers -> members |

---

### 2.5 bulletin-data.yaml — Weekly Bulletin Source Data (주보 소스 데이터)

[trace:step-1:entity-bulletin]

#### File Header

```yaml
# data/bulletin-data.yaml
# Writer: bulletin-generator agent (sole writer — Layer 1 enforced)
# Validator: validate_bulletin.py (B1-B3)
# Sensitivity: LOW (public bulletin content)
# Updated: weekly (every Wednesday/Thursday for upcoming Sunday)

schema_version: "1.0"
last_updated: "2026-03-01"
updated_by: "bulletin-generator"
```

#### Field Definitions

| Field Path | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `schema_version` | string | yes | semver | Schema version |
| `last_updated` | string | yes | YYYY-MM-DD | Last modification date |
| `updated_by` | string | yes | non-empty | Last updater |
| `bulletin.issue_number` | integer | yes | > 0, monotonically increasing, matches church-state | Bulletin issue number |
| `bulletin.date` | string | yes | YYYY-MM-DD (must be a Sunday) | Bulletin date |
| `bulletin.church_name` | string | yes | non-empty | Church name |
| `bulletin.sermon.title` | string | yes | non-empty | Sermon title |
| `bulletin.sermon.scripture` | string | yes | non-empty (e.g., "요한복음 6:16-21") | Scripture reference |
| `bulletin.sermon.preacher` | string | yes | non-empty | Preacher name/role |
| `bulletin.sermon.series` | string | no | non-empty or null | Sermon series name |
| `bulletin.sermon.series_episode` | integer | no | > 0 or null | Episode number in series |
| `bulletin.worship_order` | list[object] | yes | >= 3 items | Worship order sequence |
| `bulletin.worship_order[].order` | integer | yes | > 0, sequential | Order number |
| `bulletin.worship_order[].item` | string | yes | non-empty | Order item name (e.g., 찬양, 기도, 말씀) |
| `bulletin.worship_order[].detail` | string | no | free-text or null | Item detail |
| `bulletin.worship_order[].performer` | string | no | free-text or null | Who performs this item |
| `bulletin.announcements` | list[object] | no | list of announcements | Church announcements |
| `bulletin.announcements[].id` | string | yes | unique within bulletin | Announcement ID |
| `bulletin.announcements[].category` | string | yes | non-empty | Category (e.g., 행사, 새신자, 교육) |
| `bulletin.announcements[].title` | string | yes | non-empty | Announcement title |
| `bulletin.announcements[].content` | string | yes | non-empty | Announcement body |
| `bulletin.announcements[].priority` | enum | yes | `high`, `normal`, `low` | Display priority |
| `bulletin.announcements[].expires` | string | no | YYYY-MM-DD or null | Expiration date |
| `bulletin.prayer_requests` | list[object] | no | list of prayer items | Weekly prayer requests |
| `bulletin.prayer_requests[].category` | string | yes | non-empty | Prayer category |
| `bulletin.prayer_requests[].content` | string | yes | non-empty | Prayer request content |
| `bulletin.offering_team` | list[string] | no | each non-empty | This week's offering team |
| `bulletin.celebrations.birthday` | list[object] | no | birthday celebrants | Birthday list |
| `bulletin.celebrations.birthday[].member_id` | string | yes | regex `^M\d{3,}$` | Member ID |
| `bulletin.celebrations.birthday[].name` | string | yes | non-empty | Display name |
| `bulletin.celebrations.birthday[].date` | string | yes | MM-DD format | Birthday (month-day) |
| `bulletin.celebrations.wedding_anniversary` | list[object] | no | anniversary couples | Wedding anniversary list |
| `bulletin.celebrations.wedding_anniversary[].family_id` | string | yes | regex `^F\d{3,}$` | Family group ID |
| `bulletin.celebrations.wedding_anniversary[].date` | string | yes | MM-DD format | Anniversary date |
| `bulletin.next_week.sermon_title` | string | no | non-empty or null | Next week sermon title |
| `bulletin.next_week.scripture` | string | no | non-empty or null | Next week scripture |
| `bulletin.next_week.special_events` | list[string] | no | list of event previews | Upcoming events |
| `generation_history` | list[object] | no | append-only | Bulletin generation log |
| `generation_history[].issue` | integer | yes | matches a bulletin issue | Issue number |
| `generation_history[].generated_at` | string | no | ISO 8601 datetime or null | Generation timestamp |
| `generation_history[].generated_by` | string | no | non-empty or null | Generator agent |
| `generation_history[].output_path` | string | no | valid file path or null | Output file path |

#### Validation Rules (B1-B3)

**B1 — Required Sections Present**
```python
def check_b1(data: dict) -> tuple[bool, list[str]]:
    """B1: Bulletin contains all required sections."""
    errors = []
    bulletin = data.get("bulletin", {})

    REQUIRED_SECTIONS = {
        "issue_number": "Issue number",
        "date": "Bulletin date",
        "sermon": "Sermon information",
        "worship_order": "Worship order",
    }

    for key, label in REQUIRED_SECTIONS.items():
        val = bulletin.get(key)
        if val is None:
            errors.append(f"B1: Missing required bulletin section: '{key}' ({label})")
        elif key == "worship_order" and (not isinstance(val, list) or len(val) < 3):
            errors.append(f"B1: worship_order must have >= 3 items (found {len(val) if isinstance(val, list) else 0})")

    sermon = bulletin.get("sermon", {})
    for field in ("title", "scripture", "preacher"):
        if not sermon.get(field):
            errors.append(f"B1: Missing required sermon field: '{field}'")

    return (len(errors) == 0, errors)
```

**B2 — Issue Number Monotonicity**
```python
def check_b2(data: dict) -> tuple[bool, list[str]]:
    """B2: issue_number is monotonically increasing; no duplicates in generation_history."""
    errors = []
    bulletin = data.get("bulletin", {})
    current_issue = bulletin.get("issue_number")

    if not isinstance(current_issue, int) or current_issue <= 0:
        errors.append(f"B2: issue_number must be a positive integer (found {current_issue})")
        return (False, errors)

    history = data.get("generation_history", [])
    history_issues = [h.get("issue") for h in history if h.get("issue") is not None]

    # Check for duplicates
    if len(history_issues) != len(set(history_issues)):
        dupes = [x for x in history_issues if history_issues.count(x) > 1]
        errors.append(f"B2: Duplicate issue numbers in generation_history: {set(dupes)}")

    # Check monotonicity
    for i in range(len(history_issues) - 1):
        if history_issues[i] >= history_issues[i + 1]:
            errors.append(
                f"B2: generation_history issue numbers not monotonically increasing: "
                f"{history_issues[i]} >= {history_issues[i + 1]}"
            )

    return (len(errors) == 0, errors)
```

**B3 — Cross-Reference Validity**
```python
import re

MEMBER_ID_RE = re.compile(r'^M\d{3,}$')
FAMILY_ID_RE = re.compile(r'^F\d{3,}$')

def check_b3(data: dict, member_ids: set[str], family_ids: set[str]) -> tuple[bool, list[str]]:
    """B3: All member_id and family_id references in celebrations resolve to existing records."""
    errors = []
    bulletin = data.get("bulletin", {})
    celebrations = bulletin.get("celebrations", {})

    for bday in celebrations.get("birthday", []):
        mid = bday.get("member_id")
        if mid is not None:
            if not MEMBER_ID_RE.match(mid):
                errors.append(f"B3: Birthday member_id '{mid}' has invalid format")
            elif mid not in member_ids:
                errors.append(f"B3: Birthday member_id '{mid}' not found in members.yaml")

    for anniv in celebrations.get("wedding_anniversary", []):
        fid = anniv.get("family_id")
        if fid is not None:
            if not FAMILY_ID_RE.match(fid):
                errors.append(f"B3: Anniversary family_id '{fid}' has invalid format")
            elif fid not in family_ids:
                errors.append(f"B3: Anniversary family_id '{fid}' not found in members.yaml families")

    return (len(errors) == 0, errors)
```

#### Example Records

```yaml
bulletin:
  issue_number: 1247
  date: "2026-03-01"
  church_name: "새벽이슬교회 (Morning Dew Church)"

  sermon:
    title: "두려움을 넘어선 믿음 (Faith Beyond Fear)"
    scripture: "요한복음 6:16-21 (John 6:16-21)"
    preacher: "담임목사 (Senior Pastor)"
    series: "요한복음 강해 시리즈 (Gospel of John Exposition Series)"
    series_episode: 18

  worship_order:
    - order: 1
      item: "찬양 (Worship)"
      detail: "주님 찬양해 (경배와찬양 178)"
      performer: "찬양팀B (Worship Team B)"
    - order: 2
      item: "기도 (Prayer)"
      detail: "대표기도 (Representative Prayer)"
      performer: "김○○ 집사 (Deacon Kim)"
    - order: 3
      item: "봉헌 (Offering)"
      detail: null
      performer: null
    - order: 4
      item: "말씀 (Sermon)"
      detail: "두려움을 넘어선 믿음 (Faith Beyond Fear)"
      performer: "담임목사 (Senior Pastor)"
    - order: 5
      item: "축도 (Benediction)"
      detail: null
      performer: "담임목사 (Senior Pastor)"

  announcements:
    - id: "ANN-001"
      category: "행사 (Event)"
      title: "3월 구역모임 일정 (March Cell Group Schedule)"
      content: "이번 주 수요일 오후 7시, 각 구역별 모임이 있습니다."
      priority: "high"
      expires: "2026-03-04"
    - id: "ANN-002"
      category: "새신자 (Newcomer)"
      title: "새신자 환영회 (Newcomer Welcome Reception)"
      content: "예배 후 본당 로비에서 새신자 환영 다과 시간이 있습니다."
      priority: "normal"
      expires: "2026-03-01"

  prayer_requests:
    - category: "교회 (Church)"
      content: "3월 부흥회를 위한 성령의 역사 기도 (Pray for the March revival meeting)"
    - category: "국가 (Nation)"
      content: "나라와 민족을 위한 중보기도 (Intercessory prayer for the nation)"

  offering_team:
    - "박○○ 권사 (Deaconess Park)"
    - "최○○ 집사 (Deacon Choi)"

  celebrations:
    birthday:
      - member_id: "M045"
        name: "홍○○"
        date: "03-03"
    wedding_anniversary:
      - family_id: "F012"
        date: "03-02"

  next_week:
    sermon_title: "평화의 왕 (Prince of Peace)"
    scripture: "요한복음 6:22-40 (John 6:22-40)"
    special_events: []

generation_history:
  - issue: 1246
    generated_at: "2026-02-22T14:30:00"
    generated_by: "bulletin-generator"
    output_path: "bulletins/2026-02-22-bulletin.md"
  - issue: 1247
    generated_at: null
    generated_by: null
    output_path: null
```

#### Cross-References

| This Field | References | Direction |
|-----------|-----------|-----------|
| `bulletin.celebrations.birthday[].member_id` | `members[].id` | bulletin -> members |
| `bulletin.celebrations.wedding_anniversary[].family_id` | `members[].family.family_id` | bulletin -> members |
| `bulletin.worship_order` | Derived from `schedule.yaml` regular services | bulletin -> schedule |
| `bulletin.issue_number` | Must match `church-state.yaml` `church.current_bulletin_issue` | bulletin -> church-state |

---

### 2.6 church-glossary.yaml — Church Terminology Dictionary (교회 용어 사전)

[trace:step-1:entity-glossary]

#### File Header

```yaml
# data/church-glossary.yaml
# Writer: ANY agent (append-only — never delete or modify existing terms)
# Sensitivity: LOW (reference data)
# Deletion policy: APPEND-ONLY — never delete terms
# Seeded with 50+ terms on Day-1
# Referenced by all agents for consistent Korean church terminology

schema_version: "1.0"
last_updated: "2026-03-01"
updated_by: "orchestrator"
```

#### Field Definitions

| Field Path | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `schema_version` | string | yes | semver | Schema version |
| `last_updated` | string | yes | YYYY-MM-DD | Last modification date |
| `updated_by` | string | yes | non-empty | Last updater |
| `terms` | list[object] | yes | >= 50 items (Day-1 seed) | Terminology entries |
| `terms[].korean` | string | yes | non-empty, unique across all terms | Korean term |
| `terms[].english` | string | yes | non-empty | English translation |
| `terms[].context` | string | yes | non-empty | Usage context / definition |
| `terms[].category` | enum | no | `worship`, `governance`, `sacrament`, `finance`, `ministry`, `facility`, `role`, `event`, `general` | Term category |
| `terms[].denomination_specific` | string | no | denomination code (e.g., "PCK", "GAPCK", "KMC") or null | If term is denomination-specific |

**No separate validation script** — glossary validation is lightweight and embedded in the data ingestion flow. The primary constraint is append-only (no deletion), enforced by the PreToolUse hook that monitors for term removal.

#### Example Records

```yaml
terms:
  # Roles (직분)
  - korean: "목사"
    english: "pastor"
    context: "교회의 영적 지도자로서 설교, 심방, 성례를 담당하는 성직자"
    category: "role"
  - korean: "장로"
    english: "elder"
    context: "장로교 전통에서 목사와 함께 당회를 구성하는 평신도 직분"
    category: "role"
    denomination_specific: null
  - korean: "집사"
    english: "deacon"
    context: "교회 봉사와 행정을 담당하는 평신도 직분"
    category: "role"
  - korean: "권사"
    english: "deaconess"
    context: "여성 직분. 심방과 교인 돌봄 담당. 장로교 전통 특유의 직분"
    category: "role"
  - korean: "성도"
    english: "member"
    context: "직분이 없는 일반 교인. 세례 유무와 관계없이 등록 교인을 지칭"
    category: "role"

  # Governance (치리)
  - korean: "당회"
    english: "session_meeting"
    context: "담임 목사와 장로로 구성된 교회 의결 기관. 교인 징계, 예산 승인 등 중요 결정"
    category: "governance"
  - korean: "노회"
    english: "presbytery"
    context: "지역 교회들의 연합체. 장로를 임직하고 목사를 청빙하는 상위 기관"
    category: "governance"
  - korean: "총회"
    english: "general_assembly"
    context: "교단의 최고 의결 기관. 연 1회 개최"
    category: "governance"

  # Sacraments (성례)
  - korean: "세례"
    english: "baptism"
    context: "기독교 입문 성례. 유아세례(infant)와 성인세례(adult)로 구분"
    category: "sacrament"
  - korean: "유아세례"
    english: "infant_baptism"
    context: "부모의 신앙 고백에 기반하여 유아에게 베푸는 세례"
    category: "sacrament"
  - korean: "입교"
    english: "confirmation"
    context: "유아세례 받은 자가 성인이 되어 자신의 신앙을 고백하는 의식"
    category: "sacrament"
  - korean: "성찬"
    english: "communion"
    context: "빵과 포도주(포도즙)로 예수의 죽음을 기념하는 성례"
    category: "sacrament"

  # Finance (재정)
  - korean: "십일조"
    english: "tithe"
    context: "월 수입의 10분의 1을 하나님께 드리는 헌금"
    category: "finance"
  - korean: "주일헌금"
    english: "sunday_offering"
    context: "매주 주일예배 시 드리는 일반 헌금"
    category: "finance"
  - korean: "주정헌금"
    english: "pledged_annual_offering"
    context: "연초에 서약한 연간 헌금 총액을 분할하여 납부하는 헌금. 주일헌금과 별도"
    category: "finance"
  - korean: "감사헌금"
    english: "thanksgiving_offering"
    context: "특별한 감사의 계기가 있을 때 드리는 헌금"
    category: "finance"
  - korean: "선교헌금"
    english: "mission_offering"
    context: "국내외 선교 사업을 위해 지정 헌금"
    category: "finance"
  - korean: "건축헌금"
    english: "building_fund"
    context: "교회 건축/증축을 위한 특별 헌금"
    category: "finance"
  - korean: "기부금영수증"
    english: "tax_receipt"
    context: "소득세법에 따른 기부금 영수증. 연말정산 시 세액공제 대상"
    category: "finance"

  # Ministry (사역)
  - korean: "심방"
    english: "pastoral_visitation"
    context: "목사나 권사가 교인의 가정을 방문하는 목회 활동"
    category: "ministry"
  - korean: "전도"
    english: "evangelism"
    context: "비신자에게 복음을 전하는 활동"
    category: "ministry"
  - korean: "구역"
    english: "cell_group"
    context: "교인을 지역별로 나눈 소그룹 단위. 구역장이 주관"
    category: "ministry"
  - korean: "이명"
    english: "transfer"
    context: "교인이 다른 교회로 적을 옮기는 것. 이명증서 발급 필요"
    category: "ministry"

  # Worship (예배)
  - korean: "축도"
    english: "benediction"
    context: "예배 마지막에 목사가 성도에게 축복을 선포하는 의식"
    category: "worship"
  - korean: "봉헌"
    english: "offertory"
    context: "예배 중 헌금을 드리는 순서"
    category: "worship"
  - korean: "교독문"
    english: "responsive_reading"
    context: "인도자와 회중이 교대로 성경 구절을 낭독하는 순서"
    category: "worship"
  - korean: "찬양"
    english: "praise_worship"
    context: "예배 중 찬양팀이 인도하는 현대식 찬양 시간"
    category: "worship"

  # Denomination Abbreviations (교단 약어)
  - korean: "예장통합"
    english: "PCK"
    context: "Presbyterian Church of Korea (Tonghap). 한국 최대 장로교단"
    category: "governance"
  - korean: "예장합동"
    english: "GAPCK"
    context: "General Assembly of Presbyterian Church in Korea (Hapdong)"
    category: "governance"
  - korean: "기감"
    english: "KMC"
    context: "Korean Methodist Church. 한국 감리교"
    category: "governance"

  # Events (행사)
  - korean: "부활절"
    english: "easter"
    context: "예수 부활을 기념하는 절기. 춘분 후 첫 보름달 다음 일요일"
    category: "event"
  - korean: "성탄절"
    english: "christmas"
    context: "예수 탄생을 기념하는 절기. 12월 25일"
    category: "event"
  - korean: "추수감사절"
    english: "thanksgiving"
    context: "한국 교회의 추수감사절. 11월 셋째 주일 (미국과 날짜 다름)"
    category: "event"
  - korean: "부흥회"
    english: "revival_meeting"
    context: "외부 강사를 초청하여 연속으로 진행하는 특별 집회"
    category: "event"
  - korean: "수련회"
    english: "retreat"
    context: "교인들이 교회 밖에서 합숙하며 진행하는 영적 훈련 프로그램"
    category: "event"

  # Facility (시설)
  - korean: "본당"
    english: "main_sanctuary"
    context: "주일예배가 진행되는 주 예배실"
    category: "facility"
  - korean: "교육관"
    english: "education_building"
    context: "주일학교, 교육 프로그램이 진행되는 별도 건물 또는 층"
    category: "facility"
```

---

## 3. SOT Schema (church-state.yaml)

[trace:step-1:entity-church-state]

The central Single Source of Truth for the church administration system. Write access is restricted to the Orchestrator/Team Lead only (Absolute Principle 2).

```yaml
# church-state.yaml
# Central SOT — Orchestrator/Team Lead ONLY writer
# All other agents: READ-ONLY access
# Validates: validate_sot_schema() in _context_lib.py pattern

church:
  name: "새벽이슬교회 (Morning Dew Church)"
  denomination: "PCK"        # PCK | GAPCK | KMC | other
  current_bulletin_issue: 1247
  status: "active"           # active | inactive

  # Data file paths — central registry
  data_paths:
    members: "data/members.yaml"
    finance: "data/finance.yaml"
    schedule: "data/schedule.yaml"
    newcomers: "data/newcomers.yaml"
    bulletin: "data/bulletin-data.yaml"
    glossary: "data/church-glossary.yaml"

  # Active features (which workflows are enabled)
  features:
    bulletin_generation: true
    newcomer_pipeline: true
    finance_reporting: false     # Requires M2 milestone
    document_generation: false   # Requires M2 milestone
    denomination_reports: false  # Requires M3 milestone

  # Workflow states (per-feature state tracking)
  workflow_states:
    bulletin:
      last_generated_issue: 1246
      last_generated_date: "2026-02-22"
      next_due_date: "2026-03-01"
      status: "pending"         # pending | in_progress | completed | error
    newcomer:
      total_active: 11
      last_check_date: "2026-02-28"
      status: "idle"            # idle | processing | error
    finance:
      current_month: "2026-03"
      last_report_date: "2026-02-01"
      status: "disabled"        # idle | processing | disabled | error

  # System configuration
  config:
    autopilot:
      enabled: false            # Global autopilot toggle
      finance_override: false   # PERMANENTLY false — finance never auto-approved
    backup:
      enabled: true
      last_backup: "2026-02-28"
      backup_dir: "backups/"
    scale:
      max_members: 500          # Supported scale limit
      file_split_threshold: 1000 # When to split into multiple files
```

**SOT Field Summary**:

| Section | Purpose | Write Constraint |
|---------|---------|-----------------|
| `church` | Church identity and denomination | Orchestrator only |
| `data_paths` | Canonical file path registry | Orchestrator only (set once, rarely changed) |
| `features` | Feature toggle flags | Orchestrator only (milestone-gated) |
| `workflow_states` | Per-workflow execution state | Orchestrator only (updated per workflow run) |
| `config` | System-wide configuration | Orchestrator only |

---

## 4. Validation Rule Catalog

This section consolidates all validation rules with their exact Python-implementable specifications.

### 4.1 Members Validation (M1-M6)

| Rule | Description | Check Type | Severity |
|------|------------|-----------|----------|
| **M1** | All member IDs unique and match `^M\d{3,}$` | regex + set uniqueness | Critical |
| **M2** | `name` and `status` non-empty for every record | string emptiness check | Critical |
| **M3** | Phone matches `^010-\d{4}-\d{4}$` when present | regex (nullable) | High |
| **M4** | `status` in `{active, inactive, transferred, deceased}` | set membership | Critical |
| **M5** | `family_id` format `^F\d{3,}$` + group has >= 2 members | regex + group count | High |
| **M6** | All date fields valid YYYY-MM-DD; `birth_date` in past | date parsing + comparison | High |

### 4.2 Finance Validation (F1-F5)

| Rule | Description | Check Type | Severity |
|------|------------|-----------|----------|
| **F1** | Offering IDs `^OFF-\d{4}-\d{3,}$`, expense IDs `^EXP-\d{4}-\d{3,}$`, all unique | regex + set uniqueness | Critical |
| **F2** | All `amount` fields are positive integers (`> 0`, type `int`) | type + range check | Critical |
| **F3** | `offerings[].total == sum(items[].amount)` with tolerance < 1 | arithmetic equality | Critical |
| **F4** | `budget.total_budget == sum(budget.categories.values())` | arithmetic equality | Critical |
| **F5** | `monthly_summary` totals match non-void records for that month | aggregation + comparison | High |

### 4.3 Schedule Validation (S1-S5)

| Rule | Description | Check Type | Severity |
|------|------------|-----------|----------|
| **S1** | Service IDs `^SVC-[A-Z]+-?\d*$`, event IDs `^EVT-\d{4}-\d{3,}$`, booking IDs `^FAC-\d{4}-\d{3,}$`, all unique | regex + set uniqueness | Critical |
| **S2** | Time fields match `^([01]\d\|2[0-3]):[0-5]\d$` (HH:MM 24h) | regex | High |
| **S3** | `recurrence` in `{weekly, biweekly, monthly}`; `day_of_week` valid | set membership | High |
| **S4** | Event `status` in `{planned, confirmed, completed, cancelled}`; booking `status` in `{pending, confirmed, cancelled}` | set membership | High |
| **S5** | `time_end > time_start` for bookings; no overlaps for same facility on same date | string comparison + interval overlap | Medium |

### 4.4 Newcomers Validation (N1-N6)

| Rule | Description | Check Type | Severity |
|------|------------|-----------|----------|
| **N1** | All newcomer IDs unique and match `^N\d{3,}$` | regex + set uniqueness | Critical |
| **N2** | `journey_stage` in valid set + all prerequisite milestones completed | set membership + sequential check | Critical |
| **N3** | `first_visit`, milestone dates, `settled_date` are valid YYYY-MM-DD | date parsing | High |
| **N4** | `referred_by` and `assigned_to` reference existing member IDs when set | cross-file lookup | Critical |
| **N5** | If `status == "settled"` then `settled_as_member` must exist in members.yaml | cross-file + consistency | Critical |
| **N6** | `_stats.total_active == count(status == "active")` and `_stats.by_stage[stage] == count(journey_stage == stage)` | arithmetic consistency | High |

### 4.5 Bulletin Validation (B1-B3)

| Rule | Description | Check Type | Severity |
|------|------------|-----------|----------|
| **B1** | Required sections present: `issue_number`, `date`, `sermon` (with title/scripture/preacher), `worship_order` (>= 3 items) | key existence + list length | Critical |
| **B2** | `issue_number` positive, monotonically increasing, no duplicates in history | integer check + sequence check | High |
| **B3** | `celebrations.birthday[].member_id` -> valid member; `celebrations.wedding_anniversary[].family_id` -> valid family | cross-file lookup | Medium |

---

## 5. Entity ID System

[trace:step-1:entity-id-system]

All entities use a consistent ID format: a letter prefix indicating the entity type, followed by a zero-padded numeric sequence.

| Entity | Prefix | Format | Regex | Example | Sequence |
|--------|--------|--------|-------|---------|----------|
| Member | M | `M` + 3+ digits | `^M\d{3,}$` | M001, M002, M1234 | Auto-increment per file |
| Family Group | F | `F` + 3+ digits | `^F\d{3,}$` | F001, F042 | Auto-increment per file |
| Newcomer | N | `N` + 3+ digits | `^N\d{3,}$` | N001, N002 | Auto-increment per file |
| Offering | OFF | `OFF-YYYY-` + 3+ digits | `^OFF-\d{4}-\d{3,}$` | OFF-2026-001 | Per-year sequence |
| Expense | EXP | `EXP-YYYY-` + 3+ digits | `^EXP-\d{4}-\d{3,}$` | EXP-2026-001 | Per-year sequence |
| Service | SVC | `SVC-` + uppercase letters + optional digits | `^SVC-[A-Z]+-?\d*$` | SVC-SUN-1, SVC-WED | Named (stable) |
| Event | EVT | `EVT-YYYY-` + 3+ digits | `^EVT-\d{4}-\d{3,}$` | EVT-2026-001 | Per-year sequence |
| Facility Booking | FAC | `FAC-YYYY-` + 3+ digits | `^FAC-\d{4}-\d{3,}$` | FAC-2026-001 | Per-year sequence |
| Bulletin Issue | (integer) | Positive integer | `^\d+$` | 1247 | Monotonically increasing |

**ID Assignment Rules**:

1. **Immutability**: Once assigned, an ID must never be reused or changed, even if the record is soft-deleted.
2. **Auto-increment**: New IDs are assigned by finding the maximum existing numeric suffix and adding 1.
3. **Zero-padding**: IDs start with 3-digit zero-padding (M001) but may grow beyond 3 digits (M1234) as the church grows.
4. **Year-scoped IDs**: Financial records (OFF, EXP) and events (EVT, FAC) include the year to enable natural year-based filtering.

```python
import re

def next_id(existing_ids: list[str], prefix: str) -> str:
    """Generate the next ID in sequence.

    Example: next_id(["M001", "M002", "M005"], "M") -> "M006"
    """
    pattern = re.compile(rf'^{re.escape(prefix)}(\d+)$')
    max_num = 0
    for eid in existing_ids:
        match = pattern.match(eid)
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"{prefix}{max_num + 1:03d}"
```

---

## 6. Cross-Reference Architecture

[trace:step-1:cross-references]

This section maps all cross-file references and their validation enforcement.

### 6.1 Cross-Reference Map

```
                    ┌─────────────────────┐
                    │   church-state.yaml  │
                    │   (Central SOT)      │
                    │                      │
                    │  data_paths:         │
                    │   ├── members ───────┼──── data/members.yaml
                    │   ├── finance ───────┼──── data/finance.yaml
                    │   ├── schedule ──────┼──── data/schedule.yaml
                    │   ├── newcomers ─────┼──── data/newcomers.yaml
                    │   ├── bulletin ──────┼──── data/bulletin-data.yaml
                    │   └── glossary ──────┼──── data/church-glossary.yaml
                    └─────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
  newcomers.yaml       bulletin-data.yaml      finance.yaml
  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
  │ referred_by ─┼──→ │                  │    │ donor_id ────┼──→ members.yaml
  │ assigned_to ─┼──→ │ birthday         │    │ pledged      │
  │ settled_as  ─┼──→ │  .member_id ─────┼──→ │  .member_id ─┼──→ members.yaml
  └──────────────┘    │ anniversary      │    └──────────────┘
        │             │  .family_id ─────┼──→ members.yaml (family)
        │             │ issue_number ────┼──→ church-state (bulletin_issue)
        ▼             └──────────────────┘
  members.yaml                │
  (target of all              ▼
   cross-references)    schedule.yaml
                        (worship_order derivation)
```

### 6.2 Cross-Reference Validation Matrix

| Source File | Field | Target File | Target Field | Validator | Rule |
|------------|-------|-------------|--------------|-----------|------|
| newcomers.yaml | `referred_by` | members.yaml | `members[].id` | validate_newcomers.py | N4 |
| newcomers.yaml | `assigned_to` | members.yaml | `members[].id` | validate_newcomers.py | N4 |
| newcomers.yaml | `settled_as_member` | members.yaml | `members[].id` | validate_newcomers.py | N5 |
| bulletin-data.yaml | `celebrations.birthday[].member_id` | members.yaml | `members[].id` | validate_bulletin.py | B3 |
| bulletin-data.yaml | `celebrations.wedding_anniversary[].family_id` | members.yaml | `members[].family.family_id` | validate_bulletin.py | B3 |
| bulletin-data.yaml | `bulletin.issue_number` | church-state.yaml | `church.current_bulletin_issue` | validate_bulletin.py | B2 |
| finance.yaml | `offerings[].items[].donor_id` | members.yaml | `members[].id` | validate_finance.py | F1 (extended) |
| finance.yaml | `pledged_annual[].member_id` | members.yaml | `members[].id` | validate_finance.py | F1 (extended) |

### 6.3 Newcomer-to-Member Migration Flow

When a newcomer completes all 6 journey stages and reaches "settled" status, the following cross-file update occurs:

```
Step 1: newcomer-tracker creates new member record
        → member-manager writes to members.yaml
        → New member ID assigned (e.g., M252)

Step 2: newcomer-tracker updates newcomers.yaml
        → status: "settled"
        → settled_as_member: "M252"
        → settled_date: "2026-01-05"

Step 3: Orchestrator updates church-state.yaml
        → workflow_states.newcomer.total_active -= 1

Step 4: Validators confirm
        → validate_newcomers.py N5: settled_as_member exists in members.yaml ✓
        → validate_members.py M1: new member ID unique ✓
```

---

## 7. DKS Alignment Report

[trace:step-1:domain-knowledge]

This section validates that the data architecture specification aligns with the `domain-knowledge.yaml` entities and constraints.

### 7.1 Entity Alignment

| DKS Entity ID | DKS Type | Schema File | Alignment Status |
|--------------|----------|-------------|-----------------|
| `church-state` | sot | `church-state.yaml` (Section 3) | ALIGNED — all key_fields covered, writer_agent constraint matched |
| `members` | data-entity | `data/members.yaml` (Section 2.1) | ALIGNED — all key_fields covered, id_format M\d{3,} matched, soft-delete policy matched |
| `finance` | data-entity | `data/finance.yaml` (Section 2.2) | ALIGNED — all key_fields covered, void-only deletion, autopilot permanently disabled, KRW currency |
| `newcomers` | data-entity | `data/newcomers.yaml` (Section 2.4) | ALIGNED — all key_fields covered, 6-stage journey matched, stage_transition_requires_approval covered |
| `bulletin-data` | data-entity | `data/bulletin-data.yaml` (Section 2.5) | ALIGNED — all key_fields covered, weekly generation_frequency, monotonic issue_number |
| `church-glossary` | data-entity | `data/church-glossary.yaml` (Section 2.6) | ALIGNED — append-only policy, 50+ seed terms, korean uniqueness |
| `validate-members` | validation-script | Section 4.1 | ALIGNED — M1-M6 rules match DKS rules list |
| `validate-finance` | validation-script | Section 4.2 | ALIGNED — F1-F5 rules match DKS rules list |
| `validate-schedule` | validation-script | Section 4.3 | ALIGNED — S1-S5 rules match DKS rules list |
| `validate-newcomers` | validation-script | Section 4.4 | ALIGNED — N1-N6 rules match DKS rules list |

### 7.2 Constraint Alignment

| DKS Constraint | This Spec Section | Status |
|---------------|-------------------|--------|
| C01 (Member ID uniqueness) | M1 validation rule | COVERED — regex `^M\d{3,}$` + set uniqueness check |
| C02 (Financial arithmetic) | F3, F4, F5 validation rules | COVERED — tolerance < 1 for offerings, exact match for budget |
| C03 (Sequential journey stages) | N2 validation rule | COVERED — `STAGE_TO_REQUIRED_MILESTONES` mapping enforces ordering |
| C04 (Cross-entity references) | N4, N5, B3 validation rules + Section 6 | COVERED — all cross-references resolved against members.yaml |
| C05 (SOT write restriction) | Layer 1 architecture + guard_data_files.py | COVERED — Orchestrator-only write permission for church-state.yaml |
| C06 (Single writer per file) | Layer 1 `WRITE_PERMISSIONS` dict | COVERED — each file mapped to exactly one writer agent |
| C07 (No member deletion) | members.yaml header + M4 validation | COVERED — soft-delete only (status: inactive) |
| C08 (No finance deletion) | finance.yaml header + void pattern | COVERED — void: true for invalid records |
| C09 (Finance autopilot disabled) | church-state.yaml `config.autopilot.finance_override: false` | COVERED — permanently false |
| C10 (High-risk double review) | HITL controller design (referenced in PRD F-03) | COVERED — documented in Layer 1 architecture |
| C11 (Date/time/phone formats) | M3 (phone), M6 (dates), S2 (times), F2 (amounts) | COVERED — regex patterns and format checks specified |
| C12 (Glossary append-only) | church-glossary.yaml header + PreToolUse hook | COVERED — append-only enforcement |
| C13 (Bulletin issue monotonicity) | B2 validation rule | COVERED — monotonic check + duplicate detection |
| C14 (Facility no overlap) | S5 validation rule | COVERED — same-facility same-date overlap detection |

### 7.3 Pipeline Connection Assessment

[trace:step-1:pipeline-connection]

This specification provides the complete input for downstream workflow steps:

| Downstream Step | Required Input from This Spec | Provided |
|----------------|------------------------------|----------|
| **Step 7: Infrastructure Build** | Schema definitions for all 6 YAML files + church-state.yaml | YES — complete field definitions, types, constraints in Sections 2 and 3 |
| **Step 7: Infrastructure Build** | Validation rule specifications (Python-implementable) | YES — exact Python code for M1-M6, F1-F5, S1-S5, N1-N6, B1-B3 in Section 4 |
| **Step 7: Infrastructure Build** | guard_data_files.py PreToolUse hook specification | YES — WRITE_PERMISSIONS dict in Section 1.1 |
| **Step 7: Infrastructure Build** | atomic_write_yaml() utility function | YES — complete implementation in Section 1.1 |
| **Step 8: Validation Scripts** | Exact regex patterns, enum sets, arithmetic checks | YES — every validation rule includes Python code with regex constants, enum sets, and comparison logic |
| **Step 8: Validation Scripts** | Cross-file validation dependencies (which files to load) | YES — N4/N5/B3 rules specify member_ids dependency from members.yaml |
| **Step 8: Validation Scripts** | JSON output format specification | YES — `{"valid": bool, "errors": [...], "warnings": [...]}` |
| **Agent Development** | Field definitions for each agent's data domain | YES — each schema section specifies the writer agent and full field spec |
| **Glossary Seeding** | Day-1 glossary structure and seed terms | YES — 30+ terms provided in Section 2.6 as starting template |

---

*End of Data Architecture Specification*

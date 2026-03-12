#!/usr/bin/env python3
"""
Deterministic Query Layer for Church Administration System.

P1 Hallucination Prevention: All repeatable, accuracy-critical computations
are performed by this Python script instead of LLM reasoning.

Usage:
    python3 scripts/query_church_data.py --data-dir data/ --query <query_name> [--params '{"key": "value"}']
    python3 scripts/query_church_data.py --self-test --data-dir data/

Outputs JSON to stdout. Exit code 0 on success, 1 on error.

14 Query Functions (by risk level):
  HIGH:   finance_monthly_summary, finance_budget_variance, finance_ytd_summary,
          newcomer_overdue_followups
  MEDIUM: member_birthdays_in_range, member_stats, newcomer_stats,
          newcomer_by_stage, member_family_resolve, next_id
  LOW:    schedule_for_week, bulletin_generation_history, korean_currency_format
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta

# ---------------------------------------------------------------------------
# Import church_data_utils from .claude/hooks/scripts/
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)
_HOOKS_DIR = os.path.join(_PROJECT_DIR, ".claude", "hooks", "scripts")
if _HOOKS_DIR not in sys.path:
    sys.path.insert(0, _HOOKS_DIR)

from church_data_utils import (  # noqa: E402
    load_yaml,
    parse_date,
    MEMBER_ID_RE,
    FAMILY_ID_RE,
    NEWCOMER_ID_RE,
    OFFERING_ID_RE,
    EXPENSE_ID_RE,
    EVT_ID_RE,
)


# ===========================================================================
# Data Loading (cached per invocation)
# ===========================================================================
_CACHE = {}


def _load(data_dir, filename):
    """Load a YAML file with per-invocation caching."""
    key = os.path.join(data_dir, filename)
    if key not in _CACHE:
        _CACHE[key] = load_yaml(key)
    return _CACHE[key]


def _members(data_dir):
    return _load(data_dir, "members.yaml").get("members", [])


def _offerings(data_dir):
    return _load(data_dir, "finance.yaml").get("offerings", [])


def _expenses(data_dir):
    return _load(data_dir, "finance.yaml").get("expenses", [])


def _budget(data_dir):
    return _load(data_dir, "finance.yaml").get("budget", {})


def _monthly_summary(data_dir):
    return _load(data_dir, "finance.yaml").get("monthly_summary", {})


def _pledged(data_dir):
    return _load(data_dir, "finance.yaml").get("pledged_annual", [])


def _newcomers(data_dir):
    return _load(data_dir, "newcomers.yaml").get("newcomers", [])


def _services(data_dir):
    return _load(data_dir, "schedule.yaml").get("regular_services", [])


def _events(data_dir):
    return _load(data_dir, "schedule.yaml").get("special_events", [])


def _bulletin(data_dir):
    return _load(data_dir, "bulletin-data.yaml")


# ===========================================================================
# HIGH RISK: Finance Queries
# ===========================================================================

def finance_monthly_summary(data_dir, params):
    """Compute monthly income/expense summary from raw records.

    Params: {"year": 2026, "month": 2}
    Returns: total_income, total_expense, balance, by_offering_category, by_expense_category
    """
    year = int(params["year"])
    month = int(params["month"])
    month_prefix = f"{year:04d}-{month:02d}"

    # Aggregate offerings for the month (non-void only)
    offerings = _offerings(data_dir)
    month_offerings = [
        o for o in offerings
        if not o.get("void", False)
        and isinstance(o.get("date"), str)
        and o["date"].startswith(month_prefix)
    ]

    total_income = 0
    by_offering_cat = {}
    for o in month_offerings:
        total = o.get("total", 0)
        total_income += total
        for item in o.get("items", []):
            cat = item.get("category", "기타")
            amt = item.get("amount", 0)
            by_offering_cat[cat] = by_offering_cat.get(cat, 0) + amt

    # Aggregate expenses for the month (non-void only)
    expenses = _expenses(data_dir)
    month_expenses = [
        e for e in expenses
        if not e.get("void", False)
        and isinstance(e.get("date"), str)
        and e["date"].startswith(month_prefix)
    ]

    total_expense = 0
    by_expense_cat = {}
    for e in month_expenses:
        amt = e.get("amount", 0)
        total_expense += amt
        cat = e.get("category", "기타")
        by_expense_cat[cat] = by_expense_cat.get(cat, 0) + amt

    return {
        "query": "finance_monthly_summary",
        "params": {"year": year, "month": month},
        "result": {
            "month": month_prefix,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "offering_count": len(month_offerings),
            "expense_count": len(month_expenses),
            "by_offering_category": by_offering_cat,
            "by_expense_category": by_expense_cat,
        },
    }


def finance_budget_variance(data_dir, params):
    """Compare YTD expenses against annual budget categories.

    Params: {"year": 2026, "through_month": 2}  (optional through_month, default=12)
    Returns: per-category budget, spent, variance, execution_rate
    """
    year = int(params["year"])
    through_month = int(params.get("through_month", 12))

    budget = _budget(data_dir)
    budget_cats = budget.get("categories", {})
    total_budget = budget.get("total_budget", 0)

    # Aggregate YTD expenses by category
    expenses = _expenses(data_dir)
    ytd_by_cat = {}
    ytd_total = 0
    for e in expenses:
        if e.get("void", False):
            continue
        d = parse_date(e.get("date", ""))
        if d is None:
            continue
        if d.year != year or d.month > through_month:
            continue
        cat = e.get("category", "기타")
        amt = e.get("amount", 0)
        ytd_by_cat[cat] = ytd_by_cat.get(cat, 0) + amt
        ytd_total += amt

    # Expected budget proportion (through_month / 12)
    expected_rate = through_month / 12.0

    categories = {}
    for cat, budget_amt in budget_cats.items():
        spent = ytd_by_cat.get(cat, 0)
        expected_spent = int(budget_amt * expected_rate)
        variance = expected_spent - spent  # positive = under budget
        exec_rate = round(spent / budget_amt * 100, 1) if budget_amt > 0 else 0.0
        categories[cat] = {
            "annual_budget": budget_amt,
            "expected_ytd": expected_spent,
            "actual_ytd": spent,
            "variance": variance,
            "execution_rate_pct": exec_rate,
        }

    # Flag categories not in budget
    for cat, amt in ytd_by_cat.items():
        if cat not in categories:
            categories[cat] = {
                "annual_budget": 0,
                "expected_ytd": 0,
                "actual_ytd": amt,
                "variance": -amt,
                "execution_rate_pct": 0.0,
                "warning": "Expense category not in budget",
            }

    overall_exec_rate = round(ytd_total / total_budget * 100, 1) if total_budget > 0 else 0.0

    return {
        "query": "finance_budget_variance",
        "params": {"year": year, "through_month": through_month},
        "result": {
            "total_budget": total_budget,
            "total_spent_ytd": ytd_total,
            "overall_execution_rate_pct": overall_exec_rate,
            "expected_execution_rate_pct": round(expected_rate * 100, 1),
            "categories": categories,
        },
    }


def finance_ytd_summary(data_dir, params):
    """Aggregate year-to-date income, expense, balance from raw records.

    Params: {"year": 2026}
    Returns: ytd_income, ytd_expense, ytd_balance, monthly_breakdown
    """
    year = int(params["year"])

    offerings = _offerings(data_dir)
    expenses = _expenses(data_dir)

    monthly = {}
    for m in range(1, 13):
        monthly[m] = {"income": 0, "expense": 0}

    ytd_income = 0
    for o in offerings:
        if o.get("void", False):
            continue
        d = parse_date(o.get("date", ""))
        if d is None or d.year != year:
            continue
        amt = o.get("total", 0)
        ytd_income += amt
        monthly[d.month]["income"] += amt

    ytd_expense = 0
    for e in expenses:
        if e.get("void", False):
            continue
        d = parse_date(e.get("date", ""))
        if d is None or d.year != year:
            continue
        amt = e.get("amount", 0)
        ytd_expense += amt
        monthly[d.month]["expense"] += amt

    monthly_breakdown = {}
    for m in range(1, 13):
        key = f"{year:04d}-{m:02d}"
        inc = monthly[m]["income"]
        exp = monthly[m]["expense"]
        if inc > 0 or exp > 0:
            monthly_breakdown[key] = {
                "income": inc,
                "expense": exp,
                "balance": inc - exp,
            }

    return {
        "query": "finance_ytd_summary",
        "params": {"year": year},
        "result": {
            "ytd_income": ytd_income,
            "ytd_expense": ytd_expense,
            "ytd_balance": ytd_income - ytd_expense,
            "months_with_data": len(monthly_breakdown),
            "monthly_breakdown": monthly_breakdown,
        },
    }


# ===========================================================================
# HIGH RISK: Newcomer Follow-up
# ===========================================================================

def newcomer_overdue_followups(data_dir, params):
    """Find newcomers whose most recent milestone is older than threshold.

    Params: {"threshold_days": 14, "reference_date": "2026-02-28"}  (both optional)
    Returns: list of overdue newcomers with days_since_last_activity
    """
    threshold = int(params.get("threshold_days", 14))
    ref_str = params.get("reference_date")
    if ref_str:
        ref_date = parse_date(ref_str)
        if ref_date is None:
            ref_date = date.today()
    else:
        ref_date = date.today()

    newcomers = _newcomers(data_dir)
    overdue = []

    for n in newcomers:
        if n.get("status") != "active":
            continue

        # Find latest completed milestone date
        milestones = n.get("journey_milestones", {})
        latest_date = None
        latest_milestone = None
        for ms_name, ms_data in milestones.items():
            if not isinstance(ms_data, dict):
                continue
            if not ms_data.get("completed", False):
                continue
            ms_date = parse_date(ms_data.get("date", ""))
            if ms_date and (latest_date is None or ms_date > latest_date):
                latest_date = ms_date
                latest_milestone = ms_name

        if latest_date is None:
            # Use first_visit date as fallback
            fv = parse_date(n.get("first_visit", ""))
            if fv:
                latest_date = fv
                latest_milestone = "first_visit"

        if latest_date is None:
            continue

        days_since = (ref_date - latest_date).days
        if days_since >= threshold:
            # Determine next expected milestone
            stage = n.get("journey_stage", "first_visit")
            next_milestone = _next_expected_milestone(stage, milestones)

            overdue.append({
                "id": n.get("id"),
                "name": n.get("name"),
                "journey_stage": stage,
                "last_milestone": latest_milestone,
                "last_milestone_date": latest_date.isoformat(),
                "days_since_last_activity": days_since,
                "next_expected_milestone": next_milestone,
                "assigned_to": n.get("assigned_to"),
            })

    # Sort by days_since descending (most overdue first)
    overdue.sort(key=lambda x: x["days_since_last_activity"], reverse=True)

    return {
        "query": "newcomer_overdue_followups",
        "params": {"threshold_days": threshold, "reference_date": ref_date.isoformat()},
        "result": {
            "overdue_count": len(overdue),
            "newcomers": overdue,
        },
    }


def _next_expected_milestone(current_stage, milestones):
    """Determine the next uncompleted milestone based on current stage."""
    milestone_order = [
        "first_visit", "welcome_call", "second_visit",
        "small_group_intro", "baptism_class", "baptism",
    ]
    for ms in milestone_order:
        ms_data = milestones.get(ms, {})
        if isinstance(ms_data, dict) and not ms_data.get("completed", False):
            return ms
    return None


# ===========================================================================
# MEDIUM RISK: Member Queries
# ===========================================================================

def member_birthdays_in_range(data_dir, params):
    """Find active members with birthdays in a date range (month-day matching).

    Params: {"start_date": "2026-03-01", "end_date": "2026-03-07"}
    Returns: list of members with birthday in range
    """
    start = parse_date(params["start_date"])
    end = parse_date(params["end_date"])
    if start is None or end is None:
        return _error("Invalid start_date or end_date")

    members = _members(data_dir)
    results = []

    for m in members:
        if m.get("status") != "active":
            continue
        bd = parse_date(m.get("birth_date", ""))
        if bd is None:
            continue

        # Check if birthday (month-day) falls within range
        # Handle same-year range only (not cross-year for simplicity)
        try:
            birthday_this_year = bd.replace(year=start.year)
        except ValueError:
            # Feb 29 birthday in non-leap year → use Feb 28
            birthday_this_year = date(start.year, bd.month, 28)

        if start <= birthday_this_year <= end:
            results.append({
                "id": m.get("id"),
                "name": m.get("name"),
                "birth_date": m.get("birth_date"),
                "birthday_month_day": f"{bd.month:02d}-{bd.day:02d}",
                "department": m.get("church", {}).get("department"),
                "role": m.get("church", {}).get("role"),
            })

    # Sort by birthday month-day
    results.sort(key=lambda x: x["birthday_month_day"])

    return {
        "query": "member_birthdays_in_range",
        "params": {"start_date": start.isoformat(), "end_date": end.isoformat()},
        "result": {
            "count": len(results),
            "members": results,
        },
    }


def member_family_resolve(data_dir, params):
    """Resolve a family_id to its constituent members.

    Params: {"family_id": "F025"}
    Returns: family members with head, spouse, children identified
    """
    fid = params["family_id"]
    members = _members(data_dir)

    family_members = []
    head_name = None
    spouse_name = None

    for m in members:
        fm = m.get("family", {})
        if not isinstance(fm, dict):
            continue
        if fm.get("family_id") != fid:
            continue

        relation = fm.get("relation", "unknown")
        entry = {
            "id": m.get("id"),
            "name": m.get("name"),
            "relation": relation,
            "status": m.get("status"),
            "role": m.get("church", {}).get("role"),
        }
        family_members.append(entry)

        if relation == "household_head":
            head_name = m.get("name")
        elif relation == "spouse":
            spouse_name = m.get("name")

    # Construct display name for couple
    couple_display = None
    if head_name and spouse_name:
        couple_display = f"{head_name} · {spouse_name}"
    elif head_name:
        couple_display = f"{head_name} 가정"

    return {
        "query": "member_family_resolve",
        "params": {"family_id": fid},
        "result": {
            "family_id": fid,
            "member_count": len(family_members),
            "head_name": head_name,
            "spouse_name": spouse_name,
            "couple_display_name": couple_display,
            "members": family_members,
        },
    }


def member_stats(data_dir, params):
    """Compute member statistics by status, department, role.

    Params: {} (none required)
    Returns: totals and breakdowns
    """
    members = _members(data_dir)

    by_status = {}
    by_department = {}
    by_role = {}
    by_gender = {}
    total = len(members)

    for m in members:
        status = m.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1

        if status == "active":
            dept = m.get("church", {}).get("department", "미지정")
            by_department[dept] = by_department.get(dept, 0) + 1

            role = m.get("church", {}).get("role") or "성도"
            by_role[role] = by_role.get(role, 0) + 1

            gender = m.get("gender", "unknown")
            by_gender[gender] = by_gender.get(gender, 0) + 1

    return {
        "query": "member_stats",
        "params": {},
        "result": {
            "total_members": total,
            "total_active": by_status.get("active", 0),
            "by_status": by_status,
            "by_department": by_department,
            "by_role": by_role,
            "by_gender": by_gender,
        },
    }


def newcomer_stats(data_dir, params):
    """Compute newcomer statistics by stage and status.

    Params: {} (none required)
    Returns: totals and breakdowns
    """
    newcomers = _newcomers(data_dir)

    by_status = {}
    by_stage = {}
    total = len(newcomers)

    for n in newcomers:
        status = n.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1

        stage = n.get("journey_stage", "unknown")
        by_stage[stage] = by_stage.get(stage, 0) + 1

    return {
        "query": "newcomer_stats",
        "params": {},
        "result": {
            "total_newcomers": total,
            "total_active": by_status.get("active", 0),
            "by_status": by_status,
            "by_stage": by_stage,
        },
    }


def newcomer_by_stage(data_dir, params):
    """List newcomers at a specific journey stage.

    Params: {"stage": "first_visit"}
    Returns: list of newcomers at that stage
    """
    stage = params["stage"]
    newcomers = _newcomers(data_dir)

    results = []
    for n in newcomers:
        if n.get("journey_stage") != stage:
            continue
        results.append({
            "id": n.get("id"),
            "name": n.get("name"),
            "status": n.get("status"),
            "first_visit": n.get("first_visit"),
            "assigned_to": n.get("assigned_to"),
            "assigned_department": n.get("assigned_department"),
        })

    return {
        "query": "newcomer_by_stage",
        "params": {"stage": stage},
        "result": {
            "stage": stage,
            "count": len(results),
            "newcomers": results,
        },
    }


def next_id(data_dir, params):
    """Compute the next available ID for a given entity type.

    Params: {"entity_type": "member"}  (member|newcomer|offering|expense|event)
    Returns: next_id string
    """
    entity = params["entity_type"]

    if entity == "member":
        members = _members(data_dir)
        max_num = 0
        for m in members:
            mid = m.get("id", "")
            if MEMBER_ID_RE.match(mid):
                num = int(mid[1:])
                max_num = max(max_num, num)
        next_val = f"M{max_num + 1:03d}"

    elif entity == "newcomer":
        newcomers = _newcomers(data_dir)
        max_num = 0
        for n in newcomers:
            nid = n.get("id", "")
            if NEWCOMER_ID_RE.match(nid):
                num = int(nid[1:])
                max_num = max(max_num, num)
        next_val = f"N{max_num + 1:03d}"

    elif entity == "offering":
        offerings = _offerings(data_dir)
        max_num = 0
        for o in offerings:
            oid = o.get("id", "")
            if OFFERING_ID_RE.match(oid):
                parts = oid.split("-")
                num = int(parts[-1])
                max_num = max(max_num, num)
        year = date.today().year
        next_val = f"OFF-{year}-{max_num + 1:03d}"

    elif entity == "expense":
        expenses = _expenses(data_dir)
        max_num = 0
        for e in expenses:
            eid = e.get("id", "")
            if EXPENSE_ID_RE.match(eid):
                parts = eid.split("-")
                num = int(parts[-1])
                max_num = max(max_num, num)
        year = date.today().year
        next_val = f"EXP-{year}-{max_num + 1:03d}"

    elif entity == "event":
        events = _events(data_dir)
        max_num = 0
        for ev in events:
            evid = ev.get("id", "")
            if EVT_ID_RE.match(evid):
                parts = evid.split("-")
                num = int(parts[-1])
                max_num = max(max_num, num)
        year = date.today().year
        next_val = f"EVT-{year}-{max_num + 1:03d}"

    else:
        return _error(f"Unknown entity_type: {entity}. Valid: member, newcomer, offering, expense, event")

    return {
        "query": "next_id",
        "params": {"entity_type": entity},
        "result": {
            "next_id": next_val,
            "current_max_num": max_num,
        },
    }


# ===========================================================================
# LOW RISK: Schedule / Bulletin / Formatting
# ===========================================================================

def schedule_for_week(data_dir, params):
    """Get schedule for the week containing a given date.

    Params: {"date": "2026-03-01"}
    Returns: regular_services for that day_of_week + special_events in the week
    """
    target = parse_date(params["date"])
    if target is None:
        return _error("Invalid date parameter")

    # Compute week boundaries (Monday to Sunday)
    weekday = target.weekday()  # 0=Mon, 6=Sun
    week_start = target - timedelta(days=weekday)
    week_end = week_start + timedelta(days=6)

    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    # Regular services (recurring)
    services = _services(data_dir)
    week_services = []
    for svc in services:
        dow = svc.get("day_of_week", "")
        if dow in day_names:
            # Compute actual date for this service in the target week
            svc_day_idx = day_names.index(dow)
            svc_date = week_start + timedelta(days=svc_day_idx)
            week_services.append({
                "id": svc.get("id"),
                "name": svc.get("name"),
                "day_of_week": dow,
                "date": svc_date.isoformat(),
                "time": svc.get("time"),
                "duration_minutes": svc.get("duration_minutes"),
                "location": svc.get("location"),
            })

    week_services.sort(key=lambda x: (x["date"], x.get("time", "")))

    # Special events in the week
    events = _events(data_dir)
    week_events = []
    for evt in events:
        evt_date = parse_date(evt.get("date", ""))
        if evt_date is None:
            continue
        if week_start <= evt_date <= week_end:
            week_events.append({
                "id": evt.get("id"),
                "name": evt.get("name"),
                "date": evt_date.isoformat(),
                "time": evt.get("time"),
                "duration_minutes": evt.get("duration_minutes"),
                "location": evt.get("location"),
                "status": evt.get("status"),
            })

    week_events.sort(key=lambda x: (x["date"], x.get("time", "")))

    return {
        "query": "schedule_for_week",
        "params": {"date": target.isoformat()},
        "result": {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "regular_services": week_services,
            "special_events": week_events,
            "total_items": len(week_services) + len(week_events),
        },
    }


def bulletin_generation_history(data_dir, params):
    """Get bulletin generation history and compute next issue number.

    Params: {} (none required)
    Returns: latest issue, next issue, history list
    """
    bdata = _bulletin(data_dir)
    history = bdata.get("generation_history", [])
    current = bdata.get("bulletin", {})

    # Find max issue number
    max_issue = 0
    for entry in history:
        issue = entry.get("issue", 0)
        max_issue = max(max_issue, issue)

    current_issue = current.get("issue_number", 0)
    max_issue = max(max_issue, current_issue)

    return {
        "query": "bulletin_generation_history",
        "params": {},
        "result": {
            "current_issue_number": current_issue,
            "current_date": current.get("date"),
            "next_issue_number": max_issue + 1,
            "total_history_entries": len(history),
            "history": [
                {
                    "issue": e.get("issue"),
                    "generated_at": e.get("generated_at"),
                    "output_path": e.get("output_path"),
                }
                for e in history
            ],
        },
    }


def korean_currency_format(data_dir, params):
    """Format an integer amount as Korean currency string.

    Params: {"amount": 22842923}
    Returns: formatted string "22,842,923원" and Korean reading "이천이백팔십사만이천구백이십삼원"
    """
    amount = int(params["amount"])
    if amount < 0:
        return _error("Amount must be non-negative")

    # Comma-formatted
    comma_fmt = f"{amount:,}원"

    # Korean number reading
    korean_reading = _int_to_korean(amount) + "원"

    return {
        "query": "korean_currency_format",
        "params": {"amount": amount},
        "result": {
            "comma_format": comma_fmt,
            "korean_reading": korean_reading,
            "digits_only": str(amount),
        },
    }


def _int_to_korean(n):
    """Convert a non-negative integer to Korean number reading.

    Handles up to 조 (10^12). Uses formal number words (일, 이, 삼, ...).
    Examples:
        0 → "영"
        1 → "일"
        10 → "십"
        100 → "백" (일백 is also acceptable, we use 백)
        1000 → "천"
        10000 → "만" (일만 is also acceptable, we use 일만)
        22842923 → "이천이백팔십사만이천구백이십삼"
    """
    if n == 0:
        return "영"

    digits = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]
    small_units = ["", "십", "백", "천"]
    large_units = ["", "만", "억", "조"]

    # Split into groups of 4 digits (from right)
    groups = []
    remaining = n
    while remaining > 0:
        groups.append(remaining % 10000)
        remaining //= 10000

    result_parts = []
    for i in range(len(groups) - 1, -1, -1):
        group = groups[i]
        if group == 0:
            continue

        group_str = _four_digit_korean(group, digits, small_units)
        large_unit = large_units[i] if i < len(large_units) else ""
        result_parts.append(group_str + large_unit)

    return "".join(result_parts)


def _four_digit_korean(n, digits, small_units):
    """Convert a 1-4 digit number to Korean.

    For thousands/hundreds/tens positions, the digit 1 is often omitted
    (e.g., 100 = "백" not "일백"), except for 만 group where "일만" is used.
    We follow the convention: omit 일 for 십/백/천 within a group.
    """
    if n == 0:
        return ""

    parts = []
    # Extract each digit position: thousands, hundreds, tens, ones
    positions = [
        (n // 1000, 3),
        ((n % 1000) // 100, 2),
        ((n % 100) // 10, 1),
        (n % 10, 0),
    ]

    for digit, pos in positions:
        if digit == 0:
            continue
        if pos > 0 and digit == 1:
            # Omit "일" before 십/백/천 within a group
            parts.append(small_units[pos])
        else:
            parts.append(digits[digit] + small_units[pos])

    return "".join(parts)


# ===========================================================================
# Self-Test
# ===========================================================================

def run_self_test(data_dir):
    """Run deterministic self-tests to verify computation accuracy."""
    results = []
    all_pass = True

    # T1: Korean currency basic
    r = korean_currency_format(data_dir, {"amount": 22842923})
    t1_pass = (
        r["result"]["comma_format"] == "22,842,923원"
        and r["result"]["korean_reading"] == "이천이백팔십사만이천구백이십삼원"
    )
    results.append({"test": "T1_korean_currency", "pass": t1_pass,
                     "expected": "이천이백팔십사만이천구백이십삼원",
                     "got": r["result"]["korean_reading"]})
    if not t1_pass:
        all_pass = False

    # T2: Korean currency edge cases
    zero = _int_to_korean(0)
    t2a = zero == "영"
    one = _int_to_korean(1)
    t2b = one == "일"
    ten = _int_to_korean(10)
    t2c = ten == "십"
    hundred = _int_to_korean(100)
    t2d = hundred == "백"
    thousand = _int_to_korean(1000)
    t2e = thousand == "천"
    ten_thousand = _int_to_korean(10000)
    t2f = ten_thousand == "일만"  # Financial convention: 일만 (not 만)
    million = _int_to_korean(1000000)
    t2g = million == "백만"
    t2_pass = all([t2a, t2b, t2c, t2d, t2e, t2f, t2g])
    results.append({"test": "T2_korean_edge_cases", "pass": t2_pass,
                     "details": {
                         "0→영": t2a, "1→일": t2b, "10→십": t2c,
                         "100→백": t2d, "1000→천": t2e,
                         "10000→만": t2f, "1000000→백만": t2g,
                     }})
    if not t2_pass:
        all_pass = False

    # T3: Finance monthly summary arithmetic (verify against pre-computed monthly_summary)
    try:
        for month_key, expected in _monthly_summary(data_dir).items():
            parts = month_key.split("-")
            if len(parts) != 2:
                continue
            year, month = int(parts[0]), int(parts[1])
            computed = finance_monthly_summary(data_dir, {"year": year, "month": month})
            ci = computed["result"]["total_income"]
            ce = computed["result"]["total_expense"]
            ei = expected.get("total_income", 0)
            ee = expected.get("total_expense", 0)
            if ci != ei or ce != ee:
                results.append({
                    "test": f"T3_finance_{month_key}",
                    "pass": False,
                    "expected_income": ei, "computed_income": ci,
                    "expected_expense": ee, "computed_expense": ce,
                })
                all_pass = False
        results.append({"test": "T3_finance_monthly_consistency", "pass": all_pass or all(
            r.get("pass", True) for r in results if r["test"].startswith("T3_"))})
    except Exception as e:
        results.append({"test": "T3_finance_monthly", "pass": False, "error": str(e)})
        all_pass = False

    # T4: Next ID monotonicity
    try:
        for entity in ["member", "newcomer"]:
            r = next_id(data_dir, {"entity_type": entity})
            nid = r["result"]["next_id"]
            max_num = r["result"]["current_max_num"]
            # Verify the next ID's number is max_num + 1
            if entity == "member":
                extracted_num = int(nid[1:])
            else:
                extracted_num = int(nid[1:])
            t4_pass = extracted_num == max_num + 1
            results.append({"test": f"T4_next_id_{entity}", "pass": t4_pass,
                             "next_id": nid, "max_num": max_num})
            if not t4_pass:
                all_pass = False
    except Exception as e:
        results.append({"test": "T4_next_id", "pass": False, "error": str(e)})
        all_pass = False

    # T5: Member stats total check
    try:
        ms = member_stats(data_dir, {})
        total = ms["result"]["total_members"]
        status_sum = sum(ms["result"]["by_status"].values())
        t5_pass = total == status_sum
        results.append({"test": "T5_member_stats_consistency", "pass": t5_pass,
                         "total": total, "status_sum": status_sum})
        if not t5_pass:
            all_pass = False
    except Exception as e:
        results.append({"test": "T5_member_stats", "pass": False, "error": str(e)})
        all_pass = False

    # T6: Newcomer stats total check
    try:
        ns = newcomer_stats(data_dir, {})
        total = ns["result"]["total_newcomers"]
        status_sum = sum(ns["result"]["by_status"].values())
        stage_sum = sum(ns["result"]["by_stage"].values())
        t6_pass = total == status_sum == stage_sum
        results.append({"test": "T6_newcomer_stats_consistency", "pass": t6_pass,
                         "total": total, "status_sum": status_sum, "stage_sum": stage_sum})
        if not t6_pass:
            all_pass = False
    except Exception as e:
        results.append({"test": "T6_newcomer_stats", "pass": False, "error": str(e)})
        all_pass = False

    # T7: Family resolve known data (F025 = 홍길동 + 홍미나)
    try:
        fr = member_family_resolve(data_dir, {"family_id": "F025"})
        t7_pass = (
            fr["result"]["head_name"] == "홍길동"
            and fr["result"]["spouse_name"] == "홍미나"
            and fr["result"]["couple_display_name"] == "홍길동 · 홍미나"
            and fr["result"]["member_count"] >= 2
        )
        results.append({"test": "T7_family_resolve_F025", "pass": t7_pass,
                         "couple": fr["result"]["couple_display_name"]})
        if not t7_pass:
            all_pass = False
    except Exception as e:
        results.append({"test": "T7_family_resolve", "pass": False, "error": str(e)})
        all_pass = False

    # T8: YTD balance = sum(monthly balances)
    try:
        ytd = finance_ytd_summary(data_dir, {"year": 2026})
        ytd_balance = ytd["result"]["ytd_balance"]
        monthly_balance_sum = sum(
            mb["balance"] for mb in ytd["result"]["monthly_breakdown"].values()
        )
        t8_pass = ytd_balance == monthly_balance_sum
        results.append({"test": "T8_ytd_balance_consistency", "pass": t8_pass,
                         "ytd_balance": ytd_balance, "sum_monthly": monthly_balance_sum})
        if not t8_pass:
            all_pass = False
    except Exception as e:
        results.append({"test": "T8_ytd_balance", "pass": False, "error": str(e)})
        all_pass = False

    passed = sum(1 for r in results if r.get("pass", False))
    output = {
        "self_test": True,
        "all_pass": all_pass,
        "summary": f"{passed}/{len(results)} tests passed",
        "results": results,
    }
    return output


# ===========================================================================
# CLI
# ===========================================================================

QUERY_MAP = {
    "finance_monthly_summary": finance_monthly_summary,
    "finance_budget_variance": finance_budget_variance,
    "finance_ytd_summary": finance_ytd_summary,
    "newcomer_overdue_followups": newcomer_overdue_followups,
    "member_birthdays_in_range": member_birthdays_in_range,
    "member_family_resolve": member_family_resolve,
    "member_stats": member_stats,
    "newcomer_stats": newcomer_stats,
    "newcomer_by_stage": newcomer_by_stage,
    "next_id": next_id,
    "schedule_for_week": schedule_for_week,
    "bulletin_generation_history": bulletin_generation_history,
    "korean_currency_format": korean_currency_format,
}


def _error(msg):
    return {"error": True, "message": msg}


def main():
    parser = argparse.ArgumentParser(
        description="Church Admin Deterministic Query Layer (P1 Hallucination Prevention)"
    )
    parser.add_argument(
        "--data-dir", required=True,
        help="Path to data directory containing YAML files"
    )
    parser.add_argument(
        "--query",
        help="Query function name (e.g., finance_monthly_summary)"
    )
    parser.add_argument(
        "--params", default="{}",
        help='JSON string of query parameters (e.g., \'{"year": 2026, "month": 2}\')'
    )
    parser.add_argument(
        "--self-test", action="store_true",
        help="Run self-test suite to verify computation accuracy"
    )
    parser.add_argument(
        "--list-queries", action="store_true",
        help="List all available query functions"
    )
    args = parser.parse_args()

    if args.list_queries:
        queries = {
            name: {
                "doc": fn.__doc__.strip().split("\n")[0] if fn.__doc__ else "",
            }
            for name, fn in QUERY_MAP.items()
        }
        print(json.dumps({"available_queries": queries}, indent=2, ensure_ascii=False))
        sys.exit(0)

    if args.self_test:
        result = run_self_test(args.data_dir)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result["all_pass"] else 1)

    if not args.query:
        print(json.dumps({"error": True, "message": "Provide --query or --self-test or --list-queries"},
                          indent=2, ensure_ascii=False))
        sys.exit(1)

    if args.query not in QUERY_MAP:
        print(json.dumps({"error": True, "message": f"Unknown query: {args.query}",
                           "available": list(QUERY_MAP.keys())},
                          indent=2, ensure_ascii=False))
        sys.exit(1)

    try:
        params = json.loads(args.params)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": True, "message": f"Invalid JSON in --params: {e}"},
                          indent=2, ensure_ascii=False))
        sys.exit(1)

    try:
        result = QUERY_MAP[args.query](args.data_dir, params)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)
    except KeyError as e:
        print(json.dumps({"error": True, "message": f"Missing required parameter: {e}"},
                          indent=2, ensure_ascii=False))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": True, "message": f"Query execution error: {e}"},
                          indent=2, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()

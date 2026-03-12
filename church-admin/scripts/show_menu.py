#!/usr/bin/env python3
"""
show_menu.py — Church Administration System Context-Aware Menu Generator

Reads state.yaml + data files and produces a structured JSON output
containing: current status summary, pending alerts (prioritized),
and menu options ordered by urgency.

This script is the P1 deterministic backbone of the /start command.
Claude calls this FIRST, then uses its output to drive AskUserQuestion.

Usage:
    python3 scripts/show_menu.py [--data-dir data/] [--state state.yaml]

Output: JSON to stdout
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta

import yaml


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FOLLOWUP_OVERDUE_DAYS = 14
BULLETIN_ADVANCE_DAYS = 7  # days before Sunday to check if bulletin exists


def _load(path: str):
    """Load a YAML file, return None on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def _next_sunday(from_date: date | None = None) -> date:
    """Return the next Sunday (or today if today is Sunday)."""
    d = from_date or date.today()
    days_ahead = 6 - d.weekday()  # Monday=0, Sunday=6
    if days_ahead < 0:
        days_ahead += 7
    if days_ahead == 0 and d.weekday() == 6:
        return d
    return d + timedelta(days=days_ahead)


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(str(s), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Data Collectors
# ---------------------------------------------------------------------------

def _collect_member_stats(data_dir: str) -> dict:
    """Collect member counts by status."""
    data = _load(os.path.join(data_dir, "members.yaml"))
    if not data or "members" not in data:
        return {"total": 0, "active": 0, "error": "members.yaml not found"}
    members = data["members"]
    total = len(members)
    active = sum(1 for m in members if m.get("status") == "active")
    return {"total": total, "active": active}


def _collect_newcomer_stats(data_dir: str) -> dict:
    """Collect newcomer counts + overdue follow-ups."""
    data = _load(os.path.join(data_dir, "newcomers.yaml"))
    if not data or "newcomers" not in data:
        return {"total": 0, "active": 0, "overdue": [], "error": "newcomers.yaml not found"}
    newcomers = data["newcomers"]
    active = [n for n in newcomers if n.get("status") == "active"]
    today = date.today()
    overdue = []
    for n in active:
        first_visit = _parse_date(n.get("first_visit"))
        if first_visit and (today - first_visit).days > FOLLOWUP_OVERDUE_DAYS:
            # Check if follow-up milestone is done
            milestones = n.get("journey_milestones", {})
            followup_2wk = milestones.get("followup_2wk", {})
            if not followup_2wk.get("completed", False):
                overdue.append({
                    "id": n.get("id"),
                    "name": n.get("name"),
                    "days_since_visit": (today - first_visit).days,
                    "stage": n.get("journey_stage"),
                })
    return {"total": len(newcomers), "active": len(active), "overdue": overdue}


def _collect_bulletin_status(data_dir: str, state: dict) -> dict:
    """Check if upcoming Sunday's bulletin is generated."""
    bulletin_data = _load(os.path.join(data_dir, "bulletin-data.yaml"))
    next_sun = _next_sunday()

    ws = state.get("church", {}).get("workflow_states", {}).get("bulletin", {})
    last_issue = ws.get("last_generated_issue", 0)
    last_date = ws.get("last_generated_date", "")

    bulletin_date = None
    if bulletin_data and "bulletin" in bulletin_data:
        bulletin_date = bulletin_data["bulletin"].get("date")

    has_next_bulletin = (str(bulletin_date) == str(next_sun))

    return {
        "last_issue": last_issue,
        "last_date": last_date,
        "next_sunday": str(next_sun),
        "has_next_bulletin": has_next_bulletin,
    }


def _collect_finance_status(data_dir: str, state: dict) -> dict:
    """Check if current month finance report is done."""
    today = date.today()
    current_month = today.strftime("%Y-%m")
    prev_month = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

    ws = state.get("church", {}).get("workflow_states", {}).get("finance", {})
    outputs = ws.get("outputs", {})
    last_report = ws.get("last_report_date", "")

    # Check if previous month report exists
    has_prev_report = prev_month in outputs

    return {
        "current_month": current_month,
        "prev_month": prev_month,
        "has_prev_month_report": has_prev_report,
        "last_report_date": last_report,
    }


def _collect_validation_status(state: dict) -> dict:
    """Get latest validation gate results."""
    vg = state.get("church", {}).get("verification_gates", {}).get("aggregate", {})
    return {
        "total_passed": vg.get("total_passed", 0),
        "total_checks": vg.get("total_checks", 0),
        "last_run": vg.get("last_run", ""),
    }


# ---------------------------------------------------------------------------
# Alert Engine
# ---------------------------------------------------------------------------

def _build_alerts(newcomer: dict, bulletin: dict, finance: dict) -> list:
    """Build prioritized alert list based on collected data."""
    alerts = []

    # Priority 1: Overdue newcomer follow-ups (pastoral care)
    if newcomer.get("overdue"):
        names = ", ".join(n["name"] for n in newcomer["overdue"][:3])
        count = len(newcomer["overdue"])
        alerts.append({
            "priority": 1,
            "category": "newcomer",
            "icon": "!!",
            "message_ko": f"새신자 {count}명 후속 관리 필요 ({names})",
            "message_en": f"{count} newcomer(s) overdue for follow-up",
        })

    # Priority 2: Missing next bulletin
    if not bulletin.get("has_next_bulletin"):
        alerts.append({
            "priority": 2,
            "category": "bulletin",
            "icon": "!!",
            "message_ko": f"이번 주 주보 미생성 ({bulletin.get('next_sunday', '')})",
            "message_en": "This week's bulletin not yet generated",
        })

    # Priority 3: Missing previous month finance report
    if not finance.get("has_prev_month_report"):
        pm = finance.get("prev_month", "")
        alerts.append({
            "priority": 3,
            "category": "finance",
            "icon": "!!",
            "message_ko": f"{pm} 재정 보고서 미생성",
            "message_en": f"{pm} finance report not yet generated",
        })

    return sorted(alerts, key=lambda a: a["priority"])


# ---------------------------------------------------------------------------
# Menu Builder
# ---------------------------------------------------------------------------

MENU_ITEMS = [
    {
        "key": "bulletin",
        "label_ko": "주보 (Bulletin)",
        "desc_ko": "이번 주 주보를 만들거나 확인합니다",
        "desc_en": "Generate or preview weekly bulletin",
    },
    {
        "key": "newcomer",
        "label_ko": "새신자 (Newcomers)",
        "desc_ko": "새신자 현황을 확인하고 관리합니다",
        "desc_en": "View newcomer dashboard and manage follow-ups",
    },
    {
        "key": "member",
        "label_ko": "교인 관리 (Members)",
        "desc_ko": "교인 검색, 등록, 수정을 합니다",
        "desc_en": "Search, register, or update member info",
    },
    {
        "key": "finance",
        "label_ko": "재정 (Finance)",
        "desc_ko": "헌금/지출 내역을 확인하고 보고서를 만듭니다",
        "desc_en": "View offering/expense records and generate reports",
    },
    {
        "key": "schedule",
        "label_ko": "일정 (Schedule)",
        "desc_ko": "이번 주 일정과 행사를 확인합니다",
        "desc_en": "View this week's schedule and events",
    },
    {
        "key": "document",
        "label_ko": "문서 발급 (Documents)",
        "desc_ko": "증명서, 공문 등을 발급합니다",
        "desc_en": "Issue certificates, official letters, minutes",
    },
    {
        "key": "system",
        "label_ko": "시스템 관리 (System)",
        "desc_ko": "데이터 검증, 상태 확인을 합니다",
        "desc_en": "Run validators, check system health",
    },
]


def _build_menu(alerts: list, features: dict) -> list:
    """Order menu items by alert priority. Disabled features get filtered."""
    feature_map = {
        "bulletin": features.get("bulletin_generation", True),
        "newcomer": features.get("newcomer_pipeline", True),
        "member": True,  # always available
        "finance": features.get("finance_reporting", True),
        "schedule": True,  # always available
        "document": features.get("document_generation", True),
        "system": True,  # always available
    }

    # Filter to enabled features
    enabled = [m for m in MENU_ITEMS if feature_map.get(m["key"], True)]

    # Promote items that have alerts
    alert_keys = {a["category"] for a in alerts}
    promoted = [m for m in enabled if m["key"] in alert_keys]
    rest = [m for m in enabled if m["key"] not in alert_keys]

    # Mark promoted items
    for m in promoted:
        matching = [a for a in alerts if a["category"] == m["key"]]
        if matching:
            m["alert"] = matching[0]["message_ko"]

    return promoted + rest


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_menu(state_path: str, data_dir: str) -> dict:
    """Generate the complete menu structure."""
    state = _load(state_path)
    if not state:
        return {"error": f"Cannot load state file: {state_path}"}

    church = state.get("church", {})

    # Collect all status data
    member_stats = _collect_member_stats(data_dir)
    newcomer_stats = _collect_newcomer_stats(data_dir)
    bulletin_status = _collect_bulletin_status(data_dir, state)
    finance_status = _collect_finance_status(data_dir, state)
    validation = _collect_validation_status(state)
    features = church.get("features", {})

    # Build alerts
    alerts = _build_alerts(newcomer_stats, bulletin_status, finance_status)

    # Build menu
    menu = _build_menu(alerts, features)

    # Split menu into page1 (top 3) + page2 (rest)
    # AskUserQuestion allows max 4 options — reserve 1 slot for "더보기"
    page1 = menu[:3]
    page2 = menu[3:]

    return {
        "church_name": church.get("name", "교회"),
        "status": {
            "members": member_stats,
            "newcomers": newcomer_stats,
            "bulletin": bulletin_status,
            "finance": finance_status,
            "validation": validation,
        },
        "alerts": alerts,
        "menu": menu,
        "menu_page1": page1,
        "menu_page2": page2,
    }


def main():
    parser = argparse.ArgumentParser(description="Church Admin Menu Generator")
    parser.add_argument("--state", default="state.yaml", help="Path to state.yaml")
    parser.add_argument("--data-dir", default="data/", help="Path to data directory")
    args = parser.parse_args()

    result = generate_menu(args.state, args.data_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

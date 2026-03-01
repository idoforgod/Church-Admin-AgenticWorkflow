#!/usr/bin/env python3
"""
template_engine.py — Church Admin Template Engine

Reads a template YAML definition + data YAML file(s) and produces a formatted
Markdown document by resolving template slots against actual data values.

Usage:
    python3 template_engine.py \\
        --template ./templates/bulletin-template.yaml \\
        --data ./data/bulletin-data.yaml \\
        --output ./bulletins/2026-03-01-bulletin.md

    # Multiple data files (for cross-file references like member lookups):
    python3 template_engine.py \\
        --template ./templates/bulletin-template.yaml \\
        --data ./data/bulletin-data.yaml \\
        --data ./data/members.yaml \\
        --output ./bulletins/2026-03-01-bulletin.md

Slot Types:
    text      — Direct string substitution
    date      — Formatted date string (YYYY-MM-DD → Korean date format)
    integer   — Integer value with optional format string
    currency  — KRW amount with comma formatting
    list      — Bulleted or numbered list from array data
    table     — Markdown table from array-of-objects data
    reference — Resolved from a secondary data file via member_id/family_id

Template YAML Schema:
    See templates/*.yaml for complete examples. Each template defines:
    - sections: ordered document sections
    - slots: data-driven fields within each section
    - source: dot-path to the value in a data YAML file
    - format: optional display format with {value} or named placeholders
"""

import argparse
import sys
import os
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip3 install pyyaml", file=sys.stderr)
    sys.exit(1)


# ── Data Resolution ──────────────────────────────────────────────────────────

def resolve_dot_path(data: dict, dot_path: str):
    """Resolve a dot-separated path against a nested dictionary.

    Supports:
        - Simple dot paths: "bulletin.sermon.title"
        - Array access: "bulletin.worship_order" (returns full list)
        - Nested keys with dots

    Args:
        data: The root data dictionary to traverse.
        dot_path: Dot-separated key path (e.g., "bulletin.sermon.title").

    Returns:
        The value at the specified path, or None if not found.
    """
    if not dot_path:
        return None

    keys = dot_path.split(".")
    current = data
    for key in keys:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list):
            # If we hit a list and have more keys, we cannot traverse further
            # with a simple dot path — return None (caller should handle)
            return None
        else:
            return None
    return current


def load_data_files(data_paths: list, base_dir: str) -> dict:
    """Load multiple YAML data files and merge them into a unified namespace.

    Each file's content is stored under a key derived from the filename:
        data/bulletin-data.yaml → key "bulletin-data" and also flattened
        into the root if the top-level is a dict.

    Args:
        data_paths: List of paths to YAML data files.
        base_dir: Base directory for resolving relative paths.

    Returns:
        Merged dictionary with all data accessible by dot-path resolution.
    """
    merged = {}
    file_data = {}  # keyed by filename stem

    for path_str in data_paths:
        path = Path(path_str)
        if not path.is_absolute():
            path = Path(base_dir) / path

        if not path.exists():
            print(f"WARNING: Data file not found: {path}", file=sys.stderr)
            continue

        with open(path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            if content is None:
                continue

        stem = path.stem  # e.g., "bulletin-data"
        file_data[stem] = content

        # Flatten top-level keys into the merged dict for direct access
        if isinstance(content, dict):
            for key, value in content.items():
                if key.startswith("_") or key in ("schema_version", "last_updated", "updated_by"):
                    continue  # skip metadata keys
                merged[key] = value

    merged["_files"] = file_data
    return merged


# ── Slot Formatting ──────────────────────────────────────────────────────────

def format_date(value: str, fmt: str = None) -> str:
    """Format a date string into Korean date format.

    Args:
        value: ISO date string (YYYY-MM-DD).
        fmt: Optional format string with {year}, {month}, {day} placeholders.

    Returns:
        Formatted date string.
    """
    if not value:
        return ""
    try:
        dt = datetime.strptime(str(value), "%Y-%m-%d")
    except ValueError:
        return str(value)

    if fmt:
        return fmt.format(
            year=dt.year,
            month=dt.month,
            day=dt.day,
            weekday=_weekday_korean(dt.weekday()),
        )
    return f"{dt.year}년 {dt.month}월 {dt.day}일"


def _weekday_korean(weekday_int: int) -> str:
    """Convert Python weekday (0=Monday) to Korean day name."""
    days = ["월", "화", "수", "목", "금", "토", "주일"]
    # Sunday is weekday 6 in Python, displayed as "주일" in Korean church context
    if weekday_int == 6:
        return "주일"
    return days[weekday_int]


def format_currency(value, fmt: str = None) -> str:
    """Format an integer amount as Korean Won currency.

    Args:
        value: Integer amount in KRW.
        fmt: Optional format string with {value} placeholder.

    Returns:
        Formatted currency string.
    """
    if value is None:
        return ""
    try:
        amount = int(value)
    except (ValueError, TypeError):
        return str(value)

    if fmt:
        return fmt.format(value=f"{amount:,}")
    return f"₩{amount:,}"


def format_integer(value, fmt: str = None) -> str:
    """Format an integer value with optional format string.

    Args:
        value: Integer value.
        fmt: Optional format string with {value} placeholder.

    Returns:
        Formatted string.
    """
    if value is None:
        return ""
    if fmt:
        return fmt.format(value=value)
    return str(value)


def format_text(value, fmt: str = None) -> str:
    """Format a text value with optional format string.

    Args:
        value: String value.
        fmt: Optional format string with {value} placeholder.

    Returns:
        Formatted string.
    """
    if value is None:
        return ""
    if fmt and "{value}" in fmt:
        return fmt.format(value=value)
    return str(value)


def format_list(items: list, slot_def: dict) -> str:
    """Format a list of items into Markdown list syntax.

    Args:
        items: List of values (strings, dicts, or mixed).
        slot_def: Slot definition with list_style and item_format.

    Returns:
        Multi-line Markdown list string.
    """
    if not items:
        return ""

    style = slot_def.get("list_style", "bullet")
    item_fmt = slot_def.get("item_format")
    lines = []

    for i, item in enumerate(items, 1):
        if isinstance(item, dict) and item_fmt:
            try:
                # Replace format placeholders with dict values, handling None
                text = item_fmt
                for key in item:
                    placeholder = "{" + key + "}"
                    if placeholder in text:
                        text = text.replace(placeholder, str(item.get(key) or ""))
                line_text = text.strip()
            except (KeyError, TypeError):
                line_text = str(item)
        elif isinstance(item, str):
            line_text = item
        else:
            line_text = str(item)

        if style == "numbered":
            lines.append(f"{i}. {line_text}")
        elif style == "comma":
            lines.append(line_text)
        else:  # bullet
            lines.append(f"- {line_text}")

    if style == "comma":
        return ", ".join(lines)
    return "\n".join(lines)


def format_table(items: list, slot_def: dict) -> str:
    """Format an array of objects into a Markdown table.

    Args:
        items: List of dicts (each dict is a table row).
        slot_def: Slot definition with columns specification.

    Returns:
        Markdown table string.
    """
    if not items:
        return ""

    columns = slot_def.get("columns", [])
    if not columns:
        # Auto-detect columns from first item
        if isinstance(items[0], dict):
            columns = [{"name": k, "header": k} for k in items[0].keys()]
        else:
            return "\n".join(f"| {item} |" for item in items)

    # Build header row
    headers = [col.get("header", col["name"]) for col in columns]
    header_line = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"

    # Build data rows
    rows = []
    for item in items:
        if isinstance(item, dict):
            cells = []
            for col in columns:
                val = item.get(col["name"])
                if val is None:
                    cells.append("")
                elif col.get("type") == "currency":
                    col_fmt = col.get("format")
                    cells.append(format_currency(val, col_fmt))
                else:
                    cells.append(str(val))
            rows.append("| " + " | ".join(cells) + " |")
        else:
            rows.append("| " + str(item) + " |")

    return "\n".join([header_line, separator] + rows)


# ── Slot Resolution ──────────────────────────────────────────────────────────

def resolve_slot(slot_def: dict, data: dict) -> str:
    """Resolve a single slot definition against loaded data.

    Reads the slot type and source, fetches the value from data,
    and applies the appropriate formatting.

    Args:
        slot_def: Slot definition from the template YAML.
        data: Merged data dictionary from all loaded YAML files.

    Returns:
        Formatted string value for the slot.
    """
    slot_type = slot_def.get("type", "text")
    source = slot_def.get("source")
    fmt = slot_def.get("format")
    nullable = slot_def.get("nullable", False)
    required = slot_def.get("required", False)
    derived = slot_def.get("derived", False)

    # Skip derived slots — they need special handling by the caller
    if derived and source is None:
        return slot_def.get("default", "")

    # Resolve the value from data
    value = resolve_dot_path(data, source) if source else None

    # Handle missing values
    if value is None:
        if nullable or not required:
            return ""
        default = slot_def.get("default")
        if default is not None:
            return str(default)
        return ""

    # Format based on type
    if slot_type == "text":
        return format_text(value, fmt)
    elif slot_type == "date":
        return format_date(value, fmt)
    elif slot_type == "integer":
        return format_integer(value, fmt)
    elif slot_type == "currency":
        return format_currency(value, fmt)
    elif slot_type == "list":
        if isinstance(value, list):
            return format_list(value, slot_def)
        return format_text(value, fmt)
    elif slot_type == "table":
        if isinstance(value, list):
            return format_table(value, slot_def)
        return format_text(value, fmt)
    elif slot_type == "reference":
        # Reference types need member/family lookup — resolve inline
        return format_text(value, fmt)
    else:
        return str(value)


# ── Document Generation ──────────────────────────────────────────────────────

def generate_document(template: dict, data: dict) -> str:
    """Generate a complete Markdown document from a template and data.

    Iterates over the template sections, resolves all slots, and assembles
    the final document with proper Markdown formatting.

    Args:
        template: Parsed template YAML dictionary.
        data: Merged data dictionary from all loaded YAML files.

    Returns:
        Complete Markdown document as a string.
    """
    lines = []
    doc_type = template.get("document_type", "document")
    divider = template.get("layout", {}).get("section_divider", "---")

    # Document title — derived from first section or template metadata
    sections = template.get("sections", [])

    for section_idx, section in enumerate(sections):
        section_title = section.get("title", "")

        # Add section header
        if section_title:
            if section_idx == 0:
                # First section gets a level-1 heading
                lines.append(f"# {section_title}")
            else:
                lines.append(f"## {section_title}")
            lines.append("")

        # Render fixed content if present
        fixed = section.get("fixed_content", {})
        for key, value in fixed.items():
            if key == "title":
                continue  # already handled as section title
            if key == "seal_zone":
                lines.append(f"*{value}*")
                lines.append("")
            elif key == "legal_text":
                lines.append(f"> {value}")
                lines.append("")
            else:
                lines.append(str(value))
                lines.append("")

        # Render slots
        slots = section.get("slots", [])
        for slot in slots:
            slot_name = slot.get("name", "")
            slot_type = slot.get("type", "text")
            slot_desc = slot.get("description", "")
            resolved = resolve_slot(slot, data)

            if not resolved and not slot.get("required", False):
                continue  # skip empty optional slots

            if slot_type in ("list", "table"):
                # Lists and tables render as block content
                if resolved:
                    lines.append(resolved)
                    lines.append("")
            else:
                # Scalar values render as labeled lines within sections
                if section_idx == 0:
                    # Header section — render values prominently
                    lines.append(resolved)
                    lines.append("")
                else:
                    # Body sections — render as text
                    lines.append(resolved)
                    lines.append("")

        # Add section divider (except after last section)
        if section_idx < len(sections) - 1:
            lines.append(divider)
            lines.append("")

    return "\n".join(lines)


def generate_bulletin(template: dict, data: dict) -> str:
    """Generate a bulletin document with church-specific formatting.

    This is a specialized generator that produces a well-structured bulletin
    with proper Korean church formatting conventions.

    Args:
        template: Parsed bulletin template YAML.
        data: Merged data dictionary.

    Returns:
        Formatted Markdown bulletin.
    """
    lines = []
    b = data.get("bulletin", {})
    if not b:
        return "ERROR: No bulletin data found."

    # ── Header ────────────────────────────────────────────────
    church_name = b.get("church_name", "")
    date_str = b.get("date", "")
    issue_num = b.get("issue_number", "")

    lines.append(f"# {church_name}")
    lines.append("")
    date_formatted = format_date(date_str, "{year}년 {month}월 {day}일 주일")
    lines.append(f"**{date_formatted}** | 제 {issue_num}호")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Sermon ────────────────────────────────────────────────
    sermon = b.get("sermon", {})
    if sermon:
        lines.append("## 말씀 (The Word)")
        lines.append("")
        series = sermon.get("series")
        if series:
            episode = sermon.get("series_episode", "")
            if episode:
                lines.append(f"*[ {series} — 제 {episode}편 ]*")
            else:
                lines.append(f"*[ {series} ]*")
            lines.append("")
        lines.append(f"### {sermon.get('title', '')}")
        lines.append("")
        lines.append(f"**본문**: {sermon.get('scripture', '')}")
        lines.append("")
        lines.append(f"**설교**: {sermon.get('preacher', '')}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # ── Worship Order ─────────────────────────────────────────
    worship = b.get("worship_order", [])
    if worship:
        lines.append("## 예배 순서 (Order of Worship)")
        lines.append("")
        lines.append("| 순서 | 항목 | 내용 | 담당 |")
        lines.append("| --- | --- | --- | --- |")
        for item in worship:
            order = item.get("order", "")
            name = item.get("item", "")
            detail = item.get("detail") or ""
            performer = item.get("performer") or ""
            lines.append(f"| {order} | {name} | {detail} | {performer} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    # ── Announcements ─────────────────────────────────────────
    announcements = b.get("announcements", [])
    if announcements:
        lines.append("## 공지사항 (Announcements)")
        lines.append("")
        for ann in announcements:
            title = ann.get("title", "")
            content = ann.get("content", "")
            priority = ann.get("priority", "normal")
            prefix = "**[중요]** " if priority == "high" else ""
            lines.append(f"- {prefix}**{title}**: {content}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # ── Prayer Requests ───────────────────────────────────────
    prayers = b.get("prayer_requests", [])
    if prayers:
        lines.append("## 기도 제목 (Prayer Requests)")
        lines.append("")
        for prayer in prayers:
            category = prayer.get("category", "")
            content = prayer.get("content", "")
            lines.append(f"- **{category}**: {content}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # ── Celebrations ──────────────────────────────────────────
    celebrations = b.get("celebrations", {})
    birthdays = celebrations.get("birthday", [])
    anniversaries = celebrations.get("wedding_anniversary", [])
    if birthdays or anniversaries:
        lines.append("## 축하 (Celebrations)")
        lines.append("")
        if birthdays:
            lines.append("**생일 축하**")
            lines.append("")
            for bd in birthdays:
                name = bd.get("name", "")
                date = bd.get("date", "")
                lines.append(f"- {name} ({date})")
            lines.append("")
        if anniversaries:
            lines.append("**결혼기념일 축하**")
            lines.append("")
            for ann in anniversaries:
                family_id = ann.get("family_id", "")
                date = ann.get("date", "")
                lines.append(f"- 가정 {family_id} ({date})")
            lines.append("")
        lines.append("---")
        lines.append("")

    # ── Offering Team ─────────────────────────────────────────
    offering = b.get("offering_team", [])
    if offering:
        lines.append("## 헌금 봉사 (Offering Team)")
        lines.append("")
        lines.append(", ".join(offering))
        lines.append("")
        lines.append("---")
        lines.append("")

    # ── Next Week Preview ─────────────────────────────────────
    next_week = b.get("next_week", {})
    if next_week:
        lines.append("## 다음 주 예고 (Next Week Preview)")
        lines.append("")
        nst = next_week.get("sermon_title", "")
        nsc = next_week.get("scripture", "")
        if nst:
            lines.append(f"**설교**: {nst}")
        if nsc:
            lines.append(f"**본문**: {nsc}")
        events = next_week.get("special_events", [])
        if events:
            lines.append("")
            for evt in events:
                lines.append(f"- {evt}")
        lines.append("")

    return "\n".join(lines)


def generate_worship_order(template: dict, data: dict) -> str:
    """Generate a worship order sheet with focused single-service format.

    Args:
        template: Parsed worship order template YAML.
        data: Merged data dictionary.

    Returns:
        Formatted Markdown worship order.
    """
    lines = []
    b = data.get("bulletin", {})
    if not b:
        return "ERROR: No bulletin data found."

    church_name = b.get("church_name", "")
    date_str = b.get("date", "")
    sermon = b.get("sermon", {})

    # ── Header ────────────────────────────────────────────────
    lines.append(f"# {church_name}")
    lines.append("")
    lines.append("## 예 배 순 서")
    lines.append("")
    date_formatted = format_date(date_str, "{year}년 {month}월 {day}일 (주일)")
    lines.append(f"**{date_formatted}**")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Sermon Info ────────────────────────────────────────────
    if sermon:
        lines.append(f"**설교**: {sermon.get('title', '')}")
        lines.append(f"**본문**: {sermon.get('scripture', '')}")
        lines.append(f"**설교자**: {sermon.get('preacher', '')}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # ── Order Items ────────────────────────────────────────────
    worship = b.get("worship_order", [])
    if worship:
        lines.append("| 순서 | 항목 | 내용 | 담당 |")
        lines.append("| ---: | --- | --- | --- |")
        for item in worship:
            order = item.get("order", "")
            name = item.get("item", "")
            detail = item.get("detail") or ""
            performer = item.get("performer") or ""
            lines.append(f"| {order} | {name} | {detail} | {performer} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    # ── Offering Team ──────────────────────────────────────────
    offering = b.get("offering_team", [])
    if offering:
        lines.append(f"**헌금 봉사**: {', '.join(offering)}")
        lines.append("")

    # ── Brief Announcements ────────────────────────────────────
    announcements = b.get("announcements", [])
    if announcements:
        lines.append("## 광고")
        lines.append("")
        for ann in announcements:
            lines.append(f"- {ann.get('title', '')}")
        lines.append("")

    return "\n".join(lines)


def generate_receipt(template: dict, data: dict, member_id: str = None) -> str:
    """Generate a donation receipt for a specific member.

    Note: This is a simplified implementation. Full receipt generation requires
    per-member offering aggregation from finance.yaml, which depends on having
    member_id tags on offering records. The current seed data does not include
    per-member offering attribution, so this generator produces a template-level
    receipt that would be filled in with actual per-member data.

    Args:
        template: Parsed receipt template YAML.
        data: Merged data dictionary.
        member_id: Optional member ID for per-member receipt generation.

    Returns:
        Formatted Markdown receipt.
    """
    lines = []

    year = data.get("year", datetime.now().year)
    church_name = data.get("church", {}).get("name", "")

    # If we have bulletin data with church_name, use that
    if not church_name:
        bulletin = data.get("bulletin", {})
        church_name = bulletin.get("church_name", "교회명")

    lines.append("# 기 부 금 영 수 증")
    lines.append("")
    lines.append(f"**종교단체**")
    lines.append("")
    today = datetime.now()
    lines.append(f"발행일: {today.year}년 {today.month}월 {today.day}일")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Church Info ────────────────────────────────────────────
    lines.append("## 발행 기관")
    lines.append("")
    lines.append(f"**단체명**: {church_name}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Donor Info ─────────────────────────────────────────────
    lines.append("## 기부자 정보")
    lines.append("")

    if member_id:
        # Look up member from data
        members = data.get("members", [])
        member = None
        for m in members:
            if m.get("id") == member_id:
                member = m
                break
        if member:
            lines.append(f"**성명**: {member.get('name', '')}")
            address = member.get("contact", {}).get("address", "")
            if address:
                lines.append(f"**주소**: {address}")
        else:
            lines.append(f"**성명**: (회원 ID: {member_id})")
    else:
        lines.append("**성명**: ________________")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Donation Details ───────────────────────────────────────
    lines.append("## 기부 내역")
    lines.append("")
    lines.append(f"**기부 기간**: {year}년 1월 1일 ~ {year}년 12월 31일")
    lines.append("")
    lines.append("| 헌금 구분 | 금액 (원) |")
    lines.append("| --- | ---: |")
    lines.append("| 십일조 | |")
    lines.append("| 주일헌금 | |")
    lines.append("| 감사헌금 | |")
    lines.append("| 선교헌금 | |")
    lines.append("| **합계** | |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Legal Footer ───────────────────────────────────────────
    lines.append("> 위 금액을 소득세법 제34조, 같은 법 시행령 제80조 제1항 제5호에 "
                 "의하여 기부금으로 영수합니다.")
    lines.append("")
    lines.append(f"**{church_name}** 대표 ____________ (인)")
    lines.append("")

    return "\n".join(lines)


# ── Main Entry Point ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Church Admin Template Engine — generate Markdown documents from YAML templates and data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a bulletin:
  python3 template_engine.py --template templates/bulletin-template.yaml \\
      --data data/bulletin-data.yaml --output bulletins/2026-03-01-bulletin.md

  # Generate with multiple data files:
  python3 template_engine.py --template templates/bulletin-template.yaml \\
      --data data/bulletin-data.yaml --data data/members.yaml \\
      --output bulletins/2026-03-01-bulletin.md

  # Generate a worship order:
  python3 template_engine.py --template templates/worship-template.yaml \\
      --data data/bulletin-data.yaml --output bulletins/2026-03-01-worship.md

  # Dry-run (print to stdout):
  python3 template_engine.py --template templates/bulletin-template.yaml \\
      --data data/bulletin-data.yaml
        """,
    )
    parser.add_argument(
        "--template", "-t",
        required=True,
        help="Path to the template YAML file (e.g., templates/bulletin-template.yaml)",
    )
    parser.add_argument(
        "--data", "-d",
        action="append",
        required=True,
        help="Path to a data YAML file. Can be specified multiple times for cross-file references.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path. If omitted, prints to stdout.",
    )
    parser.add_argument(
        "--member-id",
        default=None,
        help="Member ID for per-member document generation (e.g., receipts).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print output to stdout without writing to file.",
    )

    args = parser.parse_args()

    # Resolve paths relative to CWD
    base_dir = os.getcwd()
    template_path = Path(args.template)
    if not template_path.is_absolute():
        template_path = Path(base_dir) / template_path

    if not template_path.exists():
        print(f"ERROR: Template file not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    # Load template
    with open(template_path, "r", encoding="utf-8") as f:
        template = yaml.safe_load(f)

    if not template:
        print("ERROR: Template file is empty or invalid YAML.", file=sys.stderr)
        sys.exit(1)

    # Load data files
    data = load_data_files(args.data, base_dir)

    if not data:
        print("ERROR: No data loaded from the specified files.", file=sys.stderr)
        sys.exit(1)

    # Determine document type and use appropriate generator
    doc_type = template.get("document_type", "generic")

    if doc_type == "bulletin":
        output = generate_bulletin(template, data)
    elif doc_type == "worship_order":
        output = generate_worship_order(template, data)
    elif doc_type == "receipt":
        output = generate_receipt(template, data, args.member_id)
    else:
        # Generic document generation via slot resolution
        output = generate_document(template, data)

    # Output result
    if args.output and not args.dry_run:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = Path(base_dir) / output_path

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)

        print(f"Generated: {output_path}", file=sys.stderr)
        print(f"  Template: {template_path.name}", file=sys.stderr)
        print(f"  Type: {doc_type}", file=sys.stderr)
        print(f"  Size: {len(output)} chars, {output.count(chr(10))} lines", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()

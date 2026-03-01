#!/usr/bin/env python3
"""
Tier A Parser — Structured Data (Excel/CSV)

Parses tabular files (.xlsx, .csv) with known column mappings for:
  - 헌금내역.xlsx  -> finance.yaml offerings format
  - 새신자등록카드.xlsx -> newcomers.yaml format
  - 교인명부.csv   -> members.yaml format

Uses church-glossary.yaml for Korean term normalization.
Produces JSON staging files in inbox/staging/.

Usage:
    python3 tier_a_parser.py --file <path> --glossary <glossary.yaml> --staging-dir <dir>
"""

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime

import yaml

# ---------------------------------------------------------------------------
# Optional dependency: openpyxl (graceful fallback)
# ---------------------------------------------------------------------------
try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PHONE_RE = re.compile(r"^010-\d{4}-\d{4}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATE_SLASH_RE = re.compile(r"^\d{4}/\d{2}/\d{2}$")

# Known file-to-schema mappings (basename patterns)
FILE_ROUTING = {
    "헌금내역": {"target": "data/finance.yaml", "section": "offerings", "parser": "parse_offerings"},
    "새신자등록카드": {"target": "data/newcomers.yaml", "section": "newcomers", "parser": "parse_newcomers"},
    "교인명부": {"target": "data/members.yaml", "section": "members", "parser": "parse_members"},
}

# Finance category column mappings (Korean -> glossary key)
FINANCE_CATEGORY_HINTS = {
    "십일조": "tithe",
    "주일헌금": "sunday_offering",
    "감사헌금": "thanksgiving_offering",
    "건축헌금": "building_fund",
    "선교헌금": "mission_offering",
}


# ---------------------------------------------------------------------------
# Glossary loader
# ---------------------------------------------------------------------------
def load_glossary(glossary_path):
    """Load church-glossary.yaml and build Korean->English lookup."""
    if not os.path.isfile(glossary_path):
        return {}
    with open(glossary_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    lookup = {}
    for term in data.get("terms", []):
        korean = term.get("korean", "")
        english = term.get("english", "")
        if korean and english:
            lookup[korean] = english
    return lookup


# ---------------------------------------------------------------------------
# Date normalization
# ---------------------------------------------------------------------------
def normalize_date(value):
    """Normalize various date formats to YYYY-MM-DD string.

    Returns (normalized_date_str, confidence) tuple.
    """
    if value is None:
        return None, 0.0
    s = str(value).strip()
    # Already YYYY-MM-DD
    if DATE_RE.match(s):
        return s, 1.0
    # YYYY/MM/DD
    if DATE_SLASH_RE.match(s):
        return s.replace("/", "-"), 0.95
    # Try common Korean date patterns
    # e.g., "2026년 2월 28일"
    m = re.match(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}", 0.9
    # Try datetime object (from openpyxl)
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d"), 1.0
    return s, 0.3


def normalize_phone(value):
    """Normalize phone number to 010-XXXX-XXXX format.

    Returns (normalized_phone, confidence) tuple.
    """
    if value is None:
        return None, 0.0
    s = str(value).strip().replace(" ", "")
    # Remove all non-digit characters except dash
    digits = re.sub(r"[^\d]", "", s)
    if len(digits) == 11 and digits.startswith("010"):
        formatted = f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        return formatted, 1.0
    if PHONE_RE.match(s):
        return s, 1.0
    return s, 0.3


def normalize_amount(value):
    """Normalize financial amount to integer KRW.

    Returns (amount_int, confidence) tuple.
    """
    if value is None:
        return 0, 0.0
    if isinstance(value, (int, float)):
        return int(value), 1.0
    s = str(value).strip()
    # Remove currency symbols, commas, spaces, "원"
    s = re.sub(r"[,\s원₩]", "", s)
    try:
        return int(float(s)), 0.9
    except (ValueError, TypeError):
        return 0, 0.0


# ---------------------------------------------------------------------------
# Excel reader
# ---------------------------------------------------------------------------
def read_xlsx(filepath):
    """Read .xlsx file and return list of row dicts with header mapping.

    Returns (headers, rows) where rows is list of dicts.
    Raises RuntimeError if openpyxl not available.
    """
    if not HAS_OPENPYXL:
        raise RuntimeError(
            "openpyxl is not installed. Install it with: pip install openpyxl\n"
            "Alternatively, export the Excel file as .csv and re-run."
        )
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=False))
    if not rows:
        return [], []

    # First row is header
    headers = []
    for cell in rows[0]:
        val = cell.value
        headers.append(str(val).strip() if val is not None else f"col_{cell.column}")

    data_rows = []
    for row_idx, row in enumerate(rows[1:], start=2):
        row_dict = {"_source_row": row_idx}
        for col_idx, cell in enumerate(row):
            if col_idx < len(headers):
                row_dict[headers[col_idx]] = cell.value
        # Skip entirely empty rows
        if all(v is None for k, v in row_dict.items() if k != "_source_row"):
            continue
        data_rows.append(row_dict)

    wb.close()
    return headers, data_rows


def read_csv(filepath):
    """Read .csv file and return list of row dicts.

    Returns (headers, rows) where rows is list of dicts.
    """
    rows = []
    headers = []
    # Try UTF-8 first, then EUC-KR (common for Korean CSV exports)
    for encoding in ("utf-8-sig", "utf-8", "euc-kr", "cp949"):
        try:
            with open(filepath, "r", encoding=encoding) as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                for row_idx, row in enumerate(reader, start=2):
                    row["_source_row"] = row_idx
                    rows.append(row)
            break
        except (UnicodeDecodeError, UnicodeError):
            rows = []
            headers = []
            continue
    return headers, rows


# ---------------------------------------------------------------------------
# Schema-specific parsers
# ---------------------------------------------------------------------------
def parse_offerings(rows, glossary, source_file):
    """Parse offering/finance rows into finance.yaml offerings format."""
    records = []
    warnings = []
    glossary_used = {}

    for row in rows:
        source_row = row.get("_source_row", "?")
        record_warnings = []

        # Try to find date column (various Korean headers)
        date_val = None
        for key in ("날짜", "일자", "date", "Date", "헌금일"):
            if key in row and row[key] is not None:
                date_val = row[key]
                break
        norm_date, date_conf = normalize_date(date_val)

        # Try to find service column
        service = None
        for key in ("예배", "예배명", "service", "Service"):
            if key in row and row[key] is not None:
                service = str(row[key]).strip()
                break

        # Try to find category
        category_korean = None
        category_english = None
        for key in ("구분", "헌금종류", "category", "Category", "종류"):
            if key in row and row[key] is not None:
                category_korean = str(row[key]).strip()
                break

        if category_korean:
            # Look up in glossary first, then fallback to hints
            if category_korean in glossary:
                category_english = glossary[category_korean]
                glossary_used[category_korean] = category_english
            elif category_korean in FINANCE_CATEGORY_HINTS:
                category_english = FINANCE_CATEGORY_HINTS[category_korean]
                glossary_used[category_korean] = category_english
            else:
                category_english = category_korean
                record_warnings.append(
                    f"Row {source_row}: Unknown category '{category_korean}' "
                    "— not found in glossary"
                )

        # Try to find amount
        amount_val = None
        for key in ("금액", "헌금액", "amount", "Amount"):
            if key in row and row[key] is not None:
                amount_val = row[key]
                break
        amount, amount_conf = normalize_amount(amount_val)

        # Confidence: average of available field confidences
        confidences = [c for c in [date_conf, amount_conf] if c > 0]
        confidence = sum(confidences) / len(confidences) if confidences else 0.3

        if amount == 0 and date_val is None:
            warnings.append(f"Row {source_row}: Skipped — no date or amount found")
            continue

        fields = {
            "date": norm_date,
            "service": service or "주일예배 (Sunday Service)",
            "type": category_english or "unknown",
            "category_korean": category_korean,
            "category_english": f"{category_korean} ({category_english})" if category_english and category_korean else category_english,
            "amount": amount,
        }

        records.append({
            "fields": fields,
            "confidence": round(confidence, 2),
            "source_row": source_row,
            "notes": record_warnings,
        })
        warnings.extend(record_warnings)

    return records, warnings, glossary_used


def parse_newcomers(rows, glossary, source_file):
    """Parse newcomer registration card rows into newcomers.yaml format."""
    records = []
    warnings = []
    glossary_used = {}

    for row in rows:
        source_row = row.get("_source_row", "?")
        record_warnings = []

        # Name
        name = None
        for key in ("이름", "성명", "name", "Name"):
            if key in row and row[key] is not None:
                name = str(row[key]).strip()
                break

        # Gender
        gender = None
        for key in ("성별", "gender", "Gender"):
            if key in row and row[key] is not None:
                raw = str(row[key]).strip()
                if raw in ("남", "남성", "M", "male"):
                    gender = "male"
                elif raw in ("여", "여성", "F", "female"):
                    gender = "female"
                else:
                    gender = raw
                    record_warnings.append(f"Row {source_row}: Unknown gender '{raw}'")
                break

        # Birth year
        birth_year = None
        for key in ("생년", "출생년도", "birth_year", "Birth Year", "생년월일"):
            if key in row and row[key] is not None:
                val = row[key]
                if isinstance(val, (int, float)):
                    birth_year = int(val)
                else:
                    # Try to extract year
                    m = re.search(r"(\d{4})", str(val))
                    if m:
                        birth_year = int(m.group(1))
                break

        # Phone
        phone = None
        for key in ("전화", "전화번호", "연락처", "phone", "Phone"):
            if key in row and row[key] is not None:
                phone, phone_conf = normalize_phone(row[key])
                if phone_conf < 0.5:
                    record_warnings.append(
                        f"Row {source_row}: Phone '{row[key]}' may be invalid"
                    )
                break

        # First visit date
        first_visit = None
        for key in ("첫방문일", "방문일", "first_visit", "First Visit"):
            if key in row and row[key] is not None:
                first_visit, fv_conf = normalize_date(row[key])
                break

        # Visit route
        visit_route = None
        for key in ("경로", "방문경로", "visit_route", "Route"):
            if key in row and row[key] is not None:
                visit_route = str(row[key]).strip()
                break

        # Referred by
        referred_by = None
        for key in ("소개자", "소개", "referred_by", "Referred By"):
            if key in row and row[key] is not None:
                referred_by = str(row[key]).strip()
                break

        # Department assignment
        department = None
        for key in ("부서", "배정부서", "department", "Department"):
            if key in row and row[key] is not None:
                department = str(row[key]).strip()
                break

        if not name:
            warnings.append(f"Row {source_row}: Skipped — no name found")
            continue

        confidence = 0.9 if (name and first_visit) else 0.6

        fields = {
            "name": name,
            "gender": gender,
            "birth_year": birth_year,
            "contact": {
                "phone": phone,
                "kakao_id": None,
            },
            "first_visit": first_visit,
            "visit_route": visit_route,
            "referred_by": referred_by,
            "journey_stage": "first_visit",
            "assigned_department": department,
            "status": "active",
        }

        records.append({
            "fields": fields,
            "confidence": round(confidence, 2),
            "source_row": source_row,
            "notes": record_warnings,
        })
        warnings.extend(record_warnings)

    return records, warnings, glossary_used


def parse_members(rows, glossary, source_file):
    """Parse member directory rows into members.yaml format."""
    records = []
    warnings = []
    glossary_used = {}

    for row in rows:
        source_row = row.get("_source_row", "?")
        record_warnings = []

        # Name
        name = None
        for key in ("이름", "성명", "name", "Name"):
            if key in row and row[key] is not None:
                name = str(row[key]).strip()
                break

        # Gender
        gender = None
        for key in ("성별", "gender", "Gender"):
            if key in row and row[key] is not None:
                raw = str(row[key]).strip()
                if raw in ("남", "남성", "M", "male"):
                    gender = "male"
                elif raw in ("여", "여성", "F", "female"):
                    gender = "female"
                else:
                    gender = raw
                break

        # Birth date
        birth_date = None
        for key in ("생년월일", "생일", "birth_date", "Birth Date"):
            if key in row and row[key] is not None:
                birth_date, bd_conf = normalize_date(row[key])
                break

        # Phone
        phone = None
        for key in ("전화", "전화번호", "연락처", "phone", "Phone"):
            if key in row and row[key] is not None:
                phone, _ = normalize_phone(row[key])
                break

        # Email
        email = None
        for key in ("이메일", "email", "Email", "E-mail"):
            if key in row and row[key] is not None:
                email = str(row[key]).strip()
                break

        # Address
        address = None
        for key in ("주소", "address", "Address"):
            if key in row and row[key] is not None:
                address = str(row[key]).strip()
                break

        # Registration date
        reg_date = None
        for key in ("등록일", "가입일", "registration_date", "Registration Date"):
            if key in row and row[key] is not None:
                reg_date, _ = normalize_date(row[key])
                break

        # Baptism
        baptism_date = None
        for key in ("세례일", "baptism_date", "Baptism Date"):
            if key in row and row[key] is not None:
                baptism_date, _ = normalize_date(row[key])
                break

        # Department
        department = None
        for key in ("부서", "department", "Department"):
            if key in row and row[key] is not None:
                department = str(row[key]).strip()
                break

        # Role/Position
        role = None
        for key in ("직분", "직위", "role", "Role", "Position"):
            if key in row and row[key] is not None:
                raw_role = str(row[key]).strip()
                # Normalize using glossary
                if raw_role in glossary:
                    role = glossary[raw_role]
                    glossary_used[raw_role] = role
                else:
                    role = raw_role
                break

        # Cell group
        cell_group = None
        for key in ("구역", "cell_group", "Cell Group"):
            if key in row and row[key] is not None:
                cell_group = str(row[key]).strip()
                break

        if not name:
            warnings.append(f"Row {source_row}: Skipped — no name found")
            continue

        confidence = 0.9 if (name and phone) else 0.7

        fields = {
            "name": name,
            "gender": gender,
            "birth_date": birth_date,
            "status": "active",
            "contact": {
                "phone": phone,
                "email": email,
                "address": address,
            },
            "church": {
                "registration_date": reg_date,
                "baptism_date": baptism_date,
                "baptism_type": "adult" if baptism_date else None,
                "department": department,
                "cell_group": cell_group,
                "role": role,
                "serving_area": [],
            },
        }

        records.append({
            "fields": fields,
            "confidence": round(confidence, 2),
            "source_row": source_row,
            "notes": record_warnings,
        })
        warnings.extend(record_warnings)

    return records, warnings, glossary_used


# ---------------------------------------------------------------------------
# Route detection
# ---------------------------------------------------------------------------
def detect_file_type(filepath):
    """Detect which schema parser to use based on filename patterns.

    Returns (route_key, route_info) or (None, None) if unrecognized.
    """
    basename = os.path.splitext(os.path.basename(filepath))[0]
    for pattern, info in FILE_ROUTING.items():
        if pattern in basename:
            return pattern, info
    return None, None


# ---------------------------------------------------------------------------
# Main parse entry point
# ---------------------------------------------------------------------------
def parse_file(filepath, glossary_path, staging_dir):
    """Parse a single structured file and produce a staging JSON.

    Args:
        filepath: Path to .xlsx or .csv file.
        glossary_path: Path to church-glossary.yaml.
        staging_dir: Directory for staging output.

    Returns:
        dict with parse results, or None on fatal error.
    """
    if not os.path.isfile(filepath):
        return {"error": f"File not found: {filepath}"}

    ext = os.path.splitext(filepath)[1].lower()
    glossary = load_glossary(glossary_path)

    # Read the file
    try:
        if ext == ".xlsx":
            headers, rows = read_xlsx(filepath)
        elif ext == ".csv":
            headers, rows = read_csv(filepath)
        else:
            return {"error": f"Unsupported extension for Tier A: {ext}"}
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to read {filepath}: {e}"}

    if not rows:
        return {"error": f"No data rows found in {filepath}"}

    # Detect file type and route to parser
    route_key, route_info = detect_file_type(filepath)

    if route_info:
        parser_name = route_info["parser"]
        target_file = route_info["target"]
        target_section = route_info["section"]
    else:
        # Fallback: try to guess from headers
        target_file, target_section, parser_name = _guess_from_headers(headers)

    # Execute the appropriate parser
    parser_fn = {
        "parse_offerings": parse_offerings,
        "parse_newcomers": parse_newcomers,
        "parse_members": parse_members,
    }.get(parser_name)

    if parser_fn is None:
        return {
            "error": f"No parser found for '{filepath}'. "
                     f"Headers detected: {headers}. "
                     "Rename the file to match a known pattern "
                     "(헌금내역, 새신자등록카드, 교인명부) or add a new parser."
        }

    records, parse_warnings, glossary_used = parser_fn(rows, glossary, filepath)

    # Build staging output
    confidences = [r["confidence"] for r in records]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    staging_data = {
        "source_file": filepath,
        "parser_tier": "A",
        "target_data_file": target_file,
        "target_section": target_section,
        "records": records,
        "glossary_mappings": glossary_used,
        "parse_warnings": parse_warnings,
        "headers_detected": headers,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "total_records": len(records),
        "average_confidence": round(avg_confidence, 2),
    }

    # Write staging file
    os.makedirs(staging_dir, exist_ok=True)
    basename = os.path.splitext(os.path.basename(filepath))[0]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    staging_filename = f"tier_a_{basename}_{ts}.json"
    staging_path = os.path.join(staging_dir, staging_filename)

    with open(staging_path, "w", encoding="utf-8") as f:
        json.dump(staging_data, f, indent=2, ensure_ascii=False)

    staging_data["staging_file"] = staging_path
    return staging_data


def _guess_from_headers(headers):
    """Guess target data file from column headers."""
    headers_lower = [h.lower() for h in headers]

    # Finance indicators
    finance_hints = {"금액", "헌금", "amount", "offering", "십일조", "헌금종류"}
    if any(h in finance_hints for h in headers_lower):
        return "data/finance.yaml", "offerings", "parse_offerings"

    # Newcomer indicators
    newcomer_hints = {"첫방문일", "방문경로", "first_visit", "visit_route", "새신자"}
    if any(h in newcomer_hints for h in headers_lower):
        return "data/newcomers.yaml", "newcomers", "parse_newcomers"

    # Member indicators (default for person-like data)
    member_hints = {"이름", "성명", "name", "직분", "구역", "부서"}
    if any(h in member_hints for h in headers_lower):
        return "data/members.yaml", "members", "parse_members"

    return None, None, None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Tier A Parser — Parse structured data (Excel/CSV) for church admin"
    )
    parser.add_argument(
        "--file", required=True,
        help="Path to .xlsx or .csv file to parse"
    )
    parser.add_argument(
        "--glossary", default="./data/church-glossary.yaml",
        help="Path to church-glossary.yaml (default: ./data/church-glossary.yaml)"
    )
    parser.add_argument(
        "--staging-dir", default="./inbox/staging",
        help="Directory for staging output (default: ./inbox/staging)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output full JSON result to stdout"
    )
    args = parser.parse_args()

    result = parse_file(args.file, args.glossary, args.staging_dir)

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)

    print(f"Tier A parse complete: {result['total_records']} records extracted")
    print(f"  Source:     {result['source_file']}")
    print(f"  Target:     {result['target_data_file']} [{result['target_section']}]")
    print(f"  Confidence: {result['average_confidence']:.0%}")
    print(f"  Warnings:   {len(result['parse_warnings'])}")
    if result.get("staging_file"):
        print(f"  Staging:    {result['staging_file']}")

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

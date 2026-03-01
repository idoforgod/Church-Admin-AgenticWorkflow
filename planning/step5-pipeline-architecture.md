# Step 5: Data Pipeline Architecture & Scan-and-Replicate Engine
## Church Administration AI Agentic Workflow Automation System

**Generated**: 2026-02-28
**Author Agent**: `@church-pipeline-designer`
**Input Sources**: Step 1 domain analysis, Step 2 template analysis, Step 4 data architecture spec, PRD
**Purpose**: Complete specification of the inbox/ 3-tier data pipeline, human-in-the-loop confirmation flows, scan-and-replicate template engine, error handling matrix, and integration points

---

## Table of Contents

1. [Part A: 3-Tier Pipeline Architecture](#part-a-3-tier-pipeline-architecture)
2. [Part B: Human-in-the-Loop Confirmation Flow](#part-b-human-in-the-loop-confirmation-flow)
3. [Part C: Scan-and-Replicate Engine](#part-c-scan-and-replicate-engine)
4. [Part D: Error Handling Matrix](#part-d-error-handling-matrix)
5. [Part E: Integration Points](#part-e-integration-points)
6. [Appendix: Self-Verification Report](#appendix-self-verification-report)

---

## Pipeline Overview

[trace:step-1:data-model]
[trace:step-4:schema-specs]

The inbox/ data pipeline is the primary entry point for non-technical users (PRD persona: 행정 간사 김미영, 42세, CLI 경험 없음) to feed data into the church administration system. The user places files into the `inbox/` directory structure; the pipeline automatically detects, classifies, parses, validates, previews for human confirmation, and commits data to the appropriate YAML data files.

### Architectural Principles

1. **Zero Silent Data Loss**: Every extraction failure must produce an explicit error record in `inbox/errors/`. No file is ever silently discarded or partially processed without flagging. (Inherited DNA: Quality Absolutism)
2. **Human-in-the-Loop Mandatory**: All parsed data requires human confirmation before any YAML write. No auto-commit without explicit approval. Exception: none, including high-confidence extractions. (PRD F-03)
3. **Original Preservation**: The pipeline never modifies or deletes original files. Processed files are moved to `inbox/processed/`; failed files remain in place with error metadata appended.
4. **Single Writer Respect**: The pipeline must route writes through the designated writer agent for each data file. It does not write to YAML files directly; it produces validated extraction results that the designated agent consumes. (Step 4 Layer 1: guard_data_files.py)
5. **P1 Validation Before Commit**: Every extraction result must pass the corresponding P1 deterministic validator (validate_members.py, validate_finance.py, etc.) before the human confirmation step. Invalid data is flagged, not presented for approval. (Step 4 Layer 2)

### Directory Structure

```
inbox/
├── documents/                ← Tier A + Tier B input
│   ├── 헌금내역.xlsx            → finance.yaml
│   ├── 새신자등록카드.xlsx       → newcomers.yaml
│   ├── 심방일지.docx            → members.yaml (history)
│   ├── 교인명부.csv             → members.yaml
│   └── 회의안건.pdf             → church-state.yaml (governance)
│
├── images/                   ← Tier C input
│   ├── receipt-001.jpg          → finance.yaml (expense)
│   ├── namecard-kim.jpg         → newcomers.yaml
│   └── bulletin-text.jpg        → bulletin-data.yaml
│
├── templates/                ← Scan-and-Replicate input
│   ├── bulletin-sample.jpg      → templates/bulletin-template.yaml
│   ├── receipt-form.jpg         → templates/receipt-template.yaml
│   ├── worship-order.jpg        → templates/worship-template.yaml
│   ├── letter-sample.jpg        → templates/letter-template.yaml
│   ├── meeting-minutes.jpg      → templates/minutes-template.yaml
│   ├── certificate-sample.jpg   → templates/certificate-template.yaml
│   └── invitation-sample.jpg    → templates/invitation-template.yaml
│
├── staging/                  ← Parsed results awaiting human confirmation
│   └── {timestamp}-{filename}.yaml
│
├── processed/                ← Successfully processed originals
│   └── {date}/{filename}
│
└── errors/                   ← Failed processing records
    └── {timestamp}-{filename}.error.yaml
```

---

## Part A: 3-Tier Pipeline Architecture

### A.1 Pipeline Orchestration Flow

```
inbox/{file}
    │
    ├─ [1] File Detection & Classification
    │   ├─ Extension-based tier routing
    │   ├─ MIME type verification
    │   └─ Data type inference (members? finance? schedule?)
    │
    ├─ [2] Tier-Specific Extraction
    │   ├─ Tier A: Structured (Excel/CSV)    → openpyxl / pandas
    │   ├─ Tier B: Semi-Structured (Word/PDF) → python-docx / Claude Read
    │   └─ Tier C: Unstructured (Images)      → Claude multimodal / Tesseract OCR
    │
    ├─ [3] Term Normalization
    │   └─ church-glossary.yaml lookup for Korean church terms
    │
    ├─ [4] Schema Mapping & Validation
    │   ├─ Map extracted fields to target YAML schema
    │   ├─ P1 deterministic validation (validate_*.py)
    │   └─ Confidence scoring per field
    │
    ├─ [5] Staging
    │   └─ Write to inbox/staging/{timestamp}-{filename}.yaml
    │
    ├─ [6] Human-in-the-Loop Confirmation
    │   ├─ Display parsed data preview
    │   ├─ Flag low-confidence fields
    │   └─ Accept / Reject / Edit
    │
    └─ [7] Commit
        ├─ Route to designated writer agent
        ├─ Atomic write via tempfile + rename pattern
        ├─ Move original to inbox/processed/
        └─ Log extraction metadata
```

### A.2 File Detection & Classification

[trace:step-4:schema-specs]

The first pipeline stage identifies the file type and infers the target data domain.

#### Extension-to-Tier Mapping

| Extension | Tier | Library | Notes |
|-----------|------|---------|-------|
| `.xlsx` | A (Structured) | `openpyxl` | Primary Excel format |
| `.xls` | A (Structured) | `openpyxl` (with xlrd fallback) | Legacy Excel format |
| `.csv` | A (Structured) | `pandas` | Comma/tab separated |
| `.tsv` | A (Structured) | `pandas` | Tab separated |
| `.docx` | B (Semi-Structured) | `python-docx` | Microsoft Word |
| `.pdf` | B (Semi-Structured) | Claude Read tool | PDF text extraction |
| `.hwp` | B (Semi-Structured) | Conversion guidance | HWP binary format (see HWP section) |
| `.jpg`, `.jpeg` | C (Unstructured) | Claude multimodal | Image analysis |
| `.png` | C (Unstructured) | Claude multimodal | Image analysis |
| `.heic` | C (Unstructured) | `pillow-heif` + Claude | iPhone photo format |
| `.tiff`, `.tif` | C (Unstructured) | `Pillow` + Claude | Scanned documents |

#### Data Type Inference

Data type inference determines which YAML file the extracted data targets. The inference uses a priority chain: (1) filename pattern > (2) directory hint > (3) content analysis.

**Filename Pattern Rules**:

```python
# pipeline_classifier.py — Data type inference from filename

import re

FILENAME_PATTERNS = {
    # Korean filename patterns → target data type
    r"(?:헌금|재정|finance|offering|expense|지출|수입)": "finance",
    r"(?:교인|명부|member|교적)": "members",
    r"(?:새신자|방문자|newcomer|visitor|새가족)": "newcomers",
    r"(?:주보|bulletin|소식)": "bulletin",
    r"(?:일정|행사|schedule|event|예배)": "schedule",
    r"(?:심방|visitation|돌봄)": "members_history",
    r"(?:회의|당회|제직|minutes|안건)": "governance",
    r"(?:명함|namecard|name.?card)": "newcomers",
    r"(?:영수증|receipt)": "finance_expense",
}

def infer_data_type(filename: str, content_hint: str = "") -> tuple[str, float]:
    """Infer target data type from filename. Returns (type, confidence)."""
    filename_lower = filename.lower()
    for pattern, data_type in FILENAME_PATTERNS.items():
        if re.search(pattern, filename_lower, re.IGNORECASE):
            return (data_type, 0.9)
    # Fallback: content analysis needed
    return ("unknown", 0.0)
```

**Content-Based Fallback**: When filename pattern matching returns `unknown`, the pipeline examines the file's content:
- For Excel: Check column headers against known field names from the data schemas
- For Word/PDF: Check for domain-specific keywords (e.g., "십일조", "세례", "구역")
- For images: Claude multimodal provides content classification as part of the analysis

### A.3 Tier A: Structured Data Pipeline (Excel/CSV)

[trace:step-4:schema-specs]
[trace:step-4:validation-rules]

Tier A handles the highest-confidence data extraction path. Excel and CSV files from church administration typically have consistent column structures (e.g., the standard offering ledger format used by most Korean churches).

#### A.3.1 Technology Stack

| Component | Library | Version | Purpose |
|-----------|---------|---------|---------|
| Excel reading | `openpyxl` | >= 3.1.0 | .xlsx file parsing |
| CSV reading | `pandas` | >= 2.0.0 | .csv/.tsv parsing with encoding detection |
| Encoding detection | `chardet` | >= 5.0 | EUC-KR / CP949 detection for legacy files |
| Data validation | `cerberus` or custom | N/A | Schema-based validation |

#### A.3.2 Encoding Handling

Korean church files frequently use legacy encodings. The pipeline must handle this transparently.

```python
# encoding_handler.py — Korean encoding detection and normalization

import chardet
from pathlib import Path

# Encoding priority for Korean church files
KOREAN_ENCODINGS = ["utf-8", "euc-kr", "cp949", "utf-8-sig"]

def detect_encoding(file_path: Path) -> str:
    """Detect file encoding with Korean-aware fallback chain.

    Strategy:
    1. Try chardet detection (works well for large files)
    2. If confidence < 0.7, try known Korean encodings sequentially
    3. Default to utf-8 with replacement for undecodable bytes
    """
    raw_bytes = file_path.read_bytes()

    # Step 1: chardet detection
    result = chardet.detect(raw_bytes)
    if result["confidence"] >= 0.7:
        detected = result["encoding"]
        # Normalize common Korean encoding names
        if detected and detected.lower() in ("euc-kr", "euc_kr", "iso-2022-kr"):
            return "euc-kr"
        if detected and detected.lower() in ("cp949", "ms949"):
            return "cp949"
        return detected or "utf-8"

    # Step 2: Sequential Korean encoding trial
    for enc in KOREAN_ENCODINGS:
        try:
            raw_bytes.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue

    # Step 3: Fallback with replacement
    return "utf-8"


def read_with_encoding(file_path: Path) -> str:
    """Read file content with detected encoding."""
    encoding = detect_encoding(file_path)
    return file_path.read_text(encoding=encoding, errors="replace")
```

#### A.3.3 Column Mapping Specifications

Each data type has a defined column mapping that maps common Korean column headers to the target YAML field path.

[trace:step-1:data-model]

**Members Column Mapping** (`교인명부`):

```python
MEMBERS_COLUMN_MAP = {
    # Korean header variants → YAML field path
    "이름": "name",
    "성명": "name",
    "성별": "gender",
    "남녀": "gender",
    "생년월일": "birth_date",
    "생일": "birth_date",
    "전화": "contact.phone",
    "전화번호": "contact.phone",
    "핸드폰": "contact.phone",
    "휴대폰": "contact.phone",
    "이메일": "contact.email",
    "주소": "contact.address",
    "등록일": "church.registration_date",
    "세례일": "church.baptism_date",
    "세례종류": "church.baptism_type",
    "부서": "church.department",
    "구역": "church.cell_group",
    "직분": "church.role",
    "봉사": "church.serving_area",
    "가족ID": "family.family_id",
    "가족관계": "family.relation",
    "상태": "status",

    # English variants (for bilingual spreadsheets)
    "name": "name",
    "gender": "gender",
    "phone": "contact.phone",
    "email": "contact.email",
    "address": "contact.address",
    "department": "church.department",
    "role": "church.role",
}

# Gender normalization
GENDER_MAP = {
    "남": "male", "남성": "male", "M": "male", "male": "male",
    "여": "female", "여성": "female", "F": "female", "female": "female",
}

# Role normalization (교회 직분)
ROLE_MAP = {
    "목사": "목사", "담임목사": "목사", "부목사": "목사",
    "장로": "장로",
    "집사": "집사", "안수집사": "집사",
    "권사": "권사",
    "성도": "성도", "교인": "성도", "일반": "성도",
}

# Baptism type normalization
BAPTISM_TYPE_MAP = {
    "세례": "adult", "성인세례": "adult", "일반세례": "adult",
    "유아세례": "infant", "유아": "infant",
}
```

**Finance Column Mapping** (`헌금내역`):

```python
FINANCE_COLUMN_MAP = {
    # Offering records
    "날짜": "date",
    "일자": "date",
    "예배": "service",
    "구분": "type",
    "헌금종류": "type",
    "항목": "items[].category",
    "카테고리": "items[].category",
    "금액": "items[].amount",
    "합계": "total",
    "기록자": "recorded_by",
    "확인": "verified",
    "헌금자": "items[].donor_id",

    # Expense records
    "지출일": "date",
    "지출항목": "category",
    "세부항목": "subcategory",
    "지출금액": "amount",
    "내용": "description",
    "결제방법": "payment_method",
    "승인자": "approved_by",
    "영수증": "receipt",
}

# Offering type normalization
OFFERING_TYPE_MAP = {
    "십일조": "tithe",
    "주일헌금": "sunday_offering",
    "감사헌금": "thanksgiving",
    "특별헌금": "special",
    "선교헌금": "mission",
    "주정헌금": "pledged_annual",
    "건축헌금": "building_fund",
}

# Expense category normalization
EXPENSE_CATEGORY_MAP = {
    "관리비": "관리비",
    "인건비": "인건비", "사례비": "인건비",
    "사역비": "사역비",
    "선교비": "선교비",
    "교육비": "교육비",
    "기타": "기타",
}
```

**Newcomers Column Mapping** (`새신자등록카드`):

```python
NEWCOMERS_COLUMN_MAP = {
    "이름": "name",
    "성명": "name",
    "성별": "gender",
    "출생년도": "birth_year",
    "생년": "birth_year",
    "전화": "contact.phone",
    "휴대폰": "contact.phone",
    "카카오": "contact.kakao_id",
    "카카오톡": "contact.kakao_id",
    "첫방문일": "first_visit",
    "방문일": "first_visit",
    "방문경로": "visit_route",
    "소개자": "referred_by",
    "담당자": "assigned_to",
    "배정부서": "assigned_department",
}

# Visit route normalization
VISIT_ROUTE_MAP = {
    "지인": "지인 초청", "친구": "지인 초청", "가족": "지인 초청", "소개": "지인 초청",
    "전도": "전도", "노방전도": "전도",
    "인터넷": "온라인 검색", "검색": "온라인 검색", "온라인": "온라인 검색",
    "행사": "지역사회 행사", "이벤트": "지역사회 행사",
    "기타": "기타",
}
```

#### A.3.4 Data Type Inference and Conversion

```python
# type_inference.py — Infer and convert data types from raw cell values

import re
from datetime import datetime, date

PHONE_RE = re.compile(r'^010[-.]?\d{4}[-.]?\d{4}$')
DATE_FORMATS = [
    "%Y-%m-%d",        # 2026-03-15
    "%Y.%m.%d",        # 2026.03.15
    "%Y/%m/%d",        # 2026/03/15
    "%Y년 %m월 %d일",   # 2026년 3월 15일
    "%Y년%m월%d일",      # 2026년3월15일
    "%m/%d/%Y",        # 03/15/2026 (US format from Excel)
]

def normalize_phone(raw: str) -> str | None:
    """Normalize Korean phone number to 010-NNNN-NNNN format."""
    if not raw or not isinstance(raw, str):
        return None
    digits = re.sub(r'[^\d]', '', raw)
    if len(digits) == 11 and digits.startswith("010"):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    return None  # Invalid phone

def normalize_date(raw) -> str | None:
    """Normalize date to YYYY-MM-DD format."""
    if isinstance(raw, (date, datetime)):
        return raw.strftime("%Y-%m-%d")
    if not isinstance(raw, str):
        return None
    raw = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None  # Unrecognized format

def normalize_currency(raw) -> int | None:
    """Convert currency string to integer KRW."""
    if isinstance(raw, (int, float)):
        return int(raw)
    if not isinstance(raw, str):
        return None
    # Remove currency markers and thousands separators
    cleaned = re.sub(r'[₩,원\s]', '', raw)
    try:
        return int(float(cleaned))
    except (ValueError, OverflowError):
        return None

def normalize_boolean(raw) -> bool | None:
    """Normalize boolean values from Korean/English inputs."""
    if isinstance(raw, bool):
        return raw
    if not isinstance(raw, str):
        return None
    truthy = {"o", "O", "예", "네", "y", "yes", "true", "확인", "1", "완료"}
    falsy = {"x", "X", "아니오", "아니요", "n", "no", "false", "미확인", "0", "미완"}
    if raw.strip() in truthy:
        return True
    if raw.strip() in falsy:
        return False
    return None
```

#### A.3.5 Excel Extraction Engine

```python
# excel_extractor.py — Core Excel extraction logic

import openpyxl
from pathlib import Path
from typing import Any

def extract_excel(file_path: Path, column_map: dict[str, str]) -> dict:
    """Extract structured data from an Excel file.

    Returns:
        {
            "source": str,           # original file path
            "data_type": str,        # inferred data type
            "records": list[dict],   # extracted records
            "unmapped_columns": list, # columns not in column_map
            "confidence": float,     # overall extraction confidence
            "warnings": list[str],   # non-fatal issues
            "errors": list[str],     # fatal issues
        }
    """
    result = {
        "source": str(file_path),
        "data_type": "unknown",
        "records": [],
        "unmapped_columns": [],
        "confidence": 0.0,
        "warnings": [],
        "errors": [],
    }

    try:
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    except Exception as e:
        result["errors"].append(f"Failed to open Excel file: {e}")
        return result

    ws = wb.active
    if ws is None:
        result["errors"].append("No active worksheet found")
        return result

    # Step 1: Find header row (first row with >= 3 non-empty cells)
    header_row = None
    header_values = []
    for row_idx, row in enumerate(ws.iter_rows(min_row=1, max_row=10, values_only=True), 1):
        non_empty = [c for c in row if c is not None and str(c).strip()]
        if len(non_empty) >= 3:
            header_row = row_idx
            header_values = [str(c).strip() if c else "" for c in row]
            break

    if header_row is None:
        result["errors"].append("Could not identify header row (need >= 3 non-empty cells in rows 1-10)")
        return result

    # Step 2: Map columns
    col_mapping = {}  # col_index -> yaml_field_path
    for col_idx, header in enumerate(header_values):
        if header in column_map:
            col_mapping[col_idx] = column_map[header]
        elif header:
            result["unmapped_columns"].append(header)

    mapped_ratio = len(col_mapping) / max(len([h for h in header_values if h]), 1)

    if mapped_ratio < 0.3:
        result["warnings"].append(
            f"Low column mapping rate: {mapped_ratio:.0%}. "
            f"Unmapped: {result['unmapped_columns']}"
        )

    # Step 3: Extract records
    for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
        if all(c is None for c in row):
            continue  # Skip empty rows

        record = {}
        field_confidences = []

        for col_idx, field_path in col_mapping.items():
            if col_idx < len(row):
                raw_value = row[col_idx]
                if raw_value is not None:
                    record[field_path] = raw_value
                    field_confidences.append(1.0)  # Direct cell value
                else:
                    field_confidences.append(0.0)

        if record:  # At least one mapped field has data
            record["_extraction_confidence"] = (
                sum(field_confidences) / len(field_confidences) if field_confidences else 0.0
            )
            result["records"].append(record)

    # Step 4: Calculate overall confidence
    if result["records"]:
        avg_record_confidence = sum(
            r.get("_extraction_confidence", 0) for r in result["records"]
        ) / len(result["records"])
        result["confidence"] = round(min(mapped_ratio, avg_record_confidence), 2)

    wb.close()
    return result
```

#### A.3.6 CSV Extraction Engine

```python
# csv_extractor.py — CSV extraction with encoding detection

import pandas as pd
from pathlib import Path

def extract_csv(file_path: Path, column_map: dict[str, str]) -> dict:
    """Extract structured data from a CSV file.

    Handles encoding detection for legacy Korean files (EUC-KR, CP949).
    """
    result = {
        "source": str(file_path),
        "data_type": "unknown",
        "records": [],
        "unmapped_columns": [],
        "confidence": 0.0,
        "warnings": [],
        "errors": [],
    }

    # Detect encoding
    encoding = detect_encoding(file_path)

    # Detect separator
    sample = file_path.read_text(encoding=encoding, errors="replace")[:2000]
    separator = "\t" if sample.count("\t") > sample.count(",") else ","

    try:
        df = pd.read_csv(
            file_path,
            encoding=encoding,
            sep=separator,
            dtype=str,         # Read all as strings initially
            na_values=["", "N/A", "없음", "-"],
            keep_default_na=True,
        )
    except Exception as e:
        result["errors"].append(f"Failed to read CSV: {e}")
        return result

    if df.empty:
        result["errors"].append("CSV file is empty or has no data rows")
        return result

    # Map columns (same logic as Excel)
    col_mapping = {}
    for col in df.columns:
        col_stripped = col.strip()
        if col_stripped in column_map:
            col_mapping[col] = column_map[col_stripped]
        else:
            result["unmapped_columns"].append(col_stripped)

    mapped_ratio = len(col_mapping) / max(len(df.columns), 1)

    # Extract records
    for _, row in df.iterrows():
        record = {}
        for csv_col, yaml_path in col_mapping.items():
            val = row.get(csv_col)
            if pd.notna(val):
                record[yaml_path] = str(val).strip()

        if record:
            record["_extraction_confidence"] = mapped_ratio
            result["records"].append(record)

    result["confidence"] = round(mapped_ratio, 2)
    return result
```

### A.4 Tier B: Semi-Structured Document Pipeline (Word/PDF)

[trace:step-4:schema-specs]

Tier B handles documents with natural language content that requires structured extraction. The confidence level is lower than Tier A, and human review is more critical.

#### A.4.1 Technology Stack

| Component | Library | Purpose |
|-----------|---------|---------|
| Word (.docx) | `python-docx` | Document structure + text extraction |
| PDF | Claude Read tool | PDF text extraction via Claude's built-in capability |
| HWP (.hwp) | Conversion guidance | User-directed PDF export (see A.4.4) |
| NER | Custom regex + Claude | Named entity extraction for Korean text |

#### A.4.2 Word Document Extraction

```python
# word_extractor.py — Extract structured data from Word documents

from docx import Document
from pathlib import Path
import re

def extract_word(file_path: Path, data_type: str) -> dict:
    """Extract data from a Word document based on inferred data type.

    Word documents are semi-structured: they may contain tables (higher confidence)
    or free-text paragraphs (lower confidence, requires NER).
    """
    result = {
        "source": str(file_path),
        "data_type": data_type,
        "records": [],
        "tables_found": 0,
        "paragraphs_found": 0,
        "confidence": 0.0,
        "warnings": [],
        "errors": [],
    }

    try:
        doc = Document(file_path)
    except Exception as e:
        result["errors"].append(f"Failed to open Word document: {e}")
        return result

    # Strategy 1: Extract from tables (higher confidence)
    for table in doc.tables:
        result["tables_found"] += 1
        headers = [cell.text.strip() for cell in table.rows[0].cells]

        for row in table.rows[1:]:
            record = {}
            for idx, cell in enumerate(row.cells):
                if idx < len(headers) and headers[idx]:
                    record[headers[idx]] = cell.text.strip()
            if record:
                record["_extraction_confidence"] = 0.85  # Table extraction
                record["_extraction_method"] = "table"
                result["records"].append(record)

    # Strategy 2: Extract from paragraphs (lower confidence, NER)
    if not result["records"]:
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        result["paragraphs_found"] = len(paragraphs)

        full_text = "\n".join(paragraphs)
        entities = extract_korean_entities(full_text)

        if entities:
            record = entities
            record["_extraction_confidence"] = 0.55  # NER extraction
            record["_extraction_method"] = "paragraph_ner"
            record["_raw_text"] = full_text[:2000]  # Preserve for review
            result["records"].append(record)

    # Calculate confidence
    if result["records"]:
        result["confidence"] = round(
            sum(r.get("_extraction_confidence", 0) for r in result["records"])
            / len(result["records"]),
            2
        )

    return result
```

#### A.4.3 PDF Extraction via Claude Read Tool

PDF extraction leverages Claude's built-in Read tool capability, which provides accurate text extraction including Korean character handling.

```python
# pdf_extractor.py — PDF extraction strategy

def create_pdf_extraction_prompt(file_path: str, data_type: str) -> str:
    """Generate the prompt for Claude Read tool PDF extraction.

    The Claude agent uses Read tool to view the PDF, then extracts structured data
    based on the expected data type.
    """
    type_prompts = {
        "members": (
            "Extract all member records from this document. "
            "For each person, extract: name (이름/성명), phone (전화번호), "
            "gender (성별), birth_date (생년월일), department (부서), "
            "role (직분), cell_group (구역), address (주소). "
            "Return as a structured list."
        ),
        "finance": (
            "Extract all financial records from this document. "
            "For each entry, extract: date (날짜), category (항목/구분), "
            "amount (금액, as integer in KRW), description (내용), "
            "and whether it is income or expense. "
            "Return as a structured list."
        ),
        "newcomers": (
            "Extract newcomer registration information. "
            "For each person, extract: name (이름), phone (연락처), "
            "first_visit_date (방문일), visit_route (방문경로), "
            "referrer (소개자). Return as a structured list."
        ),
        "governance": (
            "Extract meeting agenda items from this document. "
            "For each agenda item, extract: number (안건번호), "
            "title (제목), content (내용), decision type (의결방법). "
            "Return as a structured list."
        ),
    }

    base = type_prompts.get(data_type, "Extract all structured data from this document.")
    return (
        f"{base}\n\n"
        f"IMPORTANT: Return data in YAML format. "
        f"Use Korean field names as-is. "
        f"For currency amounts, provide integer values only (no commas or won sign). "
        f"For dates, use YYYY-MM-DD format. "
        f"For phone numbers, use 010-NNNN-NNNN format."
    )
```

**PDF Extraction Confidence**: PDF extraction through Claude Read tool receives a base confidence of 0.70. This is adjusted based on:
- Scanned vs. digital PDF: Digital PDFs get +0.15; scanned PDFs get -0.10
- Korean text density: High Korean text density indicates church document, +0.05
- Table presence: Structured tables raise confidence by +0.10

#### A.4.4 HWP File Handling

HWP (한글) is the proprietary file format of the Hangul word processor, ubiquitous in Korean organizations. The HWP binary format is not reliably parseable by open-source libraries. The pipeline provides a user-guided conversion path.

**HWP Processing Strategy**:

```
inbox/documents/공문.hwp
    │
    ├─ [1] Detect .hwp extension
    │
    ├─ [2] Check for pyhwp availability
    │   ├─ Available: Attempt extraction (unreliable, confidence 0.40)
    │   └─ Not available: Skip to user guidance
    │
    ├─ [3] Generate user guidance message
    │   └─ "HWP 파일이 감지되었습니다. PDF로 변환 후 다시 올려주세요.
    │      한글(HWP) 프로그램에서: 파일 → 다른 이름으로 저장 → PDF 선택
    │      또는 한글 뷰어에서: 파일 → PDF로 내보내기"
    │
    └─ [4] Move to inbox/errors/ with conversion instructions
        └─ {timestamp}-공문.hwp.error.yaml
            conversion_guidance: "PDF로 변환 필요"
            original_preserved: true
```

**pyhwp Fallback** (when available):

```python
# hwp_handler.py — Best-effort HWP text extraction

def attempt_hwp_extraction(file_path: Path) -> dict:
    """Attempt HWP extraction using pyhwp. Low confidence due to format limitations."""
    result = {
        "source": str(file_path),
        "data_type": "unknown",
        "records": [],
        "confidence": 0.40,  # Low confidence for HWP extraction
        "warnings": ["HWP extraction is best-effort. Consider PDF conversion for accuracy."],
        "errors": [],
    }

    try:
        import hwp5
        # pyhwp extraction logic here
        # ...
        result["warnings"].append("HWP extracted via pyhwp — verify all data manually")
    except ImportError:
        result["errors"].append(
            "pyhwp not installed. Please convert HWP to PDF: "
            "한글 프로그램 → 파일 → 다른 이름으로 저장 → PDF"
        )
        result["confidence"] = 0.0

    return result
```

#### A.4.5 Named Entity Extraction for Korean Text

[trace:step-1:data-model]

Korean church documents contain specific named entities that must be extracted accurately.

```python
# korean_ner.py — Korean Named Entity Recognition for church documents

import re

# Korean name pattern: 2-4 Korean syllables
KOREAN_NAME_RE = re.compile(r'[가-힣]{2,4}')

# Korean phone: 010-NNNN-NNNN (with various separators)
PHONE_RE = re.compile(r'010[-.\s]?\d{4}[-.\s]?\d{4}')

# Korean date patterns
DATE_PATTERNS = [
    re.compile(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일'),  # 2026년 3월 15일
    re.compile(r'(\d{4})[./\-](\d{1,2})[./\-](\d{1,2})'),  # 2026-03-15, 2026.03.15
]

# Currency patterns (KRW)
CURRENCY_RE = re.compile(r'(?:₩|금\s*)?(\d{1,3}(?:,\d{3})*)\s*(?:원|won)?')

# Church role patterns
ROLE_RE = re.compile(r'(목사|장로|집사|권사|성도|전도사|사모)')

# Church term patterns (for church-glossary.yaml lookup)
CHURCH_TERM_PATTERNS = [
    re.compile(r'(십일조|감사헌금|주일헌금|특별헌금|선교헌금|건축헌금)'),
    re.compile(r'(주일예배|수요예배|새벽기도|금요기도|청년예배)'),
    re.compile(r'(세례|유아세례|입교|이명|제적)'),
    re.compile(r'(당회|제직회|공동의회|구역|셀)'),
]

def extract_korean_entities(text: str) -> dict:
    """Extract named entities from Korean church document text.

    Returns dict of extracted entities with per-field confidence.
    """
    entities = {}

    # Extract names
    names = KOREAN_NAME_RE.findall(text)
    # Filter out common non-name Korean words
    NON_NAMES = {"교회", "목사", "장로", "집사", "세례", "헌금", "예배", "안건", "결의",
                 "감사", "선교", "교육", "봉사", "구역", "부서", "위원", "기도"}
    names = [n for n in names if n not in NON_NAMES]
    if names:
        entities["names"] = names
        entities["names_confidence"] = 0.6  # Name extraction is ambiguous

    # Extract phone numbers
    phones = PHONE_RE.findall(text)
    if phones:
        entities["phones"] = [normalize_phone(p) for p in phones]
        entities["phones_confidence"] = 0.95  # Phone format is unambiguous

    # Extract dates
    dates = []
    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(text):
            y, m, d = match.groups()
            dates.append(f"{y}-{int(m):02d}-{int(d):02d}")
    if dates:
        entities["dates"] = dates
        entities["dates_confidence"] = 0.90

    # Extract currency amounts
    amounts = []
    for match in CURRENCY_RE.finditer(text):
        amount_str = match.group(1).replace(",", "")
        try:
            amounts.append(int(amount_str))
        except ValueError:
            pass
    if amounts:
        entities["amounts"] = amounts
        entities["amounts_confidence"] = 0.85

    # Extract church roles
    roles = ROLE_RE.findall(text)
    if roles:
        entities["roles"] = list(set(roles))
        entities["roles_confidence"] = 0.90

    return entities
```

### A.5 Tier C: Unstructured Data Pipeline (Images)

[trace:step-4:schema-specs]

Tier C handles the lowest-confidence but highest-convenience data path: users photograph namecards, receipts, or handwritten documents and drop them into `inbox/images/`.

#### A.5.1 Technology Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| Image understanding | Claude multimodal (Read tool) | Primary analysis for structured content |
| OCR (Korean) | `Tesseract` + `kor` language pack | Fallback for dense text or low-quality images |
| Image preprocessing | `Pillow` | Rotation correction, contrast enhancement |
| HEIC conversion | `pillow-heif` | iPhone HEIC format to JPEG conversion |

#### A.5.2 Image Classification and Routing

```python
# image_classifier.py — Classify image content and route to appropriate extractor

def classify_image_content(file_path: str) -> dict:
    """Use Claude multimodal to classify image content.

    Claude Read tool views the image and classifies it into:
    - namecard: business/name card → newcomers.yaml
    - receipt: financial receipt → finance.yaml (expense)
    - offering_envelope: offering envelope → finance.yaml (offering)
    - document_photo: photographed church document → route to Tier B
    - bulletin_text: bulletin content photo → bulletin-data.yaml
    - handwritten: handwritten notes → low confidence, manual review
    - unknown: unrecognizable content
    """
    # Classification prompt for Claude multimodal
    classification_prompt = """
    Analyze this image and classify it into one of these categories:
    1. namecard — A business card or visitor card with name and contact info
    2. receipt — A financial receipt, invoice, or payment record
    3. offering_envelope — A church offering envelope with amount and category
    4. document_photo — A photo of a printed church document
    5. bulletin_text — A photo of bulletin content or announcement text
    6. handwritten — Handwritten notes or records
    7. unknown — Cannot determine content

    Return:
    - category: one of the above
    - confidence: 0.0 to 1.0
    - description: brief description of what you see
    - language: primary language detected
    """
    # This is executed by the Claude agent using Read tool on the image
    return {
        "classification_prompt": classification_prompt,
        "file_path": file_path,
    }
```

#### A.5.3 Namecard Extraction (명함 → newcomers.yaml)

```python
# namecard_extractor.py — Extract member/newcomer data from business cards

def create_namecard_extraction_prompt() -> str:
    """Prompt for Claude multimodal namecard extraction."""
    return """
    Extract all information from this business/visitor card:

    Required fields:
    - name (이름): Full Korean name. If both Korean and English present, use Korean.
    - phone (전화번호): Mobile phone in 010-NNNN-NNNN format.

    Optional fields:
    - email: Email address if present
    - organization (소속): Company or organization name
    - title (직책): Job title or position
    - address (주소): Address if present
    - kakao_id: KakaoTalk ID if present

    Return as YAML. For each field, also provide a confidence score (0.0-1.0).
    If a field is partially visible or unclear, set confidence below 0.7.
    If text is in a non-standard orientation, note this in warnings.
    """

# Expected extraction result structure:
NAMECARD_SCHEMA = {
    "name": {"type": "string", "required": True, "target": "newcomers[].name"},
    "phone": {"type": "phone", "required": True, "target": "newcomers[].contact.phone"},
    "email": {"type": "email", "required": False, "target": "newcomers[].contact.email"},
    "organization": {"type": "string", "required": False, "target": "_metadata.organization"},
    "title": {"type": "string", "required": False, "target": "_metadata.title"},
    "address": {"type": "string", "required": False, "target": "_metadata.address"},
}

# Base confidence for namecard extraction
NAMECARD_BASE_CONFIDENCE = 0.75
```

#### A.5.4 Receipt Extraction (영수증 → finance.yaml)

```python
# receipt_extractor.py — Extract financial data from receipt images

def create_receipt_extraction_prompt() -> str:
    """Prompt for Claude multimodal receipt extraction."""
    return """
    Extract financial information from this receipt/invoice:

    Required fields:
    - date (날짜): Transaction date in YYYY-MM-DD format
    - total_amount (총액): Total amount in integer KRW (no commas or currency symbol)
    - vendor (가맹점): Store or vendor name

    Optional fields:
    - items: List of line items, each with name and amount
    - payment_method (결제방법): cash/card/transfer (현금/카드/이체)
    - receipt_number (영수증번호): Receipt or transaction number
    - card_last_four: Last 4 digits of card if visible

    IMPORTANT:
    - All amounts must be integers (Korean Won has no decimal places)
    - Verify that item amounts sum to total_amount
    - If the receipt is partially obscured, flag those fields with confidence < 0.5

    Return as YAML with per-field confidence scores.
    """

# Financial extraction requires higher scrutiny
RECEIPT_BASE_CONFIDENCE = 0.65  # Lower base — finance data needs human verification
```

#### A.5.5 Document Photo Extraction

When a user photographs a printed church document rather than scanning it, the image quality may be lower (skew, shadows, partial visibility). The pipeline routes these to a combined Claude multimodal + OCR strategy.

```python
# document_photo_extractor.py

def extract_document_photo(file_path: str, data_type: str) -> dict:
    """Extract data from a photographed document.

    Strategy:
    1. Claude multimodal for content understanding (primary)
    2. Tesseract OCR for Korean text extraction (supplementary)
    3. Cross-validate Claude output against OCR text
    """
    result = {
        "source": file_path,
        "data_type": data_type,
        "confidence": 0.55,  # Base confidence for document photos
        "extraction_strategy": "multimodal_with_ocr_validation",
        "records": [],
        "warnings": ["Extracted from photograph — verify all fields manually"],
        "errors": [],
    }

    # Step 1: Preprocess image
    preprocessing_steps = [
        "auto_rotate",        # Correct orientation using EXIF data
        "deskew",             # Correct document skew
        "enhance_contrast",   # Improve text readability
        "denoise",            # Reduce photographic noise
    ]

    # Step 2: Claude multimodal extraction (primary)
    # Uses Read tool on the image with data-type-specific prompt

    # Step 3: Tesseract OCR (supplementary, for cross-validation)
    # pytesseract.image_to_string(image, lang='kor+eng')

    # Step 4: Cross-validate
    # Compare key entities (names, amounts, dates) between Claude and OCR
    # Raise confidence if both agree; lower if they disagree

    return result
```

#### A.5.6 OCR Configuration for Korean Text

```python
# ocr_config.py — Tesseract OCR configuration for Korean church documents

import subprocess
from pathlib import Path

def check_tesseract_korean() -> bool:
    """Verify Tesseract OCR is installed with Korean language pack."""
    try:
        result = subprocess.run(
            ["tesseract", "--list-langs"],
            capture_output=True, text=True, timeout=5
        )
        return "kor" in result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def install_guidance() -> str:
    """Return installation guidance for Tesseract + Korean."""
    return """
    Tesseract OCR Korean 설치 안내:

    macOS:
      brew install tesseract
      brew install tesseract-lang  # includes Korean

    Ubuntu/Debian:
      sudo apt install tesseract-ocr tesseract-ocr-kor

    Windows:
      1. Download installer from https://github.com/UB-Mannheim/tesseract/wiki
      2. During install, select "Korean" under additional languages
    """

# Tesseract configuration for Korean church documents
TESSERACT_CONFIG = {
    "lang": "kor+eng",       # Korean primary, English secondary
    "psm": 6,                # Assume uniform block of text
    "oem": 3,                # Default OCR engine (LSTM)
    "config": "--dpi 300",   # Assume 300 DPI for quality
}
```

---

## Part B: Human-in-the-Loop Confirmation Flow

[trace:step-4:validation-rules]

All parsed data must pass through a human confirmation gate before being written to any YAML data file. This is a non-negotiable architectural requirement (PRD F-03).

### B.1 Confirmation Flow Architecture

```
Extraction Result
    │
    ├─ [1] P1 Validation
    │   ├─ Run validate_*.py for target data type
    │   ├─ PASS → proceed to staging
    │   └─ FAIL → flag errors, still stage for review (with error annotations)
    │
    ├─ [2] Staging
    │   └─ Write to inbox/staging/{timestamp}-{filename}.yaml
    │       Includes: extracted data + confidence scores + validation results
    │
    ├─ [3] Preview Generation
    │   ├─ Render extracted data in human-readable format
    │   ├─ Highlight low-confidence fields (< 0.7) in yellow
    │   ├─ Highlight validation failures in red
    │   └─ Show original file reference for comparison
    │
    ├─ [4] Human Decision
    │   ├─ APPROVE → proceed to commit
    │   ├─ EDIT → modify specific fields, re-validate, re-approve
    │   └─ REJECT → move to inbox/errors/ with rejection reason
    │
    └─ [5] Commit
        ├─ Route to designated writer agent
        ├─ Atomic write to target YAML
        ├─ Move original to inbox/processed/{date}/
        ├─ Clean up staging file
        └─ Log audit trail
```

### B.2 Confidence Scoring System

Each extracted field receives a confidence score between 0.0 and 1.0. The score determines the review level required.

#### B.2.1 Confidence Score Calculation

```python
# confidence_scorer.py — Per-field and per-record confidence scoring

from dataclasses import dataclass
from enum import Enum

class ReviewLevel(Enum):
    AUTO_ELIGIBLE = "auto_eligible"      # >= 0.9, non-finance only
    STANDARD_REVIEW = "standard_review"  # >= 0.7
    MANDATORY_REVIEW = "mandatory_review" # < 0.7
    MANUAL_ENTRY = "manual_entry"        # < 0.3

@dataclass
class ConfidenceScore:
    field_name: str
    score: float
    source_tier: str           # "A", "B", "C"
    extraction_method: str     # "cell_value", "table", "ner", "multimodal", "ocr"
    review_level: ReviewLevel
    reason: str                # Why this confidence level

# Tier-based confidence multipliers
TIER_BASE_CONFIDENCE = {
    "A": 0.95,  # Excel/CSV — structured, high reliability
    "B": 0.70,  # Word/PDF — semi-structured, moderate reliability
    "C": 0.55,  # Images — unstructured, requires verification
}

# Method-based confidence adjustments
METHOD_ADJUSTMENTS = {
    "cell_value": 0.0,          # Direct cell read — no adjustment
    "table": -0.05,             # Table extraction — slight uncertainty
    "column_mapping": -0.10,    # Header mapping might be imprecise
    "ner_regex": -0.15,         # Regex NER — pattern matching ambiguity
    "ner_claude": -0.20,        # LLM NER — model uncertainty
    "multimodal": -0.25,        # Image understanding — visual ambiguity
    "ocr": -0.30,               # OCR — character recognition errors
    "ocr_handwritten": -0.45,   # Handwritten OCR — very unreliable
}

# Field type confidence bonuses
FIELD_TYPE_BONUSES = {
    "phone": 0.10,       # Phone numbers have strict format → easy to validate
    "date": 0.05,        # Dates have recognizable format
    "currency": -0.05,   # Currency amounts have high error cost
    "name": -0.05,       # Korean names are short, ambiguous with other words
    "enum": 0.10,        # Enums can be validated against known sets
    "free_text": -0.15,  # Free text is hardest to validate
}

def calculate_confidence(
    tier: str,
    method: str,
    field_type: str,
    validation_passed: bool,
) -> ConfidenceScore:
    """Calculate confidence score for a single extracted field."""
    base = TIER_BASE_CONFIDENCE.get(tier, 0.5)
    method_adj = METHOD_ADJUSTMENTS.get(method, -0.20)
    type_bonus = FIELD_TYPE_BONUSES.get(field_type, 0.0)
    validation_bonus = 0.05 if validation_passed else -0.15

    score = max(0.0, min(1.0, base + method_adj + type_bonus + validation_bonus))

    # Determine review level
    if score >= 0.9:
        review = ReviewLevel.AUTO_ELIGIBLE
    elif score >= 0.7:
        review = ReviewLevel.STANDARD_REVIEW
    elif score >= 0.3:
        review = ReviewLevel.MANDATORY_REVIEW
    else:
        review = ReviewLevel.MANUAL_ENTRY

    return ConfidenceScore(
        field_name="",  # Set by caller
        score=round(score, 2),
        source_tier=tier,
        extraction_method=method,
        review_level=review,
        reason=f"base={base}, method={method_adj}, type={type_bonus}, valid={validation_bonus}",
    )
```

#### B.2.2 Review Level Rules

| Confidence Range | Review Level | Behavior | Applicable Data Types |
|-----------------|-------------|----------|----------------------|
| >= 0.9 | Auto-Approve Eligible | Presented for review, pre-approved checkbox. User can still reject. **Except finance data: always requires explicit approval.** | Members, Schedule, Bulletin, Newcomers |
| 0.7 - 0.89 | Standard Review | Presented for review. User must explicitly approve each record. | All data types |
| 0.3 - 0.69 | Mandatory Review | Highlighted in yellow. User must review AND confirm each flagged field individually. | All data types |
| < 0.3 | Manual Entry Required | Extraction shown as reference only. User must re-enter data manually. Field is pre-populated but marked unreliable. | All data types |

**Finance Data Special Rule**: All finance-related data (offerings, expenses, budgets) requires explicit human approval regardless of confidence score. Auto-approve is permanently disabled for finance data. (PRD F-03: "재정 관련 업무는 Autopilot 대상에서 영구 제외")

### B.3 Staging File Format

```yaml
# inbox/staging/20260301-143025-헌금내역.yaml
# Auto-generated by pipeline — awaiting human confirmation

_pipeline_metadata:
  source_file: "inbox/documents/헌금내역.xlsx"
  source_tier: "A"
  extraction_timestamp: "2026-03-01T14:30:25"
  target_data_file: "data/finance.yaml"
  target_writer_agent: "finance-recorder"
  overall_confidence: 0.92
  validation_status: "passed"  # or "failed" with error list
  validation_errors: []
  validation_warnings:
    - "F5: Monthly summary will need recomputation after import"
  review_level: "standard_review"  # finance always standard or higher
  auto_approve_eligible: false     # finance: always false

records:
  - _record_index: 0
    _record_confidence: 0.95
    _flagged_fields: []
    date: "2026-02-23"
    service: "주일예배 1부"
    type: "sunday_offering"
    items:
      - category: "십일조"
        amount: 4250000
        _confidence: 0.98
      - category: "감사헌금"
        amount: 890000
        _confidence: 0.95
    total: 5140000
    recorded_by: "재정담당집사"
    verified: false  # pipeline sets false — human must verify

  - _record_index: 1
    _record_confidence: 0.72
    _flagged_fields:
      - field: "items[1].amount"
        confidence: 0.65
        reason: "Cell formatting ambiguous — could be 1,230,000 or 123,000"
    date: "2026-02-23"
    service: "주일예배 2부"
    type: "sunday_offering"
    items:
      - category: "주일헌금"
        amount: 1540000
        _confidence: 0.92
      - category: "특별헌금"
        amount: 1230000
        _confidence: 0.65  # FLAGGED
    total: 2770000
```

### B.4 Preview Display Format

The human confirmation interface presents extracted data in a clear, reviewable format. Since the system operates through Claude Code CLI, the preview is text-based.

```
╔══════════════════════════════════════════════════════════════╗
║  DATA IMPORT PREVIEW — 헌금내역.xlsx                         ║
║  Tier: A (Structured)  │  Target: finance.yaml              ║
║  Confidence: 0.92      │  Validation: PASSED                ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Record 1/2  [Confidence: 0.95]                              ║
║  ─────────────────────────────                               ║
║  날짜:    2026-02-23                                          ║
║  예배:    주일예배 1부                                          ║
║  구분:    sunday_offering                                     ║
║  항목:                                                        ║
║    ✅ 십일조     ₩4,250,000  [0.98]                           ║
║    ✅ 감사헌금   ₩  890,000  [0.95]                           ║
║  합계:   ₩5,140,000  (검산: ✅ 일치)                           ║
║                                                              ║
║  Record 2/2  [Confidence: 0.72]                              ║
║  ─────────────────────────────                               ║
║  날짜:    2026-02-23                                          ║
║  예배:    주일예배 2부                                          ║
║  구분:    sunday_offering                                     ║
║  항목:                                                        ║
║    ✅ 주일헌금   ₩1,540,000  [0.92]                           ║
║    ⚠️  특별헌금   ₩1,230,000  [0.65] ← 확인 필요              ║
║       Reason: Cell formatting ambiguous                      ║
║  합계:   ₩2,770,000  (검산: ✅ 일치)                           ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  Actions:                                                    ║
║  [1] 승인 (Approve all)                                       ║
║  [2] 개별 수정 후 승인 (Edit flagged fields)                    ║
║  [3] 거부 (Reject — return to inbox)                          ║
╚══════════════════════════════════════════════════════════════╝
```

### B.5 Error Recovery and Manual Correction

When a user chooses to edit, the pipeline supports field-level correction:

```python
# correction_handler.py — Handle manual corrections

def apply_correction(staging_file: str, corrections: dict) -> dict:
    """Apply user corrections to staged extraction result.

    Args:
        staging_file: Path to the staging YAML file
        corrections: Dict of field_path → corrected_value
            e.g., {"records[1].items[1].amount": 123000}

    Returns:
        Updated staging data with corrections applied and re-validated.
    """
    # 1. Load staging file
    # 2. Apply corrections at specified field paths
    # 3. Re-run P1 validation on modified data
    # 4. Update confidence (corrected fields get 1.0 — human verified)
    # 5. Re-save staging file
    # 6. Re-present for final approval
    pass
```

**Correction Audit Trail**: Every correction is logged in the staging file's `_pipeline_metadata.corrections` field:

```yaml
_pipeline_metadata:
  corrections:
    - field: "records[1].items[1].amount"
      original_value: 1230000
      corrected_value: 123000
      corrected_by: "human"
      correction_timestamp: "2026-03-01T14:35:12"
      reason: "Excel formatting caused 10x misread"
```

---

## Part C: Scan-and-Replicate Engine

[trace:step-2:template-analysis]

The Scan-and-Replicate engine enables church administrators to upload images or PDFs of their existing document formats, have the system analyze the layout structure, generate a reusable template, and then automatically produce documents in that format using data from the YAML data files.

### C.1 Scan-and-Replicate Architecture Overview

```
inbox/templates/{category}-sample.{jpg|pdf}
    │
    ├─ Stage 1: Image/PDF Analysis (Claude Multimodal)
    │   ├─ Fixed region detection (church identity anchors)
    │   ├─ Variable region detection (data-driven slots)
    │   ├─ Layout extraction (grid, columns, font zones, margins)
    │   └─ Seal zone identification (직인 — critical)
    │
    ├─ Stage 2: Template YAML Generation
    │   ├─ {category}-template.yaml (machine-processable structure)
    │   ├─ Fixed regions → hardcoded content
    │   ├─ Variable regions → data source mapping
    │   └─ Layout → rendering instructions
    │
    ├─ Stage 3: Human Confirmation (First Run Only)
    │   ├─ Present template structure for review
    │   ├─ Verify fixed vs variable classification
    │   ├─ Verify data source mappings
    │   ├─ Confirm layout interpretation
    │   └─ Set confirmed_by + confirmed_date
    │
    └─ Stage 4: Document Generation (Repeatable)
        ├─ Load confirmed template
        ├─ Resolve data sources (YAML files)
        ├─ Apply term normalization (church-glossary.yaml)
        ├─ Render Markdown output
        └─ Save to output directory
```

### C.2 Stage 1: Image Analysis — Layout Structure Detection

#### C.2.1 Analysis Prompt Template

The Claude multimodal analysis uses a structured prompt to ensure consistent, machine-parseable output across all 7 document types.

```python
# template_analyzer.py — Claude multimodal template analysis

def create_template_analysis_prompt(category: str) -> str:
    """Generate analysis prompt for a specific document category.

    The prompt instructs Claude to identify fixed regions, variable regions,
    layout structure, and special zones (seal, signature).
    """
    category_context = CATEGORY_CONTEXTS.get(category, "")

    return f"""
Analyze this Korean church document image to extract its template structure.
Document type: {category}
{category_context}

## Instructions

### 1. Fixed Regions (고정 영역)
Identify ALL regions that would remain identical across every instance of this document type:
- Church name banner (교회명)
- Church logo/cross symbol (로고/십자가)
- Denomination header (교단 명칭)
- Document type labels (문서 종류 라벨)
- Section header labels (섹션 제목)
- Address/contact blocks (주소/연락처)
- Decorative borders/frames (장식 테두리)
- Legal text (법적 문구) — especially for receipts
- Biblical verses (성경 구절) — especially for certificates

For each fixed region, provide:
- id: FR-{{category_code}}-NN
- name: descriptive English name
- korean_name: Korean name
- content: exact text content (preserve Korean formatting, spaces)
- position: approximate position (top_mm, left_mm, width, height)
- font: observed font characteristics (serif/sans-serif, size estimate, weight, alignment)

### 2. Variable Regions (가변 영역)
Identify ALL regions that change between document instances:
- Dates, numbers, names, amounts
- Lists (worship order items, announcements, attendee lists)
- Free-text content (letter body, meeting minutes)
- Calculated fields (totals, quorum verification)

For each variable region, provide:
- id: VR-{{category_code}}-NN
- name: descriptive English name
- korean_name: Korean name
- slot_type: string | integer | date | time | currency | enum | list[string] | list[object] | text
- position: approximate position
- format: display format pattern (e.g., "제 {{value}}호", "{{year}}년 {{month}}월 {{day}}일")
- nullable: true if the field may be absent in some instances

### 3. Special Zones
- Seal zone (직인 위치): CRITICAL — identify exact position. Mark as NO_VARIABLE_CONTENT.
- Signature lines (서명란): Position and label text
- Reserved whitespace: Intentional blank areas

### 4. Layout Structure
- Paper size: A4, A5, B5, custom
- Orientation: portrait, landscape
- Number of columns
- Margin estimates (mm)
- Column gap (mm)
- Number of logical pages

Return your analysis as YAML.
"""

CATEGORY_CONTEXTS = {
    "bulletin": "주보 (Weekly Church Bulletin). Most frequently produced document. "
                "Typically A4 or B5 folded, 2-column layout. Contains sermon info, "
                "worship order, announcements, prayer requests, celebrations.",
    "receipt": "기부금영수증 (Tax Donation Receipt). Legally significant document. "
               "Must contain specific fields required by 소득세법 시행령 §80①5호. "
               "Church seal (직인) is mandatory for legal validity.",
    "worship_order": "예배 순서지 (Order of Worship). Single-service focus. "
                     "Typically A5 or A4 half-page. Ordered list format.",
    "official_letter": "공문 (Official Letter). Highly standardized Korean administrative format. "
                       "Sequential numbering, formal field labels, mandatory seal.",
    "meeting_minutes": "회의록 (Meeting Minutes). 당회/제직회 records. "
                       "Formal parliamentary style. Quorum verification required.",
    "certificate": "세례증서/이명증서 (Baptism/Transfer Certificate). "
                   "Formal, decorative layout. Prominent seal placement. "
                   "May have variants: 세례, 이명, 유아세례.",
    "invitation": "초청장 (Event Invitation). Less standardized. "
                  "Typically A5. Event-specific branding.",
}
```

#### C.2.2 Fixed vs Variable Region Classification Algorithm

[trace:step-2:template-analysis]

The classification algorithm determines whether a detected region is fixed (church identity anchor) or variable (data-driven slot). For first-run analysis (single sample), Claude multimodal performs the classification heuristically. For refined analysis (multiple samples available), a deterministic comparison is used.

**Single-Sample Heuristics** (first run):

| Signal | Classification | Confidence |
|--------|---------------|------------|
| Church name text | Fixed | 0.99 |
| Logo/cross image | Fixed | 0.99 |
| Denomination name | Fixed | 0.95 |
| Section header labels (e.g., "공지사항", "기도제목") | Fixed | 0.90 |
| Address/phone block | Fixed | 0.90 |
| Decorative border | Fixed | 0.95 |
| Date field | Variable | 0.99 |
| Person name in content area | Variable | 0.90 |
| Numbered items list | Variable | 0.95 |
| Currency amount | Variable | 0.99 |
| Body text paragraph | Variable | 0.85 |

**Multi-Sample Comparison** (when 2+ samples available):

```python
def classify_regions_multi_sample(samples: list[dict]) -> dict:
    """Compare multiple sample analyses to classify regions deterministically.

    Rule: If a text region appears in the SAME position with IDENTICAL content
    across all samples, classify as fixed. Otherwise, variable.

    Position tolerance: +/- 5mm in any direction.
    Content tolerance: exact string match after whitespace normalization.
    """
    # 1. Align regions across samples by position proximity
    # 2. For each aligned group:
    #    - All identical content → Fixed (confidence = 1.0)
    #    - Same position, different content → Variable (confidence = 0.95)
    #    - Appears in some samples but not others → Variable, nullable (confidence = 0.85)
    pass
```

### C.3 Stage 2: Template YAML Generation

[trace:step-2:template-analysis]

After Claude multimodal analysis, the engine generates a template YAML file conforming to the schema defined in Step 2 template analysis.

#### C.3.1 Template Schema (Common Structure)

All 7 document types share a common template schema envelope:

```yaml
# Common template header
template_id: "{category}-v{version}"
document_type: "{category}"
version: "1.0"
church_name: "{{ church_state.church.name }}"
denomination: "{{ church_state.church.denomination }}"
scan_source: "inbox/templates/{category}-sample.{ext}"
confirmed_by: null       # Set after human confirmation
confirmed_date: null     # Set after human confirmation

paper:
  size: "A4"             # A4 | A5 | B5 | custom
  orientation: "portrait" # portrait | landscape
  pages: 1               # Number of logical pages
  folds: 0               # 0 = flat, 1 = half-fold

layout:
  margins:
    top_mm: 15
    bottom_mm: 15
    left_mm: 15
    right_mm: 15
  columns: 1             # 1 or 2
  column_gap_mm: 0       # 0 if single column

fixed_regions: [...]     # List of fixed region objects
variable_regions: [...]  # List of variable region objects

output_format:
  type: "markdown"
  output_path_template: "{output_dir}/{date}-{name}.md"
```

#### C.3.2 Data Source Mapping per Document Type

[trace:step-2:template-analysis]
[trace:step-1:data-model]

Each variable region must map to a specific YAML data file and field path. The Step 2 template analysis provides the complete mapping for all 7 document types. The template generator encodes these mappings directly in the template YAML.

**Document Type to Primary Data Source Mapping**:

| Document Type | Primary Source(s) | Secondary Source(s) |
|---------------|------------------|-------------------|
| Bulletin (주보) | `bulletin-data.yaml` | `schedule.yaml`, `members.yaml` |
| Receipt (영수증) | `finance.yaml` | `members.yaml`, `church-state.yaml` |
| Worship Order (순서지) | `bulletin-data.yaml` | `schedule.yaml` |
| Official Letter (공문) | `church-state.yaml` | `members.yaml` |
| Meeting Minutes (회의록) | `church-state.yaml` | `members.yaml`, `schedule.yaml` |
| Certificate (증서) | `members.yaml` | `church-state.yaml` |
| Invitation (초청장) | `schedule.yaml` | `members.yaml`, `church-state.yaml` |

### C.4 Stage 3: First-Run Human Confirmation

The first time a template is generated from a scanned sample, the user must confirm the template structure before it is used for document generation.

#### C.4.1 Confirmation Preview

```
╔══════════════════════════════════════════════════════════════╗
║  TEMPLATE CONFIRMATION — 주보 (Bulletin)                     ║
║  Source: inbox/templates/bulletin-sample.jpg                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  LAYOUT:                                                     ║
║  Paper: A4 portrait, 2 columns, 15mm margins                ║
║  Pages: 2 (front + back)                                     ║
║                                                              ║
║  FIXED REGIONS (7):                                          ║
║  ✅ FR-BUL-01  교회명 배너     "은혜교회"                       ║
║  ✅ FR-BUL-02  교회 로고       [image: assets/church-logo.png] ║
║  ✅ FR-BUL-03  교단 명칭       "대한예수교장로회 ○○노회"         ║
║  ✅ FR-BUL-04  주보 제목       "주  보"                        ║
║  ✅ FR-BUL-05  교회 주소       "서울시 마포구..."               ║
║  ✅ FR-BUL-06  장식 테두리     [single_line border]            ║
║  ✅ FR-BUL-07  섹션 제목       "말씀", "공지사항", "기도제목"    ║
║                                                              ║
║  VARIABLE REGIONS (16):                                      ║
║  📝 VR-BUL-01  발행 번호  ← bulletin-data.yaml > issue_number ║
║  📝 VR-BUL-02  날짜      ← bulletin-data.yaml > date          ║
║  📝 VR-BUL-03  설교 제목  ← bulletin-data.yaml > sermon.title ║
║  📝 VR-BUL-04  성경 본문  ← bulletin-data.yaml > sermon.scrip ║
║  📝 VR-BUL-05  설교자    ← bulletin-data.yaml > sermon.preach ║
║  📝 VR-BUL-07  예배 순서  ← bulletin-data.yaml > worship_order║
║  📝 VR-BUL-09  공지사항   ← bulletin-data.yaml > announcements║
║  📝 VR-BUL-10  기도 제목  ← bulletin-data.yaml > prayer_reqs  ║
║  📝 VR-BUL-11  생일자    ← members.yaml (filter by week)      ║
║  📝 VR-BUL-12  결혼기념   ← members.yaml (filter by week)     ║
║  📝 VR-BUL-15  헌금 봉사자 ← bulletin-data.yaml > offering_tm ║
║  ... (6 more)                                                ║
║                                                              ║
║  SPECIAL ZONES:                                              ║
║  (none — bulletins do not require a seal)                     ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  Actions:                                                    ║
║  [1] 확인 — 이 구조로 확정 (Confirm template)                  ║
║  [2] 수정 — 영역 분류 변경 (Reclassify regions)                ║
║  [3] 재분석 — 다른 샘플 이미지로 재시도 (Re-analyze)             ║
╚══════════════════════════════════════════════════════════════╝
```

#### C.4.2 Template Confirmation Protocol

```python
# template_confirmation.py

def confirm_template(template_path: str, confirmer: str) -> dict:
    """Record human confirmation of a template.

    After confirmation, the template is marked as confirmed and can be used
    for automatic document generation without further human review of the
    template structure (data still goes through HitL).
    """
    import yaml
    from datetime import date

    with open(template_path) as f:
        template = yaml.safe_load(f)

    template["confirmed_by"] = confirmer
    template["confirmed_date"] = date.today().isoformat()

    # Atomic write
    # ... (using atomic_write_yaml pattern from Step 4)

    return {
        "template_id": template["template_id"],
        "confirmed_by": confirmer,
        "confirmed_date": template["confirmed_date"],
        "fixed_regions": len(template.get("fixed_regions", [])),
        "variable_regions": len(template.get("variable_regions", [])),
    }
```

### C.5 Stage 4: Document Generation (Template + Data -> Markdown)

[trace:step-2:template-analysis]

Once a template is confirmed, the engine generates documents by populating variable regions with live data from the YAML data files.

#### C.5.1 Document Generation Engine

```python
# document_generator.py — Template-based document generation

import yaml
from pathlib import Path
from datetime import date, datetime

def generate_document(
    template_path: str,
    output_dir: str,
    context: dict | None = None,
) -> dict:
    """Generate a Markdown document from a confirmed template.

    Args:
        template_path: Path to confirmed template YAML
        output_dir: Directory for generated output
        context: Optional override values (e.g., specific member_id for certificates)

    Returns:
        {
            "output_path": str,
            "template_used": str,
            "data_sources_read": list[str],
            "variable_slots_filled": int,
            "variable_slots_total": int,
            "unfilled_slots": list[str],
            "warnings": list[str],
        }
    """
    # 1. Load template
    with open(template_path) as f:
        template = yaml.safe_load(f)

    if not template.get("confirmed_by"):
        raise ValueError(f"Template {template_path} has not been human-confirmed")

    # 2. Resolve data sources
    data_sources = load_data_sources(template)

    # 3. Populate variable regions
    filled_content = {}
    unfilled = []

    for vr in template.get("variable_regions", []):
        value = resolve_variable(vr, data_sources, context)
        if value is not None:
            filled_content[vr["id"]] = format_value(vr, value)
        elif not vr.get("nullable", False):
            unfilled.append(vr["id"])

    # 4. Apply term normalization via church-glossary.yaml
    filled_content = normalize_terms(filled_content)

    # 5. Render Markdown
    markdown = render_markdown(template, filled_content)

    # 6. Write output
    output_path = resolve_output_path(template, context, output_dir)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(markdown, encoding="utf-8")

    return {
        "output_path": output_path,
        "template_used": template["template_id"],
        "data_sources_read": list(data_sources.keys()),
        "variable_slots_filled": len(filled_content),
        "variable_slots_total": len(template.get("variable_regions", [])),
        "unfilled_slots": unfilled,
        "warnings": [],
    }


def resolve_variable(vr: dict, data_sources: dict, context: dict | None) -> object:
    """Resolve a single variable region's value from data sources."""
    ds = vr.get("data_source", {})

    if ds.get("derived"):
        return resolve_derived(ds["rule"], data_sources, context)

    file_key = ds.get("file")
    field_path = ds.get("field")

    if not file_key or not field_path:
        return None

    data = data_sources.get(file_key)
    if data is None:
        return None

    # Navigate field path
    value = navigate_field_path(data, field_path, context)

    # Apply filter if present
    filter_expr = ds.get("filter")
    if filter_expr and isinstance(value, list):
        value = apply_filter(value, filter_expr, context)

    # Apply transform if present
    transform = ds.get("transform")
    if transform and value is not None:
        value = apply_transform(value, transform)

    # Apply aggregate if present
    aggregate = ds.get("aggregate")
    if aggregate and isinstance(value, list):
        value = apply_aggregate(value, aggregate)

    return value


def format_value(vr: dict, value: object) -> str:
    """Format a resolved value according to the variable region's format spec."""
    fmt = vr.get("format")
    slot_type = vr.get("slot_type", "string")

    if fmt is None:
        return str(value)

    if slot_type == "date" and isinstance(value, str):
        # Parse YYYY-MM-DD and apply Korean date format
        dt = datetime.strptime(value, "%Y-%m-%d")
        weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "주일"]
        return fmt.format(
            year=dt.year, month=dt.month, day=dt.day,
            weekday=weekdays[dt.weekday()],
        )

    if slot_type == "currency" and isinstance(value, (int, float)):
        return fmt.format(amount=int(value))

    if slot_type == "integer":
        return fmt.format(value=int(value))

    return fmt.format(value=value)
```

#### C.5.2 Markdown Rendering per Document Type

[trace:step-2:template-analysis]

Each document type has a specific Markdown rendering strategy that respects the layout conventions defined in Step 2.

**Bulletin Markdown Rendering**:

```python
def render_bulletin_markdown(template: dict, content: dict) -> str:
    """Render a weekly bulletin as Markdown."""
    church_name = template.get("church_name", "교회명")
    denomination = template.get("denomination", "")

    md = []
    md.append(f"# {church_name}")
    if denomination:
        md.append(f"*{denomination}*")
    md.append("")
    md.append("## 주  보")
    md.append("")

    # Issue number and date
    issue = content.get("VR-BUL-01", "")
    date_str = content.get("VR-BUL-02", "")
    md.append(f"**{issue}** | {date_str}")
    md.append("")

    # Sermon info
    series = content.get("VR-BUL-06")
    if series:
        md.append(f"### {series}")
    md.append(f"## {content.get('VR-BUL-03', '설교 제목')}")
    md.append(f"**{content.get('VR-BUL-04', '')}**")
    md.append(f"*{content.get('VR-BUL-05', '')}*")
    md.append("")

    # Worship order
    md.append("### 예배 순서")
    worship_items = content.get("VR-BUL-07", [])
    if isinstance(worship_items, list):
        for item in worship_items:
            if isinstance(item, dict):
                md.append(f"| {item.get('order', '')} | {item.get('item', '')} | {item.get('performer', '')} |")
    md.append("")

    # Announcements
    md.append("### 공지사항")
    announcements = content.get("VR-BUL-09", [])
    if isinstance(announcements, list):
        for ann in announcements:
            if isinstance(ann, dict):
                md.append(f"- **{ann.get('title', '')}**: {ann.get('content', '')}")
    md.append("")

    # Prayer requests
    md.append("### 기도 제목")
    prayers = content.get("VR-BUL-10", [])
    if isinstance(prayers, list):
        for pr in prayers:
            if isinstance(pr, dict):
                md.append(f"- [{pr.get('category', '')}] {pr.get('content', '')}")
    md.append("")

    # Celebrations
    birthdays = content.get("VR-BUL-11", [])
    if birthdays:
        md.append("### 생일 축하")
        for b in birthdays:
            md.append(f"- {b}")

    anniversaries = content.get("VR-BUL-12", [])
    if anniversaries:
        md.append("### 결혼 기념일")
        for a in anniversaries:
            md.append(f"- {a}")

    # Footer
    md.append("")
    md.append("---")
    md.append(f"*{church_name}*")

    return "\n".join(md)
```

### C.6 Document Type Summaries for All 7 Types

[trace:step-2:template-analysis]

| # | Type | Fixed Regions | Variable Regions | Seal Required | Variants | Batch Mode |
|---|------|---------------|------------------|---------------|----------|------------|
| 1 | Bulletin (주보) | 7 (FR-BUL-01..07) | 16 (VR-BUL-01..16) | No | None | Weekly single |
| 2 | Receipt (영수증) | 9 (FR-RCP-01..09) | 11 (VR-RCP-01..11) | Yes (FR-RCP-06) | None | Annual bulk (per member) |
| 3 | Worship Order (순서지) | 5 (FR-WOR-01..05) | 12 (VR-WOR-01..12) | No | Per service type | Weekly single |
| 4 | Official Letter (공문) | 7 (FR-LET-01..07) | 9 (VR-LET-01..09) | Yes (FR-LET-05) | None | Per letter |
| 5 | Meeting Minutes (회의록) | 6 (FR-MIN-01..06) | 15 (VR-MIN-01..15) | Yes (FR-MIN-06) | 당회/제직회 | Per meeting |
| 6 | Certificate (증서) | 8 (FR-CRT-01..08) | 8-10 (VR-CRT-*) | Yes (FR-CRT-06) | 세례/이명/유아세례 | Per member |
| 7 | Invitation (초청장) | 5 (FR-INV-01..05) | 12 (VR-INV-01..12) | No | None | Per event (optional per-member) |

---

## Part D: Error Handling Matrix

### D.1 Error Classification and Recovery

Every error in the pipeline is classified, logged, and paired with a recovery strategy. No error results in silent data loss.

| Error Type | Detection Method | Recovery Strategy | User Impact | Severity |
|-----------|-----------------|-------------------|-------------|----------|
| **Corrupted File** | openpyxl/python-docx raises exception on open | Preserve original in `inbox/errors/`. Log error details. Prompt user to re-export or provide alternative file. | User re-uploads fixed file | HIGH |
| **Encoding Issue** | chardet confidence < 0.5 or UnicodeDecodeError | Try all KOREAN_ENCODINGS sequentially. If all fail, read with `errors="replace"` and flag every field as low-confidence. | User verifies replaced characters | MEDIUM |
| **Partial Extraction** | < 50% of expected fields populated | Stage partial result with per-field confidence. Present to user with clear indication of what is missing. Allow manual completion. | User fills missing fields | MEDIUM |
| **Unsupported Format** | Extension not in supported list | Log error with conversion guidance. For HWP: specific PDF export instructions. For other formats: generic "convert to xlsx/pdf" message. | User converts and re-uploads | LOW |
| **Network Timeout** | N/A (all processing is local) | Not applicable — the system operates entirely locally with no external API calls (PRD constraint). | None | N/A |
| **API Rate Limits** | Claude API rate limit response | Implement exponential backoff with jitter. Queue remaining files. Resume processing after backoff period. Maximum 3 retries per file. | Delayed processing | MEDIUM |
| **Empty File** | File size == 0 or no data rows after header | Log as error. Do not stage. Notify user "File is empty: {filename}". | User provides correct file | LOW |
| **Duplicate File** | Hash comparison with inbox/processed/ archives | Warn user: "This file appears to have been processed before on {date}. Re-import?" Allow re-import if confirmed. | User decides | LOW |
| **Schema Mismatch** | Column mapping rate < 30% | Stage with low confidence. Present unmapped columns to user. Offer to create custom column mapping for this file. | User maps columns manually | MEDIUM |
| **Validation Failure** | P1 validator returns errors | Stage the data with validation errors attached. Present errors clearly. User can correct and re-validate. Do NOT auto-commit invalid data. | User fixes data | HIGH |
| **Image Quality Issues** | OCR confidence < 0.3 or Claude multimodal reports low readability | Request higher-quality image. Provide guidance: "Please retake the photo with better lighting and without shadows." | User retakes photo | MEDIUM |
| **Password-Protected File** | openpyxl/python-docx raises password exception | Log error: "Password-protected file detected. Please remove password protection and re-upload." | User removes password | LOW |

### D.2 Error Logging Format

```yaml
# inbox/errors/20260301-143025-헌금내역.xlsx.error.yaml

error_id: "ERR-20260301-143025"
timestamp: "2026-03-01T14:30:25"
source_file: "inbox/documents/헌금내역.xlsx"
source_preserved: true
source_size_bytes: 45123

error_type: "encoding_issue"
error_severity: "medium"
error_message: "Character encoding detection failed. Attempted: utf-8, euc-kr, cp949. Best guess: euc-kr (confidence: 0.45)"
error_details:
  chardet_result:
    encoding: "euc-kr"
    confidence: 0.45
  attempted_encodings: ["utf-8", "euc-kr", "cp949"]
  fallback_used: "euc-kr"
  replacement_count: 3  # number of characters replaced with U+FFFD

recovery_action: "Extracted with euc-kr encoding using replacement mode. 3 characters could not be decoded. Please verify the following fields manually."
recovery_status: "partial_extraction_staged"
staging_file: "inbox/staging/20260301-143025-헌금내역.yaml"

user_guidance: |
  파일 인코딩 문제가 감지되었습니다.
  3개 문자가 정확하게 읽히지 않았습니다.
  추출된 데이터를 확인해주세요.

  해결 방법:
  1. 원본 파일을 Excel에서 열기
  2. 파일 > 다른 이름으로 저장 > CSV UTF-8 (쉼표로 분리) 선택
  3. 저장된 파일을 inbox/documents/ 폴더에 다시 넣기
```

### D.3 Error Recovery Strategies by Tier

**Tier A (Excel/CSV) Recovery Chain**:
```
1. Primary: openpyxl read_only mode
2. Fallback 1: openpyxl normal mode (for complex formatting)
3. Fallback 2: pandas with dtype=str (all-string read)
4. Fallback 3: csv.reader with encoding chain
5. Final: Stage as "manual_entry_required"
```

**Tier B (Word/PDF) Recovery Chain**:
```
1. Primary: python-docx / Claude Read
2. Fallback 1: Extract plain text only (lose formatting)
3. Fallback 2: Extract tables only (skip paragraphs)
4. Final: Request user to copy-paste text content
```

**Tier C (Images) Recovery Chain**:
```
1. Primary: Claude multimodal analysis
2. Fallback 1: Tesseract OCR (kor+eng)
3. Fallback 2: Claude multimodal with enhanced prompt (describe what you cannot read)
4. Final: Stage as "manual_entry_required" with image reference
```

---

## Part E: Integration Points

### E.1 Connection to P1 Validation Scripts

[trace:step-4:validation-rules]

The pipeline integrates with the deterministic validation scripts defined in Step 4. Every extraction result is validated before staging.

| Target Data | Validator Script | Rule IDs | Integration Point |
|-------------|-----------------|----------|-------------------|
| `data/members.yaml` | `validate_members.py` | M1-M6 | After Tier A/B/C extraction, before staging |
| `data/finance.yaml` | `validate_finance.py` | F1-F5 | After Tier A/B/C extraction, before staging |
| `data/schedule.yaml` | `validate_schedule.py` | S1-S5 | After Tier A/B extraction, before staging |
| `data/newcomers.yaml` | `validate_newcomers.py` | N1-N6 | After Tier A/C extraction, before staging |
| `data/bulletin-data.yaml` | `validate_bulletin.py` | B1-B3 | After Tier A/B extraction, before staging |

**Validation Integration Flow**:

```python
# pipeline_validator.py — Validate extracted data before staging

import subprocess
import json

def validate_extraction(data: dict, target_file: str) -> dict:
    """Run P1 validation on extracted data before staging.

    The validator checks the extraction result against the same rules
    that protect the actual YAML data files.

    Returns:
        {"valid": bool, "errors": list[str], "warnings": list[str]}
    """
    # Map target file to validator script
    VALIDATORS = {
        "data/members.yaml": "scripts/validate_members.py",
        "data/finance.yaml": "scripts/validate_finance.py",
        "data/schedule.yaml": "scripts/validate_schedule.py",
        "data/newcomers.yaml": "scripts/validate_newcomers.py",
        "data/bulletin-data.yaml": "scripts/validate_bulletin.py",
    }

    validator = VALIDATORS.get(target_file)
    if not validator:
        return {"valid": True, "errors": [], "warnings": ["No validator for target file"]}

    # Write extracted data to temp file for validation
    # Run validator subprocess
    # Parse JSON output
    # Return validation result

    result = subprocess.run(
        ["python3", validator, "--input", temp_path, "--format", "json"],
        capture_output=True, text=True, timeout=30,
    )

    return json.loads(result.stdout)
```

### E.2 Connection to guard_data_files.py Hook

[trace:step-4:schema-specs]

The pipeline does not write to data files directly. It produces validated, human-confirmed extraction results that the designated writer agent consumes. This ensures the `guard_data_files.py` PreToolUse hook remains effective.

**Write Flow**:

```
Pipeline (any agent)
    │
    ├─ Extracts data → inbox/staging/{file}.yaml
    ├─ Human confirms → staging file marked "approved"
    │
    └─ Hands off to designated writer agent
        │
        ├─ member-manager reads staging file
        ├─ member-manager writes to data/members.yaml
        │     └─ guard_data_files.py verifies writer identity ✅
        │
        └─ If non-member-manager tries to write members.yaml
              └─ guard_data_files.py blocks with exit code 2 ❌
```

**Writer Agent Routing Table**:

```python
# writer_routing.py — Route committed data to correct writer agent

WRITER_AGENTS = {
    "data/members.yaml": "member-manager",
    "data/finance.yaml": "finance-recorder",
    "data/newcomers.yaml": "newcomer-tracker",
    "data/bulletin-data.yaml": "bulletin-generator",
    "data/schedule.yaml": "schedule-manager",
    "church-state.yaml": "orchestrator",
}

def route_to_writer(target_file: str, staging_file: str) -> dict:
    """Route a confirmed staging file to its designated writer agent.

    Returns instructions for the Orchestrator to dispatch to the correct agent.
    """
    writer = WRITER_AGENTS.get(target_file)
    if not writer:
        raise ValueError(f"No designated writer for {target_file}")

    return {
        "action": "import_data",
        "target_agent": writer,
        "staging_file": staging_file,
        "target_data_file": target_file,
        "instructions": (
            f"Read the approved staging file at {staging_file}. "
            f"Merge the records into {target_file} using atomic write pattern. "
            f"Assign new IDs following existing ID sequence. "
            f"Run validate after write to confirm integrity."
        ),
    }
```

### E.3 Connection to church-glossary.yaml for Term Normalization

[trace:step-1:data-model]

The church glossary provides authoritative Korean-English term mappings. The pipeline uses it for two purposes:

1. **Input Normalization**: Convert user input terms to canonical forms during extraction
2. **Output Normalization**: Ensure generated documents use consistent terminology

```python
# term_normalizer.py — Church glossary integration

import yaml
from pathlib import Path

class ChurchGlossary:
    """Church terminology normalizer using church-glossary.yaml."""

    def __init__(self, glossary_path: str = "data/church-glossary.yaml"):
        with open(glossary_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.terms = data.get("terms", [])
        self._korean_to_english = {}
        self._english_to_korean = {}
        self._aliases = {}

        for term in self.terms:
            korean = term.get("korean", "")
            english = term.get("english", "")
            self._korean_to_english[korean] = english
            self._english_to_korean[english] = korean

            # Build alias map for common variants
            for alias in term.get("aliases", []):
                self._aliases[alias] = korean

    def normalize_korean(self, text: str) -> str:
        """Normalize Korean church terms to canonical forms.

        Example: "권찰" → "권사" (common informal variant)
        """
        # Check direct aliases
        if text in self._aliases:
            return self._aliases[text]
        return text

    def get_english(self, korean_term: str) -> str | None:
        """Get English canonical term for a Korean term."""
        normalized = self.normalize_korean(korean_term)
        return self._korean_to_english.get(normalized)

    def normalize_offering_type(self, raw_type: str) -> str:
        """Normalize offering type names to canonical enum values.

        Handles common variants and misspellings of offering types.
        """
        OFFERING_NORMALIZATION = {
            "십일조": "tithe",
            "1/10": "tithe",
            "주일헌금": "sunday_offering",
            "감사헌금": "thanksgiving",
            "특별헌금": "special",
            "선교헌금": "mission",
            "건축헌금": "building_fund",
            "주정헌금": "pledged_annual",
            "감사": "thanksgiving",  # Shortened form
        }
        return OFFERING_NORMALIZATION.get(raw_type, raw_type)

    def normalize_role(self, raw_role: str) -> str:
        """Normalize church role names to canonical values."""
        ROLE_NORMALIZATION = {
            "목사": "목사", "담임목사": "목사", "부목사": "목사",
            "전도사": "전도사",
            "장로": "장로",
            "집사": "집사", "안수집사": "집사", "무임집사": "집사",
            "권사": "권사",
            "성도": "성도", "교인": "성도", "평신도": "성도",
        }
        return ROLE_NORMALIZATION.get(raw_role, raw_role)

    def normalize_department(self, raw_dept: str) -> str:
        """Normalize department names."""
        DEPT_NORMALIZATION = {
            "장년부": "장년부", "장년": "장년부", "성인부": "장년부",
            "청년부": "청년부", "청년": "청년부", "대학부": "청년부",
            "중고등부": "중고등부", "중등부": "중고등부", "고등부": "중고등부",
            "유년부": "유년부", "초등부": "유년부", "어린이부": "유년부",
            "유아부": "유아부", "영아부": "유아부",
        }
        return DEPT_NORMALIZATION.get(raw_dept, raw_dept)
```

### E.4 Connection to Data Schemas from Step 4

[trace:step-4:schema-specs]

The pipeline uses the data schemas from Step 4 to:

1. **Generate IDs**: Follow the ID format patterns (M\d{3,}, N\d{3,}, OFF-\d{4}-\d{3,}, etc.)
2. **Validate types**: Enforce type constraints (integer amounts, date formats, enum values)
3. **Enforce relationships**: Maintain cross-reference integrity (newcomer.referred_by → member.id)

```python
# id_generator.py — Generate IDs following Step 4 schema conventions

import re
import yaml

def generate_next_id(data_file: str, prefix: str) -> str:
    """Generate the next sequential ID for a data file.

    Follows Step 4 conventions:
    - members.yaml: M001, M002, ...
    - newcomers.yaml: N001, N002, ...
    - finance.yaml offerings: OFF-2026-001, OFF-2026-002, ...
    - finance.yaml expenses: EXP-2026-001, EXP-2026-002, ...
    - schedule.yaml events: EVT-2026-001, ...
    """
    with open(data_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Extract existing IDs matching the prefix pattern
    existing_ids = []

    if prefix in ("M", "N"):
        # Simple numeric suffix: M001, N001
        pattern = re.compile(rf'^{prefix}(\d{{3,}})$')
        items = data.get("members" if prefix == "M" else "newcomers", [])
        for item in items:
            match = pattern.match(item.get("id", ""))
            if match:
                existing_ids.append(int(match.group(1)))

    elif prefix in ("OFF", "EXP", "EVT", "FAC"):
        # Year-prefixed: OFF-2026-001
        year = data.get("year", 2026)
        pattern = re.compile(rf'^{prefix}-{year}-(\d{{3,}})$')

        collection_key = {
            "OFF": "offerings",
            "EXP": "expenses",
            "EVT": "special_events",
            "FAC": "facility_bookings",
        }[prefix]

        for item in data.get(collection_key, []):
            match = pattern.match(item.get("id", ""))
            if match:
                existing_ids.append(int(match.group(1)))

    next_num = max(existing_ids, default=0) + 1

    if prefix in ("M", "N"):
        return f"{prefix}{next_num:03d}"
    else:
        year = data.get("year", 2026)
        return f"{prefix}-{year}-{next_num:03d}"
```

### E.5 Korean Numeral Conversion (for Receipt Generation)

[trace:step-2:template-analysis]

Tax donation receipts require amounts in Korean numeral notation (법정 기재 방식). This is a legally required field.

```python
# korean_numeral.py — Integer to Korean numeral conversion

def integer_to_korean_numeral(amount: int) -> str:
    """Convert an integer amount to Korean numeral notation.

    Examples:
        1,234,000 → "일백이십삼만사천"
        500,000   → "오십만"
        10,000    → "일만"
        5,670,000 → "오백육십칠만"

    Used for receipt VR-RCP-08 (donation_amount_korean_numeral).
    The final output wraps as: "금 {numeral}원정"
    """
    if amount <= 0:
        raise ValueError(f"Amount must be positive, got {amount}")

    units = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]
    positions = ["", "십", "백", "천"]
    large_units = ["", "만", "억", "조"]

    result = []
    group_index = 0

    while amount > 0:
        group = amount % 10000
        amount //= 10000

        group_str = ""
        for pos in range(4):
            digit = group % 10
            group //= 10
            if digit > 0:
                if digit == 1 and pos > 0:
                    group_str = positions[pos] + group_str
                else:
                    group_str = units[digit] + positions[pos] + group_str

        if group_str:
            result.append(group_str + large_units[group_index])

        group_index += 1

    return "".join(reversed(result)) if result else "영"
```

### E.6 Privacy Masking for Sensitive Data

[trace:step-4:schema-specs]

The pipeline applies privacy masking for sensitive fields, particularly for bulletin birthday lists and receipt donor IDs.

```python
# privacy_masker.py — Korean name and ID masking

def mask_korean_name(name: str) -> str:
    """Mask the middle character(s) of a Korean name for bulletin display.

    Korean naming convention: 2-4 characters, family name first.
    Masking: Replace middle character with ○.

    Examples:
        "김철수" → "김○수"
        "이영희" → "이○희"
        "박성민" → "박○민"
        "남궁세연" → "남궁○연"  (2-char family name)
    """
    if not name or len(name) < 2:
        return name
    if len(name) == 2:
        return name[0] + "○"
    if len(name) == 3:
        return name[0] + "○" + name[2]
    # 4+ characters: mask middle characters
    return name[0] + "○" * (len(name) - 2) + name[-1]

def mask_resident_number(number: str) -> str:
    """Mask Korean resident registration number for receipt display.

    Full format: YYMMDD-NNNNNNN (13 digits)
    Masked: YYMMDD-N****** (last 6 digits hidden)
    """
    if not number or len(number) < 14:
        return number
    # Normalize separators
    digits = number.replace("-", "")
    if len(digits) == 13:
        return f"{digits[:6]}-{digits[6]}******"
    return number  # Return as-is if format is unexpected
```

---

## Appendix: Self-Verification Report

### Verification Criteria Check

| # | Criterion | Status | Evidence |
|---|----------|--------|----------|
| 1 | 3-tier pipeline fully specified with technology choices per tier | **PASS** | Sections A.3 (Tier A: openpyxl, pandas, chardet), A.4 (Tier B: python-docx, Claude Read), A.5 (Tier C: Claude multimodal, Tesseract OCR) — each with complete code specifications |
| 2 | HitL confirmation flow designed for all data writes | **PASS** | Part B specifies the complete flow: confidence scoring (B.2), staging format (B.3), preview display (B.4), error recovery (B.5). Finance data permanently excluded from auto-approve. |
| 3 | Scan-and-replicate engine architecture for 7 document types | **PASS** | Part C covers all 7 types (Section C.6 summary table), with Stage 1 analysis (C.2), Stage 2 template generation (C.3), Stage 3 human confirmation (C.4), Stage 4 document generation (C.5). All types traced to Step 2. |
| 4 | Error handling preserves originals and handles partial extraction | **PASS** | Part D defines 12 error types with recovery strategies. Error logging format preserves source_preserved: true. Partial extraction staged with per-field confidence. |
| 5 | Integration with validation scripts and guard hooks documented | **PASS** | Part E.1 maps all 5 validators to pipeline integration points. Part E.2 documents guard_data_files.py write routing. |
| 6 | Trace markers present for step-1, step-2, step-4 | **PASS** | [trace:step-1:data-model] in A.1, A.3.3, E.3. [trace:step-2:template-analysis] in C.1-C.6. [trace:step-4:schema-specs] in A.1, A.3, A.4, E.1, E.4, E.6. [trace:step-4:validation-rules] in A.3, B.1, E.1. |
| 7 | church-glossary.yaml integration for term normalization specified | **PASS** | Part E.3 provides complete ChurchGlossary class with normalize_korean(), normalize_offering_type(), normalize_role(), normalize_department() methods. |
| 8 | Confidence scoring mechanism defined per extraction tier | **PASS** | Section B.2 defines tier base confidence (A:0.95, B:0.70, C:0.55), method adjustments, field type bonuses, and review level thresholds. |

#!/usr/bin/env python3
"""
Tier C Parser — Unstructured Data (Images)

Designed for Claude multimodal analysis of image files:
  - Receipt images     -> finance expense records
  - Name card images   -> newcomer contact records
  - Offering envelopes -> finance offering records

This parser defines the input/output contract for image analysis.
The actual image analysis is performed by the data-ingestor agent
(Claude Code with multimodal capability) which invokes this script
to generate the staging JSON after extracting data from images.

Uses church-glossary.yaml for Korean term normalization.
Produces JSON staging files in inbox/staging/.

Usage:
    # Generate staging file from pre-extracted data (agent provides JSON):
    python3 tier_c_parser.py --file <image_path> --glossary <glossary.yaml> \\
        --staging-dir <dir> --extracted-data '{"type":"receipt","fields":{...}}'

    # Describe expected contract (no extraction, just schema info):
    python3 tier_c_parser.py --describe-contract
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

import yaml


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".webp"}

# Image type classification based on filename hints or agent analysis
IMAGE_TYPES = {
    "receipt": {
        "target": "data/finance.yaml",
        "section": "expenses",
        "description": "영수증 (Receipt) — expense records",
        "expected_fields": {
            "date": "YYYY-MM-DD (purchase/payment date)",
            "category": "Expense category (관리비, 인건비, 사역비, etc.)",
            "subcategory": "Specific item description",
            "amount": "Integer KRW amount",
            "description": "What was purchased/paid for",
            "payment_method": "계좌이체/카드/현금 etc.",
            "vendor": "Store/vendor name (if visible)",
        },
    },
    "namecard": {
        "target": "data/newcomers.yaml",
        "section": "newcomers",
        "description": "명함/연락처 카드 (Name card) — newcomer contact records",
        "expected_fields": {
            "name": "Person's name (Korean)",
            "phone": "Phone number (010-XXXX-XXXX format)",
            "email": "Email address (if visible)",
            "company": "Company/organization (if visible)",
            "title": "Job title (if visible)",
        },
    },
    "offering_envelope": {
        "target": "data/finance.yaml",
        "section": "offerings",
        "description": "헌금봉투 (Offering envelope) — offering records",
        "expected_fields": {
            "date": "YYYY-MM-DD (Sunday date)",
            "name": "Donor name (for matching to member ID)",
            "category": "Offering type (십일조, 감사헌금, etc.)",
            "amount": "Integer KRW amount",
        },
    },
    "document_scan": {
        "target": "unknown",
        "section": "unknown",
        "description": "문서 스캔 (Document scan) — general document images",
        "expected_fields": {
            "document_type": "Type of document visible in the image",
            "key_text": "Key text content extracted from the image",
            "dates": "Any dates visible",
            "names": "Any names visible",
        },
    },
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
# Image type detection from filename
# ---------------------------------------------------------------------------
def detect_image_type(filepath):
    """Guess image type from filename patterns.

    Returns image_type key or 'unknown'.
    """
    basename = os.path.basename(filepath).lower()

    receipt_hints = ("영수증", "receipt", "거래", "결제", "지출")
    namecard_hints = ("명함", "namecard", "name_card", "연락처", "카드")
    envelope_hints = ("헌금", "봉투", "offering", "envelope")

    for hint in receipt_hints:
        if hint in basename:
            return "receipt"
    for hint in namecard_hints:
        if hint in basename:
            return "namecard"
    for hint in envelope_hints:
        if hint in basename:
            return "offering_envelope"

    return "document_scan"


# ---------------------------------------------------------------------------
# Normalize extracted data
# ---------------------------------------------------------------------------
def normalize_extracted_data(extracted, glossary):
    """Normalize extracted fields using glossary and standard formats.

    Args:
        extracted: dict with 'type' and 'fields' from agent analysis.
        glossary: Korean->English lookup dict.

    Returns:
        (normalized_fields, confidence, warnings, glossary_used)
    """
    fields = extracted.get("fields", {})
    image_type = extracted.get("type", "unknown")
    warnings = []
    glossary_used = {}
    confidence = extracted.get("confidence", 0.6)

    # Normalize date fields
    for date_key in ("date",):
        if date_key in fields and fields[date_key]:
            raw = str(fields[date_key]).strip()
            # Try Korean date pattern
            m = re.match(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", raw)
            if m:
                fields[date_key] = (
                    f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
                )
            elif re.match(r"\d{4}/\d{1,2}/\d{1,2}", raw):
                fields[date_key] = raw.replace("/", "-")

    # Normalize phone
    if "phone" in fields and fields["phone"]:
        digits = re.sub(r"[^\d]", "", str(fields["phone"]))
        if len(digits) == 11 and digits.startswith("010"):
            fields["phone"] = f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"

    # Normalize amount
    if "amount" in fields and fields["amount"] is not None:
        raw = fields["amount"]
        if isinstance(raw, str):
            cleaned = re.sub(r"[,\s원₩]", "", raw)
            try:
                fields["amount"] = int(float(cleaned))
            except (ValueError, TypeError):
                warnings.append(f"Could not parse amount: '{raw}'")
                fields["amount"] = 0
                confidence -= 0.2
        elif isinstance(raw, (int, float)):
            fields["amount"] = int(raw)

    # Normalize category using glossary
    if "category" in fields and fields["category"]:
        cat = str(fields["category"]).strip()
        if cat in glossary:
            glossary_used[cat] = glossary[cat]
            fields["category_english"] = glossary[cat]

    return fields, max(confidence, 0.1), warnings, glossary_used


# ---------------------------------------------------------------------------
# Main parse entry point
# ---------------------------------------------------------------------------
def create_staging(filepath, glossary_path, staging_dir, extracted_data=None):
    """Create a staging JSON for an image file.

    Args:
        filepath: Path to image file.
        glossary_path: Path to church-glossary.yaml.
        staging_dir: Directory for staging output.
        extracted_data: JSON string or dict with extracted data from agent.
            Expected format: {"type": "receipt", "fields": {...}, "confidence": 0.8}

    Returns:
        dict with staging results, or error dict.
    """
    if not os.path.isfile(filepath):
        return {"error": f"File not found: {filepath}"}

    ext = os.path.splitext(filepath)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return {"error": f"Unsupported image extension: {ext}"}

    glossary = load_glossary(glossary_path)

    # Parse extracted data
    if extracted_data is None:
        # No extracted data provided — create a placeholder staging file
        # The data-ingestor agent should analyze the image and provide data
        image_type = detect_image_type(filepath)
        type_info = IMAGE_TYPES.get(image_type, IMAGE_TYPES["document_scan"])

        staging_data = {
            "source_file": filepath,
            "parser_tier": "C",
            "target_data_file": type_info["target"],
            "target_section": type_info["section"],
            "status": "pending_analysis",
            "image_type_guess": image_type,
            "expected_fields": type_info["expected_fields"],
            "records": [],
            "glossary_mappings": {},
            "parse_warnings": [
                "Image requires multimodal analysis by data-ingestor agent. "
                "Re-run with --extracted-data after agent analysis."
            ],
            "analysis_prompt": _build_analysis_prompt(filepath, image_type, type_info),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "total_records": 0,
            "average_confidence": 0.0,
        }
    else:
        # Parse the provided extracted data
        if isinstance(extracted_data, str):
            try:
                extracted = json.loads(extracted_data)
            except json.JSONDecodeError as e:
                return {"error": f"Invalid JSON in extracted-data: {e}"}
        else:
            extracted = extracted_data

        image_type = extracted.get("type", detect_image_type(filepath))
        type_info = IMAGE_TYPES.get(image_type, IMAGE_TYPES["document_scan"])

        fields, confidence, warnings, glossary_used = normalize_extracted_data(
            extracted, glossary
        )

        records = [{
            "fields": fields,
            "confidence": round(confidence, 2),
            "source_block": 1,
            "notes": extracted.get("notes", []),
        }]

        staging_data = {
            "source_file": filepath,
            "parser_tier": "C",
            "target_data_file": type_info["target"],
            "target_section": type_info["section"],
            "status": "analyzed",
            "image_type": image_type,
            "records": records,
            "glossary_mappings": glossary_used,
            "parse_warnings": warnings,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "total_records": len(records),
            "average_confidence": round(confidence, 2),
        }

    # Write staging file
    os.makedirs(staging_dir, exist_ok=True)
    basename = os.path.splitext(os.path.basename(filepath))[0]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    staging_filename = f"tier_c_{basename}_{ts}.json"
    staging_path = os.path.join(staging_dir, staging_filename)

    with open(staging_path, "w", encoding="utf-8") as f:
        json.dump(staging_data, f, indent=2, ensure_ascii=False)

    staging_data["staging_file"] = staging_path
    return staging_data


def _build_analysis_prompt(filepath, image_type, type_info):
    """Build a prompt for the data-ingestor agent to analyze the image."""
    fields_desc = "\n".join(
        f"  - {k}: {v}" for k, v in type_info["expected_fields"].items()
    )
    return (
        f"Please analyze the image at: {filepath}\n"
        f"Detected type: {type_info['description']}\n\n"
        f"Extract the following fields:\n{fields_desc}\n\n"
        f"Return JSON in this format:\n"
        f'{{"type": "{image_type}", "fields": {{...}}, "confidence": 0.0-1.0, '
        f'"notes": ["any observations"]}}'
    )


def describe_contract():
    """Print the input/output contract for Tier C parsing."""
    contract = {
        "description": (
            "Tier C Parser handles image files for the Church Admin inbox pipeline. "
            "Image analysis is performed by the data-ingestor agent (Claude multimodal), "
            "which then passes extracted data to this script for normalization and staging."
        ),
        "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
        "image_types": {
            k: {
                "description": v["description"],
                "target": v["target"],
                "section": v["section"],
                "expected_fields": v["expected_fields"],
            }
            for k, v in IMAGE_TYPES.items()
        },
        "workflow": [
            "1. Image file placed in inbox/images/",
            "2. inbox_parser.py detects image and creates pending staging file",
            "3. data-ingestor agent reads the image using Read tool (multimodal)",
            "4. Agent extracts fields and calls tier_c_parser.py --extracted-data '{...}'",
            "5. This script normalizes data, applies glossary, produces final staging JSON",
            "6. hitl_confirmation.py presents extracted data for human review",
        ],
        "extracted_data_format": {
            "type": "string — one of: receipt, namecard, offering_envelope, document_scan",
            "fields": "dict — extracted key-value pairs matching expected_fields",
            "confidence": "float 0.0-1.0 — agent's confidence in extraction accuracy",
            "notes": "list[str] — any observations or caveats from agent",
        },
    }
    return contract


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Tier C Parser — Process image files for church admin inbox pipeline"
    )
    parser.add_argument(
        "--file",
        help="Path to image file (.jpg, .png, .jpeg, .heic, .webp)"
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
        "--extracted-data",
        help="JSON string with extracted data from agent multimodal analysis"
    )
    parser.add_argument(
        "--describe-contract", action="store_true",
        help="Print the input/output contract for Tier C parsing"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output full JSON result to stdout"
    )
    args = parser.parse_args()

    if args.describe_contract:
        contract = describe_contract()
        print(json.dumps(contract, indent=2, ensure_ascii=False))
        return

    if not args.file:
        parser.error("--file is required unless --describe-contract is used")

    result = create_staging(
        args.file, args.glossary, args.staging_dir, args.extracted_data
    )

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)

    status = result.get("status", "unknown")
    print(f"Tier C staging complete: {result['total_records']} records, status={status}")
    print(f"  Source:     {result['source_file']}")
    print(f"  Target:     {result['target_data_file']} [{result['target_section']}]")
    print(f"  Confidence: {result['average_confidence']:.0%}")
    if result.get("staging_file"):
        print(f"  Staging:    {result['staging_file']}")

    if status == "pending_analysis":
        print("\n  [!] Image requires multimodal analysis by data-ingestor agent.")
        print("      Re-run with --extracted-data after analysis.")

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

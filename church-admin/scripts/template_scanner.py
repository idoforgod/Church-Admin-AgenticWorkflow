#!/usr/bin/env python3
"""
template_scanner.py — Image-to-Template Analysis Contract

This script documents and orchestrates the expected Claude multimodal analysis
flow for the scan-and-replicate pipeline (PRD §5.1 F-06). It defines the
contract between a document image and the resulting template YAML.

The actual image analysis is performed by the @template-scanner Claude Code
agent (defined in .claude/agents/template-scanner.md), which uses vision
capabilities to:
    1. Accept a document image (.jpg/.png)
    2. Identify fixed areas (headers, logos, seals, static labels)
    3. Identify variable areas (data fields, dynamic content)
    4. Extract section boundaries and layout structure
    5. Generate a template YAML file with slot definitions

This script serves as:
    - The CLI entry point that invokes the analysis flow
    - A validator for the generated template YAML structure
    - A first-run HitL (Human-in-the-Loop) confirmation interface

Usage:
    # Analyze a document image and generate template YAML:
    python3 template_scanner.py --input inbox/templates/bulletin-sample.jpg \\
        --output templates/bulletin-template.yaml \\
        --type bulletin

    # Validate an existing template YAML:
    python3 template_scanner.py --validate templates/bulletin-template.yaml

    # Show expected template schema for a document type:
    python3 template_scanner.py --schema bulletin

Scan-and-Replicate Pipeline (4 stages):
    Stage 1 — Image/PDF Upload
        inbox/templates/{category}-sample.{jpg|pdf}

    Stage 2 — Claude Multimodal Analysis
        Fixed region detection (anchors: church name, logo, seal, denomination)
        Variable region detection (data slots: date, content, amounts)
        Layout extraction (paper size, margins, columns, section flow)

    Stage 3 — Template Generation
        {category}-template.yaml  (machine-processable structure)

    Stage 4 — Human Confirmation + Iterative Generation
        First-run: human verifies structure and variable slots
        Subsequent: fully automatic with data injection from YAML sources

Supported Document Types:
    bulletin       — Weekly church bulletin (주보)
    receipt        — Donation receipt (기부금영수증)
    worship_order  — Worship order sheet (예배 순서지)
    official_letter — Official correspondence (공문)
    meeting_minutes — Meeting minutes (회의록)
    certificate    — Baptism/transfer certificates (증서)
    invitation     — Event invitations (초청장)
"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip3 install pyyaml", file=sys.stderr)
    sys.exit(1)


# ── Template Schema Definition ───────────────────────────────────────────────

# Required top-level keys in every template YAML
REQUIRED_TOP_LEVEL_KEYS = [
    "template_id",
    "document_type",
    "version",
    "sections",
]

# Valid slot types
VALID_SLOT_TYPES = [
    "text",
    "date",
    "integer",
    "currency",
    "list",
    "table",
    "reference",
]

# Valid list styles
VALID_LIST_STYLES = ["bullet", "numbered", "comma"]

# Document type metadata — defines expected sections per type
DOCUMENT_TYPE_SCHEMAS = {
    "bulletin": {
        "description": "Weekly church bulletin (주보)",
        "expected_sections": [
            "header", "sermon", "worship_order", "announcements",
            "prayer_requests", "celebrations", "offering_team", "next_week",
        ],
        "primary_data_sources": ["bulletin-data.yaml", "members.yaml"],
    },
    "receipt": {
        "description": "Donation receipt (기부금영수증)",
        "expected_sections": [
            "header", "church_info", "donor_info", "donation_details", "legal_footer",
        ],
        "primary_data_sources": ["finance.yaml", "members.yaml"],
    },
    "worship_order": {
        "description": "Worship order sheet (예배 순서지)",
        "expected_sections": [
            "header", "sermon_info", "worship_order", "offering", "announcements",
        ],
        "primary_data_sources": ["bulletin-data.yaml", "schedule.yaml"],
    },
    "official_letter": {
        "description": "Official correspondence (공문)",
        "expected_sections": [
            "denomination_header", "document_info", "recipient_info",
            "body_content", "signature_block",
        ],
        "primary_data_sources": ["members.yaml", "state.yaml"],
    },
    "meeting_minutes": {
        "description": "Meeting minutes (회의록)",
        "expected_sections": [
            "header", "attendance", "agenda", "decisions", "closing",
        ],
        "primary_data_sources": ["members.yaml", "state.yaml"],
    },
    "certificate": {
        "description": "Baptism/transfer certificate (증서)",
        "expected_sections": [
            "header", "recipient_info", "certificate_details", "signature",
        ],
        "primary_data_sources": ["members.yaml"],
    },
    "invitation": {
        "description": "Event invitation (초청장)",
        "expected_sections": [
            "header", "event_details", "rsvp_info",
        ],
        "primary_data_sources": ["schedule.yaml", "members.yaml"],
    },
}


# ── Template Validation ──────────────────────────────────────────────────────

def validate_template(template_path: str) -> dict:
    """Validate a template YAML file against the schema contract.

    Checks:
        V1. File exists and is valid YAML
        V2. All required top-level keys present
        V3. document_type is a known type
        V4. sections is a non-empty list
        V5. Each section has 'name' and 'title'
        V6. Each slot has 'name' and 'type'
        V7. Slot types are from the valid set
        V8. Required slots have 'source' or 'derived' flag

    Args:
        template_path: Path to the template YAML file.

    Returns:
        Dict with 'valid' (bool), 'errors' (list), 'warnings' (list).
    """
    result = {"valid": True, "errors": [], "warnings": [], "stats": {}}

    path = Path(template_path)
    if not path.exists():
        result["valid"] = False
        result["errors"].append(f"V1 FAIL: Template file not found: {template_path}")
        return result

    # V1: Parse YAML
    try:
        with open(path, "r", encoding="utf-8") as f:
            template = yaml.safe_load(f)
    except yaml.YAMLError as e:
        result["valid"] = False
        result["errors"].append(f"V1 FAIL: Invalid YAML: {e}")
        return result

    if not template or not isinstance(template, dict):
        result["valid"] = False
        result["errors"].append("V1 FAIL: Template is empty or not a dict")
        return result

    # V2: Required top-level keys
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in template:
            result["valid"] = False
            result["errors"].append(f"V2 FAIL: Missing required top-level key: '{key}'")

    # V3: document_type
    doc_type = template.get("document_type", "")
    if doc_type not in DOCUMENT_TYPE_SCHEMAS:
        result["warnings"].append(
            f"V3 WARNING: Unknown document_type '{doc_type}'. "
            f"Known types: {list(DOCUMENT_TYPE_SCHEMAS.keys())}"
        )

    # V4: sections
    sections = template.get("sections", [])
    if not isinstance(sections, list) or len(sections) == 0:
        result["valid"] = False
        result["errors"].append("V4 FAIL: 'sections' must be a non-empty list")
        return result

    result["stats"]["section_count"] = len(sections)
    total_slots = 0
    required_slots = 0

    for i, section in enumerate(sections):
        # V5: Section structure
        if "name" not in section:
            result["errors"].append(f"V5 FAIL: Section {i} missing 'name'")
            result["valid"] = False
        if "title" not in section:
            result["warnings"].append(f"V5 WARNING: Section {i} missing 'title'")

        # V6-V8: Slot validation
        slots = section.get("slots", [])
        for j, slot in enumerate(slots):
            total_slots += 1
            slot_id = f"section[{i}].slot[{j}]"

            if "name" not in slot:
                result["errors"].append(f"V6 FAIL: {slot_id} missing 'name'")
                result["valid"] = False

            slot_type = slot.get("type", "")
            if "type" not in slot:
                result["errors"].append(f"V6 FAIL: {slot_id} missing 'type'")
                result["valid"] = False
            elif slot_type not in VALID_SLOT_TYPES:
                result["errors"].append(
                    f"V7 FAIL: {slot_id} has invalid type '{slot_type}'. "
                    f"Valid: {VALID_SLOT_TYPES}"
                )
                result["valid"] = False

            is_required = slot.get("required", False)
            if is_required:
                required_slots += 1

            is_derived = slot.get("derived", False)
            source = slot.get("source")
            if is_required and not is_derived and not source:
                result["warnings"].append(
                    f"V8 WARNING: {slot_id} ('{slot.get('name', '')}') is required "
                    f"but has no 'source' or 'derived' flag"
                )

    result["stats"]["total_slots"] = total_slots
    result["stats"]["required_slots"] = required_slots

    # Check expected sections for known types
    if doc_type in DOCUMENT_TYPE_SCHEMAS:
        expected = set(DOCUMENT_TYPE_SCHEMAS[doc_type]["expected_sections"])
        actual = {s.get("name", "") for s in sections}
        missing = expected - actual
        if missing:
            result["warnings"].append(
                f"Section coverage: missing expected sections {missing} for type '{doc_type}'"
            )

    return result


# ── Schema Display ───────────────────────────────────────────────────────────

def show_schema(doc_type: str):
    """Display the expected template schema for a document type.

    Args:
        doc_type: Document type identifier.
    """
    if doc_type not in DOCUMENT_TYPE_SCHEMAS:
        print(f"Unknown document type: '{doc_type}'", file=sys.stderr)
        print(f"Available types: {list(DOCUMENT_TYPE_SCHEMAS.keys())}", file=sys.stderr)
        sys.exit(1)

    schema = DOCUMENT_TYPE_SCHEMAS[doc_type]
    print(f"Template Schema: {doc_type}")
    print(f"  Description: {schema['description']}")
    print(f"  Expected Sections:")
    for section in schema["expected_sections"]:
        print(f"    - {section}")
    print(f"  Primary Data Sources:")
    for source in schema["primary_data_sources"]:
        print(f"    - {source}")
    print()
    print("Required top-level keys:")
    for key in REQUIRED_TOP_LEVEL_KEYS:
        print(f"  - {key}")
    print()
    print("Valid slot types:")
    for st in VALID_SLOT_TYPES:
        print(f"  - {st}")


# ── Scan Contract (Claude Agent Delegation) ──────────────────────────────────

def generate_scan_prompt(input_path: str, doc_type: str) -> str:
    """Generate the analysis prompt for the Claude multimodal agent.

    This prompt is passed to the @template-scanner agent which uses
    vision capabilities to analyze the document image.

    Args:
        input_path: Path to the document image.
        doc_type: Expected document type.

    Returns:
        Formatted prompt string for the Claude agent.
    """
    schema = DOCUMENT_TYPE_SCHEMAS.get(doc_type, {})
    expected_sections = schema.get("expected_sections", [])

    prompt = f"""Analyze this document image and generate a template YAML file.

Document type: {doc_type}
Description: {schema.get('description', 'Unknown')}
Expected sections: {', '.join(expected_sections)}

Analysis steps:
1. FIXED REGIONS: Identify all areas that appear consistently across documents
   of this type (church name, logos, seals, static labels, borders).

2. VARIABLE REGIONS: Identify all areas that change between document instances
   (dates, names, amounts, lists, tables).

3. LAYOUT: Determine paper size, orientation, margins, column structure.

4. SECTION BOUNDARIES: Map the document into logical sections with clear
   boundaries.

5. SLOT DEFINITIONS: For each variable region, define:
   - name: machine-readable identifier
   - type: one of {VALID_SLOT_TYPES}
   - source: dot-path to the value in the corresponding data YAML
   - required: whether this field must be non-empty
   - format: display format string (if applicable)

Output the result as a YAML template following this structure:
  template_id: "{doc_type}-v1"
  document_type: "{doc_type}"
  version: "1.0"
  sections:
    - name: "..."
      title: "..."
      slots:
        - name: "..."
          type: "..."
          source: "..."
          required: true/false

Image path: {input_path}
"""
    return prompt


# ── Main Entry Point ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Template Scanner — document image analysis contract for scan-and-replicate pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script defines the contract for converting document images into template
YAML files. The actual image analysis is performed by the @template-scanner
Claude Code agent using multimodal vision capabilities.

Examples:
  # Validate an existing template:
  python3 template_scanner.py --validate templates/bulletin-template.yaml

  # Show schema for a document type:
  python3 template_scanner.py --schema bulletin

  # Generate analysis prompt for an image:
  python3 template_scanner.py --input inbox/templates/bulletin-sample.jpg \\
      --type bulletin --prompt-only
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--validate",
        metavar="TEMPLATE_YAML",
        help="Validate an existing template YAML file against the schema contract.",
    )
    group.add_argument(
        "--schema",
        metavar="DOC_TYPE",
        help="Show the expected template schema for a document type.",
    )
    group.add_argument(
        "--input",
        metavar="IMAGE_PATH",
        help="Path to a document image to analyze (delegates to @template-scanner agent).",
    )

    parser.add_argument(
        "--type",
        metavar="DOC_TYPE",
        default="bulletin",
        help="Document type for image analysis (default: bulletin).",
    )
    parser.add_argument(
        "--output",
        metavar="YAML_PATH",
        help="Output path for the generated template YAML.",
    )
    parser.add_argument(
        "--prompt-only",
        action="store_true",
        help="Print the analysis prompt without invoking the agent.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output validation results as JSON.",
    )

    args = parser.parse_args()

    # ── Validate mode ─────────────────────────────────────────
    if args.validate:
        result = validate_template(args.validate)

        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            status = "VALID" if result["valid"] else "INVALID"
            print(f"Template Validation: {status}")
            print(f"  File: {args.validate}")
            stats = result.get("stats", {})
            print(f"  Sections: {stats.get('section_count', 0)}")
            print(f"  Slots: {stats.get('total_slots', 0)} "
                  f"(required: {stats.get('required_slots', 0)})")

            if result["errors"]:
                print(f"\nErrors ({len(result['errors'])}):")
                for err in result["errors"]:
                    print(f"  - {err}")

            if result["warnings"]:
                print(f"\nWarnings ({len(result['warnings'])}):")
                for warn in result["warnings"]:
                    print(f"  - {warn}")

        sys.exit(0 if result["valid"] else 1)

    # ── Schema mode ───────────────────────────────────────────
    if args.schema:
        show_schema(args.schema)
        sys.exit(0)

    # ── Input/scan mode ───────────────────────────────────────
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)

        prompt = generate_scan_prompt(str(input_path), args.type)

        if args.prompt_only:
            print(prompt)
            sys.exit(0)

        # In production, this would delegate to the @template-scanner agent.
        # For now, print the prompt and instructions.
        print("=" * 60)
        print("SCAN-AND-REPLICATE: Template Scanner")
        print("=" * 60)
        print()
        print(f"Input image: {input_path}")
        print(f"Document type: {args.type}")
        print(f"Output target: {args.output or '(stdout)'}")
        print()
        print("This operation requires the @template-scanner Claude Code agent")
        print("with multimodal vision capabilities.")
        print()
        print("Agent invocation:")
        print(f"  @template-scanner analyze {input_path} --type {args.type}")
        print()
        print("Generated analysis prompt:")
        print("-" * 40)
        print(prompt)

        # First-run HitL flow
        print("-" * 40)
        print()
        print("FIRST-RUN PROTOCOL:")
        print("  1. Agent scans the document image")
        print("  2. Agent generates candidate template YAML")
        print("  3. Template is displayed for human review")
        print("  4. Human confirms or requests adjustments")
        print("  5. Confirmed template is saved to templates/ directory")
        print()
        print("Subsequent generations use the confirmed template automatically.")


if __name__ == "__main__":
    main()

# Step 5: System Architecture Blueprint
## Church Administration AI Agentic Workflow Automation System

**Generated**: 2026-02-28
**Team**: `arch-blueprint` (3 parallel agents)
**Input Sources**: Step 1 (Domain Analysis), Step 2 (Template Analysis), Step 4 (Data Architecture Spec), PRD
**Component Specifications**:
- `step5-agent-architecture.md` — Agent specs + feature workflow blueprints (72KB)
- `step5-pipeline-architecture.md` — Data pipeline + scan-and-replicate engine (98KB)
- `step5-hooks-validation.md` — P1 validation scripts + hooks + slash commands (82KB)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architectural Overview](#2-architectural-overview)
3. [Agent Architecture](#3-agent-architecture)
4. [Feature Workflow Blueprints](#4-feature-workflow-blueprints)
5. [Data Pipeline Architecture](#5-data-pipeline-architecture)
6. [Scan-and-Replicate Engine](#6-scan-and-replicate-engine)
7. [P1 Validation Framework](#7-p1-validation-framework)
8. [Hook Configuration](#8-hook-configuration)
9. [Slash Command Specifications](#9-slash-command-specifications)
10. [Human-in-the-Loop Architecture](#10-human-in-the-loop-architecture)
11. [Autopilot Eligibility Matrix](#11-autopilot-eligibility-matrix)
12. [Cross-Workflow Data Dependencies](#12-cross-workflow-data-dependencies)
13. [Shared Utilities](#13-shared-utilities)
14. [Implementation Roadmap](#14-implementation-roadmap)
15. [Verification Report](#15-verification-report)

---

## 1. Executive Summary

[trace:step-1:domain-analysis] [trace:step-4:schema-specs]

This document defines the complete system architecture for the Church Administration AI Agentic Workflow Automation System, targeting Korean mid-size churches (100-500 members). The architecture comprises:

- **10 specialized agents** with strict write-permission separation (one writer per data file)
- **4 feature workflow blueprints** following the 3-phase structure with Inherited DNA
- **3-tier data ingestion pipeline** (Excel/CSV → Word/PDF → Images) with confidence scoring
- **Scan-and-replicate engine** for 7 Korean church document types
- **5 P1 validation scripts** with 25 deterministic checks (no AI judgment)
- **3 hook configurations** for data protection, YAML syntax, and infrastructure health
- **4 slash commands** for human-in-the-loop review gates

### Inherited DNA

This architecture inherits from the parent AgenticWorkflow genome:

| DNA Pattern | Application in Church Admin |
|------------|---------------------------|
| absolute-criteria | Quality > Speed; SOT single-writer; CCP before code changes |
| sot-pattern | `church-state.yaml` + 6 data files, each with exactly one writer agent |
| 3-phase-structure | All 4 feature workflows follow Research → Planning → Implementation |
| 4-layer-qa | L0 Anti-Skip → L1 Verification → L1.5 pACS → L2 Adversarial Review |
| safety-hooks | `guard_data_files.py` prevents uncontrolled YAML writes |
| adversarial-review | `@reviewer` for architecture, `@fact-checker` for data specs |
| decision-log | `autopilot-logs/` for all auto-approved decisions |
| context-preservation | IMMORTAL sections survive session boundaries |
| cross-step-traceability | All specs trace to Step 1 domain analysis and Step 4 schemas |
| domain-knowledge-structure | Schema fields align with `domain-knowledge.yaml` entities |

---

## 2. Architectural Overview

### System Layer Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface Layer                   │
│  inbox/ drop zone │ CLI commands │ NL interface (future)  │
└────────────┬───────────────┬───────────────┬─────────────┘
             │               │               │
┌────────────▼───────────────▼───────────────▼─────────────┐
│                  Pipeline Layer (Tier A/B/C)              │
│  data-ingestor │ template-scanner │ confidence scoring    │
└────────────┬───────────────┬───────────────┬─────────────┘
             │               │               │
┌────────────▼───────────────▼───────────────▼─────────────┐
│              Human-in-the-Loop Confirmation               │
│  staging/ preview │ approval gates │ dual-review (finance)│
└────────────┬───────────────┬───────────────┬─────────────┘
             │               │               │
┌────────────▼───────────────▼───────────────▼─────────────┐
│                   Agent Layer (10 agents)                 │
│  bulletin-gen │ finance-rec │ member-mgr │ newcomer-trk  │
│  schedule-mgr │ document-gen │ tester │ onboarding-auth  │
└────────────┬───────────────┬───────────────┬─────────────┘
             │               │               │
┌────────────▼───────────────▼───────────────▼─────────────┐
│                    Data Layer (YAML SOT)                  │
│  members │ finance │ schedule │ newcomers │ bulletin-data │
│  church-glossary │ church-state │ templates/*             │
└────────────┬───────────────────────────────┬─────────────┘
             │                               │
┌────────────▼───────────────────────────────▼─────────────┐
│              Validation & Safety Layer                    │
│  P1 validators (5) │ guard hooks │ atomic writes         │
└──────────────────────────────────────────────────────────┘
```

### Foundational Principles

1. **Single Writer Per Data File** [trace:step-4:schema-specs]: Each YAML data file has exactly one designated writer agent. Enforced by `guard_data_files.py` (PreToolUse hook, exit code 2 blocks unauthorized writes).

2. **Pipeline Does Not Write Data Directly**: The data-ingestor produces staging files in `inbox/staging/`; the designated writer agent consumes them after human confirmation.

3. **P1 Before Commit**: Every data mutation passes deterministic P1 validation before reaching human confirmation. Invalid data is never presented for approval.

4. **Finance Permanently Excluded from Autopilot**: Financial data has legal implications (세금영수증, 소득세법). PRD §5.1 F-03 mandates permanent exclusion from auto-approval.

5. **Korean-First UX, English-First Processing**: User-facing content respects Korean conventions (주민등록번호 masking, 한글 금액 변환, 세로쓰기). Internal processing uses English for AI performance optimization.

---

## 3. Agent Architecture

[trace:step-1:domain-analysis] [trace:step-4:schema-specs]

*Full specification: `planning/step5-agent-architecture.md` Part A*

### 3.1 Agent Inventory

| # | Agent Name | Role | Model | Write Target | Rationale |
|---|-----------|------|-------|--------------|-----------|
| 1 | `bulletin-generator` | Weekly bulletin + worship order | sonnet | `data/bulletin-data.yaml` | Template execution — pattern-based slot filling |
| 2 | `finance-recorder` | Financial recording + reports | opus | `data/finance.yaml` | High stakes — tax receipts, legal compliance |
| 3 | `member-manager` | Member registry management | sonnet | `data/members.yaml` | Structured CRUD with cross-ref validation |
| 4 | `newcomer-tracker` | Newcomer journey pipeline | sonnet | `data/newcomers.yaml` | Stage management with pastoral judgment gates |
| 5 | `data-ingestor` | inbox/ file parsing | opus | `inbox/processed/` (staging) | Complex multi-format parsing (Excel, PDF, images) |
| 6 | `template-scanner` | Scan-and-replicate extraction | opus | `templates/*.yaml` | Document analysis requires vision + reasoning |
| 7 | `document-generator` | Certificate/letter/receipt gen | sonnet | `certificates/`, `letters/` | Template-driven with denomination awareness |
| 8 | `church-integration-tester` | Cross-workflow validation | sonnet | `test-reports/` | Data integrity checking |
| 9 | `church-onboarding-author` | IT volunteer documentation | sonnet | `docs/` | Technical writing |
| 10 | `schedule-manager` | Worship/event coordination | sonnet | `data/schedule.yaml` | Schedule conflict detection + recurrence |

### 3.2 Model Selection Rationale

| Model | Assigned To | Selection Criteria |
|-------|------------|-------------------|
| **opus** | finance-recorder, data-ingestor, template-scanner | High-stakes data, complex multi-format parsing, vision+reasoning |
| **sonnet** | All others (7 agents) | Pattern execution, template filling, structured CRUD — higher throughput sufficient |

### 3.3 Write Permission Matrix

[trace:step-4:schema-specs]

| Data File | Sole Writer | All Other Agents |
|-----------|------------|-----------------|
| `data/members.yaml` | `member-manager` | Read-only |
| `data/finance.yaml` | `finance-recorder` | Read-only |
| `data/schedule.yaml` | `schedule-manager` | Read-only |
| `data/newcomers.yaml` | `newcomer-tracker` | Read-only |
| `data/bulletin-data.yaml` | `bulletin-generator` | Read-only |
| `data/church-glossary.yaml` | `template-scanner` | Read-only (append-only updates) |
| `church-state.yaml` | Orchestrator/Team Lead only | Read-only |
| `templates/*.yaml` | `template-scanner` | Read-only |
| `inbox/staging/*` | `data-ingestor` | Read-only (consumed by designated writer) |

**Enforcement**: `guard_data_files.py` (PreToolUse hook) checks the calling agent against this matrix. Unauthorized writes receive exit code 2 (tool call blocked).

### 3.4 Agent Specification Summary

Each agent specification includes (full details in `step5-agent-architecture.md`):
- **name, description, model** — identity and capability
- **Tools Required** — Read, Write, Edit, Bash, etc.
- **permissionMode** — `default` or `bypassPermissions` (finance: always `default`)
- **maxTurns** — bounded task execution (10-25 turns per agent)
- **Memory Scope** — explicit read/write file lists
- **Input/Output Contract** — structured data format specifications
- **When Invoked** — workflow step and trigger conditions
- **SOT Access Pattern** — read-only vs read-write designations
- **Specialization Boundary** — explicit "does NOT" list to prevent scope creep

---

## 4. Feature Workflow Blueprints

[trace:step-1:domain-analysis] [trace:step-2:template-analysis]

*Full specification: `planning/step5-agent-architecture.md` Part B*

### 4.1 Workflow Inventory

| Workflow | Frequency | Key Agents | Risk Level | Autopilot |
|----------|-----------|-----------|------------|-----------|
| `weekly-bulletin` | Weekly (Monday cycle) | bulletin-generator, schedule-manager | LOW | Eligible |
| `newcomer-pipeline` | On-demand (new visitor) | newcomer-tracker, member-manager | MEDIUM | Partial |
| `monthly-finance-report` | Monthly (end-of-month) | finance-recorder, document-generator | HIGH | **PERMANENTLY DISABLED** |
| `document-generator` | On-demand | document-generator, template-scanner | MEDIUM | Eligible (most types) |

### 4.2 Weekly Bulletin Workflow

**Trigger**: Monday morning preparation cycle
**Duration**: ~15 minutes automated, 1 HitL review gate
**Data Sources**: `bulletin-data.yaml`, `schedule.yaml`, `members.yaml` (birthday/anniversary filtering)

```
Step 1: Schedule Verification (schedule-manager reads schedule.yaml)
    ↓
Step 2: Data Completeness Check (bulletin-generator checks bulletin-data.yaml)
    ↓
Step 3: Bulletin Generation (bulletin-generator fills 16 variable regions)
    ↓
Step 4: P1 Validation (validate_bulletin.py — B1-B3 checks)
    ↓
Step 5: Human Review ◆ HitL GATE (review generated bulletin)
    ↓
Step 6: Finalization (output: bulletins/YYYY-MM-DD-bulletin.md)
```

**Inherited DNA**: 3-phase structure, Verification fields on every step, pACS self-rating, context preservation.

### 4.3 Newcomer Pipeline Workflow

**Trigger**: New visitor data arrives (inbox/ file or manual entry)
**Duration**: Multi-day (newcomer journey spans weeks/months)
**Journey Stages**: `first_visit` → `attending` → `small_group` → `baptism_class` → `baptized` → `settled` (milestone-based sequential progression)

```
Step 1: Data Intake (data-ingestor parses newcomer card)
    ↓
Step 2: Human Confirmation ◆ HitL GATE (verify parsed data accuracy)
    ↓
Step 3: Registration (newcomer-tracker creates N-record)
    ↓
Step 4: Welcome Action Generation (template-driven welcome letter/call list)
    ↓
Step 5: Stage Transition ◆ HitL GATE (pastoral judgment: ready for next stage?)
    ↓
Step 6: Settlement ◆ HitL GATE (create permanent member record → M-record)
```

**Cross-File Migration**: N-record → M-record (newcomer-tracker marks `settled`, member-manager creates member record). Bidirectional consistency check via N5 validation rule.

### 4.4 Monthly Finance Report Workflow

**Trigger**: End of month (1st-5th of following month)
**Duration**: Several days (data collection → verification → report generation)
**CRITICAL**: Autopilot **PERMANENTLY DISABLED** per PRD §5.1 F-03

```
Step 1: Data Ingestion ◆◆ HitL DOUBLE REVIEW (financial data accuracy)
    ↓
Step 2: Data Recording ◆◆ HitL DOUBLE REVIEW (commit financial records)
    ↓
Step 3: Monthly Summary (arithmetic aggregation — deterministic)
    ↓
Step 4: Report Generation (monthly financial report)
    ↓
Step 5: Report Review ◆◆ HitL DOUBLE REVIEW (dual approval mandatory)
    ↓
Step 6: Receipt Generation ◆◆ HitL DOUBLE REVIEW (legal tax donation receipts)
```

**Double Review Pattern**: Two separate human approvals required. First reviewer checks data accuracy; second reviewer (당회장 or designated elder) provides governance approval.

### 4.5 Document Generator Workflow

**Trigger**: On-demand (certificate request, official letter, invitation)
**Document Types**: 7 types from Step 2 analysis [trace:step-2:template-analysis]

```
Step 1: Template Check (verify template exists for document type)
    ↓
Step 2: Template Setup ◆ HitL GATE (first-time template confirmation)
    ↓
Step 3: Document Generation (template-driven slot filling)
    ↓
Step 4: Document Review ◆ HitL GATE (human reviews generated document)
```

**Denomination Awareness**: Template system supports denomination-specific headers and governance terminology (예장통합, 예장합동, 기감, 기장, 기하, 기성 — 6 denominations per Step 1 domain analysis).

---

## 5. Data Pipeline Architecture

[trace:step-1:data-model] [trace:step-4:schema-specs]

*Full specification: `planning/step5-pipeline-architecture.md` Parts A-B*

### 5.1 3-Tier Pipeline Overview

The inbox/ pipeline is the primary entry point for non-technical users (PRD persona: 행정 간사 김미영, 42세, CLI 경험 없음).

| Tier | Input Format | Technology | Base Confidence | Use Case |
|------|-------------|-----------|-----------------|----------|
| **A** | Excel (.xlsx), CSV (.csv) | openpyxl, pandas, chardet | 0.95 | 헌금내역, 교인명부, 새신자등록카드 |
| **B** | Word (.docx), PDF (.pdf) | python-docx, Claude Read | 0.70 | 심방일지, 회의안건, 공문 |
| **C** | Images (.jpg, .png) | Claude multimodal, Tesseract OCR | 0.55 | Receipts, name cards, bulletin text |

### 5.2 Pipeline Orchestration Flow

```
inbox/{file}
    │
    ▼
[File Detection] ← inotify/polling (1-minute interval)
    │
    ▼
[Format Classification] ← extension + magic bytes
    │
    ├── .xlsx/.csv ──→ [Tier A: Structured Parser]
    │                      openpyxl column mapping
    │                      pandas DataFrame validation
    │                      chardet Korean encoding detection
    │
    ├── .docx/.pdf ──→ [Tier B: Semi-Structured Parser]
    │                      python-docx paragraph extraction
    │                      Claude Read for complex PDFs
    │                      Section/heading-based field mapping
    │
    └── .jpg/.png ──→ [Tier C: Unstructured Parser]
                          Claude multimodal vision analysis
                          Tesseract OCR fallback
                          Confidence-scored field extraction
    │
    ▼
[Confidence Scoring] ← per-field + aggregate score
    │
    ▼
[P1 Validation] ← validate_members/finance/schedule/newcomers
    │
    ▼
[Staging] → inbox/staging/{timestamp}-{filename}.yaml
    │
    ▼
[Human Confirmation] ◆ HitL GATE (preview + approve/reject/edit)
    │
    ▼
[Writer Agent] ← designated sole writer consumes staging file
    │
    ▼
[Processed] → inbox/processed/{date}/{filename}
```

### 5.3 Directory Structure

```
inbox/
├── documents/           ← Tier A + Tier B input
│   ├── 헌금내역.xlsx       → finance.yaml
│   ├── 새신자등록카드.xlsx  → newcomers.yaml
│   ├── 교인명부.csv        → members.yaml
│   └── 회의안건.pdf        → church-state.yaml
├── images/              ← Tier C input
│   ├── receipt-001.jpg     → finance.yaml
│   └── namecard-kim.jpg    → newcomers.yaml
├── templates/           ← Scan-and-Replicate input
│   └── bulletin-sample.jpg → templates/bulletin-template.yaml
├── staging/             ← Parsed results awaiting confirmation
├── processed/           ← Successfully processed originals
└── errors/              ← Failed processing records
```

### 5.4 Confidence Scoring System

| Threshold | Level | Action | Finance Override |
|-----------|-------|--------|-----------------|
| ≥ 0.90 | HIGH | Auto-stage for review | Still requires dual human approval |
| 0.70-0.89 | MEDIUM | Stage with warnings highlighted | Still requires dual human approval |
| 0.50-0.69 | LOW | Stage with per-field confidence | Still requires dual human approval |
| < 0.50 | REJECTED | Route to `inbox/errors/` | Rejected |

**Key**: Finance data is **never** auto-approved regardless of confidence score.

### 5.5 Korean Encoding Handling

Legacy Korean church files frequently use EUC-KR or CP949 (not UTF-8). The pipeline uses a Korean-aware fallback chain:

1. chardet detection → if confidence > 0.8, use detected encoding
2. Sequential trial: EUC-KR → CP949 → UTF-8-SIG → UTF-8
3. Final fallback: UTF-8 with `errors='replace'` (replacement mode)

### 5.6 HWP File Handling

HWP (한글 워드프로세서) is common in Korean churches but the pyhwp library is unreliable for the binary format. Strategy:
- Detect `.hwp` files → route to `inbox/errors/` with user guidance
- Provide Korean-language instructions for manual PDF export from Hancom Office
- Process the exported PDF through Tier B

### 5.7 Error Handling

12 error types are defined with recovery strategies (full details in `step5-pipeline-architecture.md` Part D):

| Error Type | Recovery | Original Preserved |
|-----------|---------|-------------------|
| Encoding failure | Fallback chain → manual review | Yes |
| Format unsupported | User guidance (HWP → PDF) | Yes |
| Partial extraction | Stage with per-field confidence | Yes |
| Validation failure | Flag in staging, human reviews | Yes |
| Corrupt file | Route to errors/ with metadata | Yes |

**Principle**: No file is ever silently discarded or partially processed without explicit error flagging.

---

## 6. Scan-and-Replicate Engine

[trace:step-2:template-analysis]

*Full specification: `planning/step5-pipeline-architecture.md` Part C*

### 6.1 Overview

The scan-and-replicate engine converts physical document samples (photos/scans) into reusable YAML template definitions. These templates drive the document-generator agent to produce consistent outputs.

### 6.2 Four-Stage Process

```
Stage 1: Document Analysis (Claude multimodal)
    → Identifies fixed/variable regions, layout, fonts, seal placement
    │
Stage 2: Template Generation
    → Produces templates/{type}-template.yaml with slot definitions
    │
Stage 3: Human Confirmation ◆ HitL GATE
    → User reviews template, adjusts slot mappings
    │
Stage 4: Document Generation
    → document-generator fills template with data from YAML sources
```

### 6.3 Supported Document Types

All 7 types from Step 2 template analysis [trace:step-2:template-analysis]:

| # | Document Type | Korean | Variable Regions | Denomination-Specific |
|---|-------------|--------|-----------------|---------------------|
| 1 | Weekly Bulletin | 주보 | 16 regions (sermon, prayer, schedule, birthdays, announcements) | Header, governance terms |
| 2 | Tax Donation Receipt | 기부금영수증 | 8 regions (donor, amounts, periods, Korean numeral total) | Church name, registration # |
| 3 | Worship Order | 순서지 | 12 regions (service items, hymns, scripture, participants) | Liturgical order varies |
| 4 | Official Letter | 공문 | 6 regions (sender, recipient, subject, body, seal) | 당회장 vs 감독 vs 총회장 |
| 5 | Meeting Minutes | 회의록 | 10 regions (date, attendees, agenda, decisions, votes) | 당회록 vs 제직회의록 |
| 6 | Certificate | 증서 | 5 regions (type, name, date, issuer, seal) | Baptism type, church stamp |
| 7 | Invitation | 초청장 | 7 regions (event, venue, date, program, RSVP) | Minimal variation |

### 6.4 Korean Formatting Conventions

From Step 2 analysis [trace:step-2:template-analysis]:
- **Korean Numeral Notation**: 금 일백이십삼만사천원정 (legally required on tax receipts)
- **Seal Placement**: 직인 (official seal) at specific document positions per type
- **Vertical Text Areas**: 세로쓰기 for traditional elements (e.g., hymn boards)
- **Date Format**: YYYY년 MM월 DD일 (Korean era year optional)

---

## 7. P1 Validation Framework

[trace:step-4:validation-rules]

*Full specification: `planning/step5-hooks-validation.md` Part A*

### 7.1 Validation Script Inventory

| Script | Domain | Checks | Rules |
|--------|--------|--------|-------|
| `validate_members.py` | Member registry | 6 | M1 (ID), M2 (required fields), M3 (phone regex), M4 (status enum), M5 (family ID), M6 (dates) |
| `validate_finance.py` | Financial records | 5 | F1 (ID), F2 (amount positivity), F3 (offering sum), F4 (budget arithmetic), F5 (monthly summary) |
| `validate_schedule.py` | Schedule data | 5 | S1 (ID format across 3 types), S2 (time format), S3 (recurrence enum), S4 (status enum), S5 (facility overlap) |
| `validate_newcomers.py` | Newcomer records | 6 | N1 (ID), N2 (journey stage), N3 (date format), N4 (member ref), N5 (settlement consistency), N6 (_stats arithmetic) |
| `validate_bulletin.py` | Bulletin data | 3 | B1 (date consistency), B2 (issue number sequence), B3 (member reference integrity) |

### 7.2 Common Interface

All 5 scripts share:

```bash
python3 church-admin/.claude/hooks/scripts/validate_<domain>.py \
  --data-dir ./church-admin/data/ \
  [--members-file <path>]   # override for cross-ref scripts
  [--fix]                   # auto-fix computed fields (_stats)
```

**JSON Output Schema**:
```json
{
  "valid": true|false,
  "script": "validate_<domain>.py",
  "data_file": "data/<domain>.yaml",
  "checks": [
    {"rule": "M1", "name": "ID Uniqueness", "status": "PASS|FAIL", "detail": "..."}
  ],
  "errors": [],
  "warnings": [],
  "summary": "6/6 checks passed"
}
```

**Exit Codes**: 0 = validation completed (check `valid` field), 1 = fatal error. Exit code 2 is **NOT** used (reserved for PreToolUse hooks).

### 7.3 Key Validation Details

**N2 Journey Stage Sequential Milestones** [trace:step-4:schema-specs]:
```
first_visit → attending → small_group → baptism_class → baptized → settled
```
Each stage transition requires all preceding milestones to be completed (milestone-based prerequisites). Valid milestones: `first_visit`, `welcome_call`, `second_visit`, `small_group_intro`, `baptism_class`, `baptism`. Example: `baptism_class` stage requires milestones `first_visit`, `welcome_call`, `second_visit`, `small_group_intro` all completed.

**N5 Cross-File Settlement Consistency**:
- Forward: If newcomer status = `settled`, a corresponding M-record must exist in `members.yaml`
- Backward: If member has `source: newcomer` and `newcomer_id: N###`, the N-record must have status `settled`
- Graceful degradation: If `members.yaml` is unavailable, N5 emits WARNING not FAIL

**N6 Stats Arithmetic** (added per Step 4 review):
- `_stats.total_active` must equal count of records with `status: active`
- `_stats.by_stage.{stage}` must equal count of records with that `journey_stage`

**F3 Offering Sum Consistency**:
- Total offerings for a period must equal sum of individual offering records
- Void records (`status: void`) excluded from summation

**S5 Facility Booking Overlap Detection**:
- No two bookings for the same facility may have overlapping time ranges
- Algorithm: Sort by start_time, check each pair for overlap

---

## 8. Hook Configuration

[trace:step-4:schema-specs]

*Full specification: `planning/step5-hooks-validation.md` Part B*

### 8.1 Hook Inventory

| Hook | Event | Matcher | Exit Code | Purpose |
|------|-------|---------|-----------|---------|
| `guard_data_files.py` | PreToolUse | `Edit\|Write` | 0 (allow) / 2 (block) | Enforce write permission matrix |
| `validate_yaml_syntax.py` | PostToolUse | `Write` | 0 (always) | YAML syntax check on write |
| `setup_church_admin.py` | Setup | `--init` | 0 (healthy) / 1 (fatal) | Infrastructure health verification |

### 8.2 guard_data_files.py — Write Permission Guard

**Trigger**: Every Edit or Write tool call targeting `church-admin/data/*.yaml`
**Behavior**:
1. Extract target file path from tool input
2. Match against write permission matrix (Section 3.3)
3. Identify calling agent from context
4. If authorized writer → exit 0 (allow)
5. If unauthorized → exit 2 (block) + stderr feedback message

**Special Cases**:
- `church-glossary.yaml`: append-only updates permitted (existing entries never modified)
- `church-state.yaml`: Orchestrator/Team Lead only
- `templates/*.yaml`: `template-scanner` only

### 8.3 validate_yaml_syntax.py — YAML Syntax Check

**Trigger**: Every Write to `*.yaml` files in church-admin/
**Behavior**: `yaml.safe_load()` the written file → report syntax errors via stderr
**Semantics**: Warning-only (exit code 0 always). Does not block writes — reports for correction.

### 8.4 setup_church_admin.py — Infrastructure Health

**Trigger**: `claude --init` (Setup event)
**Checks** (CA-1 through CA-8):

| Check | What | Failure Action |
|-------|------|---------------|
| CA-1 | Python ≥ 3.9 | Fatal (exit 1) |
| CA-2 | PyYAML importable | Fatal (exit 1) |
| CA-3 | `church-admin/data/` directory exists | Auto-create |
| CA-4 | All 6 data files exist | Warning |
| CA-5 | All 5 validation scripts exist | Warning |
| CA-6 | `guard_data_files.py` hook exists | Warning |
| CA-7 | Runtime directories exist | Auto-create |
| CA-8 | SOT file (`church-state.yaml`) parseable | Warning |

### 8.5 settings.json Integration

Three new hook entries are added to `.claude/settings.json` alongside existing parent AgenticWorkflow hooks. All use `if test -f; then; fi` guards so hooks only fire when church-admin scripts exist.

---

## 9. Slash Command Specifications

*Full specification: `planning/step5-hooks-validation.md` Part C*

### 9.1 Command Inventory

| Command | Step | Gate | Key Checks |
|---------|------|------|-----------|
| `/review-research` | 3 | Research validation | Domain coverage, terminology, template analysis completeness |
| `/approve-architecture` | 6 | Architecture approval | Schema design, agent specs, pipeline design, hook configs |
| `/review-m1` | 10 | M1 core features | Workflow execution, P1 validation results, integration tests |
| `/final-review` | 14 | System acceptance | Full DNA inheritance, all P1 scripts pass, documentation complete |

### 9.2 Autopilot Behavior

In Autopilot mode, slash commands auto-approve with quality-maximizing defaults:
1. Execute complete review (generate full assessment, don't skip)
2. Apply quality-maximizing default approval
3. Record decision in `autopilot-logs/step-N-decision.md`
4. Advance to next step

---

## 10. Human-in-the-Loop Architecture

[trace:step-1:domain-analysis]

*Full specification: `planning/step5-agent-architecture.md` Part C*

### 10.1 Risk Classification

| Risk Level | Gate Pattern | Review Type | Finance Override |
|-----------|-------------|------------|-----------------|
| **HIGH** | ◆◆ Double Review | Two separate approvers | Always HIGH regardless |
| **MEDIUM** | ◆ Single Review | One approver | N/A |
| **LOW** | ◆ Single Review | One approver (Autopilot eligible) | N/A |

### 10.2 Gate Inventory

| Gate ID | Workflow | Step | Risk | Reviewer |
|---------|----------|------|------|----------|
| HitL-F01 | monthly-finance-report | 1 (Data Ingestion) | HIGH | 재정부장 + 당회장 |
| HitL-F02 | monthly-finance-report | 2 (Data Recording) | HIGH | 재정부장 + 당회장 |
| HitL-F03 | monthly-finance-report | 5 (Report Review) | HIGH | 재정부장 + 당회장 |
| HitL-F04 | monthly-finance-report | 6 (Receipt Gen) | HIGH | 재정부장 + 당회장 |
| HitL-N01 | newcomer-pipeline | 2 (Confirmation) | MEDIUM | 새신자 담당 |
| HitL-N02 | newcomer-pipeline | 5 (Stage Transition) | MEDIUM | 담임목사/교육전도사 |
| HitL-N03 | newcomer-pipeline | 6 (Settlement) | HIGH | 담임목사 + 행정 간사 |
| HitL-D01 | document-generator | 2 (Template Setup) | MEDIUM | 행정 간사 |
| HitL-D02 | document-generator | 4 (Document Review) | MEDIUM | 행정 간사 |
| HitL-B01 | weekly-bulletin | 5 (Bulletin Review) | LOW | 행정 간사 |

---

## 11. Autopilot Eligibility Matrix

[trace:step-4:schema-specs]

*Full specification: `planning/step5-agent-architecture.md` Part E*

### 11.1 Workflow-Level

| Workflow | Autopilot | Justification |
|----------|-----------|---------------|
| `weekly-bulletin` | **ELIGIBLE** | Low risk, informational content, errors catchable at print time |
| `newcomer-pipeline` | **PARTIAL** | Registration eligible, stage transitions require pastoral judgment |
| `monthly-finance-report` | **PERMANENTLY DISABLED** | Legal/fiduciary obligations, PRD §5.1 F-03 |
| `document-generator` | **ELIGIBLE** (most types) | Template guardrails, single review gate |

### 11.2 Guard Rails

| Guard | Implementation | Purpose |
|-------|---------------|---------|
| Financial Lock | `guard_data_files.py` + workflow config | Finance Autopilot permanently disabled |
| P1 Gate | `validate_*.py` → `valid: true` required | No auto-approval if checks fail |
| pACS Floor | pACS < 50 → mandatory human review | RED-zone never auto-approved |
| Audit Trail | `autopilot-logs/` | Complete decision record |

---

## 12. Cross-Workflow Data Dependencies

[trace:step-4:schema-specs]

*Full specification: `planning/step5-agent-architecture.md` Part D*

### 12.1 Data Access Matrix

| Agent | members | finance | schedule | newcomers | bulletin-data | glossary |
|-------|---------|---------|----------|-----------|--------------|---------|
| bulletin-generator | R | — | R | — | **W** | R |
| finance-recorder | R | **W** | — | — | — | R |
| member-manager | **W** | — | — | R | — | R |
| newcomer-tracker | R | — | — | **W** | — | R |
| schedule-manager | — | — | **W** | — | R | R |
| document-generator | R | R | — | — | — | R |
| data-ingestor | — | — | — | — | — | R |
| template-scanner | — | — | — | — | — | **W** |
| integration-tester | R | R | R | R | R | R |
| onboarding-author | — | — | — | — | — | R |

**W** = Sole writer, **R** = Read-only, **—** = No access

### 12.2 Critical Cross-File Dependencies

1. **Newcomer → Member Migration** (N5 ↔ M1): `newcomer-tracker` marks `settled` → `member-manager` creates M-record. Bidirectional consistency enforced by N5 validation.

2. **Finance → Member Donor Tracking** (F3 ↔ M): `finance-recorder` references `member_id` in offering records. Cross-ref validated by F-rules.

3. **Bulletin → Schedule + Members**: `bulletin-generator` reads `schedule.yaml` for service times and `members.yaml` for birthday/anniversary filtering.

4. **Document → Members + Finance**: `document-generator` reads member data for certificates and financial data for annual tax receipts.

---

## 13. Shared Utilities

*Full specification: `planning/step5-hooks-validation.md` Part D*

### 13.1 atomic_write_yaml()

Pattern: `fcntl.flock` + `tempfile.NamedTemporaryFile` + `os.rename`

```python
def atomic_write_yaml(filepath: str, data: dict) -> None:
    """Write YAML atomically using flock + temp file + rename pattern.

    Layer 3 of data integrity architecture [trace:step-4:schema-specs]:
    - flock guards the write phase of the temp file
    - os.rename provides atomic replacement on same filesystem
    - Layer 1 (guard_data_files.py) prevents cross-writer races
    """
```

### 13.2 church_data_utils.py

Shared helper library with:
- YAML loading with Korean encoding support
- Cross-file member/family ID lookup
- Date validation (Korean format support)
- Phone number validation (relaxed regex: `^010-\d{4}-\d{4}$`)
- ID format validators (M, F, N, OFF, EXP, SVC, EVT, FAC patterns)
- Compiled regex patterns (module-level, once per process)

### 13.3 Korean Numeral Conversion

```python
def integer_to_korean_numeral(amount: int) -> str:
    """Convert integer to Korean formal numeral notation.

    Example: 1_234_000 → "일백이십삼만사천원정"
    Legally required on tax donation receipts per 소득세법.
    """
```

### 13.4 Privacy Masking

```python
def mask_korean_name(name: str) -> str:
    """Mask middle character(s) for bulletin display.
    '김철수' → '김○수', '남궁세연' → '남궁○연'"""

def mask_resident_number(number: str) -> str:
    """Mask Korean resident registration number for receipts.
    'YYMMDD-NNNNNNN' → 'YYMMDD-N******'"""
```

---

## 14. Implementation Roadmap

This architecture blueprint provides complete implementation specifications for:

| Step | What | Key Inputs from This Blueprint |
|------|------|-------------------------------|
| **7** | Infrastructure Foundation Build | Directory structure (§5.3), seed data schemas (§3.3), SOT initialization |
| **8** | P1 Validation Scripts | Validation rules (§7), JSON output schema (§7.2), shared utilities (§13) |
| **9** | M1 Core Features | Agent specs (§3), workflow blueprints (§4), pipeline design (§5) |
| **10** | M1 Review | Integration test criteria, P1 validation results |
| **11** | M2 Extended Features | Document generator (§4.5), denomination support (§6.3), schedule manager |
| **12** | Integration Testing | Cross-workflow dependencies (§12), full P1 validation suite |
| **13** | Documentation | Agent specs for onboarding docs, pipeline overview for user guide |

### Step-Specific Context Injection

| Step | Injection Pattern | Sections to Extract |
|------|------------------|-------------------|
| Step 7 | Pattern A (Full) | §3.3 (write matrix), §5.3 (dirs), §14 (roadmap) |
| Step 8 | Pattern B (Filtered) | §7 (validation), §13 (utilities) |
| Step 9 | Pattern B (Filtered) | §3 (agents), §4 (workflows), §5 (pipeline) |
| Step 11 | Pattern B (Filtered) | §4.4-4.5 (finance/doc workflows), §6 (scan-and-replicate) |

---

## 15. Verification Report

### 15.1 Unified Verification Against Step 5 Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | 8+ agent specifications complete with: name, description, model, tools, permissionMode, maxTurns, memory scope | **PASS** | 10 agents specified in §3 (bulletin-generator, finance-recorder, member-manager, newcomer-tracker, data-ingestor, template-scanner, document-generator, church-integration-tester, church-onboarding-author, schedule-manager). Each has full spec in `step5-agent-architecture.md` A.2-A.11. |
| 2 | 4+ feature workflow blueprints follow 3-phase structure with Verification fields on every agent step | **PASS** | 4 workflows in §4 (weekly-bulletin, newcomer-pipeline, monthly-finance-report, document-generator). Each has Inherited DNA table + Verification criteria on every step. Full details in `step5-agent-architecture.md` B.1-B.4. |
| 3 | inbox/ pipeline design covers all 3 tiers with specific Python libraries and column/field mapping per tier | **PASS** | §5 covers Tier A (openpyxl, pandas, chardet), Tier B (python-docx, Claude Read), Tier C (Claude multimodal, Tesseract OCR). Column mappings in `step5-pipeline-architecture.md` A.3-A.5. |
| 4 | scan-and-replicate engine handles all 7 document types from Step 2 analysis [trace:step-2:template-analysis] | **PASS** | §6 covers all 7 types (Bulletin, Receipt, Worship Order, Official Letter, Meeting Minutes, Certificate, Invitation). 4-stage process in `step5-pipeline-architecture.md` Part C. |
| 5 | 5 validation script specs include all rules from Step 4 schema design [trace:step-4:validation-rules] | **PASS** | §7 covers validate_members (M1-M6), validate_finance (F1-F5), validate_schedule (S1-S5), validate_newcomers (N1-N6), validate_bulletin (B1-B3). 25 total checks. Full details in `step5-hooks-validation.md` Part A. |
| 6 | Human-in-the-loop gates correctly classified: high risk (finance → double-review, Autopilot disabled), medium (newcomer/docs → single-review), low (bulletin → single-review, Autopilot eligible) | **PASS** | §10 defines 3 risk levels with 10 HitL gates. Finance: HIGH with double-review (HitL-F01 to F04). Newcomer: MEDIUM/HIGH with single/double-review (HitL-N01/N02/N03). Docs: MEDIUM (HitL-D01/D02). Bulletin: LOW (HitL-B01, Autopilot eligible). |
| 7 | Cross-step traceability: architecture decisions trace to domain analysis [trace:step-1] and schema specs [trace:step-4] | **PASS** | Trace markers throughout: [trace:step-1:domain-analysis], [trace:step-1:data-model], [trace:step-1:terminology], [trace:step-2:template-analysis], [trace:step-4:schema-specs], [trace:step-4:validation-rules]. 25+ markers across component specs. |
| 8 | Pipeline connection: Architecture blueprint provides complete implementation specs for Steps 7-13 | **PASS** | §14 maps each downstream step to specific sections of this blueprint. Context injection patterns defined per step. |

### 15.2 Component Verification Summary

| Component | Spec File | Self-Verification | Criteria |
|-----------|-----------|-------------------|----------|
| Agent Architecture | `step5-agent-architecture.md` | 8/8 PASS | Agents, workflows, HitL, Autopilot, write permissions, traces, finance lock, Verification fields |
| Pipeline Architecture | `step5-pipeline-architecture.md` | 8/8 PASS | 3 tiers, HitL flow, 7 doc types, error handling, validation integration, traces, glossary, confidence scoring |
| Hook & Validation | `step5-hooks-validation.md` | 8/8 PASS | 5 validators, deterministic checks, JSON output, 3 hooks, 4 commands, atomic write, guard integration, exit codes |

### 15.3 Cross-Reference Integrity

All 3 component specs reference consistent:
- **Data file names**: members.yaml, finance.yaml, schedule.yaml, newcomers.yaml, bulletin-data.yaml, church-glossary.yaml
- **Validation rule IDs**: M1-M6, F1-F5, S1-S5, N1-N6, B1-B3 (25 total, matching Step 4 spec including N6 addition and B1-B3 bulletin validation)
- **Agent names**: 10 agents with identical names across all specs
- **Write permission matrix**: Consistent sole-writer assignments across agent specs, hook specs, and pipeline routing
- **Phone regex**: `^010-\d{4}-\d{4}$` (relaxed per Step 4 review correction)
- **Exit code conventions**: 0/2 for PreToolUse hooks, 0/1 for validators, consistent with parent AgenticWorkflow

---

## Appendix A: Trace Marker Index

| Trace Marker | Source Step | Referenced In |
|-------------|-----------|---------------|
| `[trace:step-1:domain-analysis]` | Step 1 domain analysis | §1, §3, §4, §10 |
| `[trace:step-1:data-model]` | Step 1 data model | §5 |
| `[trace:step-1:terminology]` | Step 1 terminology dictionary | component specs (step5-agent-architecture.md) |
| `[trace:step-2:template-analysis]` | Step 2 template analysis | §4, §6 |
| `[trace:step-4:schema-specs]` | Step 4 schema specifications | §1, §2, §3, §5, §7, §8, §11, §12, §13 |
| `[trace:step-4:validation-rules]` | Step 4 validation rule catalog | §7 |

---

*This document was produced by the `arch-blueprint` team (3 parallel agents: @church-agent-architect, @church-pipeline-designer, @church-hook-designer) and merged by the Team Lead with cross-reference verification.*

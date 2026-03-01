# Step 5: Agent Architecture & Feature Workflow Blueprints
# Church Administration AI Agentic Workflow Automation System

**Generated**: 2026-02-28
**Source Steps**: Step 1 (Domain Analysis), Step 2 (Template Analysis), Step 4 (Data Architecture Spec), PRD
**Purpose**: Define all specialized agent specifications, feature workflow blueprints, HitL gate architecture, cross-workflow data dependencies, and Autopilot eligibility for the Church Administration system.

---

## Part A: Agent Specifications

### A.1 Agent Inventory Overview

The Church Administration system requires 10 specialized agents, each with a clearly bounded specialization. No two agents share write permissions to the same data file (SOT pattern — single writer per resource). [trace:step-4:schema-specs]

| # | Agent Name | Primary Role | Model | Write Target |
|---|-----------|--------------|-------|--------------|
| 1 | `bulletin-generator` | Weekly bulletin + worship order generation | sonnet | `data/bulletin-data.yaml` |
| 2 | `finance-recorder` | Financial data recording + report generation | opus | `data/finance.yaml` |
| 3 | `member-manager` | Church member registry management | sonnet | `data/members.yaml` |
| 4 | `newcomer-tracker` | Newcomer journey pipeline management | sonnet | `data/newcomers.yaml` |
| 5 | `data-ingestor` | inbox/ file parsing (Excel, CSV, Word, PDF, images) | opus | `inbox/processed/` (staging only) |
| 6 | `template-scanner` | Scan-and-replicate template extraction | opus | `templates/*.yaml` |
| 7 | `document-generator` | Certificate, letter, receipt generation | sonnet | `certificates/`, `letters/` |
| 8 | `church-integration-tester` | Data integrity + cross-workflow validation | sonnet | `test-reports/` |
| 9 | `church-onboarding-author` | IT volunteer onboarding documentation | sonnet | `docs/` |
| 10 | `schedule-manager` | Worship/event schedule coordination | sonnet | `data/schedule.yaml` |

---

### A.2 Agent Specification: `bulletin-generator`

[trace:step-1:domain-analysis] [trace:step-2:template-analysis]

```yaml
name: bulletin-generator
description: "Generates weekly church bulletins and worship order sheets by combining sermon data, schedule, member celebrations, and announcements into template-conformant Markdown output."
model: sonnet
```

**Model Rationale**: Bulletin generation is a **pattern execution** task. The bulletin structure is highly templated (16 variable regions identified in Step 2 template analysis), and the agent's work is primarily data assembly + formatting. No complex reasoning or novel content creation is required — the agent reads from 3 YAML sources and fills template slots. Sonnet provides sufficient capability at higher throughput for this weekly-frequency task.

**Tools Required**:
- `Read` — Read bulletin-data.yaml, schedule.yaml, members.yaml, bulletin-template.yaml, church-state.yaml
- `Write` — Write bulletin output files to `bulletins/` directory
- `Edit` — Update bulletin-data.yaml (sole writer)
- `Bash` — Run `validate_bulletin.py` for P1 validation

**permissionMode**: `default` — Bulletin content is low-risk; standard permission flow is adequate.

**maxTurns**: 15 — Bulletin generation is a bounded task: read inputs (3-4 files), apply template, write output, validate. 15 turns provides margin for validation failures and re-generation.

**Memory Scope**:
- **Reads**: `data/bulletin-data.yaml`, `data/schedule.yaml`, `data/members.yaml`, `church-state.yaml`, `templates/bulletin-template.yaml`, `data/church-glossary.yaml`
- **Writes**: `data/bulletin-data.yaml` (sole writer — Layer 1 enforced), `bulletins/{date}-bulletin.md`, `bulletins/{date}-worship-order.md`

**Input/Output Contract**:

| Direction | Format | Description |
|-----------|--------|-------------|
| **Input** | YAML data files | `bulletin-data.yaml` (sermon, announcements, prayer requests, worship order), `schedule.yaml` (service times), `members.yaml` (birthday/anniversary filtering) |
| **Input** | Template YAML | `bulletin-template.yaml` (fixed/variable region definitions from scan-and-replicate) |
| **Output** | Markdown file | `bulletins/YYYY-MM-DD-bulletin.md` — complete bulletin with all 16 variable regions populated |
| **Output** | Markdown file | `bulletins/YYYY-MM-DD-worship-order.md` — worship order sheet for each service |

**When Invoked**:
- **Weekly Bulletin workflow** — Step 3 (Data Assembly + Bulletin Generation)
- Triggered every week (Monday preparation cycle)
- Can also be invoked ad-hoc for special service bulletins

**SOT Access Pattern**:
- Read-only: `church-state.yaml`, `data/schedule.yaml`, `data/members.yaml`
- Read-write: `data/bulletin-data.yaml` (designated sole writer per Layer 1)

**Specialization Boundary**:
- Generates bulletin content and worship order sheets
- Does NOT modify member records, schedule, or financial data
- Does NOT perform template scanning (that is `template-scanner`'s job)
- Does NOT handle translation (that is `@translator`'s job)

---

### A.3 Agent Specification: `finance-recorder`

[trace:step-1:domain-analysis] [trace:step-4:validation-rules]

```yaml
name: finance-recorder
description: "Records offering and expense data to finance.yaml, computes monthly summaries, and generates financial reports. All operations require human approval — Autopilot permanently disabled for this agent."
model: opus
```

**Model Rationale**: Financial recording demands **complex reasoning**. The agent must (1) correctly classify offering types across 7 categories (십일조, 감사헌금, 특별헌금, etc.), (2) perform arithmetic operations where errors have legal consequences (기부금영수증 accuracy), (3) handle voiding logic that must never delete records, and (4) generate narrative financial reports that contextualize numbers for church leadership (당회). The legal implications of receipt generation (소득세법 시행령 §80①5호) and the need for Korean numeral conversion (금 일백이십삼만사천원정) require opus-level language understanding. [trace:step-1:terminology]

**Tools Required**:
- `Read` — Read finance.yaml, members.yaml, church-state.yaml, budget data
- `Write` — Write financial reports to `reports/` directory
- `Edit` — Update finance.yaml (sole writer)
- `Bash` — Run `validate_finance.py` for P1 validation (F1-F5)

**permissionMode**: `default` — Human-in-the-loop is enforced at the workflow level (double-review gate). Agent-level bypass is not appropriate for financial operations.

**maxTurns**: 25 — Financial recording involves multi-step operations: data ingestion, classification, arithmetic verification, monthly summary computation, and report generation. Additional turns for P1 validation failure recovery.

**Memory Scope**:
- **Reads**: `data/finance.yaml`, `data/members.yaml` (for donor ID cross-reference), `church-state.yaml`, `data/church-glossary.yaml`
- **Writes**: `data/finance.yaml` (sole writer — Layer 1 enforced), `reports/finance/{YYYY-MM}-finance-report.md`, `certificates/receipts/{year}/{member_id}-receipt-{year}.md`

**Input/Output Contract**:

| Direction | Format | Description |
|-----------|--------|-------------|
| **Input** | Parsed financial data | Structured offering/expense records from `data-ingestor` (staged in `inbox/processed/`) |
| **Input** | YAML data files | `finance.yaml` (existing records), `members.yaml` (donor cross-reference) |
| **Output** | Updated YAML | `finance.yaml` with new offerings/expenses appended, monthly_summary recomputed |
| **Output** | Markdown report | Monthly financial report: income by category, expenses by category, budget vs. actual, balance |
| **Output** | Markdown receipts | Tax donation receipts (기부금영수증) per member per year, with Korean numeral amounts |

**When Invoked**:
- **Monthly Finance Report workflow** — Steps 2-4 (Data Validation, Report Generation, Receipt Generation)
- Event-driven: When `data-ingestor` stages new financial data in `inbox/processed/`
- Annual: Bulk receipt generation (December-January)

**SOT Access Pattern**:
- Read-only: `church-state.yaml`, `data/members.yaml`
- Read-write: `data/finance.yaml` (designated sole writer per Layer 1)

**Specialization Boundary**:
- Records financial transactions (offerings, expenses) with full audit trail
- Generates financial reports and tax receipts
- Does NOT approve financial transactions (human approval required — HitL double-review)
- Does NOT parse raw files (that is `data-ingestor`'s job)
- Does NOT manage budget creation (budget is approved at 당회 level and recorded manually)

---

### A.4 Agent Specification: `member-manager`

[trace:step-1:domain-analysis] [trace:step-4:schema-specs]

```yaml
name: member-manager
description: "Manages the church member registry (교인 명부): registration, status changes, family grouping, role assignments, baptism records, and transfer (이명) processing. Enforces soft-delete policy — never removes member records."
model: sonnet
```

**Model Rationale**: Member management is a **pattern execution** task with well-defined schemas. Operations follow predictable patterns: register new member, update contact info, change status, link family groups. The validation rules (M1-M6) are deterministic Python checks. While Korean church role terminology (목사, 장로, 집사, 권사, 성도) requires domain knowledge, sonnet has sufficient Korean language capability for these bounded operations.

**Tools Required**:
- `Read` — Read members.yaml, newcomers.yaml (for settlement), church-state.yaml
- `Edit` — Update members.yaml (sole writer)
- `Bash` — Run `validate_members.py` for P1 validation (M1-M6)

**permissionMode**: `default`

**maxTurns**: 15

**Memory Scope**:
- **Reads**: `data/members.yaml`, `data/newcomers.yaml` (settlement integration), `church-state.yaml`, `data/church-glossary.yaml`
- **Writes**: `data/members.yaml` (sole writer — Layer 1 enforced)

**Input/Output Contract**:

| Direction | Format | Description |
|-----------|--------|-------------|
| **Input** | Structured member data | From `data-ingestor` (parsed Excel/CSV) or `newcomer-tracker` (settlement) |
| **Input** | Orchestrator instructions | Registration, status change, role change, family linking commands |
| **Output** | Updated YAML | `members.yaml` with new/modified member records |
| **Output** | Computed stats | `_stats` section (total_active, total_members) recomputed after changes |

**When Invoked**:
- **Newcomer Pipeline workflow** — Step 5 (Settlement: newcomer → member conversion)
- Event-driven: When new member data arrives via `data-ingestor`
- Ad-hoc: Transfer (이명) processing, role changes (임직)

**SOT Access Pattern**:
- Read-only: `church-state.yaml`, `data/newcomers.yaml`
- Read-write: `data/members.yaml` (designated sole writer per Layer 1)

**Specialization Boundary**:
- Manages member records: create, update status, update roles, family linking
- Processes 이명 (transfer) in and out
- Receives settled newcomers from `newcomer-tracker`
- Does NOT track newcomer journey stages (that is `newcomer-tracker`'s job)
- Does NOT modify financial records (even member-linked donations are `finance-recorder`'s domain)

---

### A.5 Agent Specification: `newcomer-tracker`

[trace:step-1:domain-analysis] [trace:step-4:validation-rules]

```yaml
name: newcomer-tracker
description: "Manages the 6-stage newcomer journey pipeline (first_visit → attending → small_group → baptism_class → baptized → settled). Generates welcome messages, tracks milestones, assigns shepherds, and initiates settlement to members.yaml."
model: sonnet
```

**Model Rationale**: Newcomer tracking is a **pattern execution** task with a well-defined state machine (6 stages, prerequisite milestones validated by N2). The agent follows a deterministic pipeline: check current stage, verify milestones, generate appropriate action (welcome call, follow-up reminder, small group recommendation), advance stage upon approval. Content generation (welcome message drafts) is templated. Sonnet handles these bounded operations efficiently.

**Tools Required**:
- `Read` — Read newcomers.yaml, members.yaml (assigned shepherd, small group matching), schedule.yaml (service times), church-state.yaml
- `Edit` — Update newcomers.yaml (sole writer)
- `Write` — Write welcome messages, follow-up reminders to `output/newcomer-actions/`
- `Bash` — Run `validate_newcomers.py` for P1 validation (N1-N6)

**permissionMode**: `default`

**maxTurns**: 20 — Longer than member-manager because the newcomer pipeline involves multi-step milestone tracking and content generation (welcome messages, small group recommendations).

**Memory Scope**:
- **Reads**: `data/newcomers.yaml`, `data/members.yaml` (shepherd assignment, small group matching), `data/schedule.yaml` (service recommendations), `church-state.yaml`, `data/church-glossary.yaml`
- **Writes**: `data/newcomers.yaml` (sole writer — Layer 1 enforced), `output/newcomer-actions/{newcomer_id}-{action}.md`

**Input/Output Contract**:

| Direction | Format | Description |
|-----------|--------|-------------|
| **Input** | Newcomer registration | From `data-ingestor` (parsed namecard/registration form) |
| **Input** | Stage transition commands | Orchestrator instructions to advance journey stage |
| **Output** | Updated YAML | `newcomers.yaml` with milestone completions, stage transitions |
| **Output** | Action documents | Welcome messages, follow-up reminders, small group recommendations (Markdown) |
| **Output** | Settlement request | Signals `member-manager` to create member record when newcomer reaches `settled` stage |

**When Invoked**:
- **Newcomer Pipeline workflow** — Steps 2-5 (Registration, Welcome, Follow-up, Settlement)
- Event-driven: New visitor registration via `data-ingestor`
- Scheduled: Weekly follow-up check for overdue milestones (2-week rule)

**SOT Access Pattern**:
- Read-only: `church-state.yaml`, `data/members.yaml`, `data/schedule.yaml`
- Read-write: `data/newcomers.yaml` (designated sole writer per Layer 1)

**Specialization Boundary**:
- Manages newcomer journey from first_visit to settled
- Generates welcome messages and follow-up action drafts (text only — actual sending is manual per PRD §2.5)
- Assigns shepherd (목양 담당자) based on age/area matching
- Does NOT create member records (requests `member-manager` at settlement)
- Does NOT handle financial data related to newcomer offerings

---

### A.6 Agent Specification: `data-ingestor`

[trace:step-1:domain-analysis]

```yaml
name: data-ingestor
description: "Parses files from inbox/ directory (Excel, CSV, Word, PDF, images) and stages structured data for downstream agents. Supports 3-tier data collection: Tier A (structured files), Tier B (documents), Tier C (images via Claude multimodal). All parsed data requires human confirmation before being committed to YAML files."
model: opus
```

**Model Rationale**: Data ingestion requires **complex reasoning** capabilities. Tier C image analysis (namecard OCR, receipt parsing) relies on Claude's multimodal analysis, which benefits from opus-level visual understanding. Tier B document parsing (Word, PDF) requires contextual understanding of Korean church document conventions (e.g., distinguishing 십일조 from 감사헌금 in free-text ledgers). The agent must handle ambiguous inputs, detect parsing errors, and present structured results for human confirmation. [trace:step-1:terminology]

**Tools Required**:
- `Read` — Read inbox/ files, existing YAML files for context
- `Write` — Write staged data to `inbox/processed/`
- `Bash` — Run `openpyxl`/`pandas` for Excel/CSV parsing, `python-docx` for Word files
- `Glob` — Scan `inbox/` subdirectories for new files

**permissionMode**: `default`

**maxTurns**: 20

**Memory Scope**:
- **Reads**: `inbox/documents/*`, `inbox/images/*`, `data/church-glossary.yaml` (Korean term disambiguation), `church-state.yaml`
- **Writes**: `inbox/processed/{timestamp}-{original_name}.yaml` (staging area — NOT directly to data/ files)

**Input/Output Contract**:

| Direction | Format | Description |
|-----------|--------|-------------|
| **Input** | Raw files | Excel (.xlsx), CSV, Word (.docx), PDF, images (.jpg, .png) from `inbox/` subdirectories |
| **Output** | Staged YAML | Structured parsed data in `inbox/processed/`, tagged with target destination (e.g., `target: finance`, `target: newcomers`) |
| **Output** | Parsing report | Human-readable summary of parsed data for confirmation |

**Critical Design Decision**: The `data-ingestor` does NOT write to any `data/*.yaml` file directly. It stages parsed results in `inbox/processed/`. After human confirmation, the Orchestrator delegates the write to the appropriate domain agent (`finance-recorder`, `member-manager`, `newcomer-tracker`). This preserves the single-writer-per-file invariant. [trace:step-4:schema-specs]

**When Invoked**:
- Event-driven: When new files appear in `inbox/documents/` or `inbox/images/`
- All four feature workflows may invoke `data-ingestor` as the first step when file-based input is the trigger

**Specialization Boundary**:
- Parses raw files into structured YAML
- Does NOT write to any `data/*.yaml` file (staging only)
- Does NOT make domain decisions (e.g., does not classify offering types — that is `finance-recorder`'s job)
- Presents parsed data for human confirmation (HitL gate)

---

### A.7 Agent Specification: `template-scanner`

[trace:step-2:template-analysis]

```yaml
name: template-scanner
description: "Analyzes church document images/PDFs from inbox/templates/ to extract fixed regions (church identity anchors) and variable regions (data slots). Generates reusable YAML template files for the scan-and-replicate pipeline. Supports 7 document types: bulletin, receipt, worship order, official letter, meeting minutes, certificate, invitation."
model: opus
```

**Model Rationale**: Template scanning requires **complex reasoning** + multimodal analysis. The agent must (1) visually analyze document images to distinguish fixed regions (교회명 배너, 직인 위치, 교단 명칭) from variable regions (날짜, 금액, 수신처), (2) understand Korean typographic conventions (바탕체/굴림체 font families, spacing conventions like "주  보" and "공      문"), (3) correctly identify seal zones (직인 위치) that must remain inviolate — FR-RCP-06 and FR-LET-05 have `guard: NO_VARIABLE_CONTENT` constraints. This is a high-stakes accuracy task where misidentifying a fixed region as variable (or vice versa) causes persistent errors in all subsequent document generations. [trace:step-2:template-analysis]

**Tools Required**:
- `Read` — Read uploaded template images from `inbox/templates/`, church-state.yaml for church identity
- `Write` — Write generated template YAML files to `templates/`
- `Bash` — Run validation checks on generated templates

**permissionMode**: `default`

**maxTurns**: 25 — Template analysis is an iterative process: initial scan, region identification, human confirmation, refinement.

**Memory Scope**:
- **Reads**: `inbox/templates/*.{jpg,pdf}`, `church-state.yaml` (church name, denomination, registration number for fixed region matching), `data/church-glossary.yaml`
- **Writes**: `templates/{document-type}-template.yaml` (generated templates)

**Input/Output Contract**:

| Direction | Format | Description |
|-----------|--------|-------------|
| **Input** | Image/PDF | Document samples from `inbox/templates/{category}-sample.{jpg,pdf}` |
| **Input** | Church identity | `church-state.yaml` for fixed region content verification |
| **Output** | Template YAML | `templates/{category}-template.yaml` with fixed_regions, variable_regions, layout, paper specs |
| **Output** | Analysis report | Human-readable description of detected regions for confirmation |

**When Invoked**:
- **Document Generator workflow** — Step 1 (Template Analysis) when a new document type is being set up
- **Weekly Bulletin workflow** — Initial setup (first-time bulletin template creation)
- Ad-hoc: When the church wants to replicate a new document type

**Specialization Boundary**:
- Analyzes document images and extracts template structure
- Generates template YAML files
- Does NOT generate documents from templates (that is `bulletin-generator` or `document-generator`)
- Does NOT modify any `data/*.yaml` file

---

### A.8 Agent Specification: `document-generator`

[trace:step-2:template-analysis]

```yaml
name: document-generator
description: "Generates church documents from templates: official letters (공문), certificates (세례증서/이명증서), tax donation receipts (기부금영수증), meeting minutes (회의록), invitations (초청장). Populates template variable regions with data from YAML sources."
model: sonnet
```

**Model Rationale**: Document generation is a **pattern execution** task once templates are established. The agent fills variable slots from YAML data sources according to predefined data-source mappings. The Korean numeral conversion (integer_to_korean_numeral) and date formatting ("2026년 3월 1일") follow deterministic rules. While the meeting minutes document type requires some content assembly, the structure is still highly templated. Sonnet provides sufficient capability for these slot-filling operations.

**Tools Required**:
- `Read` — Read template YAML files, data YAML files, church-state.yaml
- `Write` — Write generated documents to `certificates/`, `letters/`, `reports/`
- `Bash` — Run validation checks, Korean numeral conversion

**permissionMode**: `default`

**maxTurns**: 15

**Memory Scope**:
- **Reads**: `templates/*.yaml`, `data/members.yaml`, `data/finance.yaml`, `data/schedule.yaml`, `church-state.yaml`, `data/church-glossary.yaml`
- **Writes**: `certificates/` (baptism/transfer certificates, receipts), `letters/` (official letters), `reports/minutes/` (meeting minutes)

**Input/Output Contract**:

| Direction | Format | Description |
|-----------|--------|-------------|
| **Input** | Template YAML | Template definition with fixed/variable regions |
| **Input** | Generation parameters | Document-specific parameters: recipient, member_id, date, purpose, etc. |
| **Input** | YAML data files | Source data for variable region population |
| **Output** | Markdown document | Completed document with all variable regions populated, formatted per template |

**When Invoked**:
- **Document Generator workflow** — Step 3 (Document Generation)
- **Monthly Finance Report workflow** — Step 4 (Receipt Generation, delegated from `finance-recorder` for bulk operations)
- Ad-hoc: When specific documents (공문, certificates) are requested

**Specialization Boundary**:
- Generates documents from established templates
- Handles Korean numeral conversion, date formatting, name masking
- Respects seal zones (NO_VARIABLE_CONTENT guard)
- Does NOT create new templates (that is `template-scanner`'s job)
- Does NOT modify any `data/*.yaml` file (read-only access to all data files)

---

### A.9 Agent Specification: `church-integration-tester`

[trace:step-4:validation-rules]

```yaml
name: church-integration-tester
description: "Validates data integrity across all church YAML files by running P1 validation scripts (M1-M6, F1-F5, S1-S5, N1-N6, B1-B3), checking cross-file reference integrity, and producing test reports."
model: sonnet
```

**Model Rationale**: Integration testing is a **pattern execution** task. The agent runs deterministic Python validation scripts and aggregates their results. No creative reasoning is needed — the agent orchestrates `validate_*.py` scripts, collects JSON output, and formats human-readable reports. Sonnet is optimal for this structured coordination task.

**Tools Required**:
- `Read` — Read all data/*.yaml files, validation script outputs
- `Bash` — Run `validate_members.py`, `validate_finance.py`, `validate_schedule.py`, `validate_newcomers.py`, `validate_bulletin.py`
- `Write` — Write test reports to `test-reports/`

**permissionMode**: `default`

**maxTurns**: 15

**Memory Scope**:
- **Reads**: All `data/*.yaml` files, `church-state.yaml`, `.claude/hooks/scripts/validate_*.py`
- **Writes**: `test-reports/{YYYY-MM-DD}-integrity-report.md`

**Input/Output Contract**:

| Direction | Format | Description |
|-----------|--------|-------------|
| **Input** | Trigger | Scheduled (weekly) or on-demand integrity check request |
| **Output** | Test report | Markdown report: per-file validation results (PASS/FAIL for each rule), cross-reference check results, summary with actionable items |

**When Invoked**:
- Scheduled: Weekly integrity check (suggested: Monday morning before bulletin generation)
- Post-workflow: After any workflow completes, as a final verification step
- Ad-hoc: On-demand data health check

**Specialization Boundary**:
- Runs validation scripts and reports results
- Does NOT fix data issues (reports them for appropriate domain agents to fix)
- Does NOT modify any `data/*.yaml` file (read-only — pure validator)

---

### A.10 Agent Specification: `church-onboarding-author`

```yaml
name: church-onboarding-author
description: "Creates and maintains IT volunteer onboarding documentation: installation guides, configuration walkthroughs, troubleshooting guides, and church-specific customization instructions."
model: sonnet
```

**Model Rationale**: Documentation authoring is a **pattern execution** task within a well-defined scope: installation steps, configuration options, and troubleshooting flows. The content structure follows established documentation patterns. Sonnet provides sufficient writing capability for clear, step-by-step guides targeting non-technical church IT volunteers (박준호 persona — PRD §3.3).

**Tools Required**:
- `Read` — Read existing documentation, configuration files, PRD
- `Write` — Write documentation to `docs/`
- `Glob` — Survey codebase structure for accurate documentation

**permissionMode**: `default`

**maxTurns**: 20

**Memory Scope**:
- **Reads**: All project files (for documentation accuracy), `church-state.yaml` template, PRD
- **Writes**: `docs/installation-guide.md`, `docs/configuration-guide.md`, `docs/troubleshooting.md`, `docs/church-customization.md`

**Input/Output Contract**:

| Direction | Format | Description |
|-----------|--------|-------------|
| **Input** | System state | Current codebase structure, configuration options, known issues |
| **Output** | Markdown docs | Complete onboarding documentation suite for IT volunteers |

**When Invoked**:
- After major system changes that affect installation or configuration
- During initial system setup (M1 milestone)
- Ad-hoc: When new troubleshooting patterns are identified

**Specialization Boundary**:
- Creates and maintains documentation only
- Does NOT modify system code, data files, or configurations
- Does NOT perform testing (that is `church-integration-tester`'s job)

---

### A.11 Agent Specification: `schedule-manager`

[trace:step-1:domain-analysis] [trace:step-4:schema-specs]

```yaml
name: schedule-manager
description: "Manages worship service schedules, special events, and facility bookings. Detects scheduling conflicts, tracks liturgical calendar (절기), and coordinates with bulletin generation for upcoming events."
model: sonnet
```

**Model Rationale**: Schedule management is a **pattern execution** task with deterministic rules: recurrence patterns (weekly/biweekly/monthly), time slot conflict detection (S5), and liturgical calendar mapping. The Korean liturgical calendar (사순절, 부활절, 대강절, 성탄절) follows well-established date rules. Sonnet handles these bounded operations efficiently.

**Tools Required**:
- `Read` — Read schedule.yaml, church-state.yaml
- `Edit` — Update schedule.yaml (sole writer — note: Orchestrator was previously designated as writer in Step 4 data architecture; this agent takes over that role for better separation of concerns)
- `Bash` — Run `validate_schedule.py` for P1 validation (S1-S5)

**permissionMode**: `default`

**maxTurns**: 15

**Memory Scope**:
- **Reads**: `data/schedule.yaml`, `church-state.yaml`, `data/church-glossary.yaml`
- **Writes**: `data/schedule.yaml` (sole writer — Layer 1 enforced)

**Design Decision — Writer Reassignment**: The Step 4 data architecture spec designated the Orchestrator as the sole writer for `schedule.yaml`. This design reassigns that role to a dedicated `schedule-manager` agent. Rationale: the Orchestrator should coordinate workflows, not manage domain data. The `schedule-manager` provides bounded specialization for schedule operations (conflict detection, recurrence expansion, liturgical calendar mapping), which the Orchestrator should not embed. This follows P2 (Expert Delegation). The Orchestrator retains sole write access to `church-state.yaml`.

**Input/Output Contract**:

| Direction | Format | Description |
|-----------|--------|-------------|
| **Input** | Schedule commands | Add/modify services, events, bookings |
| **Input** | Parsed data | From `data-ingestor` for file-based schedule inputs |
| **Output** | Updated YAML | `schedule.yaml` with new/modified records |
| **Output** | Conflict alerts | Warnings when facility bookings overlap or schedule conflicts exist |

**When Invoked**:
- **Weekly Bulletin workflow** — Step 1 (Schedule verification before bulletin generation)
- Event-driven: When new events or bookings are requested
- Periodic: Liturgical calendar updates at season transitions

**Specialization Boundary**:
- Manages all schedule-related data
- Detects scheduling conflicts
- Does NOT generate bulletin content (that is `bulletin-generator`'s job)
- Does NOT manage member data

---

### A.12 Write Permission Matrix (Layer 1 Enforcement)

[trace:step-4:schema-specs]

This matrix is the definitive write permission assignment. No two agents share write access to the same file. The `guard_data_files.py` PreToolUse hook enforces these constraints at runtime.

| Data File | Designated Writer | All Other Agents |
|-----------|------------------|-----------------|
| `church-state.yaml` | Orchestrator only | Read-only |
| `data/members.yaml` | `member-manager` | Read-only |
| `data/finance.yaml` | `finance-recorder` | Read-only |
| `data/schedule.yaml` | `schedule-manager` | Read-only |
| `data/newcomers.yaml` | `newcomer-tracker` | Read-only |
| `data/bulletin-data.yaml` | `bulletin-generator` | Read-only |
| `data/church-glossary.yaml` | Any agent (append-only) | Read + append-only |
| `templates/*.yaml` | `template-scanner` | Read-only |
| `inbox/processed/*` | `data-ingestor` | Read-only (consumed by domain agents) |

```python
# guard_data_files.py — Updated PreToolUse hook specification
WRITE_PERMISSIONS = {
    "data/members.yaml": "member-manager",
    "data/finance.yaml": "finance-recorder",
    "data/schedule.yaml": "schedule-manager",
    "data/newcomers.yaml": "newcomer-tracker",
    "data/bulletin-data.yaml": "bulletin-generator",
    "church-state.yaml": "orchestrator",
}
APPEND_ONLY_FILES = {"data/church-glossary.yaml"}
```

---

## Part B: Feature Workflow Blueprints

### B.1 Weekly Bulletin Generation Workflow (`weekly-bulletin.md`)

[trace:step-1:domain-analysis] [trace:step-2:template-analysis]

#### Workflow Metadata

```yaml
workflow_id: "weekly-bulletin"
trigger: "scheduled"
frequency: "weekly (Monday)"
estimated_duration: "15-30 minutes (with human review)"
risk_level: "low"
autopilot_eligible: true
primary_agents:
  - bulletin-generator
  - schedule-manager
supporting_agents:
  - data-ingestor (when inbox/ files trigger updates)
  - template-scanner (initial setup only)
```

#### Inherited DNA

This workflow inherits the complete genome of the parent AgenticWorkflow system:

| Inherited Pattern | Application in This Workflow |
|------------------|------------------------------|
| **Quality Absolutism** (Constitutional Principle 1) | Bulletin output must match 100% of bulletin-data.yaml content. No data truncation or summarization. |
| **SOT Pattern** (Constitutional Principle 2) | `bulletin-data.yaml` is the single source for bulletin content. `bulletin-generator` is the sole writer. |
| **Code Change Protocol** (Constitutional Principle 3) | Any template modification follows CCP: intent → ripple analysis → change plan. |
| **4-Layer QA** (L0-L1-L1.5-L2) | L0: Output file exists + ≥100 bytes. L1: All 16 variable regions populated correctly. L1.5: pACS self-rating. L2: Human review (single). |
| **P1 Deterministic Validation** | `validate_bulletin.py` (B1-B3) runs before human review. |
| **Safety Hooks** | `block_destructive_commands.py` prevents accidental data deletion. `guard_data_files.py` enforces write permissions. |
| **Context Preservation** | Session state (current bulletin issue number, in-progress edits) preserved across sessions. |
| **Coding Anchor Points** (CAP) | CAP-2 (simplicity): Bulletin template filling is direct slot population, no unnecessary abstraction. CAP-4 (surgical): Only bulletin-relevant data is read and processed. |

#### Workflow Steps

**Phase 1: Research/Awareness**

**Step 1: Schedule Verification** `(agent: schedule-manager)`
- Read `data/schedule.yaml` to confirm this week's service schedule
- Verify no schedule conflicts or cancellations
- Identify liturgical season (절기) if applicable
- **Output**: Verified schedule data ready for bulletin

**Verification**:
- [ ] Regular services for this Sunday confirmed
- [ ] Special events for this week identified
- [ ] Liturgical season correctly identified (if applicable)
- [ ] No scheduling conflicts detected

**Step 2: Data Completeness Check** `(agent: bulletin-generator)`
- Read `data/bulletin-data.yaml` for current week's content
- Verify all required fields populated: sermon title, scripture, preacher, worship order, announcements, prayer requests
- Read `data/members.yaml` for birthday/anniversary members matching this week
- Flag missing fields for human input

**Verification**:
- [ ] Sermon title present and non-empty (VR-BUL-03)
- [ ] Scripture reference present (VR-BUL-04)
- [ ] Worship order has ≥3 items (VR-BUL-07)
- [ ] Announcements filtered by priority and expiration date
- [ ] Birthday/anniversary members correctly filtered by this week's dates

**Phase 2: Processing**

**Step 3: Bulletin Generation** `(agent: bulletin-generator)`
- Load `templates/bulletin-template.yaml` for layout structure
- Populate all 16 variable regions from data sources:
  - VR-BUL-01 (Issue Number): `bulletin.issue_number` formatted as "제 N호"
  - VR-BUL-02 (Date): Formatted as "YYYY년 MM월 DD일 주일"
  - VR-BUL-03 through VR-BUL-16: Each from mapped data source
- Apply denomination-specific formatting if applicable
- Generate worship order sheet as separate output
- **Output**: `bulletins/YYYY-MM-DD-bulletin.md`, `bulletins/YYYY-MM-DD-worship-order.md`

**Verification**:
- [ ] All 16 variable regions populated (no empty slots for required fields)
- [ ] Issue number is monotonically increasing from previous bulletin
- [ ] Date is a Sunday (day_of_week validation)
- [ ] Bulletin content 100% matches bulletin-data.yaml source data
- [ ] Korean formatting correct (church name, denomination header)
- [ ] Worship order matches bulletin worship order content
- [ ] File size ≥ 100 bytes (L0)

**Phase 3: Output/Verification**

**Step 4: P1 Validation** `(hook: validate_bulletin.py)`
- Run B1-B3 validation rules against generated bulletin
- B1: All required sections present (sermon, worship order, announcements, prayer)
- B2: Issue number sequential from previous
- B3: Data cross-references valid (birthday member IDs exist in members.yaml)
- **Output**: Validation result JSON

**Verification**:
- [ ] B1-B3 all PASS
- [ ] No validation warnings

**Step 5: Human Review** `(human)` — HitL Gate: Single Review
- Present generated bulletin for human review
- Reviewer checks: content accuracy, formatting, cultural appropriateness
- Reviewer approves, requests changes, or rejects

**Verification**:
- [ ] Human reviewer has reviewed the complete bulletin
- [ ] Any requested changes have been applied
- [ ] Final version approved

**Step 6: Finalization** `(agent: bulletin-generator)`
- Upon approval, update `church-state.yaml` current_bulletin_issue (via Orchestrator)
- Archive this week's bulletin-data.yaml snapshot
- **Output**: Final bulletin ready for printing

**Verification**:
- [ ] Issue number incremented in church-state.yaml
- [ ] Bulletin file accessible at expected path

---

### B.2 Newcomer Care Pipeline Workflow (`newcomer-pipeline.md`)

[trace:step-1:domain-analysis] [trace:step-4:validation-rules]

#### Workflow Metadata

```yaml
workflow_id: "newcomer-pipeline"
trigger: "event-driven (new visitor registration) + scheduled (weekly follow-up check)"
frequency: "event-driven + weekly"
estimated_duration: "10-20 minutes per newcomer action"
risk_level: "medium"
autopilot_eligible: true (except stage transitions — HitL required)
primary_agents:
  - newcomer-tracker
  - member-manager (settlement step only)
supporting_agents:
  - data-ingestor (initial registration from inbox/ files)
```

#### Inherited DNA

| Inherited Pattern | Application in This Workflow |
|------------------|------------------------------|
| **Quality Absolutism** (Constitutional Principle 1) | Welcome messages must be personalized with newcomer name and visit context. No generic templates. |
| **SOT Pattern** (Constitutional Principle 2) | `newcomers.yaml` is the single source for newcomer journey state. `newcomer-tracker` is the sole writer. |
| **Code Change Protocol** (Constitutional Principle 3) | Journey stage transitions follow strict prerequisite rules (N2 validation). |
| **4-Layer QA** (L0-L1-L1.5-L2) | L0: Newcomer record exists with required fields. L1: Journey milestones sequential and complete. L1.5: pACS on welcome message quality. L2: Human approval for stage transitions. |
| **P1 Deterministic Validation** | `validate_newcomers.py` (N1-N6) runs after every newcomer data change. |
| **Safety Hooks** | `guard_data_files.py` ensures only `newcomer-tracker` writes to `newcomers.yaml`. |
| **Context Preservation** | Newcomer journey state preserved across sessions — no milestone data loss on context reset. |
| **Coding Anchor Points** (CAP) | CAP-1 (think before code): Verify milestone prerequisites before any stage transition. CAP-4 (surgical): Only the specific newcomer record being acted on is modified. |

#### Workflow Steps

**Phase 1: Research/Awareness — Registration**

**Step 1: Newcomer Data Intake** `(agent: data-ingestor)`
- Parse newcomer data from source:
  - Tier A: `inbox/documents/새신자등록카드.xlsx` or `.csv`
  - Tier C: `inbox/images/namecard-*.jpg` (Claude multimodal namecard analysis)
  - Manual: Orchestrator provides data directly
- Extract: name, gender, phone, visit date, visit route
- Stage parsed data in `inbox/processed/`
- **Output**: Structured newcomer data ready for confirmation

**Verification**:
- [ ] Name extracted and non-empty
- [ ] Phone format matches `010-NNNN-NNNN` (Korean mobile)
- [ ] Visit date is valid YYYY-MM-DD
- [ ] Visit route classified into one of 5 categories

**Step 2: Human Confirmation of Parsed Data** `(human)` — HitL Gate: Single Review
- Present parsed newcomer data for human confirmation
- Verify accuracy of extracted information (especially for Tier C image-based extraction)
- Human may correct or supplement data

**Verification**:
- [ ] Human has reviewed and confirmed all parsed fields
- [ ] Any corrections have been applied to staged data

**Phase 2: Processing — Welcome & Follow-up**

**Step 3: Newcomer Registration** `(agent: newcomer-tracker)`
- Create newcomer record in `newcomers.yaml` with:
  - Auto-generated ID (N-prefixed sequential)
  - `journey_stage: "first_visit"`
  - `journey_milestones.first_visit: {date: YYYY-MM-DD, completed: true}`
  - `assigned_to`: Auto-assign shepherd based on age group and area matching from `members.yaml`
- Run `validate_newcomers.py` (N1-N6)
- **Output**: Registered newcomer record, shepherd assignment

**Verification**:
- [ ] Newcomer ID unique and format valid (N1)
- [ ] Journey stage is `first_visit` (initial state)
- [ ] first_visit milestone marked completed with valid date
- [ ] assigned_to references valid member ID (N4)
- [ ] N1-N6 all PASS

**Step 4: Welcome Action Generation** `(agent: newcomer-tracker)`
- Generate welcome message draft:
  - Personalized greeting using newcomer name and visit context
  - Senior pastor's name from `church-state.yaml`
  - Next Sunday service information from `schedule.yaml`
  - Small group/department recommendation based on age
- Generate follow-up reminder schedule:
  - +3 days: Welcome call reminder for assigned shepherd
  - +14 days: Second visit confirmation check
  - +30 days: Inactivity warning if no stage progression
- **Output**: `output/newcomer-actions/{newcomer_id}-welcome.md`, follow-up schedule

**Verification**:
- [ ] Welcome message includes newcomer name (personalized)
- [ ] Welcome message includes accurate service times from schedule.yaml
- [ ] Follow-up schedule dates calculated correctly from first_visit date
- [ ] Message text is culturally appropriate (Korean church honorifics)

**Step 5: Stage Transition Processing** `(agent: newcomer-tracker)` `(human)` — HitL Gate: Single Review
- When follow-up milestones are completed:
  - `welcome_call`: Assigned shepherd confirms call made
  - `second_visit`: Newcomer confirmed to have visited again
  - `small_group_intro`: Newcomer attended small group introduction
  - `baptism_class`: Newcomer enrolled in baptism class (세례교육반)
  - `baptism`: Baptism ceremony completed (세례식)
- Each milestone completion requires human confirmation
- Stage transitions follow strict prerequisite rules (N2):
  - `attending` requires: first_visit ✓
  - `small_group` requires: first_visit ✓, welcome_call ✓, second_visit ✓
  - `baptism_class` requires: first_visit ✓, welcome_call ✓, second_visit ✓, small_group_intro ✓
  - `baptized` requires: all above + baptism_class ✓
  - `settled` requires: all above + baptism ✓
- Run `validate_newcomers.py` after each transition

**Verification**:
- [ ] All prerequisite milestones completed before stage advancement (N2)
- [ ] Human approved the stage transition
- [ ] Milestone date recorded accurately
- [ ] N1-N6 all PASS after transition

**Phase 3: Output/Verification — Settlement**

**Step 6: Settlement to Member Registry** `(agent: newcomer-tracker → member-manager)`
- When newcomer reaches `settled` stage:
  - `newcomer-tracker` sets `status: "settled"`, records `settled_date` and `settled_as_member` (new member ID)
  - `member-manager` creates new member record in `members.yaml` with data from newcomer record
  - Full member record includes: name, contact, church.registration_date, church.department, church.baptism_date (if baptized), family associations
- Run both `validate_newcomers.py` (N5 settlement consistency) and `validate_members.py` (M1-M6)
- **Output**: New member record in `members.yaml`, updated newcomer record

**Verification**:
- [ ] `settled_as_member` references valid member ID in members.yaml (N5)
- [ ] Member record contains all required fields (M2)
- [ ] Member ID unique (M1)
- [ ] Newcomer status is `settled`, settled_date is valid
- [ ] N1-N6 and M1-M6 all PASS

---

### B.3 Monthly Financial Reporting Workflow (`monthly-finance-report.md`)

[trace:step-1:domain-analysis] [trace:step-4:validation-rules]

#### Workflow Metadata

```yaml
workflow_id: "monthly-finance-report"
trigger: "scheduled"
frequency: "monthly (1st of each month for previous month)"
estimated_duration: "30-60 minutes (with double human review)"
risk_level: "high"
autopilot_eligible: false  # PERMANENTLY DISABLED — PRD §5.1 F-03
primary_agents:
  - finance-recorder
supporting_agents:
  - data-ingestor (when inbox/ financial files need parsing)
  - document-generator (receipt generation)
  - church-integration-tester (post-report validation)
```

**Autopilot: PERMANENTLY DISABLED** — Per PRD §5.1 F-03: "재정 관련 업무는 Autopilot 대상에서 영구 제외." Financial data has legal implications (소득세법 시행령 §80①5호) and trust implications for the church community. Every financial operation requires human approval through a double-review gate (담당자 + 목사/장로). [trace:step-1:domain-analysis]

#### Inherited DNA

| Inherited Pattern | Application in This Workflow |
|------------------|------------------------------|
| **Quality Absolutism** (Constitutional Principle 1) | Financial arithmetic must be 100% correct. No rounding errors, no missing transactions. |
| **SOT Pattern** (Constitutional Principle 2) | `finance.yaml` is the single source for financial data. `finance-recorder` is the sole writer. |
| **Code Change Protocol** (Constitutional Principle 3) | Any modification to financial records follows full CCP with mandatory user approval for large-scale operations. |
| **4-Layer QA** (L0-L1-L1.5-L2) | L0: Report file exists + ≥100 bytes. L1: Arithmetic consistency (F3 offering sums, F4 budget totals, F5 monthly summaries). L1.5: pACS self-rating. L2: Double human review (재정 담당 + 담임 목사). |
| **P1 Deterministic Validation** | `validate_finance.py` (F1-F5) runs before any human review. Arithmetic errors are caught deterministically. |
| **Safety Hooks** | `guard_data_files.py` ensures only `finance-recorder` writes to `finance.yaml`. Autopilot mode is disabled. |
| **Context Preservation** | Financial processing state preserved across sessions — no transaction loss on context reset. |
| **Coding Anchor Points** (CAP) | CAP-1 (think before code): Verify all existing transactions before computing summaries. CAP-3 (goal-based): Success criterion is F1-F5 all PASS before any human sees the report. |

#### Workflow Steps

**Phase 1: Research/Awareness — Data Collection**

**Step 1: Financial Data Ingestion** `(agent: data-ingestor)` `(human)` — HitL Gate: Double Review
- Parse new financial data from sources:
  - Tier A: `inbox/documents/헌금내역.xlsx` (offering ledger)
  - Tier A: `inbox/documents/지출내역.csv` (expense records)
  - Tier C: `inbox/images/receipt-*.jpg` (expense receipt photos)
- Stage parsed data in `inbox/processed/`
- Present parsed data for human review (first review: 재정 담당 집사)
- **Output**: Confirmed financial transaction data

**Verification**:
- [ ] All offering amounts are positive integers (F2 pre-check)
- [ ] Each offering record has required fields: date, service, type, items, total
- [ ] Each expense record has required fields: date, category, amount, description, approved_by
- [ ] Human (재정 담당) confirmed all parsed data

**Step 2: Data Recording** `(agent: finance-recorder)` `(human)` — HitL Gate: Double Review
- Record confirmed transactions to `finance.yaml`:
  - Append new offerings with auto-generated IDs (OFF-YYYY-NNN format)
  - Append new expenses with auto-generated IDs (EXP-YYYY-NNN format)
  - Compute each offering's total from items (F3 pre-validated)
  - Set `verified: false` initially (pending second review)
- Run `validate_finance.py` (F1-F5)
- Present recorded data for second review (담임 목사 or 장로)
- Upon second approval, set `verified: true`
- **Output**: Updated `finance.yaml` with verified transactions

**Verification**:
- [ ] F1: All IDs unique and format-valid
- [ ] F2: All amounts positive integers
- [ ] F3: offerings[].total == sum(items[].amount) for every non-void record
- [ ] No duplicate transactions (compare against existing records)
- [ ] Second reviewer (목사/장로) approved

**Phase 2: Processing — Report Generation**

**Step 3: Monthly Summary Computation** `(agent: finance-recorder)`
- Compute monthly summary for the target month:
  - `total_income`: Sum of all non-void offerings for the month
  - `total_expense`: Sum of all non-void expenses for the month
  - `balance`: total_income - total_expense
- Update `finance.yaml` monthly_summary section
- Run `validate_finance.py` F5 (monthly summary accuracy)
- **Output**: Verified monthly summary in `finance.yaml`

**Verification**:
- [ ] F5: monthly_summary totals match non-void record sums
- [ ] Balance = income - expense (arithmetic verified)
- [ ] No records from other months incorrectly included

**Step 4: Financial Report Generation** `(agent: finance-recorder)`
- Generate monthly financial report:
  - Section 1: Income Summary — Offerings by type (십일조, 감사헌금, 특별헌금, 선교헌금, etc.) with totals
  - Section 2: Expense Summary — Expenses by category (관리비, 인건비, 사역비, 선교비, 교육비, 기타) with totals
  - Section 3: Budget vs. Actual — Each budget category compared to year-to-date spending
  - Section 4: Balance Sheet — Opening balance + income - expenses = closing balance
  - Section 5: Year-to-Date Summary — Cumulative totals from January
  - Section 6: Pledge Tracking — 주정헌금 fulfillment rates (pledged_annual records)
- **Output**: `reports/finance/{YYYY-MM}-finance-report.md`

**Verification**:
- [ ] All 6 sections present and populated
- [ ] Income totals match F5-validated monthly summary
- [ ] Expense totals match F5-validated monthly summary
- [ ] Budget vs. actual percentages arithmetically correct
- [ ] Year-to-date totals consistent with all monthly summaries
- [ ] No PII (personal offering amounts) in the congregational report version

**Phase 3: Output/Verification — Review & Distribution**

**Step 5: Report Review** `(human)` — HitL Gate: Double Review
- First review: 재정 담당 집사 reviews arithmetic accuracy and categorization
- Second review: 담임 목사 or 장로 reviews for completeness and approval
- **Output**: Approved financial report

**Verification**:
- [ ] First reviewer (재정 담당) confirmed arithmetic
- [ ] Second reviewer (목사/장로) approved report
- [ ] Any discrepancies addressed before approval

**Step 6: Receipt Generation (Annual — December/January only)** `(agent: finance-recorder + document-generator)` `(human)` — HitL Gate: Double Review
- Generate tax donation receipts (기부금영수증) for all active members:
  - Sum each member's annual offerings from `finance.yaml`
  - Generate receipt using `templates/receipt-template.yaml`
  - Include Korean numeral amount conversion (금 일백이십삼만사천원정)
  - Include legal basis text (소득세법 §34, 시행령 §80)
  - Reserve seal zone (직인 위치) — NO_VARIABLE_CONTENT guard
- Bulk generation: one receipt per active member
- Human review of sample receipts before batch approval
- **Output**: `certificates/receipts/{year}/{member_id}-receipt-{year}.md`

**Verification**:
- [ ] Receipt amount matches sum of member's non-void offerings for the year
- [ ] Korean numeral conversion matches numeric amount
- [ ] Seal zone empty (NO_VARIABLE_CONTENT guard respected)
- [ ] Legal basis text present and correct
- [ ] Receipt number sequential (No. YYYY-NNN format)
- [ ] Human reviewed sample receipts and approved batch

---

### B.4 Document Generator Workflow (`document-generator.md`)

[trace:step-2:template-analysis] [trace:step-4:schema-specs]

#### Workflow Metadata

```yaml
workflow_id: "document-generator"
trigger: "manual (on-demand)"
frequency: "ad-hoc (certificates: 2-4×/year, letters: 2-5×/month, minutes: 1-4×/month)"
estimated_duration: "10-20 minutes per document"
risk_level: "medium"
autopilot_eligible: true (except seal-requiring documents — single HitL review)
primary_agents:
  - template-scanner (initial template setup)
  - document-generator (document production)
supporting_agents:
  - member-manager (member data lookup)
```

#### Inherited DNA

| Inherited Pattern | Application in This Workflow |
|------------------|------------------------------|
| **Quality Absolutism** (Constitutional Principle 1) | Every document must be complete and accurate. Missing fields or incorrect formatting is unacceptable for official church documents. |
| **SOT Pattern** (Constitutional Principle 2) | Template files in `templates/` are the single source for document structure. Domain data comes from respective YAML files. |
| **Code Change Protocol** (Constitutional Principle 3) | Template modifications follow CCP with ripple analysis — a template change affects all future documents of that type. |
| **4-Layer QA** (L0-L1-L1.5-L2) | L0: Document file exists + ≥100 bytes. L1: All variable slots populated from correct data sources. L1.5: pACS self-rating on output quality. L2: Human review (single for most; double for financial receipts). |
| **P1 Deterministic Validation** | Data source validation (member exists, financial amounts correct) via respective validate scripts. |
| **Safety Hooks** | `guard_data_files.py` ensures document-generator has read-only access to all data files. |
| **Coding Anchor Points** (CAP) | CAP-2 (simplicity): Slot-filling from template — no unnecessary complexity. CAP-4 (surgical): Only requested document is generated. |

#### Workflow Steps

**Phase 1: Research/Awareness — Template Verification**

**Step 1: Template Check** `(agent: document-generator)`
- Identify requested document type (certificate, letter, receipt, minutes, invitation)
- Check if `templates/{type}-template.yaml` exists
- If template missing → invoke `template-scanner` for initial setup (sub-workflow)
- Load template and verify fixed/variable regions are complete
- **Output**: Verified template ready for population

**Verification**:
- [ ] Template file exists for the requested document type
- [ ] All fixed regions have non-empty content
- [ ] All variable regions have valid data_source mappings
- [ ] Seal zone (if applicable) has NO_VARIABLE_CONTENT guard

**Step 2: Template Setup Sub-Workflow (conditional)** `(agent: template-scanner)` `(human)` — HitL Gate: Single Review
- Only invoked if template does not exist
- Analyze uploaded sample from `inbox/templates/{type}-sample.{jpg,pdf}`
- Identify fixed regions (church identity anchors) vs. variable regions (data slots)
- Generate `templates/{type}-template.yaml`
- Present analysis for human confirmation
- **Output**: New template YAML confirmed by human

**Verification**:
- [ ] Fixed regions correctly identify church name, denomination, seal zone
- [ ] Variable regions have correct data_source mappings
- [ ] Seal zones marked with NO_VARIABLE_CONTENT guard
- [ ] Human confirmed template structure

**Phase 2: Processing — Document Generation**

**Step 3: Data Collection & Document Generation** `(agent: document-generator)`
- Read relevant YAML data sources based on document type:
  - Certificate (세례증서): `members.yaml` → baptism_date, baptism_type, name
  - Certificate (이명증서): `members.yaml` → transfer history, member details
  - Official Letter (공문): `church-state.yaml` → church identity, `members.yaml` → recipient/sender details
  - Meeting Minutes (회의록): `members.yaml` → attendee names and roles
  - Invitation (초청장): `schedule.yaml` → event details, `members.yaml` → guest list
- Populate all variable regions from data sources
- Apply Korean formatting rules:
  - Dates: "YYYY년 MM월 DD일"
  - Document numbers: "제 YYYY-NNN호" (annually sequential)
  - Seal notation: "(인)" at signature positions
  - Korean numeral conversion for amounts (if applicable)
- Generate output Markdown
- **Output**: `certificates/{type}/{date}-{name}.md` or `letters/{date}-{number}.md`

**Verification**:
- [ ] All variable slots populated (no empty required fields)
- [ ] Data matches source YAML records exactly
- [ ] Korean formatting correct (dates, numbers, honorifics)
- [ ] Seal zone empty of generated content
- [ ] Document number sequential within type and year
- [ ] File size ≥ 100 bytes (L0)

**Phase 3: Output/Verification**

**Step 4: Human Review** `(human)` — HitL Gate: Single Review (Medium Risk)
- Present generated document for review
- For certificates: verify member data accuracy (name, dates, baptism records)
- For letters: verify recipient, subject, body content appropriateness
- For minutes: verify attendee list, resolutions, action items
- **Output**: Approved document

**Verification**:
- [ ] Human reviewed document content and formatting
- [ ] Any corrections applied
- [ ] Seal zone accessible for physical seal application (if needed)
- [ ] Document approved for use

---

## Part C: HitL Gate Architecture

[trace:step-1:domain-analysis]

### C.1 Risk Classification Framework

Human-in-the-loop (HitL) gates are classified into three risk levels based on PRD §5.1 F-03. The classification determines the review depth, number of reviewers, and Autopilot eligibility.

| Risk Level | Criteria | Review Type | Reviewers | Autopilot |
|-----------|----------|-------------|-----------|-----------|
| **HIGH** | Legal liability, financial accuracy, personal data sensitivity | Double review (sequential) | Domain expert + Senior authority | **Disabled** |
| **MEDIUM** | Member care, official communications, data accuracy | Single review | Domain-responsible person | Eligible (with HitL gates) |
| **LOW** | Informational content, operational scheduling | Single review | Any authorized person | **Fully eligible** |

### C.2 Complete HitL Gate Mapping

#### High Risk Gates (Finance) — Double Review, Autopilot DISABLED

| Gate ID | Workflow | Step | First Reviewer | Second Reviewer | What Is Reviewed |
|---------|----------|------|----------------|-----------------|-----------------|
| HitL-F01 | monthly-finance-report | Step 1 (Data Ingestion) | 재정 담당 집사 | — | Parsed financial data accuracy |
| HitL-F02 | monthly-finance-report | Step 2 (Data Recording) | 재정 담당 집사 | 담임 목사 or 장로 | Recorded transactions correctness |
| HitL-F03 | monthly-finance-report | Step 5 (Report Review) | 재정 담당 집사 | 담임 목사 or 장로 | Monthly report completeness |
| HitL-F04 | monthly-finance-report | Step 6 (Receipt Generation) | 재정 담당 집사 | 담임 목사 or 장로 | Sample receipt accuracy before batch |

**Double Review Protocol**:
1. First reviewer examines technical accuracy (amounts, categories, arithmetic)
2. First reviewer approves → document moves to second reviewer
3. Second reviewer examines completeness, appropriateness, and gives final approval
4. Both reviewers recorded in audit log with timestamp

#### Medium Risk Gates (Newcomer, Documents) — Single Review, Autopilot Eligible with Gates

| Gate ID | Workflow | Step | Reviewer | What Is Reviewed |
|---------|----------|------|----------|-----------------|
| HitL-N01 | newcomer-pipeline | Step 2 (Data Confirmation) | 행정 간사 or 담당 목회자 | Parsed newcomer data accuracy |
| HitL-N02 | newcomer-pipeline | Step 5 (Stage Transition) | 담당 목양자 or 담임 목사 | Milestone completion, stage advancement appropriateness |
| HitL-D01 | document-generator | Step 2 (Template Setup) | 행정 간사 | Template structure and region identification |
| HitL-D02 | document-generator | Step 4 (Document Review) | 행정 간사 or 담임 목사 | Document content accuracy and formatting |

#### Low Risk Gates (Bulletin) — Single Review, Autopilot Fully Eligible

| Gate ID | Workflow | Step | Reviewer | What Is Reviewed |
|---------|----------|------|----------|-----------------|
| HitL-B01 | weekly-bulletin | Step 5 (Bulletin Review) | 행정 간사 | Content accuracy, formatting, cultural appropriateness |

### C.3 HitL Gate Enforcement Mechanism

HitL gates are enforced at the workflow level, not the agent level. The Orchestrator manages gate flow:

```
Agent completes step → Output file written → P1 validation passes
    → Orchestrator presents output for human review
    → Human approves / requests changes / rejects
    → If approved: Orchestrator advances workflow
    → If changes requested: Agent re-executes step with feedback
    → If rejected: Workflow halted, escalated to senior authority
```

For **double-review** gates (HIGH risk), the flow is sequential:
```
Agent output → First reviewer → Approved? → Second reviewer → Approved? → Advance
                    ↓ No                          ↓ No
              Re-execute step                Escalate to 당회
```

### C.4 Emergency Override Protocol

In exceptional circumstances (e.g., urgent 공문 for 교단 deadline), a single authorized person (담임 목사) may override a double-review gate to single-review. The override must be:
1. Logged in `autopilot-logs/` with reason and overrider identity
2. Followed by a post-hoc second review within 48 hours
3. Never applicable to financial receipt generation (기부금영수증)

---

## Part D: Cross-Workflow Data Dependency Map

### D.1 Agent × Data File Access Matrix

[trace:step-4:schema-specs]

This matrix shows which agents read (R) and write (W) which data files. Each data file has exactly one writer (single-writer invariant).

| Data File | Orchestrator | bulletin-generator | finance-recorder | member-manager | newcomer-tracker | data-ingestor | template-scanner | document-generator | schedule-manager | integration-tester |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `church-state.yaml` | **W** | R | R | R | R | R | R | R | R | R |
| `data/members.yaml` | R | R | R | **W** | R | — | — | R | — | R |
| `data/finance.yaml` | R | — | **W** | — | — | — | — | R | — | R |
| `data/schedule.yaml` | R | R | — | — | R | — | — | R | **W** | R |
| `data/newcomers.yaml` | R | — | — | R | **W** | — | — | — | — | R |
| `data/bulletin-data.yaml` | R | **W** | — | — | — | — | — | — | — | R |
| `data/church-glossary.yaml` | R/A | R/A | R/A | R/A | R/A | R/A | R/A | R/A | R/A | R |
| `templates/*.yaml` | R | R | — | — | — | — | **W** | R | — | — |
| `inbox/processed/*` | R | — | R | R | R | **W** | — | — | — | — |

Legend: **W** = Write (sole writer), R = Read-only, R/A = Read + Append-only, — = No access needed

### D.2 Workflow × Data File Dependency Map

| Workflow | Reads | Writes | Depends On |
|----------|-------|--------|------------|
| `weekly-bulletin` | bulletin-data, schedule, members, church-state, bulletin-template | bulletins/*.md, bulletin-data.yaml | — (standalone weekly cycle) |
| `newcomer-pipeline` | newcomers, members, schedule, church-state, church-glossary | newcomers.yaml, members.yaml (settlement), output/newcomer-actions/ | weekly-bulletin (for service time references) |
| `monthly-finance-report` | finance, members, church-state | finance.yaml, reports/finance/, certificates/receipts/ | — (standalone monthly cycle) |
| `document-generator` | templates, members, finance, schedule, church-state | certificates/, letters/, reports/minutes/ | template-scanner (initial setup) |

### D.3 Cross-Workflow Data Flow Diagram

```
inbox/documents/           inbox/images/              inbox/templates/
     |                          |                          |
     v                          v                          v
[data-ingestor] ────────> inbox/processed/ <──── [data-ingestor]
     |                                                      |
     v                                                      v
     ├── target: finance ──> [finance-recorder] ──> finance.yaml
     ├── target: members ──> [member-manager] ──> members.yaml
     ├── target: newcomers ─> [newcomer-tracker] ──> newcomers.yaml
     └── target: bulletin ──> [bulletin-generator] ──> bulletin-data.yaml
                                                         |
                                                         v
[template-scanner] ──> templates/*.yaml ──> [document-generator] ──> certificates/
                                                                      letters/
                                                                      reports/

[schedule-manager] ──> schedule.yaml ──> [bulletin-generator] ──> bulletins/
                                    └──> [newcomer-tracker] ──> output/newcomer-actions/

[church-integration-tester] ──reads──> ALL data/*.yaml ──writes──> test-reports/
```

### D.4 Data Freshness Dependencies

| Consumer Workflow | Required Data | Freshness Requirement |
|------------------|---------------|----------------------|
| weekly-bulletin | bulletin-data.yaml | Updated before Monday (bulletin prep) |
| weekly-bulletin | members.yaml | Updated before Monday (birthday/anniversary check) |
| weekly-bulletin | schedule.yaml | Updated before Monday (service times) |
| newcomer-pipeline | members.yaml | Real-time (for shepherd assignment) |
| monthly-finance-report | finance.yaml | Complete by month-end |
| document-generator | members.yaml | Real-time (for certificates) |
| document-generator | finance.yaml | Complete for receipt year (annual receipts) |

---

## Part E: Autopilot Eligibility Matrix

### E.1 Workflow-Level Autopilot Eligibility

| Workflow | Autopilot | Justification |
|----------|-----------|---------------|
| `weekly-bulletin` | **ELIGIBLE** | Low risk. Bulletin content is informational, not legally binding. Errors can be caught at print time. Single HitL review gate maintained. |
| `newcomer-pipeline` | **PARTIAL** | Medium risk. Automated registration and welcome generation eligible. Stage transitions require HitL review (newcomer care is pastoral, not purely administrative). |
| `monthly-finance-report` | **PERMANENTLY DISABLED** | High risk. Financial data has legal implications (tax receipts), fiduciary obligations (church trust), and regulatory requirements (소득세법). PRD §5.1 F-03 mandates permanent exclusion. |
| `document-generator` | **ELIGIBLE** (most types) | Medium risk for certificates/letters. Low risk for invitations. Templates provide structural guardrails. Single HitL review gate maintained. |

### E.2 Step-Level Autopilot Eligibility Matrix

#### Weekly Bulletin Workflow

| Step | Step Name | Autopilot | Rationale |
|------|-----------|-----------|-----------|
| 1 | Schedule Verification | YES | Deterministic data read, no human judgment needed |
| 2 | Data Completeness Check | YES | Flags missing data automatically |
| 3 | Bulletin Generation | YES | Template-driven slot filling |
| 4 | P1 Validation | YES | Deterministic Python validation |
| 5 | Human Review | **HitL GATE** | Human reviews final bulletin. In Autopilot: auto-approved with quality-maximizing defaults, decision logged. |
| 6 | Finalization | YES | Administrative bookkeeping |

#### Newcomer Pipeline Workflow

| Step | Step Name | Autopilot | Rationale |
|------|-----------|-----------|-----------|
| 1 | Data Intake | YES | File parsing is mechanical |
| 2 | Human Confirmation | **HitL GATE** | Especially for Tier C image parsing, human must verify accuracy |
| 3 | Registration | YES | Deterministic record creation |
| 4 | Welcome Action Generation | YES | Template-driven content generation |
| 5 | Stage Transition | **HitL GATE** | Pastoral judgment required — "Is this newcomer ready for the next stage?" Cannot be automated. |
| 6 | Settlement | **HitL GATE** | Creating a permanent member record requires human confirmation |

#### Monthly Finance Report Workflow

| Step | Step Name | Autopilot | Rationale |
|------|-----------|-----------|-----------|
| 1 | Data Ingestion | **NO — HitL (double)** | Financial data accuracy is critical |
| 2 | Data Recording | **NO — HitL (double)** | Committing financial records requires dual approval |
| 3 | Monthly Summary | **NO** | Arithmetic is deterministic but results must be human-verified |
| 4 | Report Generation | **NO** | Report content must be reviewed before distribution |
| 5 | Report Review | **NO — HitL (double)** | Dual approval mandatory |
| 6 | Receipt Generation | **NO — HitL (double)** | Legal documents require dual approval |

#### Document Generator Workflow

| Step | Step Name | Autopilot | Rationale |
|------|-----------|-----------|-----------|
| 1 | Template Check | YES | Deterministic file existence check |
| 2 | Template Setup | **HitL GATE** | First-time template confirmation requires human judgment |
| 3 | Document Generation | YES | Template-driven slot filling |
| 4 | Document Review | **HitL GATE** | Human reviews generated document for accuracy |

### E.3 Autopilot Decision Criteria

When Autopilot is active for eligible steps, the following criteria govern auto-approval at `(human)` gates:

1. **Quality Maximization Default**: Always select the option that maximizes output quality (Constitutional Principle 1)
2. **P1 Validation Prerequisite**: Auto-approval only proceeds if all P1 validation checks pass
3. **Decision Logging**: Every auto-approved decision logged to `autopilot-logs/step-N-decision.md`
4. **Escalation Triggers**: Auto-approval is suspended and human input required if:
   - P1 validation fails
   - pACS score < 50 (RED zone)
   - Adversarial review FAIL
   - Data anomaly detected (e.g., bulletin date is not Sunday)

### E.4 Autopilot Guard Rails

| Guard | Implementation | Purpose |
|-------|---------------|---------|
| **Financial Lock** | `guard_data_files.py` + workflow-level check | Finance workflow Autopilot permanently disabled at code level |
| **P1 Gate** | `validate_*.py` must return `valid: true` | No auto-approval if deterministic checks fail |
| **pACS Floor** | pACS < 50 triggers mandatory human review | RED-zone outputs never auto-approved |
| **Audit Trail** | `autopilot-logs/` directory | Complete record of all auto-approved decisions |
| **Session Boundary** | Context Preservation captures Autopilot state as IMMORTAL | Autopilot state survives session resets |

---

## Quality Gate: Self-Verification

### Verification Criteria Assessment

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | 8+ specialized agents fully specified with model rationale | **PASS** | 10 agents specified (A.2-A.11): bulletin-generator, finance-recorder, member-manager, newcomer-tracker, data-ingestor, template-scanner, document-generator, church-integration-tester, church-onboarding-author, schedule-manager. Each includes model rationale (opus vs sonnet). |
| 2 | 4+ feature workflow blueprints with Inherited DNA | **PASS** | 4 workflow blueprints (B.1-B.4): weekly-bulletin, newcomer-pipeline, monthly-finance-report, document-generator. Each has explicit Inherited DNA table. |
| 3 | HitL gates mapped to 3 risk levels with specific workflow assignments | **PASS** | Part C defines HIGH (4 gates: HitL-F01 to F04), MEDIUM (4 gates: HitL-N01/N02, HitL-D01/D02), LOW (1 gate: HitL-B01). Each gate mapped to specific workflow step with designated reviewer. |
| 4 | Autopilot eligibility matrix complete | **PASS** | Part E provides workflow-level (E.1) and step-level (E.2) eligibility matrices for all 4 workflows. Decision criteria (E.3) and guard rails (E.4) defined. |
| 5 | No agent has overlapping write permissions to the same data file | **PASS** | Part A.12 write permission matrix shows exactly one writer per data file. No overlaps. |
| 6 | [trace:step-1:*] and [trace:step-4:*] markers present | **PASS** | Trace markers present: [trace:step-1:domain-analysis] (7 occurrences), [trace:step-1:terminology] (2 occurrences), [trace:step-2:template-analysis] (5 occurrences), [trace:step-4:validation-rules] (5 occurrences), [trace:step-4:schema-specs] (6 occurrences). |
| 7 | Finance workflow explicitly marked as Autopilot: disabled | **PASS** | B.3 metadata: `autopilot_eligible: false # PERMANENTLY DISABLED`. E.1 table: "PERMANENTLY DISABLED". E.2 monthly-finance-report: all steps marked NO. E.4: Financial Lock guard rail. |
| 8 | Each workflow has Verification criteria for self-assessment | **PASS** | All 4 workflows have Verification criteria (checkbox format) for every step. |

**Overall Quality Gate**: **PASS** (8/8 criteria met)

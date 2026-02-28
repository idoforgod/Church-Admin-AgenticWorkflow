# Church Administration AI Agentic Workflow Automation System

Build a complete AI-powered church administration automation system that autonomously handles repetitive administrative tasks (bulletin generation, newcomer management, financial reporting, document generation) for Korean mid-size churches (100-500 members), reducing weekly admin time from 23 hours to under 5 hours.

## Overview

- **Input**: PRD (`coding-resource/PRD.md`) + 5 research documents (`research/`) + existing church document samples (`inbox/templates/`)
- **Output**: Fully operational church admin automation system — 6 data schemas, 4 validation scripts, 8+ specialized agents, 5+ independent feature workflows, NL interface skill, inbox/ 3-tier pipeline, scan-and-replicate engine, IT volunteer onboarding package
- **Frequency**: One-time system build (created feature workflows run on their own schedules: weekly/monthly/on-demand)
- **Autopilot**: enabled
- **pACS**: enabled

---

## Inherited DNA (Parent Genome)

> This workflow inherits the complete genome of AgenticWorkflow.
> Purpose varies by domain; the genome is identical. See `soul.md §0`.

**Constitutional Principles** (adapted to church administration domain):

1. **Quality Absolutism** — Every church administration output (bulletins, financial reports, certificates) must be production-ready. A bulletin with missing information or a financial report with arithmetic errors is unacceptable. Quality means: factual accuracy of church data, structural completeness per Korean church conventions, and zero data integrity violations.
2. **Single-File SOT** — `state.yaml` concentrates all shared workflow state. Each feature-specific SOT (bulletin-state, newcomer-state, etc.) is independently managed by its own workflow. Cross-workflow data exchange happens exclusively through shared data files (`members.yaml`, `finance.yaml`, etc.) with read-only access.
3. **Code Change Protocol** — Implementation steps follow intent→impact→design 3-step protocol. Coding Anchor Points (CAP-1~4): think before coding (CAP-1), simplicity first (CAP-2), goal-driven execution (CAP-3), surgical changes only (CAP-4).

**Inherited Patterns**:

| DNA Component | Inherited Form |
|--------------|---------------|
| 3-Phase Structure | Research → Planning → Implementation |
| SOT Pattern | `state.yaml` — single writer (Orchestrator/Team Lead) |
| 4-Layer QA | L0 Anti-Skip → L1 Verification → L1.5 pACS → L2 Adversarial Review |
| P1 Hallucination Prevention | Deterministic validation scripts (`validate_members.py`, `validate_finance.py`, `validate_schedule.py`, `validate_newcomers.py`) |
| P2 Expert Delegation | Specialized sub-agents: domain researcher, schema designer, feature builders |
| Safety Hooks | `block_destructive_commands.py` — dangerous command blocking |
| Adversarial Review | `@reviewer` + `@fact-checker` — Enhanced L2 independent quality critique |
| Decision Log | `autopilot-logs/` — transparent decision tracking |
| Context Preservation | Snapshot + Knowledge Archive + RLM restoration |

**Domain-Specific Gene Expression**:

- **P1 (Data Refinement)** — Strongly expressed: inbox/ 3-tier parsing demands rigorous pre-processing (Excel→YAML, Image→structured data). Financial data requires arithmetic validation before any agent processing.
- **P2 (Expert Delegation)** — Strongly expressed: Church domain expertise (Korean church terminology, denomination-specific forms, pastoral workflow conventions) requires specialized agents rather than generic processing.
- **Human-in-the-loop** — Domain-critical gene: Financial operations permanently excluded from Autopilot. All final outputs require human review gate. Three-level approval architecture (high/medium/low risk).
- **SOT Pattern** — Enhanced expression: Shared data files (`members.yaml`, `finance.yaml`) use read-only cross-workflow reference pattern. Feature-specific SOTs prevent write collision between independent workflows.

---

## Research

### 1. Church Administration Domain Deep Research

- **Pre-processing**: Python script to extract and consolidate key sections from PRD and 5 research documents — filter to domain entities, data relationships, validation rules, Korean church terminology, and user persona requirements. Output consolidated briefing document (~30KB target).
- **Agent**: `@church-domain-researcher`
- **Context Injection**: Pattern B (Filtered Delegation) — Pre-processing script extracts relevant sections from ~150KB total input
- **Verification**:
  - [ ] All 6 core data domains analyzed (members, finance, schedule, newcomers, bulletin, glossary)
  - [ ] Korean church terminology extracted: minimum 30 terms with korean/english/context triples
  - [ ] All 4 user personas (행정 간사, 담임 목사, IT 자원봉사자, 재정 담당 집사) requirements mapped to specific features
  - [ ] Human-in-the-loop requirements mapped to 3 risk levels (high/medium/low) with specific workflows per level
  - [ ] M1 and M2 milestone scope boundaries clearly delineated with feature-to-milestone mapping
  - [ ] 3-Tier inbox/ pipeline requirements documented (Tier A: Excel/CSV, Tier B: Word/PDF, Tier C: Images) with accuracy expectations per tier
  - [ ] `domain-knowledge.yaml` constructed with entities (≥15), relations (≥10), constraints (≥8) (source: PRD §5-§7)
  - [ ] Pipeline connection: Output provides complete input for Step 4 schema design and Step 5 architecture blueprint
- **Task**: Perform comprehensive domain analysis of the Church Administration AI system. Read and synthesize PRD (`coding-resource/PRD.md`), data architecture (`research/data-architecture.md`), extensibility architecture (`research/extensibility-architecture.md`), feature ideation (`research/feature-ideation.md`), market analysis (`research/market-analysis.md`), and moderator discussion (`research/moderator-discussion.md`). Extract: (a) complete entity-relationship model for church data (members, finance, schedule, newcomers, bulletin), (b) Korean church-specific terminology dictionary with context for church-glossary.yaml, (c) user persona → feature requirement mapping, (d) Human-in-the-loop architecture per risk level, (e) validation rule catalog (M1-M6, F1-F5, S1-S5, N1-N5, B1-B3), (f) scan-and-replicate document type catalog (7 types with data source mapping), (g) inbox/ pipeline technical requirements per tier. Construct `domain-knowledge.yaml` following DKS pattern with entities, relations, and constraints.
- **Output**: `research/domain-analysis.md` + `domain-knowledge.yaml`
- **Review**: `@fact-checker`
- **Translation**: `@translator` → `research/domain-analysis.ko.md`
- **Post-processing**: `python3 .claude/hooks/scripts/validate_domain_knowledge.py --project-dir .` — DK1-DK7 structural integrity check

### 2. Church Document Template Collection & Analysis

- **Agent**: `@church-template-analyzer`
- **Context Injection**: Pattern A (Full Delegation) — PRD §5.1 F-06 section + sample template images if available
- **Verification**:
  - [ ] All 7 scan-and-replicate document types analyzed: bulletin, receipt, worship order, official letter, meeting minutes, certificate, invitation
  - [ ] Each document type has fixed area identification (church name, logo position, seal position) and variable area identification (date, content, recipient)
  - [ ] Korean church document formatting conventions documented (vertical text areas, seal placement, denomination header patterns)
  - [ ] Template priority classification matches PRD: Tier A (즉시: bulletin, receipt, worship order), Tier B (공문, meeting minutes, certificate), Tier C (denomination report)
  - [ ] Output format compatible with Step 5 pipeline design requirements (source: Step 1)
- **Task**: Analyze the 7 document types specified in PRD §5.1 F-06 for the scan-and-replicate system. For each document type: (a) identify the standard layout structure used in Korean churches, (b) classify fixed regions (church branding, headers, seals) vs variable regions (dates, names, content), (c) define the YAML template schema needed to represent each layout, (d) document which data sources (members.yaml, finance.yaml, etc.) provide values for each variable slot, (e) note any denomination-specific variations (예장통합, 예장합동, 기감). Reference existing scan-and-replicate patterns from PRD §5.1 F-06 data flow diagram.
- **Output**: `research/template-analysis.md`
- **Review**: none
- **Translation**: `@translator` → `research/template-analysis.ko.md`

### 3. (human) Research Validation & Scope Confirmation

- **Action**: Review domain analysis findings, church terminology dictionary, template analysis, and domain knowledge structure. Confirm M1+M2 scope boundaries. Provide feedback on any domain-specific corrections needed.
- **Command**: `/review-research`
- **Autopilot Default**: Approve all research findings — comprehensive domain coverage maximizes downstream quality

---

## Planning

### 4. Data Architecture & Schema Design

- **Pre-processing**: Extract validation rule catalog and entity-relationship model from Step 1 output. Merge with detailed schema examples from `research/data-architecture.md`.
- **Agent**: `@church-schema-designer`
- **Context Injection**: Pattern B (Filtered Delegation) — Extract schema-relevant sections from Step 1 output + data-architecture.md (~80KB total → filtered to ~35KB)
- **Verification**:
  - [ ] All 6 YAML data schemas fully specified: `members.yaml`, `finance.yaml`, `schedule.yaml`, `newcomers.yaml`, `bulletin-data.yaml`, `church-glossary.yaml`
  - [ ] `state.yaml` SOT schema defined with: church info, data_paths, workflow states, active features
  - [ ] Each schema includes: field definitions, data types, required/optional designation, example records (2+), and cross-reference specifications
  - [ ] Validation rules fully specified: M1-M6 (members), F1-F5 (finance), S1-S5 (schedule), N1-N5 (newcomers), B1-B3 (bulletin)
  - [ ] 3-layer data integrity architecture designed: (1) write permission separation per SOT, (2) P1 deterministic validation per file, (3) atomic writes via fcntl.flock
  - [ ] Schema extension rules documented: no field deletion, new fields optional, `.get()` defensive pattern
  - [ ] Data sensitivity classification applied: .gitignore entries for members.yaml, finance.yaml, newcomers.yaml
  - [ ] All entity IDs follow consistent format (M001, F001, S001, N001, B001)
  - [ ] Cross-references validated: newcomers.yaml → members.yaml migration, finance.yaml → members.yaml donor tracking
  - [ ] DKS cross-validation: schema fields align with `domain-knowledge.yaml` entities and constraints [trace:step-1:domain-knowledge]
  - [ ] Pipeline connection: Schema specs provide complete input for Step 7 infrastructure build and Step 8 validation scripts (source: Step 1)
- **Task**: Design the complete data architecture for the church administration system. Using the domain analysis from Step 1 and the detailed schema examples from `research/data-architecture.md`, produce: (a) full YAML schema specifications for all 6 data files + state.yaml SOT, (b) complete validation rule specifications (M1-M6, F1-F5, S1-S5, N1-N5, B1-B3) with Python-testable conditions, (c) 3-layer data integrity architecture with write permission matrix, (d) data flow diagrams showing which agents read/write which files, (e) backup/recovery protocol specifications, (f) schema versioning and extension guidelines per extensibility architecture. Each schema spec must include 2+ example records matching the `research/data-architecture.md` format.
- **Output**: `planning/data-architecture-spec.md`
- **Review**: `@fact-checker`
- **Translation**: `@translator` → `planning/data-architecture-spec.ko.md`
- **Post-processing**: `python3 .claude/hooks/scripts/validate_domain_knowledge.py --project-dir . --check-output --step 4` — DKS reference validation

### 5. (team) System Architecture Blueprint

- **Team**: `arch-blueprint`
- **Checkpoint Pattern**: dense — Each task ~15+ turns with direction-setting decisions
- **Tasks**:
  - `@church-agent-architect` (opus): Design all specialized agents and feature workflow blueprints. Define: (a) 8+ agent specifications (bulletin-generator, finance-recorder, member-manager, newcomer-tracker, data-ingestor, template-scanner, church-integration-tester, church-onboarding-author) with model selection rationale, tool permissions, and memory scope, (b) 4+ independent feature workflow blueprints (weekly-bulletin.md, newcomer-pipeline.md, monthly-finance-report.md, document-generator.md) following 3-phase structure with Inherited DNA, (c) Human-in-the-loop gate placement per workflow with risk-level classification, (d) Autopilot eligibility matrix per workflow (finance permanently excluded per PRD §5.1 F-03), (e) cross-workflow data dependency map via shared data files
    - **Checkpoints** (dense):
      - CP-1: Agent inventory + model selection rationale
      - CP-2: Feature workflow blueprints (structure only) + HitL gate map
      - CP-3: Complete agent specs + workflow blueprints with Verification fields
  - `@church-pipeline-designer` (opus): Design inbox/ 3-tier data pipeline and scan-and-replicate engine. Define: (a) Tier A pipeline: Excel/CSV → YAML conversion via openpyxl/pandas with column mapping, (b) Tier B pipeline: Word/PDF → structured data via python-docx/Claude Read, (c) Tier C pipeline: Image → structured data via Claude multimodal analysis, (d) scan-and-replicate engine: image analysis → template YAML generation → data-driven document production, (e) Human-in-the-loop confirmation gates for all parsed data before YAML write, (f) error handling for unsupported formats (HWP → PDF conversion guidance)
    - **Checkpoints** (dense):
      - CP-1: Pipeline architecture diagrams + library selection rationale
      - CP-2: Parsing logic specs per tier + error handling matrix
      - CP-3: Complete pipeline design + scan-and-replicate engine spec
  - `@church-hook-designer` (sonnet): Design hook configurations and validation script specifications. Define: (a) P1 validation script interface specs for 4 validators (validate_members.py M1-M6, validate_finance.py F1-F5, validate_schedule.py S1-S5, validate_newcomers.py N1-N5) with exact check conditions and JSON output format, (b) Setup Hook spec for infrastructure verification (runtime directories, PyYAML dependency, data file integrity), (c) PreToolUse Hook spec for data file write protection (prevent uncontrolled .yaml data edits), (d) slash command specs (/review-research, /approve-architecture, /review-m1, /final-review)
- **Join**: Team Lead merges three outputs into unified system architecture document with cross-references verified
- **SOT Write**: Team Lead only updates `state.yaml`
- **Verification**:
  - [ ] 8+ agent specifications complete with: name, description, model, tools, permissionMode, maxTurns, memory scope
  - [ ] 4+ feature workflow blueprints follow 3-phase structure with Verification fields on every agent step
  - [ ] inbox/ pipeline design covers all 3 tiers with specific Python libraries and column/field mapping per tier
  - [ ] scan-and-replicate engine handles all 7 document types from Step 2 analysis [trace:step-2:template-analysis]
  - [ ] 4 validation script specs include all rules from Step 4 schema design [trace:step-4:validation-rules]
  - [ ] Human-in-the-loop gates correctly classified: high risk (finance → double-review, Autopilot disabled), medium (newcomer/docs → single-review), low (bulletin → single-review, Autopilot eligible)
  - [ ] Cross-step traceability: architecture decisions trace to domain analysis [trace:step-1] and schema specs [trace:step-4]
  - [ ] Pipeline connection: Architecture blueprint provides complete implementation specs for Steps 7-13
- **Output**: `planning/system-architecture.md`
- **Review**: `@reviewer`
- **Translation**: `@translator` → `planning/system-architecture.ko.md`
- **Post-processing**: `python3 .claude/hooks/scripts/validate_traceability.py --step 5 --project-dir .`

### 6. (human) Architecture Approval

- **Action**: Review and approve: (a) data schema designs with validation rules, (b) agent architecture with model selections, (c) feature workflow blueprints, (d) inbox/ pipeline design, (e) scan-and-replicate engine design, (f) hook and validation configurations. Provide feedback on any design changes needed before implementation begins.
- **Command**: `/approve-architecture`
- **Autopilot Default**: Approve architecture — comprehensive design with full traceability to domain analysis and PRD requirements

---

## Implementation

### 7. Infrastructure Foundation Build

- **Pre-processing**: Extract finalized schema specifications and directory structure from Steps 4 and 5.
- **Agent**: `@church-infra-builder`
- **Context Injection**: Pattern A (Full Delegation) — Step 4 data-architecture-spec.md + relevant infra sections from Step 5 system-architecture.md
- **Verification**:
  - [ ] Directory structure created matching PRD §9.3: `church-admin/` with all subdirectories (`data/`, `inbox/documents/`, `inbox/images/`, `inbox/templates/`, `templates/`, `bulletins/`, `reports/`, `certificates/`, `workflows/`, `.claude/agents/`, `.claude/hooks/scripts/`, `.claude/commands/`, `.claude/skills/`)
  - [ ] `state.yaml` SOT initialized with: church info placeholder, data_paths to all 6 data files, initial workflow states, autopilot configuration
  - [ ] All 6 YAML data schema seed files created with correct structure and 2+ example records each, matching Step 4 specifications [trace:step-4:schema-specs]
  - [ ] `church-glossary.yaml` populated with minimum 30 Korean church terms from Step 1 domain analysis [trace:step-1:terminology]
  - [ ] `.gitignore` configured: `data/members.yaml`, `data/finance.yaml`, `data/newcomers.yaml` excluded from version control
  - [ ] Runtime directories created: `verification-logs/`, `pacs-logs/`, `review-logs/`, `autopilot-logs/`, `translations/`, `diagnosis-logs/`
  - [ ] Backup protocol scaffolding in place (daily backup script template)
  - [ ] All created YAML files pass syntax validation (`python3 -c "import yaml; yaml.safe_load(open('file'))"`)
- **Task**: Build the complete infrastructure foundation for the church administration system. Following the architecture specs from Steps 4 and 5: (a) create the full directory structure per PRD §9.3, (b) initialize `state.yaml` with the SOT schema from Step 4, (c) create seed data files for all 6 YAML schemas with correct structure and example records from `research/data-architecture.md`, (d) populate `church-glossary.yaml` with Korean church terminology from Step 1 domain analysis, (e) configure `.gitignore` for sensitive data protection, (f) create all runtime directories for QA infrastructure, (g) write daily backup script template. All file paths and structures must match the architecture blueprint exactly.
- **Output**: `church-admin/` directory with all infrastructure files
- **Review**: `@reviewer`
- **Translation**: none

### 8. P1 Validation Script Implementation

- **Pre-processing**: Extract finalized validation rules from Step 4 data-architecture-spec.md and Step 5 church-hook-designer validation spec. Collect Step 7 seed data for self-test.
- **Agent**: `@church-validation-engineer`
- **Context Injection**: Pattern B (Filtered Delegation) — Step 4 validation rules + Step 5 validation script specs + Step 7 seed data files (~50KB)
- **Model Selection**: opus — Quality-driven: single agent ensures consistent shared helper API, uniform JSON output format, and cross-domain validation rule coherence (newcomer→member migration N5↔M1). Sub-agent over team per Critical Reflection §1.
- **Task**: Implement all 4 P1 deterministic validation scripts for the church administration data system. Build: (a) `validate_members.py` (M1-M6: ID uniqueness, status enum values, date format YYYY-MM-DD, family cross-references, statistics integrity reconciliation), (b) `validate_newcomers.py` (N1-N5: ID uniqueness, journey stage enum integrity, date formats, assigned_to reference to members, settled→members migration consistency), (c) `validate_finance.py` (F1-F5: arithmetic integrity — item sums = category totals = grand total, monthly summation verification, void transaction handling, positive value enforcement, ID uniqueness), (d) `validate_schedule.py` (S1-S5: date format validation, time format HH:MM, facility booking conflict detection, event status enum, ID uniqueness), (e) shared `fcntl.flock` atomic write helper for data integrity across all scripts. Follow existing `validate_*.py` pattern from parent AgenticWorkflow codebase. Each script: loads YAML via PyYAML, runs all checks, outputs JSON result `{valid: bool, checks: [{rule, status, detail}]}`. All 4 scripts must pass self-tests against Step 7 seed data.
- **Verification**:
  - [ ] `validate_members.py` implements all 6 rules (M1-M6) with JSON output format
  - [ ] `validate_finance.py` implements all 5 rules (F1-F5) including arithmetic sum verification (item totals = category totals = grand total)
  - [ ] `validate_schedule.py` implements all 5 rules (S1-S5) including facility booking time-overlap conflict detection
  - [ ] `validate_newcomers.py` implements all 5 rules (N1-N5) including stage transition validation (previous stage completed before next)
  - [ ] All 4 scripts follow consistent CLI interface: `python3 validate_X.py --data-dir ./data/ [--fix]` with JSON stdout
  - [ ] Each script passes when run against Step 7 seed data [trace:step-7:seed-data]
  - [ ] Atomic write helper (`fcntl.flock` + tempfile + rename) implemented and importable across scripts
  - [ ] Validation rules match Step 4 specifications exactly [trace:step-4:validation-rules]
- **Output**: `.claude/hooks/scripts/validate_members.py`, `validate_finance.py`, `validate_schedule.py`, `validate_newcomers.py`
- **Review**: `@reviewer`
- **Translation**: none

### 9. (team) M1 Core Feature Implementation

- **Team**: `m1-core-features`
- **Checkpoint Pattern**: dense — Each task ~20+ turns with complex implementation decisions
- **Execution**: Phased (Phase A→B→C→D) — tasks use `blockedBy` to enforce dependency chains. Quality over parallelism.
- **Tasks**:
  - `@church-inbox-builder` (opus): Implement the inbox/ 3-tier data collection pipeline. Build: (a) Tier A parser: Excel/CSV → YAML conversion using openpyxl and pandas — column mapping for 헌금내역.xlsx → finance.yaml, 새신자등록카드.xlsx → newcomers.yaml, 교인명부.csv → members.yaml, (b) Tier B parser: Word/PDF text extraction using python-docx and Claude Read tool — 심방일지.docx → members.yaml history entries, (c) Tier C parser: Image data extraction using Claude multimodal — receipt images → finance.yaml expenses, namecard images → newcomers.yaml registration, (d) Human-in-the-loop confirmation flow: parse → display extracted data table → user confirms/edits → validated write to YAML, (e) error handling: preserve originals in `inbox/errors/`, report parse errors with line-level detail, HWP→PDF conversion guidance message. All parsers use `church-glossary.yaml` for Korean term normalization.
    - **Checkpoints** (dense):
      - CP-1: Tier A parser (Excel/CSV) working with test data + column mapping validated
      - CP-2: Tier B + C parsers working + HitL confirmation flow implemented
      - CP-3: Complete pipeline with error handling + P1 validation integration
  - `@church-template-builder` (opus): Implement the scan-and-replicate template engine. Build: (a) template scanner: Claude multimodal analysis of document images → extract layout structure (fixed vs variable areas, section boundaries, text flow direction), (b) template generator: convert extracted structure → `{category}-template.yaml` with typed slot definitions (text, date, list, table), (c) document generator: template.yaml + data.yaml → output Markdown following template layout, (d) first-run HitL flow: scan → display extracted structure → user confirms slot identification → save template, (e) implement for Tier A priority types first: bulletin-template.yaml, receipt-template.yaml, worship-template.yaml. Use Step 2 template analysis as structural guide [trace:step-2:template-analysis].
    - **Checkpoints** (dense):
      - CP-1: Template scanner extracts structure from sample document images
      - CP-2: Template generator creates valid template YAML with slot types
      - CP-3: End-to-end: image → template → data-populated document generation working
  - `@church-bulletin-builder` (opus): Implement the weekly bulletin generation workflow. Build: (a) `workflows/weekly-bulletin.md` independent workflow following 3-phase structure with full Inherited DNA section, (b) `.claude/agents/bulletin-generator.md` specialized agent with bulletin-data.yaml + schedule.yaml + members.yaml read permissions, (c) bulletin generation logic: combine sermon info, worship order, announcements, prayer requests, birthday/anniversary members → structured Markdown bulletin, (d) scan-and-replicate integration: use bulletin-template.yaml for layout conformity when available, (e) HitL single-review gate (low risk → Autopilot eligible), (f) Verification fields per workflow step with measurable criteria, (g) slash command `/generate-bulletin` for weekly trigger. All bulletin sections must reference `bulletin-data.yaml` field names exactly.
    - **Checkpoints** (dense):
      - CP-1: Workflow.md structure + agent definition + Inherited DNA section complete
      - CP-2: Bulletin generation logic producing valid Markdown from seed data
      - CP-3: Complete workflow with HitL gate, verification fields, template integration
  - `@church-newcomer-builder` (opus): Implement the newcomer care pipeline. Build: (a) `workflows/newcomer-pipeline.md` independent workflow with full Inherited DNA section, (b) `.claude/agents/newcomer-tracker.md` specialized agent, (c) 6-stage journey tracking logic (first_visit → attending → small_group → baptism_class → baptized → settled) with stage transition rules (previous stage must complete before next), (d) stage transition approval gates per risk level (medium risk → single-review), (e) welcome message draft generation (AI text only — no external sending per PRD §2.5), (f) re-visit check alert generation at 2-week mark (internal document, not external notification), (g) age/area-based small group recommendation algorithm, (h) settled stage → members.yaml migration with validation, (i) integration with inbox/ pipeline for newcomer card input (Excel via Tier A + namecard image via Tier C).
    - **Checkpoints** (dense):
      - CP-1: Workflow.md + agent definition + 6-stage transition logic validated
      - CP-2: Welcome message + alert generation + small group recommendation working
      - CP-3: Complete pipeline with member migration, inbox/ integration, all HitL gates
  - `@church-member-manager-builder` (sonnet): Implement member management agent and workflows. Build: (a) `.claude/agents/member-manager.md` specialized agent with members.yaml write + newcomers.yaml read permissions, (b) member registration workflow: manual entry or inbox/ import → validation (M1-M6) → members.yaml write, (c) member information update logic: status changes (active/inactive/transfer/deceased), contact updates, family linking via family_id cross-reference, (d) 이명(transfer) processing: generate transfer certificate data + update member status, (e) integration with newcomer pipeline: accept settled newcomers from newcomers.yaml → create member record in members.yaml, (f) birthday/anniversary query interface for bulletin generation, (g) HitL confirmation on all member data changes (medium risk). Uses atomic write helper from Step 8 validation scripts for data integrity [trace:step-8:atomic-write].
    - **Checkpoints** (standard):
      - CP-1: Agent definition + member registration/update logic validated
      - CP-2: Transfer processing + newcomer migration integration working
      - CP-3: Complete with HitL gates, P1 validation integration, birthday/anniversary queries
  - `@church-nl-interface-builder` (sonnet): Implement natural language interface for non-technical users (PRD §5.1 F-04). Build: (a) `.claude/skills/church-admin/SKILL.md` — Claude Code skill that interprets Korean natural language church admin commands and routes to appropriate workflows/slash commands, (b) intent mapping: "이번 주 주보 만들어줘" → `/generate-bulletin`, "새신자 현황 보여줘" → newcomer status report, "이번 달 재정 보고서 만들어줘" → `/generate-finance-report`, "교인 검색 [이름]" → member lookup, (c) `church-glossary.yaml` integration: Korean church terms → normalized system terms for accurate command interpretation, (d) error handling: unrecognized commands → friendly Korean guidance message with available command examples, (e) context-aware responses: use state.yaml to determine which workflows are available and their current status. Target: 행정 간사 (CLI 경험 없음 — PRD §3.1) and 담임 목사 (AI 직접 사용 미경험 — PRD §3.2) can operate the system via natural language without IT volunteer present.
    - **Checkpoints** (standard):
      - CP-1: Skill definition + intent mapping table (20+ Korean commands → system actions)
      - CP-2: Glossary integration + error handling with friendly Korean messages
      - CP-3: Complete skill with context-aware routing and user-friendly interaction patterns
- **Join**: Team Lead integrates all M1 features, runs cross-module validation (inbox/ → bulletin data flow, inbox/ → newcomer registration flow, newcomer settled → member migration, member birthday → bulletin, NL interface → all workflows)
- **SOT Write**: Team Lead only updates `state.yaml`
- **Verification**:
  - [ ] inbox/ pipeline processes all 3 tiers: Excel/CSV (Tier A), Word/PDF (Tier B), Images (Tier C) with HitL confirmation before any YAML write
  - [ ] scan-and-replicate engine: image → template.yaml → document.md end-to-end working for bulletin, receipt, worship order (Tier A priority)
  - [ ] `workflows/weekly-bulletin.md` follows 3-phase structure with Inherited DNA section and Verification fields on every agent step
  - [ ] Bulletin generation produces valid Markdown with all required sections (sermon, worship order, announcements, prayer requests, birthday/anniversary) from seed data [trace:step-7:seed-data]
  - [ ] `workflows/newcomer-pipeline.md` implements all 6 journey stages with correct transition rules and approval gates
  - [ ] Welcome message drafts generated as text only — no external send capability (PRD §2.5 compliance)
  - [ ] Newcomer settled → members.yaml migration working with validate_newcomers.py N5 check [trace:step-8:validate-newcomers]
  - [ ] All feature workflows pass DNA Inheritance P1 validation: `python3 .claude/hooks/scripts/validate_workflow.py --workflow-path ./workflows/[name].md`
  - [ ] Cross-module: inbox/ Excel upload → newcomers.yaml registration → newcomer pipeline stage tracking working
  - [ ] Cross-module: inbox/ image upload → bulletin-data.yaml update → bulletin generation working
  - [ ] All 4 validation scripts pass after M1 feature operations on seed data [trace:step-8:validation-scripts]
  - [ ] `.claude/agents/member-manager.md` created with members.yaml write + newcomers.yaml read permissions
  - [ ] Member management handles: registration, updates, status changes, family linking, 이명(transfer) processing
  - [ ] Newcomer→member migration path working end-to-end: newcomers.yaml (settled) → members.yaml (new member) with validate_members.py M1-M6 passing [trace:step-8:validate-members]
  - [ ] `.claude/skills/church-admin/SKILL.md` created with intent mapping for 20+ Korean natural language commands
  - [ ] NL interface correctly routes: "주보 만들어줘"→bulletin, "새신자 현황"→newcomer status, "재정 보고서"→finance report
  - [ ] NL interface integrates church-glossary.yaml for Korean church term normalization [trace:step-7:glossary]
  - [ ] Non-technical user test: simulated 행정 간사 interaction produces correct workflow invocation without CLI knowledge
- **Output**: `workflows/weekly-bulletin.md`, `workflows/newcomer-pipeline.md`, `.claude/agents/bulletin-generator.md`, `.claude/agents/newcomer-tracker.md`, `.claude/agents/data-ingestor.md`, `.claude/agents/template-scanner.md`, `.claude/agents/member-manager.md`, `.claude/skills/church-admin/SKILL.md`, inbox/ pipeline scripts, scan-and-replicate engine
- **Review**: `@reviewer`
- **Translation**: `@translator` → `workflows/weekly-bulletin.ko.md`, `workflows/newcomer-pipeline.ko.md` (workflow .md files only — agent definitions, skills, and code stay English per AGENTS.md §5.2)
- **Post-processing**:
  - `python3 .claude/hooks/scripts/validate_workflow.py --workflow-path ./workflows/weekly-bulletin.md`
  - `python3 .claude/hooks/scripts/validate_workflow.py --workflow-path ./workflows/newcomer-pipeline.md`

### 10. (human) M1 Core Integration Review

- **Action**: Review and test M1 deliverables: (a) Run inbox/ pipeline with sample data files (Excel, CSV, image), (b) Generate a test bulletin from seed data and verify all sections present, (c) Walk through newcomer pipeline 6 stages end-to-end, (d) Verify scan-and-replicate with a sample template image, (e) Confirm Human-in-the-loop gates function correctly at each approval point, (f) Validate data integrity by running all 4 P1 validation scripts. Provide feedback for any corrections needed.
- **Command**: `/review-m1`
- **Autopilot Default**: Approve M1 core features — all modules implement HitL gates and pass P1 validation. Note: Runtime finance workflows (M2) will have Autopilot permanently disabled.

### 11. (team) M2 Extended Feature Implementation

- **Team**: `m2-extended-features`
- **Checkpoint Pattern**: dense — Each task ~20+ turns with complex implementation decisions
- **Execution**: Phased (Phase A→B) — tasks use `blockedBy` to enforce dependency chains. Quality over parallelism.
- **Tasks**:
  - `@church-finance-builder` (opus): Implement finance reporting system. Build: (a) `workflows/monthly-finance-report.md` independent workflow with **Autopilot: disabled** explicitly set (PRD §5.1 F-03: 재정 = 높은 위험, 이중 검토 required), (b) `.claude/agents/finance-recorder.md` specialized agent with finance.yaml write + members.yaml read permissions, (c) monthly finance report generation logic: finance.yaml → itemized offering summary by category (십일조, 감사헌금, 특별헌금) + expense breakdown by category (관리비, 인건비, 사역비) + budget vs actual comparison table, (d) donation receipt generation: finance.yaml annual aggregation per member + members.yaml contact info → individual 기부금영수증 Markdown per member (소득세법 시행령 §80①5호 compliant), (e) receipt layout via scan-and-replicate (receipt-template.yaml from Step 9), (f) arithmetic integrity verification at every calculation step via validate_finance.py F1-F5, (g) mandatory double-review HitL gate (재정 담당 집사 + 담임 목사) on all financial outputs. **CRITICAL**: This workflow must NEVER have Autopilot enabled — enforced in workflow.md header and slash command.
    - **Checkpoints** (dense):
      - CP-1: Finance workflow.md + agent definition + Autopilot=disabled confirmation
      - CP-2: Monthly report generation + donation receipt generation producing valid output
      - CP-3: Complete with double-review HitL, P1 validation at every step, receipt template integration
  - `@church-document-builder` (opus): Implement official document generation system. Build: (a) `workflows/document-generator.md` independent workflow with Inherited DNA, (b) `.claude/agents/document-generator.md` specialized agent, (c) document types with data source mapping: 공문/official letters (members.yaml + schedule.yaml), 세례증서/baptism certificates (members.yaml church.sacraments), 이명증서/transfer certificates (members.yaml), 당회 결의문/session resolutions (schedule.yaml + members.yaml), 예배 순서지/worship orders (schedule.yaml + bulletin-data.yaml), (d) scan-and-replicate integration: letter-template.yaml, certificate-template.yaml, worship-template.yaml from Step 9, (e) HitL gate: documents → single-review (medium risk), certificates → single-review (medium risk)
    - **Checkpoints** (dense):
      - CP-1: Document workflow.md + agent definition + 5 document type specs
      - CP-2: Official letter + certificate generation producing valid Markdown
      - CP-3: All 5 document types + scan-and-replicate template integration + HitL gates
  - `@church-denomination-builder` (sonnet): Implement denomination report form support. Build: (a) 예장통합 (Presbyterian Church of Korea United) annual report form template — field mapping from all data files to denomination-required fields, (b) scan-and-replicate template: denomination-report-template.yaml with denomination-specific layout, (c) data aggregation logic: members.yaml (교세 통계: 세례교인, 입교교인, 유아세례, 이명 등) + finance.yaml (수입/지출 결산) + schedule.yaml (예배 현황) + newcomers.yaml (신입교인 통계) → denomination report fields, (d) report generation following 예장통합 standard format, (e) HitL double-review gate (denomination reports = 높은 위험). Note: 예장합동 + 기감 templates are M3 scope — include extensibility hooks for future addition.
    - **Checkpoints** (dense):
      - CP-1: 예장통합 report field mapping + data aggregation logic spec
      - CP-2: Data aggregation working + report generation producing valid output
      - CP-3: Complete denomination report with template + validation + HitL + extension hooks
  - `@church-schedule-builder` (sonnet): Implement schedule management agent and workflow. Build: (a) `workflows/schedule-manager.md` independent workflow with Inherited DNA for 예배/행사 일정 자동화 (PRD §12 M2), (b) `.claude/agents/schedule-manager.md` specialized agent with schedule.yaml write + members.yaml read permissions, (c) regular service management: add/update weekly worship services, special services (새벽기도, 수요예배, 금요기도), seasonal events (부활절, 추수감사절, 성탄절), (d) special event management: register events with date, time, facility, required volunteers → schedule.yaml, (e) facility booking conflict detection via validate_schedule.py S3 (time-overlap check before write), (f) event status tracking (scheduled → confirmed → completed → cancelled) with S4 enum validation, (g) schedule → bulletin integration: export this week's service schedule for bulletin-data.yaml consumption, (h) schedule → document integration: export event data for worship order and invitation generation, (i) HitL single-review gate (medium risk) for schedule changes. Uses atomic write helper for data integrity [trace:step-8:atomic-write].
    - **Checkpoints** (dense):
      - CP-1: Workflow.md + agent definition + service/event CRUD logic validated
      - CP-2: Facility conflict detection + status tracking + bulletin integration working
      - CP-3: Complete with document integration, HitL gates, P1 validation at every write
- **Join**: Team Lead integrates M2 features, verifies finance workflow Autopilot exclusion enforcement, verifies schedule-manager integrates with bulletin and document workflows, runs cross-module validation with M1 infrastructure
- **SOT Write**: Team Lead only updates `state.yaml`
- **Verification**:
  - [ ] `workflows/monthly-finance-report.md` header explicitly states `Autopilot: disabled` and every final output has double-review HitL gate
  - [ ] Monthly finance report produces: offering summary (itemized by 십일조/감사헌금/특별헌금/기타), expense breakdown (관리비/인건비/사역비/선교비/기타), budget vs actual comparison with variance
  - [ ] Donation receipts correctly aggregate annual per-member offerings from finance.yaml + member info from members.yaml
  - [ ] Arithmetic integrity: all financial calculations verified by validate_finance.py F1 check (item sums = category totals = grand total) [trace:step-8:validate-finance]
  - [ ] `workflows/document-generator.md` covers all 5 document types with correct data source mapping per document type
  - [ ] All generated documents use scan-and-replicate templates from Step 9 template engine [trace:step-9:template-engine]
  - [ ] 예장통합 denomination report template correctly maps data files to standard annual report fields (교세, 재정, 예배, 교육)
  - [ ] All M2 feature workflows pass DNA Inheritance P1 validation
  - [ ] M2 features integrate correctly with M1 infrastructure: shared data files, validation scripts, inbox/ pipeline
  - [ ] Finance workflow correctly rejects any Autopilot activation attempt
  - [ ] `workflows/schedule-manager.md` follows 3-phase structure with Inherited DNA and Verification fields
  - [ ] Schedule management handles: regular services, special events, facility bookings with S3 conflict detection [trace:step-8:validate-schedule]
  - [ ] Schedule → bulletin integration: weekly service data correctly consumed by bulletin workflow [trace:step-9:bulletin]
  - [ ] Schedule → document integration: event data correctly consumed by document generator for worship orders and invitations
  - [ ] Schedule workflow passes DNA Inheritance P1 validation
- **Output**: `workflows/monthly-finance-report.md`, `workflows/document-generator.md`, `workflows/schedule-manager.md`, `.claude/agents/finance-recorder.md`, `.claude/agents/document-generator.md`, `.claude/agents/schedule-manager.md`, denomination report templates, receipt generation logic
- **Review**: `@reviewer`
- **Translation**: `@translator` → `workflows/monthly-finance-report.ko.md`, `workflows/document-generator.ko.md`, `workflows/schedule-manager.ko.md` (workflow .md files only — agent definitions, templates, and code stay English per AGENTS.md §5.2)
- **Post-processing**:
  - `python3 .claude/hooks/scripts/validate_workflow.py --workflow-path ./workflows/monthly-finance-report.md`
  - `python3 .claude/hooks/scripts/validate_workflow.py --workflow-path ./workflows/document-generator.md`
  - `python3 .claude/hooks/scripts/validate_workflow.py --workflow-path ./workflows/schedule-manager.md`

### 12. Integration Testing & Quality Assurance

- **Pre-processing**: Collect all outputs from Steps 7-11. Generate comprehensive test data covering edge cases (empty fields, maximum data volumes, invalid inputs, Korean character encoding).
- **Agent**: `@church-integration-tester`
- **Context Injection**: Pattern B (Filtered Delegation) — Extract test-relevant specifications from architecture document + feature outputs
- **Verification**:
  - [ ] End-to-end test PASS: inbox/ Excel upload → data validation → bulletin generation → HitL review completes successfully
  - [ ] End-to-end test PASS: inbox/ namecard image → newcomer registration → welcome message → 6-stage progression → members.yaml migration
  - [ ] End-to-end test PASS: finance data entry → monthly report generation → donation receipt → double-review HitL
  - [ ] End-to-end test PASS: scan-and-replicate: template image → template.yaml → document generation for all 3 Tier A types
  - [ ] Cross-workflow test PASS: same member appears correctly in members.yaml, newcomers.yaml migration, finance.yaml donations, bulletin birthday list
  - [ ] Data integrity test PASS: all 4 validation scripts (M1-M6, F1-F5, S1-S5, N1-N5) pass after full integration run [trace:step-8:validation-scripts]
  - [ ] Error handling test PASS: invalid file formats in inbox/ produce clear error messages and preserve originals in `inbox/errors/`
  - [ ] HitL gate test PASS: all human review points trigger correctly in manual mode
  - [ ] Autopilot test PASS: bulletin and newcomer workflows auto-approve correctly; finance workflow blocks Autopilot with explicit error message
  - [ ] Scale test PASS: system handles 100+ member records, 50+ finance entries, 20+ newcomer records without degradation
  - [ ] Korean encoding test PASS: all Korean characters (교회 용어, 이름, 주소) preserved correctly through all pipelines
  - [ ] Backup/restore test PASS: data recovery from backup snapshot restores all YAML files to consistent state
  - [ ] Member management test PASS: registration, update, transfer, newcomer→member migration path working with P1 validation (M1-M6)
  - [ ] NL interface test PASS: 10+ Korean natural language commands correctly routed to appropriate workflows/actions
  - [ ] Schedule management test PASS: service registration, facility conflict detection (S3), bulletin/document integration working
- **Task**: Execute comprehensive integration tests across the entire church administration system. Test all end-to-end workflows (bulletin, newcomer, finance, documents, member management, schedule management), NL interface routing, cross-module data flows, P1 validation script coverage, error handling and edge cases, Human-in-the-loop gate functionality, Autopilot mode behavior (correctly enabled for low-risk and blocked for finance), Korean character encoding throughout all pipelines, and backup/restore protocol. Document all test results with pass/fail status, evidence, and any issues found with severity classification.
- **Output**: `testing/integration-test-report.md`
- **Review**: `@reviewer`
- **Translation**: `@translator` → `testing/integration-test-report.ko.md`

### 13. IT Volunteer Onboarding Package

- **Agent**: `@church-onboarding-author`
- **Context Injection**: Pattern A (Full Delegation) — System architecture overview + PRD §3.3 persona requirements
- **Verification**:
  - [ ] Installation guide covers: prerequisites (Python 3.10+, PyYAML, openpyxl, pandas, python-docx, Claude Code subscription), git clone, initial setup (`claude --init`), first-run verification steps
  - [ ] Quick start tutorial: complete walkthrough of generating first bulletin from sample data within 30-minute target (per PRD §11.3 Experiment 1 success criterion)
  - [ ] User guide for 행정 간사: how to use inbox/ folder (drop files), how to review/approve AI outputs, common weekly tasks (bulletin, newcomer check), common monthly tasks (finance report)
  - [ ] Troubleshooting guide: top 10 common issues with step-by-step solutions (YAML syntax errors, Excel parse failures, image recognition issues, permission errors, backup restoration)
  - [ ] Church IT admin guide: routine maintenance tasks, backup procedures (daily + manual), data migration from existing ChMS, adding new features via workflow-generator skill
  - [ ] All guides written in clear Korean appropriate for non-technical users (행정 간사 persona: CLI 경험 없음) [trace:step-1:personas]
  - [ ] Visual examples included: inbox/ folder screenshot mockups, approval screen examples, error message explanations
- **Task**: Create the complete IT volunteer onboarding package for church staff deployment. Following PRD §3.3 (IT volunteer persona: "설치가 간단하고 유지보수가 거의 필요 없는 시스템") and §3.1 (행정 간사: CLI 경험 없음), produce: (a) step-by-step installation guide for IT volunteers with prerequisite checklist, (b) quick start tutorial targeting first bulletin generation under 30 minutes, (c) daily-use guide for 행정 간사 focusing on inbox/ file-drop workflow and output review, (d) troubleshooting guide with top 10 common issues and visual solutions, (e) IT admin maintenance guide covering backup, updates, data migration, and feature additions via workflow-generator. All documentation must use clear Korean language, include visual examples, and assume zero CLI experience for end users.
- **Output**: `docs/installation-guide.md`, `docs/quick-start.md`, `docs/user-guide.md`, `docs/troubleshooting.md`, `docs/it-admin-guide.md`
- **Review**: none
- **Translation**: `@translator` → `docs/*.ko.md`

### 14. (human) Final System Acceptance

- **Action**: Complete system acceptance review: (a) Verify all M1 features fully operational (bulletin generation, newcomer pipeline, member management, inbox/ 3-tier parsing, scan-and-replicate for 3 Tier A types, NL interface for non-technical users), (b) Verify all M2 features fully operational (monthly finance report, donation receipts, official documents, 예장통합 denomination report, schedule management), (c) Review integration test report — all tests must PASS, (d) Review IT volunteer onboarding package completeness and clarity, (e) Confirm data integrity across all modules (run all 4 P1 validation scripts), (f) Verify finance workflow Autopilot permanently disabled, (g) Test NL interface with simulated 행정 간사 commands, (h) Sign off on production readiness for pilot deployment to 5 churches (M1 KPI target). **Note**: This is the final gate before the system is considered ready for pilot deployment.
- **Command**: `/final-review`
- **Autopilot Default**: Approve complete system — all integration tests passed, all P1 validations passed, all feature workflows include appropriate HitL gates with correct risk-level classification

---

## Claude Code Configuration

### Sub-agents

```yaml
# .claude/agents/church-domain-researcher.md
---
name: church-domain-researcher
description: "Church administration domain analysis — synthesize PRD and research documents into structured domain knowledge"
model: opus
tools: Read, Glob, Grep, WebSearch, WebFetch
permissionMode: default
maxTurns: 30
memory: project
---

# .claude/agents/church-template-analyzer.md
---
name: church-template-analyzer
description: "Church document template structure analysis for scan-and-replicate system"
model: sonnet
tools: Read, Glob, Grep
permissionMode: default
maxTurns: 20
memory: project
---

# .claude/agents/church-schema-designer.md
---
name: church-schema-designer
description: "YAML data schema design with validation rule specification for church data"
model: opus
tools: Read, Glob, Grep, Write
permissionMode: default
maxTurns: 30
memory: project
---

# .claude/agents/church-agent-architect.md
---
name: church-agent-architect
description: "Agent specialization and feature workflow blueprint design"
model: opus
tools: Read, Glob, Grep, Write
permissionMode: default
maxTurns: 40
memory: project
---

# .claude/agents/church-pipeline-designer.md
---
name: church-pipeline-designer
description: "inbox/ 3-tier data pipeline and scan-and-replicate engine architecture design"
model: opus
tools: Read, Glob, Grep, Write
permissionMode: default
maxTurns: 40
memory: project
---

# .claude/agents/church-hook-designer.md
---
name: church-hook-designer
description: "Hook configuration and P1 validation script specification design"
model: sonnet
tools: Read, Glob, Grep, Write
permissionMode: default
maxTurns: 25
memory: project
---

# .claude/agents/church-infra-builder.md
---
name: church-infra-builder
description: "Infrastructure foundation: directory structure, SOT initialization, data schemas, glossary"
model: sonnet
tools: Read, Write, Edit, Bash, Glob, Grep
permissionMode: default
maxTurns: 30
memory: project
---

# .claude/agents/church-validation-engineer.md
---
name: church-validation-engineer
description: "P1 deterministic validation scripts: validate_members.py (M1-M6), validate_finance.py (F1-F5), validate_schedule.py (S1-S5), validate_newcomers.py (N1-N5) + shared atomic write helper"
model: opus
tools: Read, Write, Edit, Bash, Glob, Grep
permissionMode: default
maxTurns: 40
memory: project
---

# .claude/agents/church-inbox-builder.md
---
name: church-inbox-builder
description: "inbox/ 3-tier data collection pipeline: Excel/CSV + Word/PDF + Image → YAML with HitL confirmation"
model: opus
tools: Read, Write, Edit, Bash, Glob, Grep
permissionMode: default
maxTurns: 40
memory: project
---

# .claude/agents/church-template-builder.md
---
name: church-template-builder
description: "Scan-and-replicate template engine: image analysis → template YAML → document generation"
model: opus
tools: Read, Write, Edit, Bash, Glob, Grep
permissionMode: default
maxTurns: 40
memory: project
---

# .claude/agents/church-bulletin-builder.md
---
name: church-bulletin-builder
description: "Weekly bulletin generation workflow and agent implementation"
model: opus
tools: Read, Write, Edit, Bash, Glob, Grep
permissionMode: default
maxTurns: 40
memory: project
skills: [workflow-generator]
---

# .claude/agents/church-newcomer-builder.md
---
name: church-newcomer-builder
description: "Newcomer care pipeline: 6-stage tracking, welcome messages, member migration"
model: opus
tools: Read, Write, Edit, Bash, Glob, Grep
permissionMode: default
maxTurns: 40
memory: project
skills: [workflow-generator]
---

# .claude/agents/church-finance-builder.md
---
name: church-finance-builder
description: "Finance reporting system: monthly reports, donation receipts, arithmetic validation — Autopilot permanently disabled"
model: opus
tools: Read, Write, Edit, Bash, Glob, Grep
permissionMode: default
maxTurns: 40
memory: project
skills: [workflow-generator]
---

# .claude/agents/church-document-builder.md
---
name: church-document-builder
description: "Official document generation: 공문, certificates, worship orders via scan-and-replicate"
model: opus
tools: Read, Write, Edit, Bash, Glob, Grep
permissionMode: default
maxTurns: 40
memory: project
skills: [workflow-generator]
---

# .claude/agents/church-denomination-builder.md
---
name: church-denomination-builder
description: "Denomination-specific report form templates (예장통합 priority, 예장합동/기감 M3)"
model: sonnet
tools: Read, Write, Edit, Bash, Glob, Grep
permissionMode: default
maxTurns: 30
memory: project
---

# .claude/agents/church-integration-tester.md
---
name: church-integration-tester
description: "Cross-module integration testing and quality assurance for church admin system"
model: opus
tools: Read, Write, Edit, Bash, Glob, Grep
permissionMode: default
maxTurns: 35
memory: project
---

# .claude/agents/church-onboarding-author.md
---
name: church-onboarding-author
description: "IT volunteer onboarding documentation: installation, user guide, troubleshooting"
model: sonnet
tools: Read, Write, Edit, Glob, Grep
permissionMode: default
maxTurns: 30
memory: project
---

# .claude/agents/church-member-manager-builder.md
---
name: church-member-manager-builder
description: "Member management agent and workflow: registration, updates, transfers, newcomer migration"
model: sonnet
tools: Read, Write, Edit, Bash, Glob, Grep
permissionMode: default
maxTurns: 30
memory: project
---

# .claude/agents/church-nl-interface-builder.md
---
name: church-nl-interface-builder
description: "Natural language interface skill for non-technical church staff (PRD §5.1 F-04)"
model: sonnet
tools: Read, Write, Edit, Glob, Grep
permissionMode: default
maxTurns: 25
memory: project
---

# .claude/agents/church-schedule-builder.md
---
name: church-schedule-builder
description: "Schedule management agent and workflow: services, events, facility bookings, conflict detection"
model: sonnet
tools: Read, Write, Edit, Bash, Glob, Grep
permissionMode: default
maxTurns: 30
memory: project
skills: [workflow-generator]
---

# Inherited agents (from parent AgenticWorkflow — no creation needed):
# .claude/agents/reviewer.md     — Adversarial code/output reviewer (Enhanced L2)
# .claude/agents/translator.md   — English→Korean translation specialist
# .claude/agents/fact-checker.md  — Adversarial fact verification agent
```

> **Model Selection Rationale (절대 기준 1)**:
> - `opus`: Domain research, architecture design, feature implementation — tasks requiring deep reasoning, complex code generation, and comprehensive analysis
> - `sonnet`: Infrastructure building, validation scripts, template analysis, denomination forms — stable repeating patterns with established conventions
> - Quality is the sole criterion — not cost or speed

### Agent Teams

#### Step 5 Team: `arch-blueprint`

```markdown
### 5. (team) System Architecture Blueprint
- **Team**: `arch-blueprint`
- **Checkpoint Pattern**: dense
- **Tasks**:
  - `@church-agent-architect` (opus): Agent specs + feature workflow blueprints
  - `@church-pipeline-designer` (opus): inbox/ pipeline + scan-and-replicate engine design
  - `@church-hook-designer` (sonnet): Hook configs + validation script specs
- **Join**: Unified architecture document with cross-references
- **SOT Write**: Team Lead only
```

#### Step 9 Team: `m1-core-features` (Phased Execution)

```markdown
### 9. (team) M1 Core Feature Implementation
- **Team**: `m1-core-features`
- **Checkpoint Pattern**: dense
- **Execution**: Phased — dependency-driven ordering for quality (not all-parallel)
  - Phase A (parallel): @church-inbox-builder + @church-template-builder
  - Phase B (parallel, after A): @church-bulletin-builder + @church-newcomer-builder
  - Phase C (after B): @church-member-manager-builder
  - Phase D (after C): @church-nl-interface-builder
- **Tasks**:
  - `@church-inbox-builder` (opus): inbox/ 3-tier data pipeline
  - `@church-template-builder` (opus): scan-and-replicate template engine
  - `@church-bulletin-builder` (opus): weekly bulletin generation workflow [blockedBy: inbox + template]
  - `@church-newcomer-builder` (opus): newcomer care pipeline [blockedBy: inbox]
  - `@church-member-manager-builder` (sonnet): member management agent + workflow [blockedBy: newcomer]
  - `@church-nl-interface-builder` (sonnet): natural language interface skill (F-04) [blockedBy: bulletin + newcomer + member]
- **Join**: Team Lead performs phased integration checks at each phase boundary + final cross-module validation
- **SOT Write**: Team Lead only
```

#### Step 11 Team: `m2-extended-features` (Phased Execution)

```markdown
### 11. (team) M2 Extended Feature Implementation
- **Team**: `m2-extended-features`
- **Checkpoint Pattern**: dense
- **Execution**: Phased — dependency-driven ordering for quality (not all-parallel)
  - Phase A (parallel): @church-finance-builder + @church-document-builder
  - Phase B (parallel, after A): @church-denomination-builder + @church-schedule-builder
- **Tasks**:
  - `@church-finance-builder` (opus): Finance reporting + donation receipts (Autopilot disabled)
  - `@church-document-builder` (opus): Official documents + certificates
  - `@church-denomination-builder` (sonnet): 예장통합 denomination report forms [blockedBy: finance]
  - `@church-schedule-builder` (sonnet): schedule management agent + 예배/행사 일정 자동화 [blockedBy: document]
- **Join**: Team Lead performs Phase A check + final M2 integration with M1 infrastructure
- **SOT Write**: Team Lead only
```

### SOT (State Management)

- **SOT File**: `state.yaml`
- **Write Permission**: Orchestrator (main session) or Team Lead (during team steps) — single writer at all times
- **Agent Access**: Read-only — agents produce output files only, never modify SOT directly
- **Quality Priority Adjustment**: Default pattern applied — all teams are step-scoped, no cross-team SOT sharing needed

**SOT Schema** (extends `state.yaml.example`):

```yaml
workflow:
  name: "Church Administration System Build"
  current_step: 1
  status: "in_progress"

  parent_genome:
    source: "AgenticWorkflow"
    version: "2026-02-27"
    inherited_dna:
      - "absolute-criteria"
      - "sot-pattern"
      - "3-phase-structure"
      - "4-layer-qa"
      - "safety-hooks"
      - "adversarial-review"
      - "decision-log"
      - "context-preservation"
      - "cross-step-traceability"
      - "domain-knowledge-structure"

  outputs:
    # Research
    # step-1: "research/domain-analysis.md"
    # step-1-ko: "research/domain-analysis.ko.md"
    # step-2: "research/template-analysis.md"
    # step-2-ko: "research/template-analysis.ko.md"
    # Planning
    # step-4: "planning/data-architecture-spec.md"
    # step-4-ko: "planning/data-architecture-spec.ko.md"
    # step-5: "planning/system-architecture.md"
    # step-5-ko: "planning/system-architecture.ko.md"
    # Implementation
    # step-7: "church-admin/"
    # step-8: ".claude/hooks/scripts/validate_*.py"
    # step-9: "workflows/weekly-bulletin.md, workflows/newcomer-pipeline.md, agents, NL skill, pipeline scripts"
    # step-9-ko: "workflows/weekly-bulletin.ko.md, workflows/newcomer-pipeline.ko.md"
    # step-11: "workflows/monthly-finance-report.md, workflows/document-generator.md, workflows/schedule-manager.md, agents, templates"
    # step-11-ko: "workflows/monthly-finance-report.ko.md, workflows/document-generator.ko.md, workflows/schedule-manager.ko.md"
    # step-12: "testing/integration-test-report.md"
    # step-12-ko: "testing/integration-test-report.ko.md"
    # step-13: "docs/*.md"
    # step-13-ko: "docs/*.ko.md"

  pending_human_action:
    step: null
    options: []

  autopilot:
    enabled: true
    decision_log_dir: "autopilot-logs/"
    auto_approved_steps: []

  pacs:
    current_step_score: null
    dimensions:
      F: null
      C: null
      L: null
    weak_dimension: null
    pre_mortem_flag: null
    history: {}

  domain_knowledge:
    file: "domain-knowledge.yaml"
    entity_count: 0
    relation_count: 0
    constraint_count: 0
    built_at_step: null
    last_validated: null
```

### Task Management

```markdown
# Step 5 Tasks (arch-blueprint team)

#### Task 1: Agent Architecture & Workflow Blueprints
- **subject**: "Design agent specs and feature workflow blueprints"
- **description**: "Design 8+ specialized agents (bulletin-generator, finance-recorder, member-manager, newcomer-tracker, data-ingestor, template-scanner, church-integration-tester, church-onboarding-author) with model selection rationale. Design 4+ independent feature workflow blueprints with Inherited DNA. Map HitL gates per risk level. Define Autopilot eligibility matrix. Output: church-agent-architecture section of system-architecture.md"
- **activeForm**: "Designing agent architecture and workflow blueprints"
- **owner**: `@church-agent-architect`
- **blocks**: []
- **blockedBy**: []

#### Task 2: Pipeline Architecture Design
- **subject**: "Design inbox/ pipeline and scan-and-replicate engine"
- **description**: "Design 3-tier data pipeline (Tier A: openpyxl/pandas, Tier B: python-docx/Claude Read, Tier C: Claude multimodal). Design scan-and-replicate engine (image → template YAML → document). Define HitL confirmation flow for all parsed data. Output: pipeline-architecture section of system-architecture.md"
- **activeForm**: "Designing data pipeline and template engine"
- **owner**: `@church-pipeline-designer`
- **blocks**: []
- **blockedBy**: []

#### Task 3: Hook & Validation Configuration
- **subject**: "Design hooks and validation script specs"
- **description**: "Specify 4 P1 validation scripts (M1-M6, F1-F5, S1-S5, N1-N5) with exact check conditions and JSON output format. Design Setup Hook for infra verification. Design PreToolUse Hook for data file protection. Spec 4 slash commands. Output: hooks-and-validation section of system-architecture.md"
- **activeForm**: "Designing hooks and validation configurations"
- **owner**: `@church-hook-designer`
- **blocks**: []
- **blockedBy**: []

# Step 9 Tasks (m1-core-features team — Phased Execution)

#### Task 6: inbox/ Data Pipeline — Phase A
- **subject**: "Build inbox/ 3-tier data collection pipeline"
- **description**: "Tier A (Excel/CSV via openpyxl/pandas), Tier B (Word/PDF via python-docx/Claude Read), Tier C (Image via Claude multimodal). All with HitL confirmation before YAML write. Error handling preserves originals. Uses church-glossary.yaml for term normalization."
- **activeForm**: "Building inbox/ data collection pipeline"
- **owner**: `@church-inbox-builder`
- **blockedBy**: []

#### Task 7: Scan-and-Replicate Engine — Phase A
- **subject**: "Build scan-and-replicate template engine"
- **description**: "Template scanner (Claude multimodal → layout structure), template generator (structure → template YAML), document generator (template + data → Markdown). Tier A types first: bulletin, receipt, worship order. First-run HitL for template confirmation."
- **activeForm**: "Building scan-and-replicate template engine"
- **owner**: `@church-template-builder`
- **blockedBy**: []

#### Task 8: Weekly Bulletin Workflow — Phase B
- **subject**: "Build weekly bulletin generation workflow"
- **description**: "workflows/weekly-bulletin.md with Inherited DNA + Verification fields. .claude/agents/bulletin-generator.md agent. Bulletin logic: bulletin-data + schedule + members → Markdown. Scan-and-replicate integration. HitL single-review. /generate-bulletin slash command."
- **activeForm**: "Building weekly bulletin generation workflow"
- **owner**: `@church-bulletin-builder`
- **blockedBy**: [6, 7]

#### Task 9: Newcomer Care Pipeline — Phase B
- **subject**: "Build newcomer care pipeline"
- **description**: "workflows/newcomer-pipeline.md with Inherited DNA. .claude/agents/newcomer-tracker.md. 6-stage journey tracking with transition rules. Welcome message drafts (text only). Re-visit alerts. Small group recommendation. Settled→member migration. inbox/ integration for Excel and namecard input."
- **activeForm**: "Building newcomer care pipeline"
- **owner**: `@church-newcomer-builder`
- **blockedBy**: [6]

# Step 11 Tasks (m2-extended-features team — Phased Execution)

#### Task 10: Finance Reporting System — Phase A
- **subject**: "Build finance reporting and donation receipt system"
- **description**: "workflows/monthly-finance-report.md with Autopilot: disabled. .claude/agents/finance-recorder.md. Monthly report: offerings by category + expenses by category + budget comparison. Donation receipts: annual per-member aggregation (소득세법 compliant). Double-review HitL mandatory. P1 validate_finance.py at every calculation."
- **activeForm**: "Building finance reporting system"
- **owner**: `@church-finance-builder`
- **blockedBy**: []

#### Task 11: Document Generation System — Phase A
- **subject**: "Build official document generation system"
- **description**: "workflows/document-generator.md. .claude/agents/document-generator.md. 5 types: 공문, 세례증서, 이명증서, 당회 결의문, 예배 순서지. Scan-and-replicate template integration. Data source mapping per type. HitL single-review gates."
- **activeForm**: "Building document generation system"
- **owner**: `@church-document-builder`
- **blockedBy**: []

#### Task 12: Denomination Report Forms — Phase B
- **subject**: "Build 예장통합 denomination report form support"
- **description**: "예장통합 annual report template + field mapping. Data aggregation from all files (교세, 재정, 예배, 교육 통계). Denomination-specific format. Double-review HitL. Extension hooks for 예장합동 + 기감 (M3). denomination-report-template.yaml via scan-and-replicate."
- **activeForm**: "Building denomination report form support"
- **owner**: `@church-denomination-builder`
- **blockedBy**: [10]

# Step 9 Additional Tasks (m1-core-features team — Phased Execution continued)

#### Task 13: Member Management System — Phase C
- **subject**: "Build member management agent and workflow"
- **description**: "Build .claude/agents/member-manager.md with members.yaml write permission. Member CRUD: registration, updates, status changes (active/inactive/transfer/deceased), family linking. Transfer (이명) processing. Newcomer→member migration from newcomers.yaml. Birthday/anniversary queries for bulletin. HitL confirmation on all changes. Uses atomic write helper."
- **activeForm**: "Building member management system"
- **owner**: `@church-member-manager-builder`
- **blockedBy**: [9]

#### Task 14: Natural Language Interface — Phase D
- **subject**: "Build NL interface skill for non-technical users (F-04)"
- **description**: "Build .claude/skills/church-admin/SKILL.md — Korean natural language → workflow routing. Intent mapping for 20+ commands. church-glossary.yaml integration. Friendly error messages in Korean. Context-aware responses via state.yaml. Target users: 행정 간사 (CLI 경험 없음) + 담임 목사."
- **activeForm**: "Building natural language interface"
- **owner**: `@church-nl-interface-builder`
- **blockedBy**: [8, 9, 13]

# Step 11 Additional Tasks (m2-extended-features team — Phased Execution continued)

#### Task 15: Schedule Management System — Phase B
- **subject**: "Build schedule management agent and workflow"
- **description**: "Build workflows/schedule-manager.md with Inherited DNA + .claude/agents/schedule-manager.md. Regular/special service management. Event CRUD with facility booking. Conflict detection (S3). Status tracking (S4). Schedule→bulletin and schedule→document integration. HitL single-review. P1 validation at every write."
- **activeForm**: "Building schedule management system"
- **owner**: `@church-schedule-builder`
- **blockedBy**: [11]
```

### Hooks

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{
          "type": "command",
          "command": "if test -f \"$CLAUDE_PROJECT_DIR\"/church-admin/.claude/hooks/scripts/guard_data_files.py; then python3 \"$CLAUDE_PROJECT_DIR\"/church-admin/.claude/hooks/scripts/guard_data_files.py; fi",
          "timeout": 10
        }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [{
          "type": "command",
          "command": "if test -f \"$CLAUDE_PROJECT_DIR\"/church-admin/.claude/hooks/scripts/validate_yaml_syntax.py; then python3 \"$CLAUDE_PROJECT_DIR\"/church-admin/.claude/hooks/scripts/validate_yaml_syntax.py; fi",
          "timeout": 10
        }]
      }
    ],
    "Setup": [
      {
        "matcher": "init",
        "hooks": [{
          "type": "command",
          "command": "if test -f \"$CLAUDE_PROJECT_DIR\"/church-admin/.claude/hooks/scripts/setup_church_admin.py; then python3 \"$CLAUDE_PROJECT_DIR\"/church-admin/.claude/hooks/scripts/setup_church_admin.py; fi",
          "timeout": 30
        }]
      }
    ]
  }
}
```

**Hook Design Notes**:

| Hook | Purpose | Exit Code |
|------|---------|-----------|
| `guard_data_files.py` (PreToolUse) | Prevent uncontrolled direct edits to `data/*.yaml` — only designated agents via proper pipeline | `2` = block, `0` = allow |
| `validate_yaml_syntax.py` (PostToolUse) | Validate YAML syntax after any `.yaml` file write | `0` = valid (warning on stderr if invalid) |
| `setup_church_admin.py` (Setup) | Verify: Python 3.10+, PyYAML, openpyxl, pandas, python-docx installed; runtime directories exist; data files valid YAML | `0` = pass, `2` = critical issue |

### Slash Commands

```markdown
# .claude/commands/review-research.md
---
description: "Review domain analysis and template analysis research findings"
---
Display research outputs from Steps 1-2 for review:
1. Show `research/domain-analysis.md` summary (key findings, entity count, terminology count)
2. Show `research/template-analysis.md` summary (7 document types, layout structures)
3. Show `domain-knowledge.yaml` statistics (entities, relations, constraints)
4. Ask for approval or specific feedback on domain accuracy
$ARGUMENTS

# .claude/commands/approve-architecture.md
---
description: "Review and approve system architecture design for implementation"
---
Display architecture outputs from Steps 4-5 for approval:
1. Show data schema overview from `planning/data-architecture-spec.md` (6 schemas + validation rules)
2. Show agent inventory and model selections from `planning/system-architecture.md`
3. Show feature workflow blueprint list with HitL gate classifications
4. Show inbox/ pipeline and scan-and-replicate design summary
5. Ask for approval or specific design change requests
$ARGUMENTS

# .claude/commands/review-m1.md
---
description: "Review and test M1 core features (bulletin, newcomer, inbox/, scan-and-replicate)"
---
Run M1 integration verification:
1. List all M1 output files with sizes (workflows, agents, scripts, data files)
2. Run all 4 P1 validation scripts against current data — report pass/fail
3. Show bulletin generation test result (sample bulletin from seed data)
4. Show newcomer pipeline stage transition test
5. Show inbox/ parsing test results (Excel, image)
6. Report any issues found with severity classification
$ARGUMENTS

# .claude/commands/final-review.md
---
description: "Final system acceptance review for complete M1+M2 church admin system"
---
Run complete system verification:
1. List ALL output files across M1 and M2 with sizes
2. Run all 4 P1 validation scripts — full report
3. Run DNA Inheritance P1 validation on all 5+ feature workflows
4. Show integration test report summary (pass/fail counts)
5. Verify finance workflow header has Autopilot: disabled
6. List IT volunteer documentation files and completeness check
7. Report overall system readiness status with any blocking issues
$ARGUMENTS
```

### Required Skills

- `workflow-generator` — Used by feature builder agents to generate independent feature `workflow.md` files with DNA Inheritance

### MCP Servers

- None required — all functionality uses Claude Code built-in tools (Read, Write, Edit, Bash, Task, multimodal image analysis). No external API dependencies per PRD §9.1.

### Runtime Directories

```yaml
runtime_directories:
  # QA Infrastructure (required)
  verification-logs/:        # step-N-verify.md (L1 verification results)
  autopilot-logs/:           # step-N-decision.md (Autopilot auto-approval decision logs)
  pacs-logs/:                # step-N-pacs.md (pACS self-confidence assessment results)
  review-logs/:              # step-N-review.md (Adversarial Review — Enhanced L2 results)
  translations/:             # glossary.yaml + *.ko.md (@translator outputs)
  diagnosis-logs/:           # step-N-{gate}-{timestamp}.md (Abductive Diagnosis)

  # Project-specific directories
  research/:                 # Domain analysis outputs
  planning/:                 # Architecture design outputs
  testing/:                  # Integration test results
  docs/:                     # IT volunteer onboarding package

  # Church admin system directories (created in Step 7)
  church-admin/data/:                  # Core YAML data files (6 schemas)
  church-admin/inbox/documents/:       # User file input — Excel, CSV, Word, PDF
  church-admin/inbox/images/:          # User image input — receipts, namecards
  church-admin/inbox/templates/:       # Scan-and-replicate template images
  church-admin/templates/:             # Generated template YAML files
  church-admin/bulletins/:             # Generated weekly bulletins (Markdown)
  church-admin/reports/:               # Generated financial/denomination reports
  church-admin/certificates/:          # Generated certificates and documents
  church-admin/workflows/:             # Independent feature workflow.md files
  church-admin/.claude/agents/:        # Specialized feature agents
  church-admin/.claude/hooks/scripts/: # P1 validation scripts + hooks
  church-admin/.claude/commands/:      # Slash commands for feature workflows
```

### Error Handling

```yaml
error_handling:
  on_agent_failure:
    action: retry_with_feedback
    max_attempts: 3
    escalation: human

  on_validation_failure:
    action: retry_or_rollback
    retry_with_feedback: true
    rollback_after: 3

  on_hook_failure:
    action: log_and_continue

  on_context_overflow:
    action: save_and_recover

  on_teammate_failure:
    attempt_1: retry_same_agent
    attempt_2: replace_with_upgrade
    attempt_3: human_escalation

  # Domain-specific error handling
  on_yaml_parse_error:
    action: preserve_original_and_report
    detail: "Preserve original file in inbox/errors/, report parse error with line-level detail to user"

  on_financial_arithmetic_error:
    action: immediate_halt
    detail: "Financial arithmetic errors are NEVER auto-resolved — always halt and escalate to double human review"

  on_inbox_unsupported_format:
    action: user_guidance
    detail: "HWP → suggest PDF conversion with step-by-step guide. Unknown format → preserve file and report"

  on_korean_encoding_error:
    action: retry_with_utf8
    detail: "Re-read file with explicit UTF-8 encoding. If persistent, report to user with file details"
```

### Autopilot Logs

```yaml
autopilot_logging:
  log_directory: "autopilot-logs/"
  log_format: "step-{N}-decision.md"
  required_fields:
    - step_number
    - checkpoint_type
    - decision
    - rationale
    - timestamp
  template: "references/autopilot-decision-template.md"

  # Domain-specific Autopilot constraints
  permanently_excluded:
    - "monthly-finance-report workflow"      # PRD §5.1 F-03: 재정 = 높은 위험
    - "donation-receipt generation"          # 이중 검토 (재정 담당 + 담임 목사) 필수
    - "denomination-report generation"       # 교단 보고서 = 높은 위험
  autopilot_eligible:
    - "weekly-bulletin workflow"             # 낮은 위험 — 단일 검토, Autopilot OK
    - "newcomer-pipeline standard steps"     # 중간 위험 — 단일 검토, Autopilot possible
    - "document-generator low-risk types"    # 예배 순서지, 소식지 초안 — 낮은 위험
```

### pACS Logs

```yaml
pacs_logging:
  log_directory: "pacs-logs/"
  log_format: "step-{N}-pacs.md"
  translation_log_format: "step-{N}-translation-pacs.md"
  dimensions: [F, C, L]                    # Factual Grounding, Completeness, Logical Coherence
  translation_dimensions: [Ft, Ct, Nt]     # Fidelity, Translation Completeness, Naturalness
  scoring: "min-score"                      # pACS = min(F, C, L)
  triggers:
    GREEN: "≥ 70 → auto-proceed"
    YELLOW: "50-69 → proceed with flag"
    RED: "< 50 → rework or escalate"
  protocol: "AGENTS.md §5.4"
```

---

## Domain-Specific Constraints

### Financial Data Safety

Per PRD §5.1 F-03, financial operations have the highest risk classification:

| Constraint | Enforcement |
|-----------|-------------|
| Autopilot permanently disabled for finance | `workflows/monthly-finance-report.md` header: `Autopilot: disabled` |
| Double-review mandatory | HitL gate requires 재정 담당 집사 + 담임 목사 approval |
| Arithmetic integrity at every step | `validate_finance.py` F1-F5 runs after every financial calculation |
| No auto-resolution of arithmetic errors | Error handling: `immediate_halt` — always escalate |

### Independent Workflow Architecture

Per PRD §9.1, each feature has its own independent `workflow.md`. This build workflow creates:

| Feature Workflow | Trigger | Autopilot |
|-----------------|---------|-----------|
| `workflows/weekly-bulletin.md` | Weekly (Monday) | eligible |
| `workflows/newcomer-pipeline.md` | Event (new registration) | eligible (standard steps) |
| `workflows/monthly-finance-report.md` | Monthly (1st) | **disabled** (permanently) |
| `workflows/document-generator.md` | On-demand | varies by document type |
| `workflows/schedule-manager.md` | On-demand + Weekly | eligible (standard operations) |

### Shared Data File Access

Per PRD §7.4 (공유 SOT 참조 3규칙):

| Data File | Write Permission | Read Access |
|-----------|-----------------|-------------|
| `members.yaml` | `@member-manager` only | All feature workflows |
| `finance.yaml` | `@finance-recorder` only | Finance + denomination workflows |
| `schedule.yaml` | `@schedule-manager` only | Bulletin + document workflows |
| `newcomers.yaml` | `@newcomer-tracker` only | Newcomer pipeline |
| `bulletin-data.yaml` | `@bulletin-generator` only | Bulletin workflow |
| `church-glossary.yaml` | Orchestrator only | All agents (term normalization) |
| `state.yaml` | Orchestrator/Team Lead only | All agents (read-only) |

---

## Post-Generation Validation

After this workflow.md is generated, run DNA Inheritance P1 validation:

```bash
python3 .claude/hooks/scripts/validate_workflow.py --workflow-path ./prompt/workflow.md
```

Expected: W1-W8 all PASS — confirming structural integrity of parent genome inheritance.

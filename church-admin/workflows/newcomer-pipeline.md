# Newcomer Pipeline

Manages the complete newcomer journey from first visit registration through settlement into the member registry, ensuring every newcomer receives personalized care through a 6-stage progression model.

## Overview

- **Input**: New visitor registration (event-driven: xlsx/csv upload, namecard image, or manual input) + weekly follow-up check (scheduled)
- **Output**: Newcomer records in `data/newcomers.yaml`, personalized welcome messages, follow-up reminders, and eventual migration to `data/members.yaml` upon settlement
- **Frequency**: Event-driven (new registration) + weekly (follow-up check every Monday)
- **Autopilot**: enabled (except stage transitions — HitL required for journey progression decisions)
- **pACS**: enabled

---

## Inherited DNA (Parent Genome)

> This workflow inherits the complete genome of AgenticWorkflow.
> Purpose varies by domain; the genome is identical. See `soul.md SS0`.

**Constitutional Principles** (adapted to the newcomer care domain):

1. **Quality Absolutism** -- Welcome messages are fully personalized with newcomer name, recommended small group, and next service time. No generic templates. Every stage transition is verified against prerequisite milestones. Thoroughness of care is the sole metric; speed of pipeline throughput is irrelevant.
2. **Single-File SOT** -- `data/newcomers.yaml` is the single source of truth for all newcomer records and journey state. The `newcomer-tracker` agent is the sole writer. No other agent or script writes to this file. `state.yaml` tracks workflow-level state (total_active, last_check_date, status).
3. **Code Change Protocol** -- Journey stage transitions follow strict prerequisite rules defined in `church_data_utils.py` (`STAGE_TO_REQUIRED_MILESTONES`). Before any transition, verify: (1) intent -- which stage is the newcomer moving to and why, (2) ripple effects -- does this affect shepherd assignments, small group rosters, or settlement eligibility, (3) change plan -- update milestones first, then stage, then `_stats`, then run validation.

**Inherited Patterns**:

| DNA Component | Inherited Form |
|--------------|----------------|
| 3-Phase Structure | Research (intake + confirmation) -> Processing (registration + welcome + transitions) -> Output (settlement) |
| SOT Pattern | `data/newcomers.yaml` -- single writer (`newcomer-tracker`). `state.yaml` -- Orchestrator only |
| 4-Layer QA | L0: record exists in newcomers.yaml. L1: milestones sequential per N2 rules. L1.5: pACS self-rating. L2: human approval for stage transitions |
| P1 Hallucination Prevention | `validate_newcomers.py` (N1-N6) deterministic validation after every newcomer data change |
| P2 Expert Delegation | `data-ingestor` for parsing, `newcomer-tracker` for journey management, `member-manager` for settlement target |
| Safety Hooks | `guard_data_files.py` enforces write permissions -- only designated agents can modify data files |
| Adversarial Review | None for this pipeline (operational workflow, not content generation) |
| Decision Log | `autopilot-logs/` -- transparent tracking of auto-approved (human) steps |
| Context Preservation | Journey state (milestones, stage, shepherd assignment) preserved in IMMORTAL snapshot sections across sessions |
| Coding Anchor Points (CAP) | CAP-1: verify all prerequisite milestones before any stage transition. CAP-2: minimal record fields -- no speculative attributes. CAP-3: define success as N1-N6 all PASS before proceeding. CAP-4: only modify the specific newcomer record being processed, never batch-update unrelated records |

**Domain-Specific Gene Expression**:

The newcomer pipeline expresses the following DNA components most strongly:

- **SOT Gene (dominant)**: The 6-stage journey model requires absolute data consistency. A newcomer's `journey_stage` and `journey_milestones` must be in perfect agreement at all times (N2 rule). Any inconsistency means a care gap -- a newcomer might not receive their welcome call, or might be prematurely advanced to a stage they are not ready for.
- **P1 Gene (dominant)**: `validate_newcomers.py` runs after every mutation to `newcomers.yaml`. The N2 check (milestone prerequisites) is the most critical -- it is the computational guarantee that no newcomer skips a care step. This is not a suggestion; it is a structural enforcement.
- **Safety Gene (expressed)**: PII data (phone, kakao_id) requires careful handling. Soft-delete only policy (status: "inactive") preserves historical records for pastoral care continuity.

---

## Research

### 1. Newcomer Data Intake

- **Agent**: `@data-ingestor`
- **Trigger**: Event-driven -- file dropped in `inbox/newcomers/` OR manual input via `/register-newcomer`
- **Pre-processing**: Route input to appropriate tier parser:
  - **Tier A** (xlsx/csv): `scripts/tier_a_parser.py` -- extract columns: name, gender, birth_year, phone, kakao_id, visit_route, referred_by, first_visit_date
  - **Tier C** (namecard image): `scripts/tier_c_parser.py` -- multimodal extraction of name, phone, and any discernible details
  - **Manual**: Direct field entry via `/register-newcomer` slash command
- **Verification**:
  - [ ] Staging JSON file exists in `inbox/staging/` with `target_data_file: "data/newcomers.yaml"`
  - [ ] All extracted records contain required fields: `name`, `gender`, `birth_year`, `contact.phone`, `first_visit` date
  - [ ] Phone numbers match `010-XXXX-XXXX` format (Korean mobile)
  - [ ] Date fields are in `YYYY-MM-DD` format
  - [ ] Confidence score >= 0.5 for each record (records below threshold flagged for manual review)
  - [ ] Korean term normalization applied using `data/church-glossary.yaml` (e.g., visit_route terms standardized)
  - [ ] [trace:step-1:domain-analysis] -- newcomer care domain fields correctly mapped from source format
- **Task**: Parse incoming newcomer data from any supported input format into a structured staging JSON file for human review
- **Output**: `inbox/staging/{timestamp}-newcomer-intake.json`
- **Post-processing**: Move source file to `inbox/processed/` on success, `inbox/errors/` on failure
- **Translation**: none

### 2. (human) Parsed Data Confirmation

- **Action**: Review the staging JSON produced by Step 1. Verify each extracted field is correct. Fix any OCR errors (Tier C) or column mapping issues (Tier A). Confirm or reject each record.
- **Command**: `/confirm-newcomer`
- **HitL Pattern**: Single Review -- one confirmation per intake batch
- **Verification**:
  - [ ] Human has reviewed each record in the staging JSON
  - [ ] All confirmed records have `confidence >= 0.9` after human review (human either corrects or confirms)
  - [ ] Rejected records are documented with rejection reason
  - [ ] Decision log entry created at `autopilot-logs/step-2-decision.md` (Autopilot mode)

---

## Processing

### 3. Newcomer Registration

- **Agent**: `@newcomer-tracker`
- **Pre-processing**: Read confirmed staging JSON from Step 2. Load current `data/newcomers.yaml` to determine next available ID (max existing N-number + 1).
- **Verification**:
  - [ ] New record appended to `data/newcomers.yaml` with unique ID matching `N\d{3,}` format (N1)
  - [ ] `journey_stage` initialized to `"first_visit"` with `first_visit` milestone marked `completed: true` (N2)
  - [ ] `first_visit` date matches the confirmed intake date (N3)
  - [ ] `assigned_to` references a valid member ID from `data/members.yaml` -- shepherd auto-assignment based on department match (N4)
  - [ ] `status` set to `"active"`
  - [ ] `settled_as_member` and `settled_date` both `null` (N5 consistency)
  - [ ] `_stats.total_active` incremented by number of new registrations (N6)
  - [ ] `_stats.by_stage.first_visit` incremented accordingly (N6)
  - [ ] P1 validation passes: `python3 .claude/hooks/scripts/validate_newcomers.py --data-dir data/`
- **Task**: Create a newcomer record in `data/newcomers.yaml` with initial journey state, auto-assign a shepherd from the matching department, and initialize all 6 milestone tracking fields
- **Output**: Updated `data/newcomers.yaml` with new record(s)
- **Post-processing**: Run `validate_newcomers.py --data-dir data/` and verify `valid: true`
- **Translation**: none

#### Shepherd Auto-Assignment Algorithm

The `newcomer-tracker` assigns a shepherd (`assigned_to`) using the following priority:

1. **Referral match**: If `referred_by` is set, assign to that member (they already have a relationship)
2. **Department + serving area match**: Find active members in `data/members.yaml` whose `church.serving_area` includes "newcomer care" (or equivalent glossary term) AND whose `church.department` matches the newcomer's age-appropriate department
3. **Department fallback**: If no newcomer care specialists, assign to any active member in the matching department
4. **Load balancing**: Among candidates, prefer the member with the fewest current newcomer assignments (count `assigned_to` references in `data/newcomers.yaml` where `status = "active"`)

Department mapping by birth year:

| Birth Year Range | Department | Korean |
|-----------------|------------|--------|
| 2005 or later | Youth | 청년부 |
| 1990-2004 | Young Adult | 청년부 |
| 1960-1989 | Adult | 장년부 |
| Before 1960 | Senior | 장년부 |

### 4. Welcome Action Generation

- **Agent**: `@newcomer-tracker`
- **Pre-processing**: Load `data/schedule.yaml` for next Sunday service times. Load `data/members.yaml` for shepherd contact info. Load `data/church-glossary.yaml` for term standardization.
- **Verification**:
  - [ ] Welcome message file exists at `output/newcomer-actions/{newcomer_id}-welcome.md`
  - [ ] Message is personalized with newcomer's name (not generic "Dear visitor")
  - [ ] Message includes senior pastor's welcome greeting
  - [ ] Message includes next Sunday service time sourced from `data/schedule.yaml` (`SVC-SUN-1` or `SVC-SUN-2`)
  - [ ] Message includes small group recommendation based on age/area algorithm
  - [ ] Message is text-only Markdown -- no external links, no send capability (PRD SS2.5 compliance)
  - [ ] Follow-up schedule file exists at `output/newcomer-actions/{newcomer_id}-followup-schedule.md`
  - [ ] Follow-up schedule contains 3 checkpoints: +3 days (welcome call), +14 days (re-visit check), +30 days (engagement review)
  - [ ] [trace:step-4:validation-rules] -- N1-N6 validation rules referenced for data integrity during generation
- **Task**: Generate a personalized welcome message and follow-up reminder schedule for each newly registered newcomer
- **Output**: `output/newcomer-actions/{newcomer_id}-welcome.md` + `output/newcomer-actions/{newcomer_id}-followup-schedule.md`
- **Translation**: none (messages generated in Korean for the congregation)

#### Welcome Message Template Structure

```markdown
# Welcome to Morning Dew Church

Dear {newcomer_name},

We are delighted that you visited Morning Dew Church on {first_visit_date}.
{senior_pastor_welcome_greeting}

## Next Sunday Service
- 1st Service: {SVC-SUN-1.time} at {SVC-SUN-1.location}
- 2nd Service: {SVC-SUN-2.time} at {SVC-SUN-2.location}

## Your Shepherd
{assigned_member_name} ({assigned_member_role}) has been assigned as your
shepherd and will be reaching out to you soon.
Contact: {assigned_member_phone}

## Recommended Small Group
Based on your profile, we recommend: {recommended_cell_group}
Department: {assigned_department}

## Your Journey With Us
We look forward to walking alongside you in your faith journey.

---
Generated: {timestamp}
Newcomer ID: {newcomer_id}
```

#### Small Group Recommendation Algorithm

1. **Age group matching**: Map newcomer `birth_year` to department (see table in Step 3)
2. **Area matching**: If newcomer address is available, match to nearest `cell_group` from `data/members.yaml` member records in the same area
3. **Interest matching**: If `visit_route` indicates specific interest (e.g., "youth group invitation"), weight that department's cell groups higher
4. **Fallback**: Recommend the cell group led by the assigned shepherd's cell group leader

#### Follow-up Reminder Schedule

| Checkpoint | Days After First Visit | Action | Responsible |
|-----------|----------------------|--------|-------------|
| Welcome Call | +3 days | Phone call to newcomer -- express welcome, answer questions | Shepherd (`assigned_to`) |
| Re-visit Check | +14 days | Check if newcomer has visited again. Generate internal alert if not. | `newcomer-tracker` (automated) |
| Engagement Review | +30 days | Review journey progress. Recommend small group introduction if attending. | Shepherd + Pastor |

> **Important**: The +14 day re-visit check generates an internal document (`output/newcomer-actions/{newcomer_id}-revisit-alert.md`), NOT an external notification. This is a reminder for the shepherd and pastoral staff. Per PRD SS2.5, the system does not send messages externally.

### 5. (human) Stage Transition Processing

- **Agent**: `@newcomer-tracker` (prepares transition proposal) + human (approves)
- **HitL Pattern**: Single Review per transition -- each stage change requires explicit human approval
- **Pre-processing**: Load current newcomer record from `data/newcomers.yaml`. Verify all prerequisite milestones for the target stage.
- **Verification**:
  - [ ] Target stage is a valid next stage in the 6-stage model (no skipping)
  - [ ] All prerequisite milestones for the target stage are marked `completed: true` (N2 rule -- see prerequisite table below)
  - [ ] Milestone dates are chronologically ordered (N3)
  - [ ] Human has reviewed and approved the transition
  - [ ] `journey_stage` updated to the new stage in `data/newcomers.yaml`
  - [ ] `_stats.by_stage` counters updated correctly (N6)
  - [ ] P1 validation passes: `python3 .claude/hooks/scripts/validate_newcomers.py --data-dir data/`
  - [ ] Decision log entry created at `autopilot-logs/step-5-decision.md` (Autopilot mode)
- **Task**: Process a newcomer's stage transition after verifying all prerequisite milestones are met and obtaining human approval
- **Output**: Updated `data/newcomers.yaml` with new `journey_stage` value
- **Post-processing**: Run `validate_newcomers.py --data-dir data/` and verify `valid: true`
- **Translation**: none

#### 6-Stage Journey Model

```
first_visit --> attending --> small_group --> baptism_class --> baptized --> settled
```

#### Stage Transition Prerequisite Table

This table defines which milestones MUST be `completed: true` before a newcomer can advance to each stage. These rules are enforced by `validate_newcomers.py` check N2 and are defined in `church_data_utils.py` as `STAGE_TO_REQUIRED_MILESTONES`.

| Target Stage | Required Milestones (all must be completed) |
|-------------|---------------------------------------------|
| `first_visit` | (none -- initial stage) |
| `attending` | `first_visit` |
| `small_group` | `first_visit`, `welcome_call`, `second_visit` |
| `baptism_class` | `first_visit`, `welcome_call`, `second_visit`, `small_group_intro` |
| `baptized` | `first_visit`, `welcome_call`, `second_visit`, `small_group_intro`, `baptism_class` |
| `settled` | `first_visit`, `welcome_call`, `second_visit`, `small_group_intro`, `baptism_class`, `baptism` |

#### Transition Flow

For each proposed transition, the `newcomer-tracker` agent:

1. **CAP-1 (verify before acting)**: Read the newcomer record and check every prerequisite milestone
2. **Prepare proposal**: Generate a transition summary showing:
   - Current stage and target stage
   - Milestone completion status (all prerequisites met? which are missing?)
   - Days since first visit
   - Shepherd's assessment (if available)
3. **Present to human**: Display the proposal for approval via `/approve-transition`
4. **CAP-4 (surgical change)**: On approval, update ONLY: `journey_stage`, the newly completed milestone's `date` and `completed` fields, and `_stats.by_stage` counters
5. **Validate**: Run N1-N6 validation to confirm data integrity

### 6. Settlement to Member Registry

- **Agent**: `@newcomer-tracker` (initiates) + `@member-manager` (executes settlement)
- **Pre-processing**: Verify newcomer has reached `settled` stage with ALL 6 milestones completed. Prepare member record template from newcomer data.
- **Verification**:
  - [ ] Newcomer `journey_stage` is `"settled"` with all milestones completed (N2)
  - [ ] Newcomer `status` updated to `"settled"` in `data/newcomers.yaml`
  - [ ] `settled_as_member` field populated with the new member ID (N5)
  - [ ] `settled_date` field populated with today's date (N5)
  - [ ] New member record created in `data/members.yaml` by `@member-manager` with:
    - Unique member ID matching `M\d{3,}` format (M1)
    - Name, gender, contact info carried over from newcomer record
    - `church.registration_date` set to settlement date
    - `church.baptism_date` carried from newcomer's baptism milestone date
    - `church.department` matching newcomer's `assigned_department`
    - `history` entry: `{date: settlement_date, event: "transfer_in", note: "newcomer settlement (N{id} -> M{id})"}`
  - [ ] `data/members.yaml` passes P1 validation: `python3 .claude/hooks/scripts/validate_members.py --data-dir data/`
  - [ ] `data/newcomers.yaml` passes P1 validation: `python3 .claude/hooks/scripts/validate_newcomers.py --data-dir data/`
  - [ ] `state.yaml` `workflow_states.newcomer.total_active` decremented by 1
  - [ ] `_stats` in both files recomputed and validated (N6, M7)
- **Task**: Migrate a settled newcomer from `data/newcomers.yaml` to `data/members.yaml`, creating a full member record while preserving the newcomer record with settled status for historical tracking
- **Output**: Updated `data/newcomers.yaml` (status: settled) + updated `data/members.yaml` (new member record)
- **Post-processing**: Run both `validate_newcomers.py` and `validate_members.py` to confirm cross-file consistency
- **Translation**: none

#### Settlement Protocol

The settlement process involves two agents with strict write boundaries:

```
newcomer-tracker                          member-manager
     |                                         |
     |  1. Verify all milestones completed     |
     |  2. Prepare member record template      |
     |  3. Request settlement ----------------> |
     |                                         |  4. Create member record in members.yaml
     |                                         |  5. Run validate_members.py
     |                                         |  6. Return new member ID
     |  <-------------------------------------- |
     |  7. Update newcomer record:             |
     |     - status: "settled"                 |
     |     - settled_as_member: "{new_id}"     |
     |     - settled_date: "{today}"           |
     |  8. Run validate_newcomers.py           |
     |                                         |
```

**Write boundary enforcement**:
- `newcomer-tracker` writes ONLY to `data/newcomers.yaml`
- `member-manager` writes ONLY to `data/members.yaml`
- Neither agent writes to the other's data file
- This boundary is enforced by `guard_data_files.py` safety hook

---

## Claude Code Configuration

### Sub-agents

```yaml
agents:
  newcomer-tracker:
    description: "Manages 6-stage newcomer journey pipeline"
    model: sonnet          # Pattern execution -- well-defined state machine
    tools: [Read, Write, Edit, Bash, Glob, Grep]
    write_permissions:
      - data/newcomers.yaml
      - output/newcomer-actions/
    permissionMode: default
    maxTurns: 20

  data-ingestor:
    description: "Parses files from inbox/ into structured staging JSON"
    model: opus            # Multimodal analysis for Tier C (namecard images)
    tools: [Read, Write, Edit, Bash, Glob, Grep]
    write_permissions:
      - inbox/staging/
      - inbox/processed/
      - inbox/errors/

  member-manager:
    description: "Manages member registry -- settlement target only in this workflow"
    model: sonnet
    tools: [Read, Write, Edit, Bash, Glob, Grep]
    write_permissions:
      - data/members.yaml
```

### SOT (State Management)

- **SOT files**:
  - `state.yaml` -- workflow-level state (Orchestrator only writes)
  - `data/newcomers.yaml` -- newcomer records (`newcomer-tracker` sole writer)
  - `data/members.yaml` -- member records (`member-manager` sole writer)
- **Write permission**: Each data file has exactly one designated writer agent
- **Agent access**: All agents can READ all data files. Write restricted per agent definition.
- **Quality adjustment**: Default pattern applied -- no cross-write needed since settlement uses inter-agent request protocol

### Slash Commands

```yaml
commands:
  /register-newcomer:
    description: "Manually register a new visitor with name, phone, visit date"
    triggers: Step 1 (manual input path)

  /confirm-newcomer:
    description: "Review and confirm parsed newcomer data from staging"
    triggers: Step 2

  /approve-transition:
    description: "Review and approve a newcomer stage transition proposal"
    triggers: Step 5

  /newcomer-status:
    description: "Display current newcomer pipeline status -- active count, by-stage breakdown"
    triggers: On-demand

  /weekly-followup:
    description: "Run weekly follow-up check -- identify overdue milestones and generate alerts"
    triggers: Weekly scheduled or on-demand
```

### Hooks

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "if test -f \"$CLAUDE_PROJECT_DIR/.claude/hooks/scripts/guard_data_files.py\"; then python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/scripts/guard_data_files.py\"; fi",
            "timeout": 10
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "if echo \"$TOOL_INPUT\" | grep -q 'newcomers.yaml'; then python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/scripts/validate_newcomers.py\" --data-dir \"$CLAUDE_PROJECT_DIR/data/\"; fi",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

### Runtime Directories

```yaml
runtime_directories:
  output/newcomer-actions/:        # Welcome messages, follow-up schedules, revisit alerts
  inbox/newcomers/:                # Incoming newcomer data files (xlsx, csv, images)
  inbox/staging/:                  # Parsed staging JSON for human review
  inbox/processed/:                # Successfully processed source files
  inbox/errors/:                   # Failed parsing -- source files + error reports
  verification-logs/:              # step-N-verify.md (L1 verification results)
  autopilot-logs/:                 # step-N-decision.md (auto-approved decisions)
  pacs-logs/:                      # step-N-pacs.md (pACS self-rating results)
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
    critical_rule: "N2 (milestone prerequisite) failures ALWAYS escalate -- never auto-retry stage transitions"

  on_hook_failure:
    action: log_and_continue

  on_context_overflow:
    action: save_and_recover
    critical_state: "newcomer journey_stage and milestones must be preserved in IMMORTAL snapshot"

  on_settlement_failure:
    action: rollback_newcomer_status
    detail: "If member-manager fails to create member record, newcomer-tracker must NOT update newcomer status to 'settled'. Atomic settlement -- both files updated or neither."
```

### pACS Logs

```yaml
pacs_logging:
  log_directory: "pacs-logs/"
  log_format: "step-{N}-pacs.md"
  dimensions: [F, C, L]
  scoring: "min-score"
  triggers:
    GREEN: ">= 70 -> auto-proceed"
    YELLOW: "50-69 -> proceed with flag"
    RED: "< 50 -> rework or escalate"
  protocol: "AGENTS.md SS5.4"
  domain_calibration:
    F_weight: "critical -- newcomer data must match source exactly"
    C_weight: "high -- all milestones and fields must be populated"
    L_weight: "medium -- stage transitions must follow prerequisite logic"
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
  hitl_steps: [2, 5]
  note: "Steps 2 and 5 require human confirmation even in Autopilot mode"
```

---

## Weekly Follow-up Check (Scheduled Trigger)

In addition to the event-driven newcomer registration flow (Steps 1-6), this workflow runs a weekly follow-up check:

### Trigger

- **Schedule**: Every Monday (configurable)
- **Command**: `/weekly-followup`
- **Agent**: `@newcomer-tracker`

### Process

1. Load all active newcomers from `data/newcomers.yaml` (status = "active")
2. For each active newcomer, calculate days since `first_visit`
3. Generate alerts for overdue milestones:

| Alert Type | Condition | Output |
|-----------|-----------|--------|
| Welcome Call Overdue | +3 days passed, `welcome_call.completed = false` | `output/newcomer-actions/{id}-alert-welcome-call.md` |
| Re-visit Check | +14 days passed, `second_visit.completed = false` | `output/newcomer-actions/{id}-revisit-alert.md` |
| Engagement Stall | +30 days passed, still at `first_visit` or `attending` stage | `output/newcomer-actions/{id}-alert-engagement.md` |
| Long Plateau | +90 days at same stage (not settled) | `output/newcomer-actions/{id}-alert-plateau.md` |

4. Generate a weekly summary report: `output/newcomer-actions/weekly-summary-{date}.md`
5. All alerts are internal documents for pastoral staff review -- no external notifications

### Weekly Summary Report Structure

```markdown
# Newcomer Pipeline Weekly Summary -- {date}

## Active Newcomers: {count}

### By Stage
- first_visit: {count}
- attending: {count}
- small_group: {count}
- baptism_class: {count}
- baptized: {count}

### Overdue Alerts
{list of newcomers with overdue milestones}

### Recent Transitions
{newcomers who changed stage in the past 7 days}

### Settlement Candidates
{newcomers at baptized stage with all prerequisites for settled}
```

---

## Data Architecture Reference

### newcomers.yaml Record Schema

```yaml
- id: "N001"                        # Unique ID (N\d{3,}) -- N1 validated
  name: "Name"                      # Required
  gender: "male|female"             # Required
  birth_year: 1992                  # Required (integer)
  contact:
    phone: "010-XXXX-XXXX"          # Required (Korean mobile format)
    kakao_id: "optional_id"         # Optional
  first_visit: "YYYY-MM-DD"         # Required -- N3 validated
  visit_route: "Category"           # How they found the church
  referred_by: "M001"               # Optional member ID -- N4 cross-referenced
  journey_stage: "first_visit"      # One of 6 stages -- N2 validated
  journey_milestones:                # All 6 milestone tracking fields
    first_visit:
      date: "YYYY-MM-DD"
      completed: true|false
    welcome_call:
      date: "YYYY-MM-DD"|null
      completed: true|false
      notes: "optional notes"
    second_visit:
      date: "YYYY-MM-DD"|null
      completed: true|false
    small_group_intro:
      date: "YYYY-MM-DD"|null
      completed: true|false
    baptism_class:
      date: "YYYY-MM-DD"|null
      completed: true|false
    baptism:
      date: "YYYY-MM-DD"|null
      completed: true|false
  assigned_to: "M023"               # Shepherd member ID -- N4 cross-referenced
  assigned_department: "Department"  # Age-appropriate department
  status: "active|settled|inactive"  # N5 validated with settled fields
  settled_as_member: null|"M252"    # Populated only when settled -- N5
  settled_date: null|"YYYY-MM-DD"   # Populated only when settled -- N5
```

### Cross-File References

```
newcomers.yaml                    members.yaml
  assigned_to: "M023"  --------->  id: "M023" (shepherd)
  referred_by: "M001"  --------->  id: "M001" (referrer)
  settled_as_member: "M252" ---->  id: "M252" (settled member)

state.yaml
  workflow_states.newcomer:
    total_active: {matches _stats.total_active in newcomers.yaml}
    status: "idle|processing"
```

### Validation Rules Summary (N1-N6)

| Rule | What It Checks | Enforcement |
|------|---------------|-------------|
| N1 | ID uniqueness + `N\d{3,}` format | Every write to newcomers.yaml |
| N2 | Journey stage valid + all prerequisite milestones completed | Every stage transition |
| N3 | All date fields valid `YYYY-MM-DD` | Every write |
| N4 | `referred_by` and `assigned_to` reference valid member IDs | Every write (cross-file) |
| N5 | Settlement consistency: `settled` status <-> `settled_as_member` + `settled_date` | Every write |
| N6 | `_stats` arithmetic matches actual record counts | Every write |

---

## Post-processing

After each pipeline run, execute the following validation scripts:

```bash
# P1 Newcomer validation (N1-N6)
python3 .claude/hooks/scripts/validate_newcomers.py --data-dir data/

# P1 Member validation (M1-M7) — when settlement occurs
python3 .claude/hooks/scripts/validate_members.py --data-dir data/

# Cross-step traceability validation (CT1-CT5)
python3 .claude/hooks/scripts/validate_traceability.py --step 9 --project-dir .
```

---

## Traceability Index

The following cross-step traceability markers are used throughout this workflow:

| Marker | Step | Description |
|--------|------|-------------|
| [trace:step-1:domain-analysis] | Step 1 | Newcomer care domain field mapping from source formats |
| [trace:step-4:validation-rules] | Step 4 | N1-N6 validation rules referenced during welcome message generation |
| [trace:step-7:seed-data] | (external) | Test newcomer data for validation script development |
| [trace:step-8:validate-newcomers] | (external) | `validate_newcomers.py` script implementing N1-N6 rules |

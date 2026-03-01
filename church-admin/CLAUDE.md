# Church Administration System

AI-powered church administration automation for Korean Presbyterian churches. This is a **child system** of the AgenticWorkflow parent genome — all constitutional principles are inherited and enforced.

## Absolute Criteria (Inherited)

1. **Quality Above All** — Speed, token cost, and effort are irrelevant. Only output quality matters.
2. **Single-File SOT** — `state.yaml` is the sole source of truth. All agents read it; only the Orchestrator writes it.
3. **Code Change Protocol** — Read before modify. Analyze impact. Plan changes. No blind edits.

## SOT Discipline

**`state.yaml`** (this directory root) is the central state file.

- **Writer**: Orchestrator (main Claude session) ONLY
- **Readers**: All agents (read-only)
- **Contents**: Church metadata, data file registry, feature flags, workflow states, configuration

### Data File Sole-Writer Map

Each data file has exactly ONE designated writer agent. This is enforced by `guard_data_files.py` (PreToolUse hook).

| Data File | Sole Writer | Validator | Sensitivity | Deletion Policy |
|-----------|------------|-----------|-------------|-----------------|
| `data/members.yaml` | `member-manager` | `validate_members.py` (M1-M7) | HIGH (PII) | Soft-delete only |
| `data/finance.yaml` | `finance-recorder` | `validate_finance.py` (F1-F7) | HIGH (Financial) | Void-only |
| `data/schedule.yaml` | `schedule-manager` | `validate_schedule.py` (S1-S6) | LOW | Status cancel |
| `data/newcomers.yaml` | `newcomer-tracker` | `validate_newcomers.py` (N1-N6) | HIGH (PII) | Soft-delete only |
| `data/bulletin-data.yaml` | `bulletin-generator` | `validate_bulletin.py` (B1-B3) | LOW | Overwrite per issue |
| `data/church-glossary.yaml` | ANY agent | — | LOW | Append-only |

**Total: 29 deterministic validation rules across 5 scripts.**

### Agent Roster

| Agent | Role | Writes To | Depends On |
|-------|------|-----------|------------|
| `bulletin-generator` | Weekly bulletin generation | `data/bulletin-data.yaml`, `bulletins/` | members (birthday), schedule (services) |
| `newcomer-tracker` | Newcomer journey pipeline | `data/newcomers.yaml` | members (settlement handoff) |
| `member-manager` | Member CRUD + lifecycle | `data/members.yaml` | newcomers (settlement intake) |
| `finance-recorder` | Offerings, expenses, receipts | `data/finance.yaml` | members (donor cross-ref) |
| `schedule-manager` | Services, events, facilities | `data/schedule.yaml` | — |
| `document-generator` | Certificates, letters, minutes | `docs/generated/` | members, schedule |
| `data-ingestor` | Parse inbox files → staging | `inbox/staging/`, `inbox/processed/`, `inbox/errors/` | — |
| `template-scanner` | Image → YAML template | `templates/` | — |

### Agent Dependency Graph

```
schedule-manager ─────────────────────────────────┐
                                                   ↓
data-ingestor → [staging JSON] → human review → member-manager ←── newcomer-tracker
                                                   ↑                      ↓
template-scanner → [YAML templates]          finance-recorder       (settlement)
                        ↓                          ↑                      ↓
                  document-generator         members (cross-ref)    member-manager
                        ↑
                  bulletin-generator ← members (birthday) + schedule (services)
```

## Data Sensitivity

The following files contain PII and are `.gitignore`'d:

- `data/members.yaml` — Names, phone numbers, addresses
- `data/finance.yaml` — Donation records with donor names
- `data/newcomers.yaml` — Newcomer personal information

**These files must NEVER be committed to a public repository.**

## Finance Safety

Finance operations have **autopilot permanently disabled**. This is triple-enforced:

1. `state.yaml` → `config.autopilot.finance_override: false`
2. `finance-recorder.md` → explicit autopilot prohibition in agent spec
3. `monthly-finance-report.md` workflow → human confirmation at every write step

## Korean Terminology

All agents must normalize Korean church terms using `data/church-glossary.yaml`. This glossary covers 50+ terms across:

- Roles (직분): 목사, 장로, 집사, 권사, 성도, 구역장
- Governance (치리): 당회, 제직회, 공동의회, 노회
- Worship (예배): 찬양, 기도, 봉헌, 축도, 주보
- Finance (재정): 십일조, 감사헌금, 건축헌금, 선교헌금
- Sacraments (성례): 세례, 유아세례, 입교, 성찬식

## Validation Infrastructure

Run all validators at once:
```bash
python3 scripts/validate_all.py
```

Or individually:
```bash
python3 .claude/hooks/scripts/validate_members.py --data-dir data/
python3 .claude/hooks/scripts/validate_finance.py --data-dir data/
python3 .claude/hooks/scripts/validate_schedule.py --data-dir data/
python3 .claude/hooks/scripts/validate_newcomers.py --data-dir data/
python3 .claude/hooks/scripts/validate_bulletin.py --data-dir data/
```

All 29 rules must pass before any workflow advances.

## NL Interface

The Korean natural language interface is defined in `.claude/skills/church-admin/SKILL.md`. It maps 41 Korean command patterns to system actions across 8 categories: bulletin, newcomer, member, finance, schedule, document, data import, and system commands.

## Workflows

| Workflow | File | Trigger |
|----------|------|---------|
| Weekly Bulletin | `workflows/weekly-bulletin.md` | "주보 만들어줘" |
| Newcomer Pipeline | `workflows/newcomer-pipeline.md` | Event-driven |
| Monthly Finance Report | `workflows/monthly-finance-report.md` | "재정 보고서" |
| Document Generator | `workflows/document-generator.md` | "증명서 발급" |
| Schedule Manager | `workflows/schedule-manager.md` | "행사 등록" |

## Inherited DNA

This system inherits the full AgenticWorkflow genome:

- **Constitutional Principles**: Quality absolutism, SOT pattern, Code Change Protocol
- **Quality Assurance**: L0 Anti-Skip Guard, L1 Verification, L1.5 pACS, L2 human review
- **Safety Hooks**: Destructive command blocking, data file guards, YAML syntax validation
- **Context Preservation**: Snapshots, knowledge archives, RLM pattern
- **Adversarial Review**: Generator-Critic pattern for output quality
- **Coding Anchor Points**: CAP-1 (think before code), CAP-2 (simplicity), CAP-3 (goal-based), CAP-4 (surgical changes)

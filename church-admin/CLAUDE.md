# Church Administration System

AI-powered church administration automation for Korean Presbyterian churches. This is a **child system** of the AgenticWorkflow parent genome — all constitutional principles are inherited and enforced.

## Absolute Criteria (Inherited)

1. **Quality Above All** — Speed, token cost, and effort are irrelevant. Only output quality matters.
2. **Single-File SOT** — `state.yaml` is the sole source of truth. All agents read it; only the Orchestrator writes it.
3. **Code Change Protocol** — Read before modify. Analyze impact. Plan changes. No blind edits.

## Mandatory Start Menu (시작 메뉴 필수 표시 규칙)

**사용자가 아래 패턴 중 하나를 입력하면, 다른 어떤 행동보다 먼저 아래 3단계를 반드시 실행한다.**

> 이 규칙은 절대 기준과 동등한 우선순위를 가진다. 생략, 축약, 대체 불가.

### 트리거 패턴

"시작", "시작하자", "시작해줘", "시작합니다", "워크플로우 시작", "메뉴", "메뉴 보여줘", "메뉴판", "뭐 할 수 있어?", "뭘 할 수 있어?", "가능한 기능", "도움말", "사용법", "어떻게 해?", "처음", "처음부터", "다시 시작", 또는 구체적 작업 지시 없는 인사말

### 필수 실행 순서

**Step 1** — 상태 수집 스크립트 실행 (Bash tool):
```bash
python3 scripts/show_menu.py --state state.yaml --data-dir data/
```

**Step 2** — JSON 출력을 바탕으로 환영 배너 + 현재 상태 + 주의사항(alerts) 표시

**Step 3** — `AskUserQuestion` 도구로 대화형 메뉴 표시:
- JSON `menu_page1` 배열의 3개 항목 + "더보기..." 옵션 (총 4개)
- `alert` 필드가 있는 항목은 설명 앞에 "!!" 표시
- 질문: "어떤 작업을 도와드릴까요?"
- "더보기" 선택 시 → `menu_page2`의 나머지 항목으로 두 번째 `AskUserQuestion` 표시

### 절대 금지

- 메뉴 없이 "무엇을 도와드릴까요?"라고만 묻는 행위
- `AskUserQuestion` 대신 텍스트로 메뉴 목록만 출력하는 행위
- show_menu.py 실행을 건너뛰고 직접 데이터 파일을 읽는 행위
- "시작하자" 입력에 대해 시스템 설명이나 분석으로 응답하는 행위

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

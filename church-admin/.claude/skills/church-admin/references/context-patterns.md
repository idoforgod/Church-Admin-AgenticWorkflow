# NL Interface — Context Injection Patterns

How the Korean Natural Language interface routes commands to system actions.

## Routing Architecture

```
Korean Input → Term Normalization → Intent Classification → Agent/Workflow Dispatch
     ↓               ↓                      ↓                       ↓
  raw text    church-glossary.yaml    SKILL.md patterns    state.yaml context
```

## Context Injection Flow

### Step 1: State Check

Before routing any command, read `state.yaml` to determine:

```yaml
# What to check:
church.features:          # Which workflows are enabled?
church.workflow_states:    # Is any workflow currently in progress?
church.config.autopilot:   # Autopilot mode?
```

**Routing implications:**
- If `features.finance_reporting: false` and user says "재정 보고서" → inform that finance reporting is not yet enabled
- If `workflow_states.bulletin.status: "in_progress"` → offer to resume rather than restart
- If `config.autopilot.enabled: false` → all workflow steps require human confirmation

### Step 2: Term Normalization

Map Korean church terminology to system terms using `data/church-glossary.yaml`:

| Korean Input | Normalized Term | Category |
|-------------|----------------|----------|
| 집사 | deacon | role |
| 십일조 | tithe | offering_type |
| 청년부 | youth_ministry | department |
| 구역장 | cell_group_leader | role |
| 세례 | baptism | sacrament |
| 이명 | transfer | member_event |

### Step 3: Intent Classification

Match the normalized input against SKILL.md intent patterns:

| Intent Category | Key Signals | Route To |
|----------------|------------|----------|
| Bulletin (주보) | 주보, 예배순서, 생성, 미리보기 | bulletin-generator or data read |
| Newcomer (새신자) | 새신자, 새가족, 등록, 단계, 환영 | newcomer-tracker |
| Member (교인) | 교인, 검색, 등록, 수정, 생일, 이명 | member-manager |
| Finance (재정) | 재정, 헌금, 지출, 예산, 영수증 | finance-recorder |
| Schedule (일정) | 일정, 예배, 행사, 시설, 예약 | schedule-manager |
| Document (문서) | 증명서, 공문, 결의문, 회의록, 이명증서 | document-generator |
| Data Import (데이터) | 파일, 가져오기, 엑셀, 사진, 승인 | data-ingestor |
| System (시스템) | 검증, 상태, 도움말, 용어 | system commands |

### Step 4: Context-Aware Dispatch

Based on state + intent, choose the appropriate action:

```
IF intent == "bulletin" AND bulletin already exists for this week:
    → Offer preview instead of regeneration

IF intent == "newcomer_status" AND any newcomer past 14-day mark:
    → Proactively flag overdue follow-ups

IF intent == "finance" AND finance_override == false:
    → Require explicit human confirmation at every step

IF intent == "data_import" AND inbox/staging has pending files:
    → Show pending count and offer to process
```

## Ambiguity Resolution

When a command is ambiguous, prefer the most specific interpretation:

1. **"김철수 검색"** → Member search (most common use case)
2. **"이번 주"** → Current week based on today's date
3. **"보고서"** → Monthly finance report if in finance context, otherwise clarify
4. **"등록"** → Context-dependent: newcomer registration if preceded by 새신자/새가족, member registration if preceded by 교인

## Error Response Pattern

When a command cannot be classified:

```
죄송합니다. 말씀하신 명령을 이해하지 못했습니다.

사용 가능한 명령 예시:
  [show 8 category examples from SKILL.md]

더 자세한 도움이 필요하시면 "도움말"을 입력하세요.
```

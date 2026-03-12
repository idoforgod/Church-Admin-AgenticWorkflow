# NL Interface — Context Injection Patterns

How the Korean Natural Language interface routes commands to system actions.

## Routing Architecture

```
Korean Input → Startup Detection → Term Normalization → Intent Classification → Agent/Workflow Dispatch
     ↓               ↓                    ↓                      ↓                       ↓
  raw text     /start menu?       church-glossary.yaml    SKILL.md patterns    state.yaml context
```

## Routing Priority (matches SKILL.md § Routing Priority)

1. **Startup/Menu patterns** → `/start` interactive menu (highest priority)
2. **Specific category commands** → Direct workflow routing
3. **Ambiguous or greeting-like input** → `/start` interactive menu (catch-all)

## Context Injection Flow

### Step 0: Startup Detection (NEW — highest priority)

Check if user input matches startup patterns:
- "시작", "시작하자", "시작해줘", "시작합니다"
- "워크플로우 시작", "워크플로우를 시작하자"
- "메뉴", "메뉴 보여줘"
- "뭐 할 수 있어?", "도움말", "어떻게 해?"
- "처음", "처음부터", "다시 시작"
- Greetings without specific tasks ("안녕", "안녕하세요")

If matched → execute `/start` command flow:
1. Read `state.yaml` for current context
2. Display status summary (Korean, 존댓말)
3. Show interactive menu via `AskUserQuestion` (context-aware priority)
4. Route based on user selection

If NOT matched → proceed to Step 1.

### Step 1: State Check

Before routing any command, read `state.yaml` to determine:

```yaml
# What to check:
church.features:          # Which workflows are enabled?
church.workflow_states:    # Is any workflow currently in progress?
church.config.autopilot:   # Autopilot mode?
```

**Routing implications:**
- If `features.X: false` and user requests X → inform that the feature is not yet enabled, suggest "시작" for available options
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
| Startup (시작) | 시작, 메뉴, 도움말, 처음 | `/start` interactive menu |
| Bulletin (주보) | 주보, 예배순서, 생성, 미리보기 | bulletin-generator or data read |
| Newcomer (새신자) | 새신자, 새가족, 등록, 단계, 환영 | newcomer-tracker |
| Member (교인) | 교인, 검색, 등록, 수정, 생일, 이명 | member-manager |
| Finance (재정) | 재정, 헌금, 지출, 예산, 영수증 | finance-recorder |
| Schedule (일정) | 일정, 예배, 행사, 시설, 예약 | schedule-manager |
| Document (문서) | 증명서, 공문, 결의문, 회의록, 이명증서 | document-generator |
| Data Import (데이터) | 파일, 가져오기, 엑셀, 사진, 승인 | data-ingestor |
| System (시스템) | 검증, 상태, 용어 | system commands |

### Step 4: Context-Aware Dispatch

Based on state + intent, choose the appropriate action:

```
IF intent == "startup" OR intent is ambiguous:
    → Execute /start interactive menu

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

If no specific interpretation is possible → route to `/start` interactive menu (never show a dead-end error).

## Error Response Pattern

When a command cannot be classified, do NOT show a static error message. Instead, route to the `/start` interactive menu:

1. Briefly acknowledge: "말씀하신 내용을 더 잘 도와드리기 위해 메뉴를 보여드리겠습니다."
2. Execute the `/start` command flow (state.yaml read → status display → AskUserQuestion menu)
3. This ensures beginner users always land in a guided experience, never a dead end.

Fallback (only if `/start` is unavailable):

```
"시작"이라고 입력하시면 대화형 메뉴를 보여드립니다.

또는 아래 명령어를 직접 입력하실 수 있습니다:
  주보: "이번 주 주보 만들어줘"
  새신자: "새신자 현황 보여줘"
  교인: "교인 검색 [이름]"
  재정: "재정 보고서 만들어줘"
  일정: "이번 주 일정 보여줘"
  문서: "증명서 발급해줘"
  시스템: "데이터 검증해줘"
```

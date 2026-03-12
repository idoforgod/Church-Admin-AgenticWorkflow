# Church Administration Natural Language Interface

Korean natural language command interface for non-technical church administration staff.

## Purpose

This skill enables non-technical users (행정 간사 who has no CLI experience, and 담임 목사 who has no direct AI experience — PRD §3.1, §3.2) to operate the Church Administration system via natural Korean language commands. The skill interprets Korean church terminology, routes to appropriate workflows or agents, and provides friendly Korean responses.

## When to Use

This skill activates when the user issues church administration commands in Korean, such as:
- "시작하자", "시작", "시작해줘" → **MUST show interactive main menu** (`/start`)
- "이번 주 주보 만들어줘" → Generate weekly bulletin
- "새신자 현황 보여줘" → Show newcomer status
- "교인 검색 김철수" → Search member by name
- "이번 달 재정 보고서 만들어줘" → Generate monthly finance report

## CRITICAL — Start Menu Rule

**When the user types a startup pattern (시작, 시작하자, 메뉴, etc.), you MUST:**
1. Run `python3 scripts/show_menu.py --state state.yaml --data-dir data/` FIRST
2. Display the welcome screen with status from the script output
3. Show `AskUserQuestion` with the top 4 menu items from the script output

**This is NOT optional.** Users who type "시작하자" do not know what the system can do. The menu is their only guide. Never skip the menu, never just describe capabilities — always show the interactive AskUserQuestion menu.

## Intent Mapping

### Startup / Menu Commands (시작)

| Korean Command Pattern | System Action | Route |
|----------------------|---------------|-------|
| "시작", "시작하자", "시작해줘", "시작합니다" | Show interactive main menu | `/start` command |
| "워크플로우 시작", "워크플로우를 시작하자" | Show interactive main menu | `/start` command |
| "메뉴", "메뉴 보여줘", "메뉴판" | Show interactive main menu | `/start` command |
| "뭐 할 수 있어?", "뭘 할 수 있어?", "가능한 기능" | Show interactive main menu | `/start` command |
| "도움말", "사용법", "어떻게 해?", "어떻게 사용해?" | Show interactive main menu | `/start` command |
| "처음", "처음부터", "다시 시작" | Show interactive main menu | `/start` command |

> **Priority**: Startup patterns are checked FIRST, before any category-specific routing. Any ambiguous or generic input that doesn't match a specific category should also route to the start menu.

### Bulletin Commands (주보)

| Korean Command Pattern | System Action | Route |
|----------------------|---------------|-------|
| "주보 만들어줘", "이번 주 주보 생성" | Generate weekly bulletin | `/generate-bulletin` workflow |
| "주보 미리보기", "주보 확인" | Preview current bulletin draft | Read `bulletins/` latest file |
| "주보 항목 수정", "설교 제목 변경" | Update bulletin data | Edit `data/bulletin-data.yaml` |
| "주보 발행 이력", "지난 주보" | View bulletin history | Read `data/bulletin-data.yaml` generation_history |
| "예배 순서 만들어줘" | Generate worship order sheet | `/generate-bulletin` (worship order mode) |

### Newcomer Commands (새신자)

| Korean Command Pattern | System Action | Route |
|----------------------|---------------|-------|
| "새신자 등록", "새가족 등록" | Register new visitor | Newcomer pipeline Step 1-3 |
| "새신자 현황", "새가족 현황" | Show newcomer status dashboard | Read `data/newcomers.yaml` with stage summary |
| "새신자 단계 변경", "단계 진행" | Advance newcomer journey stage | Newcomer pipeline Step 5 |
| "환영 메시지 작성" | Generate welcome message | Newcomer pipeline Step 4 |
| "재방문 확인", "2주 체크" | Check for overdue follow-ups | Filter newcomers past 14-day mark |
| "정착 처리", "교인 전환" | Process settlement to member | Newcomer pipeline Step 6 |

### Member Commands (교인)

| Korean Command Pattern | System Action | Route |
|----------------------|---------------|-------|
| "교인 검색 [이름]", "교인 찾기" | Search member by name | Read `data/members.yaml` filter by name |
| "교인 등록", "새 교인 추가" | Register new member | member-manager registration protocol |
| "교인 정보 수정", "연락처 변경" | Update member info | member-manager update protocol |
| "이명 처리", "이명 입/출" | Process transfer | member-manager transfer protocol |
| "생일 축하 대상", "이번 주 생일" | Birthday members query | member-manager birthday query |
| "결혼기념일 대상" | Anniversary members query | member-manager anniversary query |
| "교인 통계", "교인 현황" | Member statistics | Read `data/members.yaml` _stats |
| "가족 연결", "가족 등록" | Link family members | member-manager family linking |

### Finance Commands (재정)

| Korean Command Pattern | System Action | Route |
|----------------------|---------------|-------|
| "재정 보고서", "이번 달 재정" | Generate monthly finance report | `/generate-finance-report` workflow |
| "헌금 내역", "헌금 현황" | View offering records | Read `data/finance.yaml` offerings |
| "지출 내역", "지출 현황" | View expense records | Read `data/finance.yaml` expenses |
| "예산 현황", "예산 집행률" | Budget status | Read `data/finance.yaml` budget |
| "기부금 영수증 발행" | Issue donation receipt | finance-recorder receipt mode |

### Schedule Commands (일정)

| Korean Command Pattern | System Action | Route |
|----------------------|---------------|-------|
| "이번 주 일정", "금주 일정" | Show this week's schedule | Read `data/schedule.yaml` filter by date |
| "예배 시간", "예배 일정" | Show service schedule | Read `data/schedule.yaml` services |
| "행사 등록", "일정 추가" | Add event | schedule-manager add event |
| "시설 예약", "장소 예약" | Book facility | schedule-manager facility booking |

### Document Commands (문서)

| Korean Command Pattern | System Action | Route |
|----------------------|---------------|-------|
| "증명서 발급", "재직 증명" | Generate certificate | document-generator certificate mode |
| "이명증서 발급" | Generate transfer certificate | document-generator transfer-cert mode |
| "공문 작성" | Generate official letter | document-generator letter mode |
| "당회 결의문 작성" | Generate session resolution | document-generator resolution mode |
| "회의록 작성" | Generate meeting minutes | document-generator minutes mode |

### Data Import Commands (데이터 입력)

| Korean Command Pattern | System Action | Route |
|----------------------|---------------|-------|
| "파일 가져오기", "데이터 입력" | Process inbox files | inbox_parser.py pipeline |
| "엑셀 가져오기" | Import Excel file | Tier A parser |
| "사진 분석", "이미지 업로드" | Analyze image | Tier C parser |
| "확인 대기", "승인 대기" | Show pending confirmations | hitl_confirmation.py list mode |

### System Commands (시스템)

| Korean Command Pattern | System Action | Route |
|----------------------|---------------|-------|
| "데이터 검증", "유효성 검사" | Run all P1 validators | Run 5 validate_*.py scripts |
| "시스템 상태", "상태 확인" | System health check | Read state.yaml + check data files |
| "도움말", "사용법" | Show help | Display available commands |
| "용어 사전", "용어 검색" | Search glossary | Read `data/church-glossary.yaml` |

## Glossary Integration

This skill uses `data/church-glossary.yaml` for Korean church term normalization:

```
Korean Input → Glossary Lookup → Normalized System Term

Examples:
  "집사 김철수" → role: "deacon", name: "김철수"
  "십일조 내역" → offering_type: "tithe"
  "청년부 소속 교인" → department: "청년부"
  "구역장 변경" → role: "cell_group_leader"
```

The glossary covers 50+ terms across categories:
- **Roles** (직분): 목사, 장로, 집사, 권사, 성도, 구역장
- **Governance** (치리): 당회, 제직회, 공동의회, 노회
- **Worship** (예배): 찬양, 기도, 봉헌, 축도, 주보
- **Finance** (재정): 십일조, 감사헌금, 건축헌금, 선교헌금
- **Sacraments** (성례): 세례, 유아세례, 입교, 성찬식
- **Newcomer** (새신자): 방문자, 등록, 정착, 목양
- **Documents** (문서): 이명증서, 기부금영수증, 증명서

## Error Handling

When a command is not recognized, do NOT just print a list — instead, **route to the `/start` interactive menu** so the user can choose from options:

1. Briefly acknowledge: "말씀하신 내용을 더 잘 도와드리기 위해 메뉴를 보여드리겠습니다."
2. Execute the `/start` command flow (read state.yaml → show status → AskUserQuestion menu)
3. This ensures beginners always land in a guided experience, never a dead end.

If the `/start` command is not available for any reason, fall back to this static help:

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

## Routing Priority

The intent matching follows this priority order:

1. **Startup/Menu patterns** → `/start` interactive menu (highest priority)
2. **Specific category commands** → Direct workflow routing (e.g., "주보 만들어줘" → `/generate-bulletin`)
3. **Ambiguous or greeting-like input** → `/start` interactive menu (catch-all)

This ensures beginner users who type vague requests like "뭐 하면 되지?" or just "안녕" are guided to the interactive menu rather than receiving an error.

## Context-Aware Routing

The skill reads `state.yaml` to determine:
1. Which workflows are available and their current status
2. Current step in any active workflow (avoid interrupting in-progress work)
3. Autopilot mode status (adjust confirmation prompts accordingly)

It also checks data file states:
- If `data/bulletin-data.yaml` has a current week's bulletin, offer preview rather than regeneration
- If `data/newcomers.yaml` has pending follow-ups past 14 days, proactively alert
- If `data/finance.yaml` monthly summary is missing for past month, suggest generating

## Response Style

- **Language**: Korean (this is the user-facing interface)
- **Tone**: Friendly, respectful, professional (존댓말)
- **Format**: Brief confirmation + action summary + next steps
- **Honorifics**: Use appropriate Korean church honorifics (목사님, 장로님)

Example interaction:

```
사용자: 이번 주 주보 만들어줘

시스템: 이번 주 주보를 생성합니다.
  📅 날짜: 2026년 3월 1일 (주일)
  📖 말씀: "두려움을 넘어선 믿음" (요한복음 6:16-21)
  📋 예배 순서: 10개 항목 확인됨
  🎂 생일 축하: 이영희 권사 (3/2)

주보 생성을 시작할까요? [확인/취소]
```

## Available Workflows

| Workflow | Trigger Command | Status |
|----------|----------------|--------|
| Weekly Bulletin | `/generate-bulletin` | Available |
| Newcomer Pipeline | (event-driven) | Available |
| Monthly Finance Report | `/generate-finance-report` | Available |
| Document Generation | (ad-hoc) | Available |
| Schedule Management | (ad-hoc) | Available |

## Inherited DNA

This skill inherits from the parent AgenticWorkflow genome:
- **Quality Absolutism**: Accurate command interpretation — no misrouting
- **SOT Pattern**: Reads state.yaml for context-aware routing
- **Safety Hooks**: Finance commands always require human confirmation
- **Coding Anchor Points (CAP)**: CAP-2 (simplicity) — direct intent mapping without unnecessary abstraction

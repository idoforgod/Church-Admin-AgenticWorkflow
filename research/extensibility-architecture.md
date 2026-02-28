# 확장성 아키텍처 연구: 교회 행정 AI Agentic Workflow Automation System

**작성자**: 확장성 아키텍처 연구원
**작성일**: 2026-02-27
**기반**: 코드베이스 직접 분석 (CLAUDE.md, soul.md, workflow-generator SKILL.md, .claude/agents/, .claude/settings.json)

---

## 1. 이 코드베이스의 확장성 메커니즘 분석

### 1.1 핵심 발견: "부모-자식" 확장 패턴

코드베이스를 직접 읽은 결과, 이 시스템의 확장성은 "새 기능을 기존 코드에 끼워 넣는" 방식이 아니라 **"부모 유기체가 자식 시스템을 낳는"** 생물학적 분화 모델로 설계되어 있다.

`soul.md §0`에서 이 철학을 명시적으로 선언한다:

> "줄기세포가 근육 세포로, 신경 세포로, 혈액 세포로 분화하듯 — 이 코드베이스는 연구 자동화 시스템으로, 콘텐츠 생산 파이프라인으로, 데이터 분석 워크플로우로, 소프트웨어 개발 자동화로 — 어떤 것으로든 분화한다."

**교회 행정 시스템에 대한 함의**: "봉사자 배정"이나 "소그룹 관리"는 새로운 코드 라인이 아니다. **새로운 자식 워크플로우**이며, 부모의 전체 DNA(검증, SOT 패턴, 4계층 품질보장)를 자동으로 상속받는다.

### 1.2 workflow-generator 스킬 — 기능 추가 엔진

**위치**: `/Users/cys/Desktop/AIagentsAutomation/Church-Admin-AgenticWorkflow/.claude/skills/workflow-generator/SKILL.md`

이 스킬이 기능 추가의 핵심 엔진이다. SKILL.md를 직접 읽은 결과:

```
사용자가 "워크플로우 만들어줘", "자동화 파이프라인 설계", "작업 흐름 정의" 등을
요청할 때 사용. 대화를 통해 사용자의 의도를 파악하고,
Research → Planning → Implementation 3단계 구조의 workflow.md를 생성.
```

**기능 추가 엔진으로서의 workflow-generator 활용 흐름:**

```
사용자: "봉사자 배정 기능도 넣고 싶어요"
    ↓
workflow-generator 스킬 활성화
    ↓
케이스 판별: 아이디어만 있으면 Case 1 (대화형), 문서 있으면 Case 2 (문서 분석)
    ↓
3개 핵심 질문으로 요구사항 수집:
  1. "어떤 결과물을 만들고 싶으신가요?" → 봉사 배정표
  2. "해결해야 할 문제는?" → 매주 수작업 배정의 부담
  3. "주요 입력 소스는?" → 교인 명부 + 봉사 가능 일정
    ↓
Research → Planning → Implementation 구조로 workflow.md 자동 생성
    ↓
Inherited DNA 섹션에 부모 게놈 자동 내장
```

**핵심 결론**: 사용자가 "이런 기능 추가해줘"라고 하면, workflow-generator가 **표준화된 워크플로우를 자동 생성**하며, 품질 검증(4계층 QA)·SOT 패턴·안전 훅이 자동으로 포함된다. 개발자가 수동으로 품질 인프라를 다시 설계할 필요가 없다.

### 1.3 Sub-agent 시스템 — 전문가 추가 패턴

**위치**: `/Users/cys/Desktop/AIagentsAutomation/Church-Admin-AgenticWorkflow/.claude/agents/`

현재 3개의 전문 에이전트가 존재한다:
- `reviewer.md` — 적대적 코드/산출물 리뷰어 (Enhanced L2 품질 계층)
- `translator.md` — 영한 번역 전문 에이전트 (glossary 기반 용어 일관성)
- `fact-checker.md` — 적대적 사실 검증 에이전트

**새 에이전트 추가 패턴** (reviewer.md frontmatter 분석):

```yaml
---
name: [고유 식별자]
description: [자동 위임 트리거 설명]  # Claude Code가 자동으로 이 에이전트를 선택하는 기준
model: opus                           # 품질 기준으로 선택 (절대 기준 1)
tools: [허용 도구]
maxTurns: 25
---
```

**교회 행정 특화 에이전트 예시**:
- `member-data-analyst.md` — 교인 데이터 분석 전문
- `schedule-optimizer.md` — 봉사 일정 최적화 전문
- `finance-reporter.md` — 재정 보고서 생성 전문
- `newsletter-writer.md` — 교회 소식지 작성 전문

각 에이전트는 `reviewer.md`처럼 **Inherited DNA 조항**을 내장하여 품질 절대 기준을 자동 상속한다.

### 1.4 Hooks 시스템 — 검증/자동화 확장 패턴

**위치**: `/Users/cys/Desktop/AIagentsAutomation/Church-Admin-AgenticWorkflow/.claude/settings.json`

현재 9개 Hook 이벤트가 `.claude/settings.json`에 정의되어 있다:

```json
"Stop", "PostToolUse", "PreCompact", "SessionStart", "PreToolUse", "SessionEnd", "Setup"
```

**새 기능을 위한 Hook 확장 방법**:

1. **새 검증 Hook 추가** (예: 봉사 배정 중복 검증):
```json
{
  "PreToolUse": [{
    "matcher": "Write",
    "hooks": [{
      "type": "command",
      "command": "python3 church-admin/hooks/validate_volunteer_assignment.py"
    }]
  }]
}
```

2. **새 데이터 품질 Hook 추가** (예: 헌금 데이터 정합성 검증):
```json
{
  "PostToolUse": [{
    "matcher": "Edit|Write",
    "hooks": [{
      "type": "command",
      "command": "python3 church-admin/hooks/validate_finance_data.py"
    }]
  }]
}
```

**Hook 확장의 핵심 규칙**: `if test -f; then; fi` 패턴 사용으로 Hook 스크립트 부재 시 안전하게 건너뜀. exit code 2로 차단, 0으로 경고 전용 동작.

### 1.5 Skills 디렉터리 — 재사용 로직 추가 패턴

현재 2개 스킬:
- `workflow-generator/` — 워크플로우 설계·생성
- `doctoral-writing/` — 박사급 학술 글쓰기

**교회 행정 특화 스킬 추가 예시**:
```
.claude/skills/
├── workflow-generator/      # 기존 (재사용)
├── doctoral-writing/        # 기존 (재사용)
├── church-data-processor/   # 신규: 교인 데이터 CSV 정제 로직
├── bulletin-formatter/      # 신규: 주보 포맷팅 규칙 + 이미지 처리
└── finance-analyzer/        # 신규: 재정 데이터 분석 패턴
```

각 스킬은 `SKILL.md`(WHY/진입점) + `references/`(HOW/WHAT) 구조를 따른다.

---

## 2. 기능 추가 시나리오별 구현 경로

### 시나리오 A: "봉사자 배정 기능을 추가하고 싶어요"

**구현 경로: 새 workflow.md + 새 Sub-agent + 공유 데이터 참조**

```
church-admin/
├── workflows/
│   ├── weekly-bulletin.md      # 기존
│   └── volunteer-assignment.md # 신규 ← workflow-generator로 자동 생성
├── .claude/agents/
│   ├── reviewer.md             # 기존 (상속)
│   └── schedule-optimizer.md  # 신규: 봉사 배정 최적화 전문
└── data/
    ├── members.yaml            # 공유 (봉사자 명부 — 교인 명부에서 참조)
    └── volunteer-schedule.yaml # 신규 SOT
```

**`volunteer-assignment.md` 워크플로우 구조**:

```markdown
## Research
### 1. 교인 봉사 가능 현황 수집
- Pre-processing: python3 scripts/extract_available_volunteers.py
  → members.yaml에서 봉사 가능 플래그 + 최근 배정 이력 필터링
- Agent: @schedule-optimizer
- Verification:
  - [ ] 모든 봉사 부서(찬양/안내/주차/청소년부)에 대해 가능자 목록 존재
  - [ ] 각 봉사자에 최근 3개월 배정 이력 포함 (균등 배분 계산 필요)
- Output: volunteer-availability.md

### 2. (human) 특별 요청 사항 확인
- Action: 특별 사정 (장기 출장, 결혼 등) 입력
- Command: /review-special-requests

## Planning
### 3. 최적 배정안 생성
- Agent: @schedule-optimizer
- Verification:
  - [ ] 모든 봉사 시간대(1부/2부/3부)에 최소 인원 충족
  - [ ] 동일인 동일 주 중복 배정 없음
  - [ ] Step 1 가용 목록과 교차 검증 완료 (source: Step 1)
- Output: assignment-draft.md

## Implementation
### 4. 배정 통보 메시지 생성
- Agent: @newsletter-writer (재사용)
- Output: volunteer-notification.yaml (카카오톡 발송용)
```

**데이터 공유 패턴**: `members.yaml` (교인 명부 SOT)를 봉사자 배정 워크플로우가 **읽기 전용**으로 참조한다. 봉사 결과는 별도 `volunteer-schedule.yaml` SOT에 기록되며, 두 SOT 간 쓰기 충돌이 없다.

---

### 시나리오 B: "소그룹 출석 관리를 추가하고 싶어요"

**구현 경로: 별도 독립 workflow.md + 공유 members.yaml 참조**

소그룹 출석은 주보 워크플로우와 완전히 독립적이므로 **별도 워크플로우**가 적합하다.

```
church-admin/
├── workflows/
│   ├── weekly-bulletin.md         # 기존
│   ├── volunteer-assignment.md    # 시나리오 A
│   └── small-group-attendance.md  # 신규 ← 독립 워크플로우
├── .claude/agents/
│   └── attendance-analyzer.md    # 신규: 출석 패턴 분석 전문
└── data/
    ├── members.yaml               # 공유 SOT (교인 명부)
    ├── small-groups.yaml          # 신규 SOT (소그룹 구조)
    └── attendance-log.yaml        # 신규 SOT (출석 기록)
```

**`small-group-attendance.md` 핵심 단계**:

```markdown
## Research
### 1. 소그룹 출석 현황 파싱
- Pre-processing: python3 scripts/parse_attendance_input.py
  → 리더 제출 카카오톡 메시지 / 구글폼 응답 → 구조화 YAML
- Agent: @attendance-analyzer
- Verification:
  - [ ] 전체 소그룹 수 대비 응답 수 100% (미응답 소그룹 명시)
  - [ ] 각 소그룹에 날짜·참석자 목록·결석 사유 포함
- Output: attendance-raw.yaml

## Implementation
### 4. 월간 출석 리포트 생성
- Agent: @attendance-analyzer
- Verification:
  - [ ] 각 소그룹의 출석률 추이 (최근 3개월 비교) 포함
  - [ ] 3회 연속 결석자 목록 별도 표시 (목양 알림 대상)
- Review: @fact-checker
- Output: monthly-attendance-report.md
- Translation: @translator → monthly-attendance-report.ko.md
```

**기존 워크플로우와의 데이터 연결**: 소그룹 출석 리포트의 "3회 연속 결석자" 목록은 봉사자 배정 워크플로우가 배정 시 참조할 수 있다 (`[trace:step-attendance-1]` 마커 활용).

---

### 시나리오 C: "교회 소식지 자동 발행을 추가하고 싶어요"

**구현 경로: 주보 워크플로우 변형 vs 완전 새 워크플로우 판단 기준**

주보(bulletin)와 소식지(newsletter)는 목적이 다르다:
- 주보: 당주 예배 정보 (매주 반복, 구조 고정)
- 소식지: 월간 교회 소식·스토리 (비정기, 콘텐츠 다양)

**결론: 완전 새 워크플로우**. 단, `@newsletter-writer` 에이전트는 공유 재사용한다.

```
church-admin/
├── workflows/
│   ├── weekly-bulletin.md         # 기존
│   └── monthly-newsletter.md      # 신규 ← workflow-generator로 생성
├── .claude/agents/
│   ├── newsletter-writer.md       # 신규: 콘텐츠 작성 + 이미지 배치 전문
│   └── fact-checker.md            # 기존 (상속) — 사실 검증 재사용
└── data/
    ├── church-events.yaml          # 공유 (행사 캘린더)
    └── newsletter-archive/         # 신규: 과거 소식지 아카이브
```

**`monthly-newsletter.md` 특징적 단계**:

```markdown
## Research
### 1. 이번 달 교회 소식 수집
- Pre-processing: python3 scripts/collect_church_news.py
  → 구글 캘린더 MCP + 목사/부서장 제출 소식 → 구조화
- Agent: @newsletter-writer
- MCP: google-calendar-mcp

### 3. (human) 소식 선별 및 우선순위 결정
- Action: 소식 목록에서 소식지 포함 항목 선택, 스토리 각도 제시
- Command: /select-newsletter-stories

## Implementation
### 5. 소식지 최종본 생성
- Agent: @newsletter-writer
- Review: @reviewer  # 콘텐츠 품질 + 완전성 검증
- Translation: @translator → monthly-newsletter.ko.md
```

---

### 시나리오 D: "재정 분석 차트를 자동으로 만들고 싶어요"

**구현 경로: 기존 재정 데이터 SOT + 새 시각화 단계 추가**

재정 데이터가 이미 `finance.yaml` SOT로 관리된다고 가정하면, **기존 재정 워크플로우에 단계를 추가**하거나 **별도 분석 워크플로우를 생성**하는 두 가지 경로가 있다.

**판단 기준**: 재정 입력(데이터 수집)과 시각화 분석(차트 생성)이 항상 같이 실행되면 기존 워크플로우에 단계 추가. 시각화를 독립적으로 실행해야 하면 별도 워크플로우.

```
church-admin/
├── workflows/
│   ├── finance-management.md     # 기존 (데이터 입력/관리)
│   └── finance-analysis.md       # 신규 ← 분석·시각화 전용
├── .claude/agents/
│   └── finance-analyst.md        # 신규: 차트 생성 + 트렌드 분석 전문
└── data/
    └── finance.yaml              # 공유 SOT (읽기 전용으로 참조)
```

**`finance-analysis.md` 특징**:

```markdown
## Research
### 1. 재정 데이터 집계
- Pre-processing: python3 scripts/aggregate_finance_data.py
  → finance.yaml에서 기간별 헌금·지출 집계 → pandas DataFrame 생성
- Agent: @finance-analyst
- Verification:
  - [ ] 분석 기간(월/분기/연) 전체 데이터 포함
  - [ ] 항목별 합계가 총계와 일치 (산술 검증)

## Implementation
### 4. 차트 자동 생성
- Pre-processing: python3 scripts/generate_charts.py
  → matplotlib/plotly로 PNG + HTML 인터랙티브 차트 생성
- Agent: @finance-analyst
- Verification:
  - [ ] 헌금 추이(월별), 항목별 지출 비율(파이차트), 예산 대비 실적 3종 차트 모두 생성
  - [ ] 각 차트에 날짜 레이블 및 범례 포함
- Output: finance-charts/ (PNG 3종 + HTML 인터랙티브)
- Review: @fact-checker  # 숫자 정확성 검증
```

---

## 3. 플러그인/모듈 아키텍처 설계

### 3.1 표준화된 기능 추가 패턴 (Feature Module Pattern)

코드베이스 분석 결과, 기능 추가는 **3-레이어 모듈 패턴**으로 표준화할 수 있다:

```
Layer 1 — 워크플로우 (설계도): workflow.md
    ↓ 정의
Layer 2 — 에이전트 (실행자): .claude/agents/[specialist].md
    ↓ 사용
Layer 3 — 데이터 (상태): data/[domain].yaml (SOT)
```

**각 기능 모듈의 구성 요소**:

```
church-admin/
├── workflows/
│   └── [feature-name].md          # 필수: Research→Planning→Implementation 구조
├── .claude/agents/
│   └── [specialist].md            # 선택: 도메인 특화 전문 에이전트
├── .claude/hooks/scripts/
│   └── validate_[feature].py      # 선택: 기능별 P1 결정론적 검증
├── .claude/commands/
│   └── [feature-command].md       # 선택: 사람 개입 slash command
└── data/
    └── [feature]-state.yaml       # 필수: 기능별 독립 SOT
```

### 3.2 기능 추가 표준 절차 (Feature Addition Protocol)

사용자가 새 기능을 요청할 때 표준화된 5단계 절차:

```
Step 1 — 분류 판단
  Q: 기존 워크플로우의 새 단계인가? vs 완전 독립 기능인가?
  판단 기준:
    - 기존 워크플로우와 동일 트리거(매주 실행) → 기존에 단계 추가
    - 독립 트리거(월간/온디맨드) → 새 workflow.md 생성

Step 2 — 데이터 의존성 매핑
  Q: 어떤 기존 SOT 데이터를 읽어야 하는가?
  → members.yaml, finance.yaml 등 공유 SOT 목록 확인
  → 새 기능 전용 SOT 파일 설계

Step 3 — 에이전트 재사용 판단
  Q: 기존 에이전트(reviewer, translator, fact-checker)로 충분한가?
  → 기존 에이전트 조합으로 가능 → 재사용
  → 새로운 전문 역량 필요 → 새 .claude/agents/[specialist].md 생성

Step 4 — workflow-generator로 workflow.md 자동 생성
  트리거: "워크플로우 만들어줘" 또는 "자동화 파이프라인 설계해줘"
  → 대화로 요구사항 수집 → Inherited DNA 포함 workflow.md 자동 생성
  → DNA Inheritance P1 검증: validate_workflow.py 실행

Step 5 — Hook 등록 (선택)
  새 기능에 검증 Hook이 필요하면 .claude/settings.json에 추가
  → if test -f 패턴으로 안전하게 등록
```

### 3.3 "기능 추가 워크플로우" 자동화

workflow-generator 스킬 자체를 "기능 추가 도구"로 활용하는 흐름:

```
사용자: "소그룹 출석 관리 기능 추가해줘"
    ↓
Claude: workflow-generator 스킬 활성화
    ↓ (Case 1: 아이디어만 있는 경우)
    Q1: "출석 데이터를 어떻게 수집하실 건가요?"
        A. 카카오톡 메시지 → 수동 입력
        B. 구글폼 응답 → 자동 파싱
        C. 전용 앱 → API 연동
    Q2: "산출물이 무엇이면 좋겠나요?"
        A. 주간 출석 현황표
        B. 월간 리포트 (PDF)
        C. 목자 별 출석 알림
    Q3: "어느 단계에서 사람 검토가 필요한가요?"
    Q4: "기존 교인 명부 데이터(members.yaml)와 연결이 필요한가요?"
    ↓
    workflow.md 자동 생성 (Inherited DNA 포함)
    ↓
    DNA Inheritance P1 검증: python3 validate_workflow.py
    ↓
    사용자: "실행해줘" → Orchestrator가 workflow.md 기준으로 실행
```

---

## 4. 확장 시 데이터 호환성

### 4.1 공유 SOT 참조 패턴

새 기능이 기존 데이터를 참조할 때의 표준 패턴:

```
                    ┌─────────────────────────────────┐
                    │         공유 SOT 레이어           │
                    │                                  │
                    │  members.yaml (교인 명부)         │ ← 단일 쓰기 지점
                    │  finance.yaml (재정 데이터)        │   (Orchestrator만)
                    │  church-events.yaml (행사 캘린더)  │
                    └─────────────────────────────────┘
                              ↑ 읽기 전용
          ┌───────────────────┼───────────────────┐
          │                   │                   │
    ┌──────────┐       ┌──────────┐       ┌──────────┐
    │ bulletin  │       │volunteer │       │attendance│
    │ workflow  │       │ workflow │       │ workflow │
    │ state.yaml│       │ state.yaml│       │ state.yaml│
    └──────────┘       └──────────┘       └──────────┘
    (기능별 독립 SOT — 각자 단일 쓰기 지점 보유)
```

**규칙**:
1. **공유 SOT (members.yaml 등)**: Orchestrator만 쓰기, 모든 워크플로우가 읽기 전용으로 참조
2. **기능별 SOT (volunteer-state.yaml 등)**: 해당 워크플로우의 Orchestrator만 쓰기
3. **교차 워크플로우 데이터**: 공유 SOT를 통해서만 교환. 직접 참조 금지.

### 4.2 스키마 확장 시 하위 호환성 규칙

기존 `members.yaml`에 새 필드를 추가할 때:

```yaml
# members.yaml — 기존 스키마
members:
  - id: "M001"
    name: "홍길동"
    phone: "010-1234-5678"
    # 기존 필드

# members.yaml — 봉사자 기능 추가 후 확장
members:
  - id: "M001"
    name: "홍길동"
    phone: "010-1234-5678"
    # 기존 필드 (변경 없음)
    volunteer:           # 신규 추가 (선택적 필드)
      available: true
      departments: ["찬양", "안내"]
      last_assigned: "2026-02-16"
```

**하위 호환성 보장 원칙**:
- 기존 필드 **삭제 또는 이름 변경 금지**
- 새 필드는 항상 **선택적(optional)** — 기존 워크플로우는 새 필드를 무시
- Pre-processing 스크립트가 필드 존재 여부를 검사 후 처리:
  ```python
  volunteer_info = member.get('volunteer', {})  # 없으면 빈 딕셔너리 반환
  ```

### 4.3 워크플로우 간 데이터 공유 패턴

**Cross-Step Traceability 마커를 워크플로우 간에도 적용**:

```markdown
# volunteer-assignment.md의 Research 단계 산출물에서

## 배정 불가 대상자 (3회 이상 연속 결석)
[trace:attendance-workflow:step-4-monthly-report]
← 소그룹 출석 워크플로우 Step 4 리포트에서 추출된 데이터
- 김○○: 소그룹 4주 연속 결석 → 봉사 배정 보류
- 이○○: 소그룹 3주 연속 결석 → 담당 목사 상담 후 결정
```

이를 통해 워크플로우 간 데이터 출처가 명시적으로 추적된다.

---

## 5. 구체적 아키텍처 제안

### 5.1 교회 행정 시스템 디렉터리 구조

```
church-admin/
├── workflow.md                    # 메인 (현재 설계 중)
│
├── workflows/                     # 기능별 독립 워크플로우 ← 핵심 확장 지점
│   ├── weekly-bulletin.md         # 주보 생성 (기본 기능)
│   ├── volunteer-assignment.md    # 봉사자 배정 (시나리오 A)
│   ├── small-group-attendance.md  # 소그룹 출석 (시나리오 B)
│   ├── monthly-newsletter.md      # 소식지 발행 (시나리오 C)
│   ├── finance-analysis.md        # 재정 분석 (시나리오 D)
│   └── [future-feature].md        # 미래 기능 추가 지점
│
├── data/                          # 공유 데이터 (SOT 계층)
│   ├── members.yaml               # 교인 명부 SOT (마스터)
│   ├── small-groups.yaml          # 소그룹 구조 SOT
│   ├── church-events.yaml         # 행사 캘린더 SOT
│   ├── finance.yaml               # 재정 데이터 SOT
│   └── [domain].yaml              # 새 도메인 추가 시
│
├── scripts/                       # 전처리/후처리 Python 스크립트
│   ├── extract_available_volunteers.py
│   ├── parse_attendance_input.py
│   ├── aggregate_finance_data.py
│   ├── generate_charts.py
│   └── [feature-script].py        # 기능 추가 시 스크립트 추가
│
├── .claude/
│   ├── agents/                    # 전문 에이전트
│   │   ├── reviewer.md            # 기존 (상속)
│   │   ├── translator.md          # 기존 (상속)
│   │   ├── fact-checker.md        # 기존 (상속)
│   │   ├── schedule-optimizer.md  # 신규: 봉사 배정
│   │   ├── attendance-analyzer.md # 신규: 출석 분석
│   │   ├── newsletter-writer.md   # 신규: 소식지 작성
│   │   ├── finance-analyst.md     # 신규: 재정 분석
│   │   └── [specialist].md        # 미래 에이전트 추가 지점
│   │
│   ├── commands/                  # Slash Commands (사람 개입 지점)
│   │   ├── review-bulletin.md     # 주보 검토
│   │   ├── review-special-requests.md  # 봉사 특별 요청
│   │   ├── select-newsletter-stories.md # 소식지 기사 선정
│   │   └── [feature-command].md   # 미래 명령 추가 지점
│   │
│   ├── hooks/scripts/             # 결정론적 검증 스크립트
│   │   ├── [부모 시스템 hooks 상속]
│   │   ├── validate_volunteer_assignment.py  # 신규: 배정 중복 검증
│   │   ├── validate_finance_data.py          # 신규: 재정 정합성 검증
│   │   └── validate_[feature].py             # 미래 검증 추가 지점
│   │
│   ├── skills/
│   │   ├── workflow-generator/    # 기존 (기능 추가 엔진)
│   │   └── church-data-processor/ # 신규: 교회 데이터 정제 패턴
│   │
│   ├── settings.json              # Hook 등록 (기능 추가 시 갱신)
│   └── state.yaml                 # 메인 워크플로우 SOT
│
├── verification-logs/             # L1 검증 결과 (런타임)
├── pacs-logs/                     # pACS 자체 평가 (런타임)
├── review-logs/                   # Adversarial Review 결과 (런타임)
├── autopilot-logs/                # 자동 승인 결정 로그 (런타임)
└── translations/                  # 번역 산출물 + glossary.yaml
```

### 5.2 기능 추가 의사결정 트리

```
새 기능 요청 수신
    │
    ├─ 기존 워크플로우 확장?
    │   ├─ YES → 기존 workflow.md에 단계 추가
    │   │         CCP 3단계 수행 후 수정
    │   └─ NO ↓
    │
    ├─ 새 전문 에이전트 필요?
    │   ├─ YES → .claude/agents/[specialist].md 신규 생성
    │   │         Inherited DNA 조항 필수 포함
    │   └─ NO → 기존 에이전트(reviewer, translator 등) 재사용
    │
    ├─ 새 데이터 SOT 필요?
    │   ├─ YES → data/[domain].yaml 신규 생성
    │   │         공유 SOT(members.yaml 등) 참조 시 읽기 전용 패턴 설계
    │   └─ NO → 기존 공유 SOT 읽기 전용 참조
    │
    ├─ workflow-generator로 workflow.md 자동 생성
    │   → validate_workflow.py로 DNA Inheritance P1 검증
    │
    └─ Hook 검증 필요?
        ├─ YES → .claude/hooks/scripts/validate_[feature].py 신규 생성
        │         settings.json에 등록 (if test -f 패턴)
        └─ NO → 기존 Hook 인프라로 충분
```

### 5.3 확장성 보장 핵심 원칙 요약

코드베이스 분석에서 도출한 이 시스템의 확장성을 보장하는 4가지 핵심 설계 원칙:

| 원칙 | 메커니즘 | 확장 시 이점 |
|------|---------|------------|
| **DNA 유전** | 모든 workflow.md에 Inherited DNA 섹션 필수 | 새 기능이 자동으로 4계층 품질보장 상속 |
| **SOT 분리** | 기능별 독립 SOT + 공유 SOT 읽기 전용 참조 | 기능 추가가 기존 데이터를 오염시키지 않음 |
| **에이전트 조합** | 기존 에이전트 재사용 + 필요 시 신규 추가 | 전문성 축적 — 새 기능이 기존 품질 인프라 활용 |
| **Hook 격리** | `if test -f` 패턴으로 Hook 선택적 활성화 | Hook 추가/제거가 기존 시스템에 영향 없음 |

### 5.4 IT 자원봉사자를 위한 기능 추가 가이드

교회 IT 자원봉사자(비전문 개발자)가 새 기능을 추가할 때의 최소 절차:

**방법 1: Claude에게 자연어로 요청 (권장)**
```
사용자: "소그룹 출석 관리 워크플로우 만들어줘.
         매주 리더들이 카카오톡으로 보내는 출석 명단을
         자동으로 취합해서 월별 리포트를 만들고 싶어."

→ workflow-generator 스킬이 자동으로 workflow.md 생성
→ DNA Inheritance 자동 포함
→ 바로 실행 가능한 상태
```

**방법 2: 기존 workflow.md를 템플릿으로 복사**
```
1. workflows/weekly-bulletin.md를 복사
2. 새 기능명으로 파일명 변경
3. 단계별 Task/Output/Verification 내용 교체
4. Inherited DNA 섹션은 변경하지 않음 (자동 상속)
5. validate_workflow.py로 검증
```

---

## 6. 결론: 이 시스템의 확장성 강점과 제약

### 강점

1. **자기 복제적 품질 보장**: 새 기능이 자동으로 4계층 QA(L0-L1-L1.5-L2)를 상속받는다. 품질 인프라를 매번 새로 설계할 필요가 없다.

2. **자연어 기반 기능 추가**: workflow-generator 스킬 덕분에 IT 지식 없이도 "이런 기능 추가해줘"라는 자연어 요청만으로 완전한 워크플로우가 생성된다.

3. **데이터 격리 원칙**: 각 기능이 독립 SOT를 가지므로, 새 기능 추가가 기존 기능을 깨뜨릴 위험이 구조적으로 차단된다.

4. **에이전트 재사용**: reviewer, translator, fact-checker는 모든 워크플로우에서 재사용된다. 새 기능은 기존 전문 에이전트 역량을 즉시 활용한다.

### 제약 및 고려사항

1. **공유 SOT 쓰기 병목**: members.yaml 같은 공유 SOT는 단일 쓰기 지점 원칙으로 인해 동시 갱신이 불가능하다. 여러 워크플로우가 동시에 교인 데이터를 수정해야 하는 경우 조율 프로토콜이 필요하다.

2. **에이전트 수 증가에 따른 컨텍스트 관리**: 기능이 많아질수록 에이전트 수가 늘어나며, 각 에이전트가 올바른 컨텍스트를 참조하는지 관리가 복잡해진다. Context Injection 패턴(Pattern A/B/C)을 워크플로우 설계 시 명시해야 한다.

3. **데이터 스키마 진화**: members.yaml 스키마가 기능 추가에 따라 점점 커질 수 있다. 정기적인 스키마 검토와 선택적 필드 원칙 준수가 필요하다.

4. **비전문 자원봉사자의 Verification 기준 작성**: workflow.md의 Verification 기준은 "제3자가 참/거짓 판정 가능한 구체적 문장"이어야 한다. 비전문 사용자가 이를 작성하기 어려울 수 있으므로, workflow-generator 스킬이 기준 예시를 제시하는 역할이 중요하다.

---

*이 연구는 AgenticWorkflow 코드베이스의 CLAUDE.md, soul.md, .claude/skills/workflow-generator/SKILL.md, .claude/agents/ 3개 파일, .claude/settings.json을 직접 읽고 분석한 결과입니다.*

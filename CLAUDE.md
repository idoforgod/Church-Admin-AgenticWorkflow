# AgenticWorkflow

Claude Code 기반의 에이전트 워크플로우 자동화 프로젝트.

## 최종 목표

이 코드베이스의 최종 목표는 두 단계로 구성된다:

1. **워크플로우 설계**: 복잡한 작업을 Research → Planning → Implementation 3단계 구조의 `workflow.md`로 설계한다. Sub-agents/Agent Teams/Hooks/Skills/MCP Servers를 조합한 구현 설계를 포함한다.
2. **워크플로우 실행**: 생성된 `workflow.md`를 기준 삼아, 그 안에 정의된 에이전트·스크립트·자동화 구성을 **실제로 구현**한다. 워크플로우 문서는 설계도이고, 최종 산출물은 그 설계도대로 작동하는 실제 시스템이다.

> 워크플로우를 만드는 것은 중간 산출물이다. **워크플로우에 기술된 내용이 실제로 동작하는 것**이 최종 목표다.

### 존재 이유 — DNA 유전

AgenticWorkflow는 그 자체로 완결되는 시스템이 아니다. **또 다른 agentic workflow automation system을 낳는 부모 유기체**다.
`workflow-generator` 스킬이 생산 라인이며, 이 라인에서 태어나는 모든 자식 시스템은 부모의 **전체 게놈**을 구조적으로 내장한다:

- **헌법**: 절대 기준 3개 (품질 > SOT, CCP)
- **구조**: Research → Planning → Implementation 3단계 제약
- **검증**: 4계층 품질 보장 (L0 → L1 → L1.5 → L2) + P1 할루시네이션 봉쇄
- **안전**: Safety Hook + 결정론적 검증
- **기억**: Context Preservation + Knowledge Archive + RLM 패턴
- **비판**: Adversarial Review (Generator-Critic 패턴)
- **투명**: Decision Log + 감사 추적

유전은 선택이 아니라 **구조**다. 자식은 부모의 DNA를 "참고"하는 것이 아니라 **내장**한다. 상세: `soul.md §0`.

## 절대 기준

> 이 프로젝트의 모든 설계·구현·수정 의사결정에 적용되는 최상위 규칙이다.
> 아래의 모든 원칙, 가이드라인, 관례보다 상위에 있다.

### 절대 기준 1: 최종 결과물의 품질

> **속도, 토큰 비용, 작업량, 분량 제한은 완전히 무시한다.**
> 모든 의사결정의 유일한 기준은 **최종 결과물의 품질**이다.
> 단계를 줄여서 빠르게 만드는 것보다, 단계를 늘려서라도 품질을 높이는 방향을 선택한다.

### 절대 기준 2: 단일 파일 SOT + 계층적 메모리 구조

> **단일 파일 SOT(Single Source of Truth) + 계층적 메모리 구조 설계 아래서, 수십 개의 에이전트가 동시에 작동해도 데이터 불일치가 발생하지 않는다.**

설계 함의:
- **상태 관리**: 모든 공유 상태는 단일 파일에 집중. 분산 금지.
- **쓰기 권한**: SOT 파일 쓰기는 Orchestrator/Team Lead만. 나머지는 읽기 전용 + 산출물 파일 생성.
- **충돌 방지**: 병렬 에이전트가 동일 파일을 동시 수정하는 구조 금지.

### 절대 기준 3: 코드 변경 프로토콜 (Code Change Protocol)

> **코드를 작성·수정·추가·삭제하기 전에, 반드시 아래 3단계를 내부적으로 수행한다.**
> 이 프로토콜을 건너뛰는 것은 절대 기준 위반이다.
> 프로토콜은 항상 수행하되, 분석 깊이는 변경의 영향 범위에 비례한다.

**Step 1 — 의도 파악**:
- 변경 목적(버그 수정/기능 추가/리팩토링/성능)과 제약(호환성, 기술 스택)을 1-2문장으로 정의
- 경미한 변경(오타, 주석, 포맷팅)이면 "파급 효과 없음" 확인 후 즉시 실행 가능

**Step 2 — 영향 범위 분석 (Ripple Effect Analysis)**:
- 직접 의존 + 호출 관계 (caller/callee)
- 구조적 관계 (상속, 합성, 참조)
- 데이터 모델/스키마/타입 연쇄 변경
- 테스트, 설정, 문서, API 스펙
- 강결합·샷건 서저리 위험이 있으면 **반드시** 사전 고지 후 사용자와 협의

**Step 3 — 변경 설계 (Change Plan)**:
- 단계별 변경 순서 (어떤 파일/함수부터 → 의존성 전파 → 테스트/문서 정합)
- 결합도 감소 / 응집도 증가 기회가 보이면 함께 제안 (실행은 사용자 승인 후)

**비례성 규칙:**

| 변경 규모 | 적용 깊이 |
|----------|---------|
| 경미 (오타, 주석) | Step 1만 — 파급 효과 없음 확인 |
| 표준 (함수/로직 변경) | 전체 3단계 |
| 대규모 (아키텍처, API) | 전체 3단계 + 사전 사용자 승인 필수 |

**커뮤니케이션 규칙:**
- 불필요하게 장황한 이론 설명은 피하고, 실질적인 코드와 구체적 단계 위주로 설명한다.
- 중요한 설계 선택에는 간단한 이유를 덧붙인다.
- 모호한 부분이 있어도 작업을 회피하지 말고, "합리적인 가정"을 명시한 뒤 최선의 설계를 제안한다.

**코딩 기준점 (CAP):** CCP의 모든 단계는 아래 4가지 태도를 내면화한 상태에서 수행한다:
- **CAP-1**: 코딩 전 사고 — 코드를 읽기 전에 수정 금지. 트레이드오프 표면화. 불명확하면 질문
- **CAP-2**: 단순성 우선 — 최소 코드. 추측성 기능·조기 추상화·불필요 헬퍼 금지
- **CAP-3**: 목표 기반 실행 — 성공 기준 먼저 정의, 구현 후 검증
- **CAP-4**: 외과적 변경 — 요청받은 변경만. 관련 없는 "개선" 금지

> CAP는 CCP 하위이므로, 절대 기준 1(품질)과 충돌 시 품질이 이긴다. 상세: AGENTS.md §2 절대 기준 3.

### 절대 기준 간 우선순위

> **절대 기준 1(품질)이 최상위이다. 절대 기준 2(SOT)와 절대 기준 3(CCP)은 품질을 보장하기 위한 동위 수단이다.**
> 어느 기준이든 절대 기준 1과 충돌하면 품질이 이긴다. SOT와 CCP 모두 품질을 제약하는 **목적**이 아니라, 품질을 보장하기 위한 **수단**이다.

---

## 프로젝트 구조

```
AgenticWorkflow/
├── CLAUDE.md                              ← 이 파일 (Claude Code 전용 지시서)
├── AGENTS.md                              ← 모든 AI 에이전트 공통 지시서 (Hub — 방법론 SOT)
├── GEMINI.md                              ← Gemini CLI 전용 지시서 (Spoke)
├── README.md                              ← 프로젝트 소개
├── AGENTICWORKFLOW-USER-MANUAL.md         ← 이 코드베이스 자체의 사용자 매뉴얼
├── AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md  ← 설계 철학 및 아키텍처 전체 조감도
├── DECISION-LOG.md                        ← 프로젝트 설계 결정 로그 (ADR)
├── COPYRIGHT.md                           ← 저작권
├── soul.md                                ← 프로젝트 영혼 (자식 시스템에 유전되는 DNA 정의)
├── .github/
│   └── copilot-instructions.md            ← GitHub Copilot 전용 지시서 (Spoke)
├── .cursor/
│   └── rules/
│       └── agenticworkflow.mdc            ← Cursor 전용 지시서 (Spoke, alwaysApply)
├── .gemini/
│   └── settings.json                      ← Gemini CLI 설정 (AGENTS.md 추가 로드)
├── .claude/
│   ├── settings.json                      ← Hook 설정 (Setup + SessionEnd)
│   ├── agents/                             ← Sub-agent 정의
│   │   ├── translator.md                  (영→한 번역 전문 에이전트 — glossary 기반 용어 일관성)
│   │   ├── reviewer.md                    (적대적 코드/산출물 리뷰어 — Enhanced L2 품질 계층, 읽기 전용)
│   │   └── fact-checker.md                (적대적 사실 검증 에이전트 — 독립 소스 대비 claim-by-claim 확인)
│   ├── commands/                           ← Slash Commands
│   │   ├── install.md                     (Setup Init 검증 결과 분석 — /install)
│   │   └── maintenance.md                 (Setup Maintenance 건강 검진 — /maintenance)
│   ├── hooks/scripts/                     ← Context Preservation System + Setup Hooks + Safety Hooks
│   │   ├── context_guard.py               (Hook 통합 디스패처 — 4개 이벤트의 단일 진입점)
│   │   ├── _context_lib.py                (공유 라이브러리 — 파싱, 생성, SOT 캡처, Smart Throttling, Autopilot 상태 읽기·검증, ULW 감지, 절삭 상수 중앙화, sot_paths() 경로 통합, 다단계 전환 감지, 결정 품질 태그 정렬, Error Taxonomy 12패턴+Resolution 매칭, Success Patterns(Edit/Write→Bash 성공 시퀀스 추출), IMMORTAL-aware 압축+감사 추적, E5 Guard 중앙화(is_rich_snapshot+update_latest_with_guard), Knowledge Archive 통합(archive_and_index_session — 부분 실패 격리), 경로 태그 추출(extract_path_tags), KI 스키마 검증(_validate_session_facts — RLM 필수 키 보장), SOT 스키마 검증(validate_sot_schema — 워크플로우 state.yaml 구조 무결성 8항목 검증: S1-S6 기본 + S7 pacs 구조(S7a-S7e: dimensions·score·weak_dimension·history·pre_mortem_flag) + S8 active_team 구조(S8a-S8e: name·status·tasks_completed·tasks_pending·completed_summaries)), Quality Gate 상태 추출(_extract_quality_gate_state — pacs/review/verification 로그에서 최신 단계 품질 게이트 상태를 IMMORTAL 스냅샷에 보존), Adversarial Review P1 검증(validate_review_output+parse_review_verdict+calculate_pacs_delta+validate_review_sequence — Enhanced L2 결정론적 검증), Translation P1 검증(validate_translation_output T1-T7 + check_glossary_freshness T8 + verify_pacs_arithmetic T9 범용 + validate_verification_log V1a-V1c), Predictive Debugging P1(aggregate_risk_scores+validate_risk_scores RS1-RS6+_RISK_WEIGHTS 13개 가중치+_RECENCY_DECAY_DAYS 감쇠), Cross-Step Traceability P1 검증(validate_cross_step_traceability CT1-CT5 + _TRACE_MARKER_RE + _HEADING_SLUG_RE), Domain Knowledge Structure P1 검증(validate_domain_knowledge DK1-DK7 + _DKS_REF_RE + _DKS_ID_RE), Abductive Diagnosis Layer(diagnose_failure_context 사전 증거 수집 + validate_diagnosis_log AD1-AD10 사후 검증 + _extract_diagnosis_patterns KA 아카이빙 + Fast-Path FP1-FP3 + 가설 우선순위 H1/H2/H3), 모듈 레벨 regex 컴파일(9개+8개+8개+4개+5개 패턴 — 프로세스당 1회))
│   │   ├── save_context.py                (SessionEnd/PreCompact 저장 엔진)
│   │   ├── restore_context.py             (SessionStart 복원 — RLM 포인터 + 동적 RLM 쿼리 힌트 + Error→Resolution 자동 표면화 + Predictive Debugging 위험 점수 캐시 생성)
│   │   ├── update_work_log.py             (PostToolUse 작업 로그 누적 — Edit|Write|Bash|Task|NotebookEdit|TeamCreate|SendMessage|TaskCreate|TaskUpdate 9개 도구 추적)
│   │   ├── generate_context_summary.py    (Stop 증분 스냅샷 + Knowledge Archive + E5 Guard + Autopilot Decision Log 안전망 + Adversarial Review 누락 감지 + Verification 누락 감지 + Traceability 누락 감지 + DKS 누락 감지 + Diagnosis 누락 감지 + ULW Compliance 안전망)
│   │   ├── diagnose_context.py             (Abductive Diagnosis 사전 분석 독립 스크립트 — 품질 게이트 FAIL 시 증거 번들 수집, JSON 출력, Hook 아님 — Orchestrator가 수동 호출)
│   │   ├── validate_diagnosis.py          (Abductive Diagnosis P1 검증 독립 스크립트 — AD1-AD10 구조적 무결성, JSON 출력, Hook 아님 — Orchestrator가 수동 호출)
│   │   ├── validate_pacs.py               (pACS P1 검증 독립 스크립트 — PA1-PA7 구조적 무결성(PA7: RED < 50 차단) + L0 Anti-Skip Guard, JSON 출력, Hook 아님 — Orchestrator가 수동 호출)
│   │   ├── validate_review.py             (Adversarial Review P1 검증 독립 스크립트 — JSON 출력, Hook 아님 — Orchestrator가 수동 호출)
│   │   ├── validate_traceability.py       (Cross-Step Traceability P1 검증 독립 스크립트 — CT1-CT5 교차 단계 추적성, JSON 출력, Hook 아님 — Orchestrator가 수동 호출)
│   │   ├── validate_domain_knowledge.py   (Domain Knowledge Structure P1 검증 독립 스크립트 — DK1-DK7 도메인 지식 구조, JSON 출력, Hook 아님 — Orchestrator가 수동 호출)
│   │   ├── validate_translation.py        (Translation P1 검증 독립 스크립트 — T1-T9 + glossary 검증 + Review verdict 필수 체크, JSON 출력, Hook 아님 — Orchestrator가 수동 호출)
│   │   ├── validate_verification.py       (Verification Log P1 검증 독립 스크립트 — V1a-V1c 구조적 무결성, JSON 출력, Hook 아님 — Orchestrator가 수동 호출)
│   │   ├── validate_workflow.py           (Workflow.md DNA Inheritance P1 검증 독립 스크립트 — W1-W8 구조적 무결성(W7 CT Verification-Validator 정합성, W8 DKS Verification-Validator 정합성), JSON 출력, Hook 아님 — workflow-generator 완료 후 수동 호출)
│   │   ├── validate_retry_budget.py       (Retry Budget P1 검증 독립 스크립트 — RB1-RB3 재시도 예산 판정(ULW-aware), JSON 출력, Hook 아님 — Orchestrator가 재시도 전후 수동 호출)
│   │   ├── setup_init.py                  (Setup Init — 인프라 건강 검증 + SOT 쓰기 패턴 검증(P1 할루시네이션 봉쇄) + 런타임 디렉터리 자동 생성(SOT 존재 시), --init 트리거)
│   │   ├── setup_maintenance.py           (Setup Maintenance — 주기적 건강 검진, --maintenance 트리거)
│   │   ├── block_destructive_commands.py  (PreToolUse Safety Hook — 위험 명령 차단(P1 할루시네이션 봉쇄), exit code 2로 차단 + Claude 자기 수정)
│   │   ├── block_test_file_edit.py        (PreToolUse TDD Guard — 테스트 파일 수정 차단, .tdd-guard 토글, exit code 2 + Claude 자기 수정)
│   │   └── predictive_debug_guard.py      (PreToolUse Predictive Debug — 에러 이력 기반 위험 파일 경고, exit code 0 경고 전용)
│   ├── context-snapshots/                 ← 런타임 스냅샷 (gitignored)
│   │   ├── latest.md                      (최신 스냅샷)
│   │   ├── knowledge-index.jsonl          (세션 간 축적 인덱스 — RLM 프로그래밍적 탐색 대상)
│   │   ├── risk-scores.json               (Predictive Debugging 캐시 — SessionStart 생성, PreToolUse 읽기)
│   │   └── sessions/                      (세션별 아카이브)
│   └── skills/
│       ├── workflow-generator/            ← 워크플로우 설계·생성 스킬
│       │   ├── SKILL.md
│       │   └── references/                (claude-code-patterns, workflow-template, document-analysis-guide, context-injection-patterns, autopilot-decision-template, state.yaml.example)
│       └── doctoral-writing/              ← 박사급 학술 글쓰기 스킬
│           ├── SKILL.md
│           └── references/                (clarity-checklist, common-issues, before-after-examples, discipline-guides, korean-quick-reference)
├── translations/                          ← 번역 산출물 + 용어 사전
│   └── glossary.yaml                      (@translator 용어 사전 — 워크플로우 간 용어 일관성 유지)
├── prompt/                                ← 프롬프트 자료
│   ├── crystalize-prompt.md               (프롬프트 압축 기법)
│   ├── distill-partner.md                 (에센스 추출 및 최적화 인터뷰)
│   └── crawling-skill-sample.md           (크롤링 스킬 샘플)
└── coding-resource/                       ← 이론적 기반 자료
    └── recursive language models.pdf      (장기기억 구현 이론)
```

## Context Preservation System

컨텍스트 토큰 초과·`/clear`·압축 시 작업 내역 상실을 방지하는 자동 저장·복원 시스템이다.

### 동작 원리

| Hook 이벤트 | 스크립트 | 동작 |
|------------|---------|------|
| **Setup** (`--init`) | `setup_init.py` | 세션 시작 전 인프라 건강 검증 (Python 버전, 스크립트 구문(19개), 디렉터리, PyYAML, SOT 쓰기 패턴 검증, 런타임 디렉터리 자동 생성(6개)) |
| **Setup** (`--maintenance`) | `setup_maintenance.py` | 주기적 건강 검진 (stale archives, knowledge-index 무결성, work_log 크기, doc-code 동기화 검증(DC-1 NEVER DO 재시도 한도, DC-2 D-7 Risk 상수, DC-3 D-7 ULW 패턴)) |
| **PreToolUse** (Bash) | `block_destructive_commands.py` | 위험 명령 실행 전 차단 (git push --force, git reset --hard, rm -rf / 등). exit code 2로 차단 + stderr 피드백으로 Claude 자기 수정 |
| **PreToolUse** (Edit\|Write) | `block_test_file_edit.py` | TDD 모드(`.tdd-guard` 존재) 시 테스트 파일 수정 차단. Tier 1(디렉터리) + Tier 2(파일명) 2계층 탐지. exit code 2 + stderr 피드백으로 구현 코드 수정 유도 |
| **PreToolUse** (Edit\|Write) | `predictive_debug_guard.py` | 에러 이력 기반 위험 파일 경고. `risk-scores.json` 캐시 조회 → 임계값 초과 시 stderr 경고. exit code 0 (경고 전용) |
| **SessionEnd** (`/clear`) | `save_context.py` | 전체 스냅샷 저장 + Knowledge Archive 아카이빙 |
| **PreCompact** | `save_context.py` | 컨텍스트 압축 전 스냅샷 저장 + Knowledge Archive 아카이빙 |
| **SessionStart** | `restore_context.py` | RLM 패턴: 포인터 + 요약 + 과거 세션 인덱스 포인터 출력 + Error→Resolution 자동 표면화 + Predictive Debugging 캐시 생성 |
| **PostToolUse** | `update_work_log.py` | 9개 도구(Edit, Write, Bash, Task, NotebookEdit, TeamCreate, SendMessage, TaskCreate, TaskUpdate) 작업 로그 누적. 토큰 75% 초과 시 proactive 저장 |
| **Stop** | `generate_context_summary.py` | 매 응답 후 증분 스냅샷 + Knowledge Archive 아카이빙 (30초 throttling, 5KB growth threshold) + Autopilot Decision Log 안전망 + ULW 상태 IMMORTAL 보존 + ULW Compliance 안전망 + Traceability 누락 감지 + DKS 누락 감지 + Diagnosis 누락 감지 |

### Claude의 활용 방법

- 세션 시작 시 `[CONTEXT RECOVERY]` 메시지가 표시되면, 안내된 경로의 파일을 **반드시 Read tool로 읽어** 이전 맥락을 복원한다.
- 스냅샷은 `.claude/context-snapshots/latest.md`에 저장된다.
- **Knowledge Archive**: `knowledge-index.jsonl`은 세션 간 축적되는 구조화된 인덱스이다. Stop hook과 SessionEnd/PreCompact 모두에서 기록된다. 각 엔트리에는 completion_summary(도구 성공/실패), git_summary(변경 상태), session_duration_entries(세션 길이), phase(세션 전체 단계), phase_flow(다단계 전환 흐름, 예: `research → implementation`), primary_language(주요 파일 확장자), error_patterns(Error Taxonomy 12패턴 분류 + resolution 매칭), success_patterns(Edit/Write→Bash 성공 시퀀스 — cross-session 성공 패턴 학습), tool_sequence(RLE 압축 도구 시퀀스), final_status(success/incomplete/error/unknown), tags(경로 기반 검색 태그 — CamelCase/snake_case 분리 + 확장자 매핑)가 포함된다. Grep tool로 프로그래밍적 탐색이 가능하다 (RLM 패턴).
- **Resume Protocol**: 스냅샷에 포함된 "복원 지시" 섹션은 수정/참조 파일 목록과 세션 정보를 결정론적으로 제공한다. `[CONTEXT RECOVERY]` 출력에는 완료 상태(도구 성공/실패)와 Git 변경 상태도 표시된다. **동적 RLM 쿼리 힌트**: 수정 파일 경로에서 추출한 태그(`extract_path_tags()`)와 에러 정보를 기반으로 세션별 맞춤 Grep 쿼리 예시를 자동 생성한다.
- Hook 스크립트는 SOT(`state.yaml`)를 **읽기 전용**으로만 접근한다 (절대 기준 2 준수). SOT 파일 경로는 `sot_paths()` 헬퍼로 중앙 관리되며, `SOT_FILENAMES` 상수(`state.yaml`, `state.yml`, `state.json`)에서 파생된다.
- **절삭 상수 중앙화**: `_context_lib.py`에 10개 절삭 상수(`EDIT_PREVIEW_CHARS=1000`, `ERROR_RESULT_CHARS=3000`, `MIN_OUTPUT_SIZE=100` 등)를 중앙 정의. Edit preview는 5줄×1000자로 편집 의도·맥락을 보존하고, 에러 메시지는 3000자로 stack trace 전체를 보존한다.
- **다단계 전환 감지**: `detect_phase_transitions()` 함수가 sliding window(20개 도구, 50% 오버랩)로 세션 내 단계 전환(research → planning → implementation 등)을 결정론적으로 감지한다. Knowledge Archive의 `phase_flow` 필드에 기록된다.
- **결정 품질 태그 정렬**: 스냅샷의 "주요 설계 결정" 섹션(IMMORTAL 우선순위)은 품질 태그 기반으로 정렬된다 — `[explicit]` > `[decision]` > `[rationale]` > `[intent]` 순으로 15개 슬롯을 채워, 일상적 의도 선언(`하겠습니다` 패턴)이 실제 설계 결정을 밀어내지 않는다. 비교·트레이드오프·선택 패턴도 추출한다.
- **IMMORTAL-aware 압축**: 스냅샷 크기 초과 시 Phase 7 hard truncate에서 IMMORTAL 섹션을 우선 보존한다. 비-IMMORTAL 콘텐츠를 먼저 절삭하고, IMMORTAL 자체가 한계를 초과하는 극단적 경우에도 IMMORTAL 텍스트의 시작 부분을 보존한다. **압축 감사 추적**: 각 압축 Phase가 제거한 문자 수를 HTML 주석(`<!-- compression-audit: ... -->`)으로 스냅샷 끝에 기록한다 (Phase 1~7 단계별 delta + 최종 크기). 렌더링에 영향 없이 Grep으로 디버깅 가능.
- **Error Taxonomy**: 도구 에러를 12개 패턴(file_not_found, permission, syntax, timeout, dependency, edit_mismatch, type_error, value_error, connection, memory, git_error, command_not_found)으로 분류한다. Knowledge Archive의 error_patterns 필드에 기록되어, "unknown" 분류를 ~30%로 감소시킨다. False positive 방지를 위해 negative lookahead, 한정어 매칭 등을 적용한다. **Error→Resolution 매칭**: 에러 발생 후 5 entries 이내의 성공적 도구 호출을 file-aware 매칭으로 탐지하여 `resolution` 필드에 기록한다 (도구명 + 파일명). 매칭 실패 시 `null`. `Grep "resolution" knowledge-index.jsonl`로 해결 패턴을 cross-session 탐색 가능.
- **P1 할루시네이션 봉쇄 (Hallucination Prevention)**: 반복적으로 100% 정확해야 하는 작업을 Python 코드로 강제한다. (1) **KI 스키마 검증**: `_validate_session_facts()`가 knowledge-index 쓰기 직전 RLM 필수 키(session_id, tags, final_status, diagnosis_patterns 등 11개) 존재를 보장 — 누락 시 안전 기본값 채움. (2) **부분 실패 격리**: `archive_and_index_session()`에서 archive 파일 쓰기 실패가 knowledge-index 갱신을 차단하지 않음 — RLM 핵심 자산 보호. (3) **SOT 쓰기 패턴 검증**: `setup_init.py`의 `_check_sot_write_safety()`가 Hook 스크립트에서 SOT 파일명 + 쓰기 패턴 공존을 AST 함수 경계 기반으로 탐지 (Tier 1: 비-SOT 스크립트의 SOT 참조 차단, Tier 2: SOT-aware 스크립트의 함수별 쓰기 패턴 검사). (4) **SOT 스키마 검증**: `validate_sot_schema()`가 워크플로우 state.yaml의 구조적 무결성을 8항목(S1-S6: current_step 타입·범위, outputs 타입·키 형식, 미래 단계 산출물 탐지, workflow_status 유효값, auto_approved_steps 정합성 + S7: pacs 5개 필드 검증(S7a dimensions F/C/L 0-100, S7b current_step_score 0-100, S7c weak_dimension F/C/L, S7d history dict→{score, weak}, S7e pre_mortem_flag string) + S8: active_team 5개 필드 검증(S8a name string, S8b status partial|all_completed, S8c tasks_completed list, S8d tasks_pending list, S8e completed_summaries dict→dict))으로 검증 — SessionStart와 Stop hook 양쪽에서 실행. (5) **Adversarial Review P1 검증**: `validate_review_output()`이 리뷰 보고서의 구조적 무결성(파일 존재 R1, 최소 크기 R2, 필수 섹션 4개 R3, PASS/FAIL 명시적 추출 R4, 이슈 테이블 ≥ 1행 R5)을 결정론적으로 검증. `parse_review_verdict()`가 regex로 이슈 심각도(Critical/Warning/Suggestion) 카운트 추출. `calculate_pacs_delta()`가 Generator-Reviewer pACS 차이(Delta ≥ 15 → 재조정 필요)를 산술 연산. `validate_review_sequence()`가 Review PASS → Translation 순서를 파일 타임스탬프로 강제. 독립 실행 스크립트: `validate_review.py`. (6) **Translation P1 검증**: `validate_translation_output()`이 번역 산출물의 구조적 무결성을 7항목(파일 존재 T1, 최소 크기 T2, 영어 원본 존재 T3, .ko.md 확장자 T4, 비-공백 T5, 헤딩 수 ±20% T6, 코드 블록 수 일치 T7)으로 검증. `check_glossary_freshness()`가 glossary 타임스탬프 신선도(T8). `verify_pacs_arithmetic()`이 모든 pACS 로그의 min() 산술 정확성(T9 — 범용). `validate_verification_log()`이 검증 로그 구조적 무결성(V1a-V1c: 파일 존재, 기준별 PASS/FAIL, 논리적 일관성). `validate_translation.py`는 Review verdict=PASS를 필수 체크(--check-sequence 없이도 항상 실행). 독립 실행 스크립트: `validate_translation.py`. (7) **pACS P1 검증**: `validate_pacs_output()`이 pACS 로그의 구조적 무결성을 6항목(PA1 파일 존재, PA2 최소 크기 50 bytes, PA3 차원 점수 ≥ 3개(0-100 범위), PA4 Pre-mortem 섹션 존재, PA5 min() 산술 정확성(verify_pacs_arithmetic 위임), PA7 RED 차단(pACS < 50 → FAIL — 단계 진행 차단))으로 검증. PA6(선택): 점수-색상 영역 정합성(RED/YELLOW/GREEN). 독립 실행 스크립트: `validate_pacs.py`. (8) **L0 Anti-Skip Guard 코드 구현**: `validate_step_output()`이 산출물 파일의 L0 검증을 3항목(L0a SOT outputs.step-N 경로의 파일 존재, L0b 파일 크기 ≥ MIN_OUTPUT_SIZE(100 bytes), L0c 비-공백 확인)으로 수행. Orchestrator가 current_step 증가 전 호출. `validate_pacs.py --check-l0`으로 pACS + L0 동시 검증 가능. (9) **Predictive Debugging P1 검증**: `validate_risk_scores()`가 risk-scores.json의 구조적 무결성을 6항목(RS1 필수 키, RS2 data_sessions 정수, RS3 risk_score 범위, RS4 error_count 산술 정합, RS5 resolution_rate 범위, RS6 top_risk_files 정렬+존재)으로 검증. `aggregate_risk_scores()`가 생성 직후 자기 검증 호출. (10) **Retry Budget P1 검증**: `validate_retry_budget.py`가 재시도 예산을 결정론적으로 판정한다. RB1(카운터 파일 읽기 — 정수, 없으면 0), RB2(ULW 활성 감지 — 스냅샷 regex), RB3(예산 비교 — `retries_used < max_retries`). `max_retries`는 ULW 활성 시 3, 비활성 시 2. `--increment` 모드로 카운터를 atomic write로 증가. Orchestrator가 Verification Gate/pACS RED/Review FAIL 재시도 전후에 호출. 카운터 파일: `{gate}-logs/.step-N-retry-count`.
- **Abductive Diagnosis P1 검증**: `validate_diagnosis_log()`이 진단 로그의 구조적 무결성을 10항목(AD1 파일 존재, AD2 최소 크기 100 bytes, AD3 Gate 필드 일치, AD4 선택 가설 존재, AD5 증거 ≥ 1개, AD6 Action Plan 섹션 존재, AD7 순방향 참조 금지, AD8 가설 ≥ 2개, AD9 선택 가설 일관성, AD10 이전 진단 참조(재시도 > 0))으로 검증. `diagnose_failure_context()`가 사전 증거 수집(retry_history, upstream_evidence, hypothesis_priority, fast_path, raw_evidence). Fast-Path(FP1-FP3)로 결정론적 단축. 독립 실행 스크립트: `diagnose_context.py`(사전 분석), `validate_diagnosis.py`(사후 검증). Knowledge Archive에 `diagnosis_patterns`로 아카이빙.
- **Cross-Step Traceability P1 검증**: `validate_cross_step_traceability()`가 산출물의 교차 단계 추적성을 5항목(CT1 trace 마커 존재, CT2 참조 단계 산출물 존재, CT3 섹션 ID 해결(Warning), CT4 최소 밀도 ≥ 3, CT5 순방향 참조 금지)으로 검증. 독립 실행 스크립트: `validate_traceability.py`. Verification 기준에 교차 단계 추적성이 포함된 단계에서 수동 호출.
- **Domain Knowledge Structure P1 검증**: `validate_domain_knowledge()`가 domain-knowledge.yaml의 구조적 무결성을 7항목(DK1 파일 존재+YAML 유효, DK2 metadata 필수 키, DK3 entities 구조(id 유일+slug, type, attributes), DK4 relations 참조 무결성(subject/object→entities.id, confidence), DK5 constraints 구조, DK6 산출물 DKS 참조 해결, DK7 제약 조건 비위반)으로 검증. 독립 실행 스크립트: `validate_domain_knowledge.py`. DKS 패턴 사용 워크플로우에서 수동 호출. 선택적 — 모든 워크플로우가 필요로 하지 않음.
- **Workflow.md DNA Inheritance P1 검증**: `validate_workflow_md()`가 생성된 workflow.md의 DNA 유전 구조적 무결성을 8항목(W1 파일 존재, W2 최소 크기 500 bytes, W3 `## Inherited DNA` 헤더 존재, W4 Inherited Patterns 테이블 ≥ 3행, W5 Constitutional Principles 섹션 존재, W6 Coding Anchor Points(CAP) 참조 존재, W7 교차 단계 추적성 Verification-Validator 정합성(Verification에 CT 기준이 있으면 validate_traceability Post-processing 필수), W8 도메인 지식 구조 Verification-Validator 정합성(DKS 참조 시 validate_domain_knowledge Post-processing 필수))으로 검증. 독립 실행 스크립트: `validate_workflow.py`. workflow-generator 완료 후(SKILL.md Step 13) 수동 호출.
- **Quality Gate 상태 IMMORTAL 보존**: `_extract_quality_gate_state()` 함수가 `pacs-logs/`, `review-logs/`, `verification-logs/`에서 최신 단계의 품질 게이트 결과(pACS 점수·약점 차원, Review verdict·이슈 카운트, Verification PASS/FAIL)를 추출하여 스냅샷에 IMMORTAL 섹션으로 보존한다. 세션 경계(compact/clear)에서 Verification Gate/pACS/Adversarial Review 재개 맥락이 유실되지 않는다.
- **Phase Transition 스냅샷 헤더**: 다단계 전환이 감지된 세션에서는 스냅샷 헤더에 단일 phase 대신 `Phase flow: research(12) → implementation(25)` 형식의 전환 흐름을 표시한다. 각 단계의 도구 호출 수가 괄호 안에 포함되어 세션 복원 시 작업 흐름 맥락을 즉시 파악할 수 있다.
- **Error→Resolution 자동 표면화**: `restore_context.py`의 `_extract_recent_error_resolutions()` 함수가 Knowledge Archive의 최근 세션에서 error_patterns(type + resolution)을 읽어 SessionStart 출력에 최대 3개의 에러→해결 패턴을 직접 표시한다. 수동 Grep 없이 이전 세션의 에러 해결 경험을 즉시 활용할 수 있다.
- **런타임 디렉터리 자동 생성**: `setup_init.py`의 `_check_runtime_dirs()` 함수가 SOT 파일 존재 시 `verification-logs/`, `pacs-logs/`, `review-logs/`, `autopilot-logs/`, `translations/`, `diagnosis-logs/` 6개 디렉터리를 자동 생성한다. 워크플로우 실행 중 디렉터리 부재로 인한 silent failure를 방지한다.
- **시스템 명령 필터링**: 스냅샷의 "현재 작업" 섹션에서 `/clear`, `/help` 등 시스템 명령을 자동 필터링하여 실제 사용자 작업 의도만 캡처한다.
- **Autopilot 런타임 강화**: Autopilot 활성 시 SessionStart가 실행 규칙을 컨텍스트에 주입하고, 스냅샷에 Autopilot 상태 섹션(IMMORTAL 우선순위)을 포함하며, Stop hook이 Decision Log 누락을 감지·보완한다. PostToolUse는 work_log에 autopilot_step 필드를 추가하여 단계 진행을 추적한다.
- **ULW 모드 감지·보존**: `detect_ulw_mode()` 함수가 트랜스크립트에서 word-boundary 정규식으로 `ulw` 키워드를 감지한다. 활성 시 스냅샷에 ULW 상태 섹션(IMMORTAL 우선순위)을 포함하고, SessionStart가 3개 강화 규칙(Intensifiers)을 컨텍스트에 주입한다. **암묵적 해제**: 새 세션(`source=startup`)에서는 이전 스냅샷에 ULW 상태가 있어도 규칙을 주입하지 않는다 — `clear`/`compact`/`resume` source만 ULW를 계승한다. `check_ulw_compliance()` 함수가 3개 강화 규칙의 준수를 결정론적으로 검증하여 스냅샷 IMMORTAL에 경고를 포함한다. Knowledge Archive에 `ulw_active: true`로 태깅되어 `Grep "ulw_active" knowledge-index.jsonl`로 RLM 쿼리 가능하다.
- **Predictive Debugging**: `aggregate_risk_scores()`가 Knowledge Archive의 error_patterns를 파일별로 집계하여 위험 점수를 산출한다 (가중치 × 감쇠). SessionStart 시 1회 실행되어 `risk-scores.json` 캐시를 생성하고, `predictive_debug_guard.py`(PreToolUse Hook)가 매 Edit/Write마다 캐시를 읽어 임계값 초과 시 stderr 경고를 출력한다. **Startup 트레이드오프**: SessionStart matcher가 `clear|compact|resume`이므로 최초 startup에서는 캐시 미생성 — 이전 캐시(2시간 이내)에 의존하거나, 첫 compact/clear 시 생성 (ADR-036). **D-7 상수 동기화**: `predictive_debug_guard.py`의 `RISK_THRESHOLD`/`MIN_SESSIONS`는 `_context_lib.py`의 `_RISK_SCORE_THRESHOLD`/`_RISK_MIN_SESSIONS`와 D-7 의도적 중복이다 — 변경 시 양쪽 동기화 필수. **Basename merge**: bare name(`_context_lib.py`)과 relative path(`.claude/hooks/scripts/_context_lib.py`)가 혼재할 때, 동일 basename 엔트리를 자동 병합하여 risk score 과소평가를 방지한다.

### Hook 설정 위치

모든 Hook은 **Project** (`.claude/settings.json`)에 통합 정의되어 있다. `git clone`만으로 Hook 인프라가 자동 적용된다.

- Stop → `context_guard.py --mode=stop` → `generate_context_summary.py`
- PostToolUse → `context_guard.py --mode=post-tool` → `update_work_log.py` (matcher: `Edit|Write|Bash|Task|NotebookEdit|TeamCreate|SendMessage|TaskCreate|TaskUpdate`)
- PreCompact → `context_guard.py --mode=pre-compact` → `save_context.py --trigger precompact`
- SessionStart → `context_guard.py --mode=restore` → `restore_context.py` (matcher: `clear|compact|resume`)
- **PreToolUse** → `block_destructive_commands.py` (matcher: `Bash`, 독립 실행 — exit code 2 보존)
- **PreToolUse** → `block_test_file_edit.py` (matcher: `Edit|Write`, 독립 실행 — `.tdd-guard` 토글 기반 TDD 테스트 파일 보호)
- **PreToolUse** → `predictive_debug_guard.py` (matcher: `Edit|Write`, 독립 실행 — 경고 전용 exit code 0)
- SessionEnd → `save_context.py --trigger sessionend` (matcher: `clear`)
- Setup (init) → `setup_init.py` — 인프라 건강 검증 (`claude --init`)
- Setup (maintenance) → `setup_maintenance.py` — 주기적 건강 검진 (`claude --maintenance`)

> **`if test -f; then; fi` 패턴 통일**: 모든 Hook 명령이 `if test -f; then; fi` 패턴을 사용한다. 이전의 `|| true` 패턴(exit code 2 차단 신호를 삼키는 잠복 버그)을 제거하여, `context_guard.py` 자식 스크립트에 차단 기능 추가 시에도 exit code 2가 안전하게 전파된다.
> **PreToolUse Safety Hook의 독립 실행 근거**: `block_destructive_commands.py`(안전)와 `block_test_file_edit.py`(TDD 보호)는 컨텍스트 보존과는 다른 도메인이다. exit code 2 보존이 필수이므로, `context_guard.py`를 거치지 않고 직접 실행한다. `block_test_file_edit.py`는 `.tdd-guard` 파일 존재 시에만 활성화된다 (`touch .tdd-guard`로 TDD 모드 시작, `rm .tdd-guard`로 해제).
> **D-7 의도적 중복 인스턴스**: (1) `REQUIRED_SCRIPTS` — `setup_init.py` ↔ `setup_maintenance.py` (19개 스크립트 목록). (2) `predictive_debug_guard.py` 상수 — `RISK_THRESHOLD`/`MIN_SESSIONS` ↔ `_context_lib.py`의 `_RISK_SCORE_THRESHOLD`/`_RISK_MIN_SESSIONS`. (3) `ERROR_TAXONOMY` 타입명 — `_classify_error_patterns()` 내 12개 타입 ↔ `_RISK_WEIGHTS` 13개 키. (4) ULW 감지 패턴 — `_context_lib.py`의 `_gather_retry_history()` ↔ `validate_retry_budget.py`의 `_ULW_SNAPSHOT_RE` ↔ `restore_context.py`의 ULW 상태 문자열 검사 (모두 `"ULW 상태"` 기반). (5) 재시도 한도 상수 — `validate_retry_budget.py`의 `DEFAULT_MAX_RETRIES`/`ULW_MAX_RETRIES` ↔ `_context_lib.py`의 `_DEFAULT_MAX_RETRIES`/`_ULW_MAX_RETRIES` ↔ `restore_context.py`의 ULW+Autopilot 주입 텍스트. 각 D-7 인스턴스는 코드에 cross-reference 주석이 있으며, 한쪽 변경 시 반드시 대응 쪽도 동기화해야 한다.

## 스킬 사용 판별

| 사용자 요청 패턴 | 스킬 | 진입점 |
|----------------|------|--------|
| "워크플로우 만들어줘", "자동화 파이프라인 설계", "작업 흐름 정의" | `workflow-generator` | SKILL.md → 케이스 판별 |
| "논문 스타일로 써줘", "학술적 글쓰기", "논문 문장 다듬기" | `doctoral-writing` | SKILL.md → 맥락 파악 |

## 설계 원칙

1. **P1 — 정확도를 위한 데이터 정제**: AI에게 전달하기 전 Python 등으로 노이즈 제거. 전처리·후처리 명시.
2. **P2 — 전문성 기반 위임 구조**: 전문 에이전트에게 위임하여 품질 극대화. Orchestrator는 조율만.
3. **P3 — 이미지/리소스 정확성**: 정확한 다운로드 경로 명시. placeholder 누락 불가.
4. **P4 — 질문 설계 규칙**: 최대 4개 질문, 각 3개 선택지. 모호함 없으면 질문 없이 진행. Claude Code에서는 `AskUserQuestion` 도구로 구현. Slash Command가 사전 정의된 선택형 개입이라면, AskUserQuestion은 동적 질문이 필요한 상황에 사용.

## Autopilot Mode (Claude Code 구현)

워크플로우 실행 시 `(human)` 단계와 AskUserQuestion을 자동 승인하는 모드. 상세: `AGENTS.md §5.1`

### 활성화 패턴

| 사용자 명령 | 동작 |
|-----------|------|
| "autopilot 모드로 실행", "자동 모드로 워크플로우 실행", "전자동으로 실행" | SOT에 `autopilot.enabled: true` 설정 후 워크플로우 시작 |
| "autopilot 해제", "수동 모드로 전환" | SOT에 `autopilot.enabled: false` — 다음 `(human)` 단계부터 적용 |

### Checkpoint별 동작

| Checkpoint | Autopilot 동작 |
|-----------|---------------|
| `(human)` + Slash Command | 완전한 산출물 생성 → 품질 극대화 기본값으로 자동 승인 → 결정 로그 기록 |
| AskUserQuestion | 선택지 중 품질 극대화 옵션 자동 선택 → 결정 로그 기록 |
| `(hook)` exit code 2 | **변경 없음** — 그대로 차단, 피드백 전달, 재작업 |

### Anti-Skip Guard + Verification Gate + pACS (4계층 품질 보장)

Orchestrator는 `current_step`을 순차적으로만 증가. 각 단계 완료 시 최대 4계층 검증을 통과해야 진행한다:

1. **L0 Anti-Skip Guard** (결정론적) — 산출물 파일 존재 + 최소 크기(100 bytes). Hook 계층의 `validate_step_output()` 함수가 수행.
2. **L1 Verification Gate** (의미론적) — 산출물이 `Verification` 기준을 100% 달성했는지 에이전트 자기 검증. 실패 시 해당 부분만 재실행(최대 10회). `verification-logs/step-N-verify.md`에 기록.
3. **L1.5 pACS Self-Rating** (신뢰도) — Pre-mortem Protocol 수행 후 F/C/L 3차원 채점. `pacs-logs/step-N-pacs.md`에 기록. RED(< 50) 시 재작업.
4. **[L2 Calibration]** (선택적) — 별도 `@verifier` 에이전트가 pACS 점수 교차 검증. 고위험 단계만.

> `Verification` 필드가 없는 단계는 Anti-Skip Guard만으로 진행 (하위 호환). 상세: `AGENTS.md §5.3`, `§5.4`

### 결정 로그

자동 승인된 결정은 `autopilot-logs/step-N-decision.md`에 기록: 단계, 옵션, 선택 근거(절대 기준 1 기반).
Decision Log 표준 템플릿: `references/autopilot-decision-template.md`

### 런타임 강화 메커니즘

Autopilot의 설계 의도를 런타임에서 강화하는 하이브리드(Hook + 프롬프트) 시스템:

| 계층 | 메커니즘 | 강화 내용 |
|------|---------|----------|
| **Hook** (결정론적) | `restore_context.py` — SessionStart | Autopilot 활성 시 6개 실행 규칙 + 이전 단계 산출물 검증 결과를 컨텍스트에 주입 |
| **Hook** (결정론적) | `generate_snapshot_md()` — 스냅샷 | Autopilot 상태 + Agent Team 상태 섹션을 IMMORTAL 우선순위로 보존 (세션 경계에서 유실 방지) |
| **Hook** (결정론적) | `generate_context_summary.py` — Stop | 자동 승인 패턴 감지 → Decision Log 누락 시 보완 생성 (안전망) |
| **Hook** (결정론적) | `update_work_log.py` — PostToolUse | `autopilot_step` 필드로 단계 진행 추적 (사후 분석 가능) |
| **프롬프트** (행동 유도) | Execution Checklist (아래) | 각 단계의 시작/실행/완료 시 필수 행동 명시 |

> Hook 계층은 SOT를 읽기 전용으로만 접근하며 (절대 기준 2 준수), 쓰기는 `context-snapshots/`와 `autopilot-logs/`에만 수행한다.

### Autopilot Execution Checklist (MANDATORY)

Autopilot 모드에서 워크플로우를 실행할 때, 각 단계마다 아래 체크리스트를 **반드시** 수행한다.

#### 각 단계 시작 전
- [ ] SOT `current_step` 확인
- [ ] 이전 단계 산출물 파일 존재 + 비어있지 않음 확인
- [ ] 이전 단계 산출물 경로가 SOT `outputs`에 기록 확인
- [ ] 해당 단계의 `Verification` 기준 읽기 — "100% 완료"의 정의를 먼저 인식 (AGENTS.md §5.3)

#### 단계 실행 중
- [ ] 단계의 모든 작업을 **완전히** 실행 (축약 금지 — 절대 기준 1)
- [ ] 산출물을 **완전한 품질**로 생성

#### 단계 완료 후 (Verification Gate — `Verification` 필드 있는 단계만)
- [ ] 산출물 파일을 디스크에 저장
- [ ] 산출물을 각 `Verification` 기준 대비 자기 검증
- [ ] 실패 기준 있으면:
  - [ ] P1 재시도 예산 확인+소비: `python3 .claude/hooks/scripts/validate_retry_budget.py --step N --gate verification --project-dir . --check-and-increment`
  - [ ] `can_retry: true` → **Abductive Diagnosis 수행** (아래 진단 서브섹션 참조) → 진단 기반 재실행
  - [ ] `can_retry: false` → 사용자 에스컬레이션 (재시도 예산 소진, 카운터 미증가)
- [ ] 모든 기준 PASS 확인
- [ ] `verification-logs/step-N-verify.md` 생성
- [ ] P1 검증 실행: `python3 .claude/hooks/scripts/validate_verification.py --step N --project-dir .`
- [ ] P1 검증 결과 `valid: true` 확인 (V1a-V1c 모두 통과)

#### 단계 완료 후 (Cross-Step Traceability — Verification에 "교차 단계 추적성" 기준이 포함된 단계만)
- [ ] 산출물에 `[trace:step-N:section-id]` 마커가 최소 3개 이상 포함 확인
- [ ] 모든 마커가 이전 단계만 참조 (순방향 참조 금지)
- [ ] P1 검증 실행: `python3 .claude/hooks/scripts/validate_traceability.py --step N --project-dir .`
- [ ] P1 검증 결과 `valid: true` 확인 (CT1-CT5 모두 통과)
- [ ] CT3 WARNING(섹션 ID 미해결) 있으면 마커 정확성 재확인

#### 단계 완료 후 (Domain Knowledge Structure — DKS 패턴 사용 워크플로우만, 선택적)
- [ ] `domain-knowledge.yaml` 구축 단계: P1 검증 실행: `python3 .claude/hooks/scripts/validate_domain_knowledge.py --project-dir .`
- [ ] P1 검증 결과 `valid: true` 확인 (DK1-DK5 모두 통과)
- [ ] DKS 참조 단계 (산출물에 `[dks:xxx]` 마커 포함): P1 교차 검증 실행: `python3 .claude/hooks/scripts/validate_domain_knowledge.py --project-dir . --check-output --step N`
- [ ] P1 교차 검증 결과 `valid: true` 확인 (DK6-DK7 포함 모두 통과)

#### 단계 완료 후 (pACS — Verification Gate 통과 후 수행)
- [ ] Pre-mortem Protocol 3개 질문에 답하기 (AGENTS.md §5.4)
- [ ] F, C, L 3차원 채점 → pACS = min(F, C, L) 산출
- [ ] `pacs-logs/step-N-pacs.md` 생성
- [ ] SOT `pacs` 필드 갱신 (current_step_score, dimensions, weak_dimension, history)
- [ ] pACS RED(< 50) 시:
  - [ ] P1 재시도 예산 확인+소비: `python3 .claude/hooks/scripts/validate_retry_budget.py --step N --gate pacs --project-dir . --check-and-increment`
  - [ ] `can_retry: true` → **Abductive Diagnosis 수행** (아래 진단 서브섹션 참조) → 진단 기반 재작업 + 재채점
  - [ ] `can_retry: false` → 사용자 에스컬레이션 (재시도 예산 소진, 카운터 미증가)
- [ ] pACS YELLOW(50-69) 시: Decision Log에 약점 차원 기록 후 진행
- [ ] P1 검증 실행: `python3 .claude/hooks/scripts/validate_pacs.py --step N --check-l0 --project-dir .`
- [ ] P1 검증 결과 `valid: true` 확인 (PA1-PA7 + L0 모두 통과)
- [ ] SOT `outputs`에 산출물 경로 기록
- [ ] SOT `current_step` +1 증가
- [ ] `(human)` 단계: `autopilot-logs/step-N-decision.md` 생성
- [ ] `(human)` 단계: SOT `auto_approved_steps`에 추가

#### `(team)` 단계 추가 체크리스트
- [ ] `TeamCreate` 직후 → SOT `active_team` 기록 (name, status, tasks_pending)
- [ ] 각 Teammate는 보고 전 자기 Task의 검증 기준 대비 자기 검증 수행 (L1 — AGENTS.md §5.3)
- [ ] 각 Teammate는 L1 통과 후 pACS 자기 채점 수행 (L1.5 — 세션 내부 완결, 점수를 보고 메시지에 포함)
- [ ] 각 Teammate 완료 시 → Team Lead가 단계 검증 기준 대비 종합 검증 (L2) + 단계 pACS 산출
- [ ] L2 FAIL 또는 Teammate pACS RED 시 → SendMessage로 구체적 피드백 + 재실행 지시
- [ ] 각 Teammate 완료 시 → SOT `active_team.tasks_completed` + `completed_summaries` 갱신
- [ ] 모든 Task 완료 시 → SOT `outputs` 기록, `current_step` +1, `active_team.status` → `all_completed`
- [ ] `TeamDelete` 직후 → SOT `active_team` → `completed_teams` 이동
- [ ] Teammate 산출물에 판단 근거(Decision Rationale) + 교차 참조 단서(Cross-Reference Cues) 포함 확인

#### 단계 완료 후 (Adversarial Review — `Review: @reviewer|@fact-checker`인 단계만)
- [ ] `Review:` 필드에 지정된 에이전트를 Sub-agent로 호출
- [ ] 리뷰 보고서를 `review-logs/step-N-review.md`에 저장
- [ ] P1 검증 실행: `python3 .claude/hooks/scripts/validate_review.py --step N --project-dir . --check-pacs-arithmetic`
- [ ] P1 검증 결과 `valid: true` 확인 (R1-R5 모두 통과)
- [ ] Verdict 확인:
  - [ ] PASS → 다음 단계 진행 (Translation 포함)
  - [ ] FAIL → P1 재시도 예산 확인+소비: `python3 .claude/hooks/scripts/validate_retry_budget.py --step N --gate review --project-dir . --check-and-increment`
  - [ ] `can_retry: true` → **Abductive Diagnosis 수행** (아래 진단 서브섹션 참조) → 진단 기반 재작업
  - [ ] `can_retry: false` → 사용자 에스컬레이션 (재시도 예산 소진, 카운터 미증가)
- [ ] pACS Delta ≥ 15 시 → Decision Log에 기록 + 재조정 사유 문서화
- [ ] Review FAIL 상태에서 Translation 실행 금지

#### 품질 게이트 FAIL 시 진단 (Abductive Diagnosis — 재시도 가능 시 수행)
- [ ] Step A — P1 사전 증거 수집: `python3 .claude/hooks/scripts/diagnose_context.py --step N --gate {verification|pacs|review} --project-dir .`
- [ ] Fast-Path 확인: `fast_path.eligible == true` → FP1/FP2는 즉시 재실행, FP3는 사용자 에스컬레이션
- [ ] Fast-Path 해당 없으면 → Step B — LLM 진단: 증거 번들 + 가설 우선순위 기반으로 원인 분석
- [ ] 진단 로그 생성: `diagnosis-logs/step-N-{gate}-{timestamp}.md`
- [ ] Step C — P1 사후 검증: `python3 .claude/hooks/scripts/validate_diagnosis.py --step N --gate {verification|pacs|review} --project-dir .`
- [ ] P1 검증 결과 `valid: true` 확인 (AD1-AD10 모두 통과)
- [ ] 진단 결과에 따라 선택된 가설(H1/H2/H3) 기반 재작업 실행

#### 단계 완료 후 (번역 — `Translation: @translator`인 단계만)
- [ ] `@translator` 서브에이전트 호출 (`translations/glossary.yaml` 참조 포함)
- [ ] 번역 파일(`*.ko.md`) 디스크에 존재 확인
- [ ] 번역 파일 비어있지 않음 확인
- [ ] SOT `outputs.step-N-ko`에 번역 경로 기록
- [ ] `translations/glossary.yaml` 갱신 확인
- [ ] Translation pACS 채점 완료 (Ft/Ct/Nt — `@translator` Step 4, AGENTS.md §5.4)
- [ ] Translation pACS 로그 생성 (`pacs-logs/step-N-translation-pacs.md`)
- [ ] P1 검증 실행: `python3 .claude/hooks/scripts/validate_translation.py --step N --project-dir . --check-pacs --check-sequence`
- [ ] P1 검증 결과 `valid: true` 확인 (T1-T9 + sequence 모두 통과)

#### NEVER DO
- `current_step`을 2 이상 한 번에 증가 금지
- 산출물 없이 다음 단계 진행 금지
- "자동이니까 간략하게" 금지 — 절대 기준 1 위반
- `(hook)` exit code 2 차단 무시 금지
- `(team)` 단계에서 Teammate가 SOT를 직접 수정 금지 — Team Lead만 SOT 갱신
- 세션 복원 시 `active_team`을 빈 객체로 초기화 금지 — 기존 `completed_summaries` 보존 필수 (보존적 재개 프로토콜)
- Verification 기준 FAIL인 채로 다음 단계 진행 금지 — 최대 10회(ULW 활성 시 15회) 재시도 후 사용자 에스컬레이션
- Verification 기준을 "모두 PASS"로 허위 기록 금지 — 각 기준에 구체적 Evidence 필수
- Pre-mortem Protocol 생략하고 pACS 점수만 부여 금지 — 약점 인식이 점수의 전제
- pACS를 Verification Gate 없이 단독 수행 금지 — L1 통과가 L1.5의 전제
- pACS 점수를 전부 90+ 부여 금지 — Pre-mortem에서 식별한 약점과 점수 정합성 필수
- Review FAIL 상태에서 Translation 실행 금지 — Review PASS가 Translation의 전제
- Review 이슈 0건으로 PASS 처리 금지 — P1 검증이 자동 거부 (R5 체크)
- Reviewer pACS를 Generator pACS 참조 후 채점 금지 — 독립 채점이 필수
- 품질 게이트 FAIL 재시도 시 진단 없이 동일 접근법으로 재시도 금지 — Abductive Diagnosis 또는 Fast-Path 필수
- 진단 로그에 가설 1개만 기록 금지 — 최소 2개 가설 비교 (AD8)
- 진단에서 이전 진단과 동일 가설 3회 연속 선택 금지 — FP3 에스컬레이션 (I-3 연동)

## ULW (Ultrawork) Mode

프롬프트에 `ulw`를 포함하면 **Ultrawork 모드**가 활성화된다. ULW는 Autopilot과 **직교하는 철저함 강도(thoroughness intensity) 오버레이**이다.

- **Autopilot** = 자동화 축(HOW) — `(human)` 승인 건너뛰기
- **ULW** = 철저함 축(HOW THOROUGHLY) — 빠짐없이, 에러 해결까지 완벽 수행

두 축은 독립적이므로, 어떤 조합이든 가능하다:

|  | **ULW OFF** (보통) | **ULW ON** (최대 철저함) |
|---|---|---|
| **Autopilot OFF** | 표준 대화형 | 대화형 + Sisyphus Persistence(3회 재시도) + 필수 태스크 분해 |
| **Autopilot ON** | 표준 자동 워크플로우 | 자동 워크플로우 + Sisyphus 강화(재시도 3회) + 팀 철저함 |

### 2축 비교

| 축 | 관심사 | 활성화 | 비활성화 | 적용 범위 |
|----|--------|--------|---------|----------|
| **Autopilot** | 자동화(HOW) | SOT `autopilot.enabled: true` | SOT 변경 | 워크플로우 단계 |
| **ULW** | 철저함(HOW THOROUGHLY) | 프롬프트에 `ulw` | 암묵적 (새 세션 시 `ulw` 없으면 비활성) | 모든 작업 (대화형 + 워크플로우) |

### 활성화 패턴

| 사용자 명령 | 동작 |
|-----------|------|
| "ulw 이거 해줘", "ulw 리팩토링해줘" | 트랜스크립트에서 `ulw` 감지 → ULW 모드 활성화 |
| 새 세션에서 `ulw` 없는 프롬프트 | ULW 비활성 (암묵적 해제 — 명시적 해제 불필요) |

### 3가지 강화 규칙 (Intensifiers)

ULW가 활성화되면 아래 3가지 강화 규칙이 **현재 컨텍스트에 오버레이**된다:

| 강화 규칙 | 설명 | 대화형 효과 | Autopilot 결합 효과 |
|----------|------|-----------|-------------------|
| **I-1. Sisyphus Persistence** | 최대 3회 재시도, 각 시도는 다른 접근법. 100% 완료 또는 불가 사유 보고 | 에러 시 3회까지 대안 시도 | 품질 게이트(Verification/pACS) 재시도 한도 10→15회 상향 |
| **I-2. Mandatory Task Decomposition** | TaskCreate → TaskUpdate → TaskList 필수 | 비-trivial 작업 시 태스크 분해 강제 | 변경 없음 (Autopilot은 이미 SOT 기반 추적) |
| **I-3. Bounded Retry Escalation** | 동일 대상 3회 초과 연속 재시도 금지(품질 게이트는 별도 예산 적용) — 초과 시 사용자 에스컬레이션 | 무한 루프 방지 | Safety Hook 차단은 항상 존중 |

### 런타임 강화 메커니즘

| 계층 | 메커니즘 | 강화 내용 |
|------|---------|----------|
| **Hook** (결정론적) | `_context_lib.py` — `detect_ulw_mode()` | 트랜스크립트 정규식으로 `ulw` 감지 |
| **Hook** (결정론적) | `generate_snapshot_md()` — 스냅샷 | ULW 상태 섹션을 IMMORTAL 우선순위로 보존 |
| **Hook** (결정론적) | `extract_session_facts()` — Knowledge Archive | `ulw_active: true` 태깅 → RLM 쿼리 가능 |
| **Hook** (결정론적) | `restore_context.py` — SessionStart | ULW 활성 시 3개 강화 규칙을 컨텍스트에 주입 (startup source 제외 — 암묵적 해제) |
| **Hook** (결정론적) | `_context_lib.py` — `check_ulw_compliance()` | 3개 강화 규칙 준수를 결정론적으로 검증 → 스냅샷 IMMORTAL에 경고 포함 |
| **Hook** (결정론적) | `generate_context_summary.py` — Stop | ULW Compliance 안전망 — 위반 시 stderr 경고 |

### NEVER DO
- 동일 대상에 3회 초과 연속 재시도 금지(품질 게이트는 별도 예산 적용) — I-3 위반, 사용자 에스컬레이션 필수
- Safety Hook(`(hook)` exit code 2) 차단을 ULW 명목으로 override 금지
- ULW 활성 상태에서 Task를 "일부 완료"로 남기고 멈추기 금지 — I-1 위반
- 에러 발생 시 대안 시도 없이 포기 금지 — I-1 위반
- TaskCreate 없이 암묵적으로 작업 진행 금지 (비-trivial 작업 시) — I-2 위반

## 언어 및 스타일 규칙

- **프레임워크 문서·사용자 대화**: 한국어
- **워크플로우 실행**: 영어 (AI 성능 극대화 — 절대 기준 1 근거)
- **최종 산출물**: 영어 원본 + 한국어 번역 쌍 (각 단계별 `@translator` 서브에이전트가 생성)
- **기술 용어**: 영어 유지 (e.g., SOT, Agent Team, Hooks)
- **시각화**: Mermaid 다이어그램 선호
- **깊이**: 간략 요약보다 포괄적·데이터 기반 서술 선호

### English-First 실행 원칙

워크플로우 **실행** 시 모든 에이전트(Sub-agent, Teammate)는 **영어로 작업**하고 **영어로 산출물을 생성**한다.

| 단계 | 언어 | 근거 |
|------|------|------|
| 워크플로우 설계 (workflow-generator) | 한국어 | 사용자와의 대화 |
| 워크플로우 실행 (에이전트 작업) | **영어** | AI 성능 극대화 |
| 산출물 번역 | 영어→한국어 | `@translator` 서브에이전트 |
| SOT 기록 | 언어 무관 (경로·숫자) | 구조적 데이터 |

### 번역 프로토콜 (워크플로우 실행 시)

1. 각 단계의 영어 산출물이 SOT `outputs.step-N`에 기록된 후
2. 워크플로우에 `Translation: @translator`로 표기된 단계에 한해
3. `@translator` 서브에이전트 호출 (`.claude/agents/translator.md`)
4. 번역 완료 후 SOT `outputs.step-N-ko`에 한국어 경로 기록
5. 용어 사전(`translations/glossary.yaml`)이 자동 유지됨 (RLM 외부 지속 상태)

> **번역 대상**: 텍스트 콘텐츠 산출물만 (`.md`, `.txt` 등). 코드(`.py`, `.js`), 데이터(`.json`, `.csv`), 설정(`.yaml` config) 파일은 번역하지 않는다.
> **SOT 호환성**: `step-N-ko` 키는 Anti-Skip Guard의 `.isdigit()` 가드에 의해 자동으로 건너뛰어진다 (Hook 코드 변경 없음).

## 스킬 개발 규칙

새로운 스킬을 만들거나 기존 스킬을 수정할 때:

1. **모든 절대 기준을 반드시 포함**한다 — 해당 도메인에 맞게 맥락화하여 적용 (코드 변경이 아닌 도메인의 경우 절대 기준 3은 N/A 가능).
2. **파일 간 역할 분담**을 명확히 한다 — SKILL.md(WHY), references/(WHAT/HOW/VERIFY).
3. **절대 기준 간 충돌 시나리오**를 구체적으로 명시한다 — 추상적 규칙이 아닌 실전 판단 기준.
4. 수정 후 반드시 **절대 기준 관점에서 성찰**한다 — 문구만 넣지 않고 기존 내용과 충돌 여부를 점검.

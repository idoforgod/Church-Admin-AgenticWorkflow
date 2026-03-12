# 교회 행정 시스템: 시스템 관리자 매뉴얼

> **이 문서의 범위**: 이 매뉴얼은 교회 행정 AI 시스템을 **운영·유지보수하는 시스템 관리자(IT 자원봉사자)**를 위한 안내서입니다.
> 최종 사용자(행정 간사, 담임 목사)를 위한 사용법은 [`church-admin/docs/user-guide.md`](church-admin/docs/user-guide.md)를 참조하세요.

| 문서 | 대상 독자 |
|------|---------|
| **이 문서 (`CHURCH-ADMIN-USER-MANUAL.md`)** | IT 자원봉사자 / 시스템 관리자 — 설치, 운영, 유지보수 |
| [`CHURCH-ADMIN-README.md`](CHURCH-ADMIN-README.md) | 모든 사람 — 시스템 개요 |
| [`CHURCH-ADMIN-ARCHITECTURE-AND-PHILOSOPHY.md`](CHURCH-ADMIN-ARCHITECTURE-AND-PHILOSOPHY.md) | 개발자 — 설계 철학과 아키텍처 |
| [`church-admin/docs/user-guide.md`](church-admin/docs/user-guide.md) | 최종 사용자 — 일상 사용법 |
| [`church-admin/docs/quick-start.md`](church-admin/docs/quick-start.md) | 최종 사용자 — 빠른 시작 |
| [`church-admin/docs/troubleshooting.md`](church-admin/docs/troubleshooting.md) | 모든 사람 — 문제 해결 |

---

## 1. 시스템 개요

교회 행정 AI 시스템은 한국 중소형 교회(100-500명)의 반복 행정 업무를 자동화합니다. 주당 약 23시간의 행정 업무를 약 4시간 15분으로 줄여줍니다.

**핵심 구성 요소**:
- 8개 전문 AI 에이전트 (데이터 파일당 단독 작성자)
- 5개 독립 워크플로우 (주보, 새신자, 재정, 문서, 일정)
- 29개 결정론적 데이터 검증 규칙
- 47개 한국어 자연어 명령 패턴
- 3계층 수신함 파이프라인 (Excel/CSV, Word/PDF, 이미지)
- Scan-and-Replicate 엔진 (문서 이미지 → YAML 템플릿)
- Streamlit 대시보드 (범용 채팅 인터페이스, 8개 기능 카드, P1 독립 검증)
- 4개 문서 템플릿 (주보, 순서지, 기부금영수증, 교단보고서)
- 50개 이상의 교회 용어 사전

**대상 교회 규모**: 100-500명 (YAML 리스트 기반 데이터 구조 — 이 규모에서 충분한 성능)

**시간 절감 효과**:

| 업무 | 수동 처리 | AI 자동화 | 절감 |
|------|---------|---------|------|
| 주보 제작 | 4시간 | 15분 | 94% |
| 새신자 관리 | 3시간 | 30분 | 83% |
| 재정 기록·보고 | 6시간 | 2시간 | 67% |
| 문서 발급 | 3시간 | 15분 | 92% |
| 일정 관리 | 2시간 | 15분 | 88% |
| 데이터 입력·검증 | 5시간 | 1시간 | 80% |

---

## 2. 사전 준비 및 설치

### 2.1 필수 요구사항

| 항목 | 최소 버전 | 확인 방법 |
|------|---------|---------|
| Python | 3.9+ | `python3 --version` |
| PyYAML | 6.0+ | `python3 -c "import yaml; print(yaml.__version__)"` |
| [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) | 최신 | `claude --version` |

### 2.2 선택 요구사항

| 항목 | 용도 | 설치 |
|------|------|------|
| Streamlit 1.30+ | 대시보드 (웹 UI) | `pip install streamlit` |
| openpyxl | Excel 파싱 (Tier A 파이프라인) | `pip install openpyxl` |
| pandas | 데이터 검증 (Tier A 파이프라인) | `pip install pandas` |
| chardet | 한국어 인코딩 감지 | `pip install chardet` |
| python-docx | Word 파싱 (Tier B 파이프라인) | `pip install python-docx` |

### 2.3 설치

```bash
# 저장소 클론
git clone https://github.com/idoforgod/AgenticWorkflow.git
cd AgenticWorkflow

# 인프라 건강 검증
cd church-admin
claude --init
```

`claude --init` 실행 시 `setup_church_admin.py`가 CA-1 ~ CA-8 검사를 수행합니다:

| 검사 | 내용 | 실패 시 |
|------|------|--------|
| CA-1 | Python ≥ 3.9 | Fatal (진행 불가) |
| CA-2 | PyYAML 임포트 가능 | Fatal (진행 불가) |
| CA-3 | `data/` 디렉터리 존재 | 자동 생성 |
| CA-4 | 6개 데이터 파일 존재 | 경고 |
| CA-5 | 5개 검증 스크립트 존재 | 경고 |
| CA-6 | `guard_data_files.py` Hook 존재 | 경고 |
| CA-7 | 런타임 디렉터리 존재 | 자동 생성 |
| CA-8 | SOT 파일 파싱 가능 | 경고 |

상세 설치 가이드: [`church-admin/docs/installation-guide.md`](church-admin/docs/installation-guide.md)

---

## 3. 시스템 아키텍처 개관

### 3.1 4계층 아키텍처

```
┌─────────────────────────────────────────────┐
│ 사용자 인터페이스 계층 (3가지 모드)            │
│  ① Streamlit 대시보드 (웹 UI — 범용 채팅)     │
│  ② 대화형 CLI 메뉴 (start_router → show_menu)│
│  ③ 47개 한국어 자연어 명령                    │
└──────────────────────────────────┬──────────┘
                                   ↓
┌──────────────────────────────────▼──────────┐
│ 파이프라인 계층 (3-Tier 수신함)               │
│  Tier A: Excel/CSV (신뢰도 0.95)             │
│  Tier B: Word/PDF (신뢰도 0.70)              │
│  Tier C: 이미지 (신뢰도 0.55)                │
└──────────────────────────────────┬──────────┘
                                   ↓
┌──────────────────────────────────▼──────────┐
│ 에이전트 계층 (8개 전문 Sub-agent)            │
│  bulletin-generator, finance-recorder,       │
│  member-manager, newcomer-tracker,           │
│  schedule-manager, document-generator,       │
│  data-ingestor, template-scanner             │
└──────────────────────────────────┬──────────┘
                                   ↓
┌──────────────────────────────────▼──────────┐
│ 데이터 계층 (YAML + 결정론적 검증)            │
│  6개 데이터 파일 + state.yaml (SOT)           │
│  29개 P1 검증 규칙 + 3개 Safety Hook          │
└─────────────────────────────────────────────┘
```

### 3.2 에이전트 의존성 그래프

```
schedule-manager ─────────────────────────────────┐
                                                   ↓
data-ingestor → [staging JSON] → human review → member-manager ←── newcomer-tracker
                                                   ↑                      ↓
template-scanner → [YAML templates]          finance-recorder       (정착 처리)
                        ↓                          ↑                      ↓
                  document-generator         members (교차 참조)    member-manager
                        ↑
                  bulletin-generator ← members (생일) + schedule (예배)
```

상세 아키텍처: [`CHURCH-ADMIN-ARCHITECTURE-AND-PHILOSOPHY.md`](CHURCH-ADMIN-ARCHITECTURE-AND-PHILOSOPHY.md)

---

## 4. 시스템 실행

### 4.1 기본 실행

```bash
cd church-admin
claude --init              # 최초 1회: 인프라 건강 검증 (CA-1 ~ CA-8)
claude                     # 시스템 시작
```

Claude Code가 `church-admin/CLAUDE.md`를 자동 로드하여 에이전트 로스터, SOT 규칙, 데이터 정책을 적용합니다.

### 4.2 스마트 라우터 시작 흐름

"시작", "시작하자", "메뉴" 등을 입력하면 **스마트 라우터**가 실행됩니다:

1. `start_router.py`가 `state.yaml` + Streamlit 설치 상태를 확인하여 JSON 데이터를 반환
2. 환영 배너 표시 (교회명, 시스템 상태, 데이터 무결성 — Python이 생성한 확정 텍스트)
3. `AskUserQuestion`으로 실행 모드 선택: **대화형 모드 (CLI)** 또는 **대시보드 모드 (Web UI)**
4. 선택한 모드로 분기

> **트리거 패턴** (총 20개 이상): "시작", "시작하자", "시작해줘", "시작합니다", "메뉴", "메뉴 보여줘", "도움말", "사용법", "처음", "다시 시작", "뭐 할 수 있어?", "start", "let's start", "begin", "get started" 등. 구체적 작업 지시 없는 인사말도 포함.

### 4.3 실행 모드 1 — 대화형 CLI 메뉴

"대화형 모드 (CLI)" 선택 시:

1. `show_menu.py`가 `state.yaml` + 6개 데이터 파일을 읽어 현재 상태를 수집
2. 현재 상태 요약 표시:
   ```
   현재 상태:
     교인: 42명 (활동 39명)
     새신자: 6명 관리 중
     최근 주보: 제 1250호 (2026-03-29)
     데이터 무결성: 29/29 통과
   ```
3. 긴급 알림 표시 (후속 관리 필요, 누락된 주보, 누락된 보고서)
4. 2페이지 구조의 `AskUserQuestion` 기능 메뉴 (페이지 1: 상위 3개 + "더보기", 페이지 2: 나머지)

**기능 메뉴 항목**:

| 메뉴 | 설명 | 라우팅 |
|------|------|--------|
| 주보 (Bulletin) | 현재 주보 상태 확인 → 생성/미리보기/수정 | `bulletin-data.yaml` 읽기 → 하위 메뉴 |
| 새신자 (Newcomers) | 새신자 현황 대시보드 → 등록/현황/단계변경 | `newcomers.yaml` 읽기 → 하위 메뉴 |
| 교인 관리 (Members) | 검색/등록/수정/통계 | `AskUserQuestion`으로 하위 동작 |
| 재정 (Finance) | 이번 달 요약 → 보고서/내역/영수증 | `finance.yaml` 읽기 → 하위 메뉴 |
| 일정 (Schedule) | 이번 주 일정 → 확인/등록/예약 | `schedule.yaml` 읽기 → 하위 메뉴 |
| 문서 발급 (Documents) | 증명서/이명증서/공문/회의록 | `AskUserQuestion`으로 문서 유형 선택 |
| 시스템 관리 (System) | 전체 P1 검증 실행 → 한국어 결과 | `validate_all.py` 실행 |

### 4.4 실행 모드 2 — Streamlit 대시보드 (웹 UI)

비기술 사용자(행정 간사, 담임 목사)를 위한 웹 브라우저 기반 인터페이스입니다.

#### 실행 방법

```bash
cd church-admin
pip install streamlit pyyaml          # 최초 1회
streamlit run dashboard/app.py        # 대시보드 시작
```

브라우저에서 `http://localhost:8501`로 접근합니다. 포트 충돌 시 `--server.port 8502`로 변경 가능.

#### 대시보드 구조

```
┌─────────────────────────────────────────────────────────────────┐
│  ⛪ 소망과사랑의교회                              [새 대화]    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────┐│
│  │ 📰 주보 생성  │  │ 👋 새신자 관리│  │ 👥 교인 관리  │  │ 💰  ││
│  │              │  │              │  │              │  │재정  ││
│  └──────────────┘  └──────────────┘  └──────────────┘  │보고서││
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │(이중 ││
│  │ 📅 일정 관리  │  │ 📄 문서 발급  │  │ ✅ 데이터 검증│  │승인  ││
│  │              │  │              │  │              │  │필요) ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────┘│
│  ────────────────────────────────────────────────────────────── │
│  💬 메시지를 입력하세요 (예: 주보 만들어줘, 김영희 새신자 등록)    │
└─────────────────────────────────────────────────────────────────┘
           │                                    │
     사이드바: 시스템 상태                   채팅 영역:
      교인 39명, 새신자 6명                 대화 히스토리 +
      최근 주보 #1250                     P1 검증 결과 인라인
      데이터 검증 29/29                    HitL 승인 패널
```

#### 8개 기능 카드

카드를 클릭하면 해당 한국어 명령이 자동으로 채팅에 전송되어 Claude가 작업을 실행합니다.

| 카드 | 아이콘 | 전송되는 명령 | 위험 수준 |
|------|-------|-------------|---------|
| **주보 생성** | 📰 | "주보 만들어줘" | LOW |
| **새신자 관리** | 👋 | "새신자 현황 보여줘" | MEDIUM |
| **교인 관리** | 👥 | "교인 관리" | MEDIUM |
| **재정 보고서** | 💰 | "재정 보고서 만들어줘" | HIGH (이중 승인 필요) |
| **일정 관리** | 📅 | "이번 주 일정 보여줘" | LOW |
| **문서 발급** | 📄 | "문서 발급" | MEDIUM |
| **데이터 검증** | ✅ | "데이터 검증 실행해줘" | LOW |
| **시스템 상태** | 🔧 | "시스템 상태 보여줘" | LOW |

#### 대시보드 핵심 기능

| 기능 | 설명 | 기술 구현 |
|------|------|---------|
| **범용 채팅** | 카드 클릭 또는 자유 텍스트 입력으로 모든 기능 실행 | `command_bridge.py` NL 라우팅 → `claude -p` subprocess |
| **세션 연속성** | 다중 턴 대화 — 이전 응답 기반 후속 질문 가능 | `--resume` 세션 ID 기반 대화 이어가기 |
| **시스템 상태 패널** | 사이드바에 4개 메트릭 (교인, 새신자, 주보, 검증) 실시간 표시 | `sot_watcher.py` → `show_menu.py` JSON 파싱 |
| **실시간 진행** | 작업 실행 중 도구 사용 현황 표시 | `stream_parser.py` → stream-json 이벤트 파싱 |
| **P1 독립 검증** | 작업 완료 후 대시보드가 직접 `validate_*.py` 실행 | `post_execution_validator.py` — LLM 밖에서 Python 실행 |
| **HitL 승인 UI** | 재정 등 고위험 작업의 승인/반려/수정 요청 3버튼 | `hitl_panel.py` — P1 검증 결과를 기계적 신호로 표시 |
| **Cold Start 해결** | 매 subprocess에 SOT 상태, 검증 기준, 도메인 제약 자동 주입 | `context_builder.py` — AST로 검증 규칙 추출 → `--append-system-prompt` |
| **주보 미리보기** | 2단 신문 스타일 레이아웃으로 현재 주보 미리보기 | `bulletin_viewer.py` — HTML/CSS 렌더링 |
| **실행 취소** | 진행 중 작업 취소 버튼 | `ClaudeRunner.cancel()` → `process.terminate()` |
| **실행 로그** | 모든 대시보드 실행을 YAML 로그로 감사 추적 | `dashboard-logs/{timestamp}.yaml` |

#### 대시보드 엔진 구성

| 모듈 | 역할 | SOT 접근 |
|------|------|---------|
| `dashboard/app.py` | 메인 앱 — 기능 카드, 채팅, 진행 표시 | 읽기 전용 |
| `engine/claude_runner.py` | `claude -p` subprocess 실행기 (비동기, 단일 프로세스 보장) | 읽기 전용 |
| `engine/sot_watcher.py` | `state.yaml` 실시간 변경 감지 | 읽기 전용 |
| `engine/context_builder.py` | Cold Start 해결 — AST 규칙 추출 + `--append-system-prompt` | 읽기 전용 |
| `engine/post_execution_validator.py` | P1 독립 검증 — `validate_*.py`를 LLM 밖에서 실행 | 읽기 전용 |
| `engine/command_bridge.py` | NL 라우팅 (47개 패턴) + 카드 메타데이터 | 읽기 전용 |
| `engine/stream_parser.py` | Claude stream-json 이벤트 파싱 | 읽기 전용 |
| `components/status_panel.py` | 사이드바 4개 메트릭 카드 렌더링 | 읽기 전용 |
| `components/progress_panel.py` | 실행 중 진행 상태 표시 | 읽기 전용 |
| `components/result_panel.py` | 실행 결과 텍스트 + 파일 링크 렌더링 | 읽기 전용 |
| `components/hitl_panel.py` | HitL 승인/반려/수정 요청 UI | 읽기 전용 |
| `components/bulletin_viewer.py` | 2단 레이아웃 주보 미리보기 | 읽기 전용 |
| `pages/1_📋_주보_미리보기.py` | 전용 주보 미리보기 페이지 (사이드바 접근) | 읽기 전용 |

> **핵심 설계 원칙**: 대시보드의 모든 컴포넌트는 `state.yaml`을 읽기 전용으로만 접근합니다 (SOT 규율 준수). 데이터 수정은 Claude Code subprocess를 통해서만 이루어집니다.

#### 대시보드 주의사항

- 대시보드는 동시에 **하나의 작업만** 실행할 수 있습니다 (`threading.Lock` 보장)
- 재정 관련 작업은 대시보드에서도 **Autopilot이 영구 비활성화**됩니다
- 대시보드 사용 중에는 CLI 세션에서 동시 데이터 수정을 피하세요
- `CLAUDECODE` 환경변수는 대시보드가 자동 제거합니다 (중첩 세션 방지)
- 실행 로그는 `church-admin/dashboard-logs/`에 YAML로 저장됩니다

### 4.5 실행 모드 3 — Slash Commands

시스템 관리자(IT 자원봉사자)를 위한 구조화된 진입점입니다:

| Command | 파일 | 설명 | 사용 예시 |
|---------|------|------|---------|
| `/start` | `.claude/commands/start.md` | 스마트 라우터 시작 메뉴 | 현재 상태 확인 + 모드 선택 + 작업 선택 |
| `/generate-bulletin` | `.claude/commands/generate-bulletin.md` | 주보 생성 파이프라인 | 다음 주보 생성 (데이터 완전성 → 생성 → 검증 → HitL) |
| `/generate-finance-report` | `.claude/commands/generate-finance-report.md` | 월별 재정 보고서 | 이번 달 재정 보고 (이중 검토 필수) |
| `/system-status` | `.claude/commands/system-status.md` | 시스템 건강 검사 | SOT 상태, 데이터 파일, 검증 상태, 인프라 확인 |
| `/validate-all` | `.claude/commands/validate-all.md` | 전체 P1 검증 | 29개 규칙 한 번에 검증 |

### 4.6 한국어 자연어 명령

시스템은 47개 한국어 명령 패턴을 인식합니다. 8개 카테고리로 분류됩니다:

**주보 (Bulletin)** — 4개 명령:
```
"주보 만들어줘"        → 주보 생성 워크플로우
"주보 미리보기"        → 현재 주보 초안 확인
"주보 항목 수정"       → 주보 데이터 편집
"예배 순서 만들어줘"   → 순서지 생성
```

**새신자 (Newcomer)** — 6개 명령:
```
"새신자 등록"          → 새신자 파이프라인 시작
"새신자 현황"          → 새신자 상태 대시보드
"환영 메시지 작성"     → 환영 메시지 생성 (개인화, 목양 담당 배정)
"재방문 확인"          → 14일 재방문 체크
"단계 진행"            → 여정 단계 전환 (HitL 필수)
"정착 처리"            → 교인 전환 (HitL 필수, 6단계 전 이수 확인)
```

**교인 (Member)** — 8개 명령:
```
"교인 검색 김철수"     → 이름으로 교인 검색
"교인 등록"            → 새 교인 등록
"교인 정보 수정"       → 교인 정보 수정
"이명 처리"            → 전입/전출 처리 (이명증서 자동 생성)
"생일 축하 대상"       → 이번 주 생일 교인 조회
"결혼기념일 대상"      → 이번 주 결혼기념일 조회
"교인 통계"            → 교인 현황 통계
"가족 연결"            → 가족 그룹 연결 (2명 이상 동일 family_id)
```

**재정 (Finance)** — 5개 명령 (모든 쓰기 작업에 이중 검토 필수):
```
"재정 보고서"          → 월별 재정 보고서 생성
"헌금 내역"            → 헌금 기록 조회
"지출 내역"            → 지출 기록 조회
"예산 현황"            → 예산 대비 실적 조회
"기부금 영수증 발행"   → 기부금영수증 발급 (소득세법 제34조 준수)
```

**일정 (Schedule)** — 4개 명령:
```
"이번 주 일정"         → 금주 일정 조회
"예배 시간"            → 정기 예배 시간표
"행사 등록"            → 행사 추가 (충돌 자동 감지)
"시설 예약"            → 시설 예약 (시설 이중 예약 자동 방지)
```

**문서 (Document)** — 5개 명령:
```
"증명서 발급"          → 세례증서, 임직증서 등
"이명증서 발급"        → 이명증서 생성 (재적 기간 자동 계산)
"공문 작성"            → 공문 생성
"당회 결의문 작성"     → 당회 회의록 + 투표 기록
"회의록 작성"          → 회의록 생성
```

**데이터 입력 (Data Import)** — 4개 명령:
```
"파일 가져오기"        → inbox 3-Tier 파이프라인 실행
"엑셀 가져오기"        → Tier A 파서 (Excel/CSV, 신뢰도 0.95)
"사진 분석"            → Tier C 파서 (이미지, 신뢰도 0.55)
"확인 대기"            → HitL 대기 목록 확인 (staging → 확인 → 머지)
```

**시스템 (System)** — 5개 명령:
```
"데이터 검증"          → 전체 P1 검증 실행 (29개 규칙)
"시스템 상태"          → 건강 검사
"용어 사전"            → 교회 용어 사전 검색
"도움말"               → 사용 가능한 명령 표시
"백업"                 → 데이터 백업 실행
```

---

## 5. 5개 독립 워크플로우

### 5.1 주간 주보 생성

- **트리거**: "주보 만들어줘" 또는 `/generate-bulletin`
- **위험도**: LOW (Autopilot 허용)
- **에이전트**: `@bulletin-generator`, `@schedule-manager`
- **산출물**: `bulletins/{날짜}-bulletin.md`, `bulletins/{날짜}-worship-order.md`
- **16개 변수 영역 (VR-BUL-01 ~ VR-BUL-16)**: 호수, 날짜, 설교 제목/본문/설교자, 예배 순서 테이블, 공지사항, 기도제목, 생일/결혼기념일 축하, 헌금 봉사팀, 다음 주 예고, 주간 일정, 교회 연락처
- **교차 참조**: `members.yaml` (생일), `schedule.yaml` (예배 시간)
- **검증**: B1-B3 (날짜 일관성, 호수 연속, 교인 참조 무결성)

### 5.2 새신자 관리 파이프라인

- **트리거**: "새신자 등록" 또는 이벤트 기반 (새 방문자)
- **위험도**: MEDIUM (부분 Autopilot)
- **에이전트**: `@newcomer-tracker`, `@member-manager` (정착 시)
- **6단계 여정 모델**:
  1. `first_visit` (첫 방문)
  2. `attending` (출석 중) — 조건: 첫 방문 확인
  3. `small_group` (소그룹 참여) — 조건: 환영 전화 + 재방문
  4. `baptism_class` (세례반) — 조건: 소그룹 소개
  5. `baptized` (세례 완료) — 조건: 세례 이수
  6. `settled` (정착) — 조건: 6개 이정표 완료 → `@member-manager`에 인계
- **자동 알림**: 14일 재방문 미확인, 참여 정체, 이정표 지연
- **검증**: N1-N6 (ID 고유성, 이정표 선행조건, 정착 교차 참조 일관성)

### 5.3 월별 재정 보고서

- **트리거**: "재정 보고서" 또는 `/generate-finance-report`
- **위험도**: HIGH (Autopilot 영구 비활성화)
- **에이전트**: `@finance-recorder`, `@reviewer` (적대적 검토), `@fact-checker` (사실 검증)
- **3중 안전 장치**: SOT 설정 + 에이전트 명세 + 워크플로우 정의에서 Autopilot 영구 비활성화
- **기능**: 헌금 7개 유형(십일조, 감사헌금, 특별헌금, 선교헌금, 건축헌금, 주일헌금, 기타) / 지출 6개 유형(관리비, 인건비, 사역비, 선교비, 교육비, 기타) / 월간 요약 / 예산 대비 분석 / 기부금영수증 발급
- **기부금영수증**: 한글 금액 표기 (예: 금 삼백팔십오만원정), 주민등록번호 마스킹 (XXXXXX-X*****), 소득세법 제34조 준수
- **삭제 정책**: Void-only (절대 삭제 불가, `void: true`로 무효 처리)
- **검증**: F1-F7 (ID 형식, 금액 양수, 헌금 합계 정합성, 예산 산술, 월간 요약 정확성)

### 5.4 문서 발급

- **트리거**: "증명서 발급", "공문 작성" 등
- **위험도**: MEDIUM (Autopilot 허용)
- **에이전트**: `@document-generator`, `@template-scanner`
- **지원 문서 유형**:
  - 세례증서 (집례자, 세례 유형)
  - 임직증서 (직분, 안수일)
  - 이명증서 (재적 기간 자동 계산)
  - 당회 결의문 (회의록 + 투표 기록)
  - 공문 (교회 공식 서신)
  - 기부금영수증 (법적 서식)
- **산출물**: `docs/generated/` 디렉터리
- **템플릿 엔진**: `templates/*.yaml` 기반 슬롯 렌더링 (text, date, currency, list, table, reference 타입)

### 5.5 일정 관리

- **트리거**: "행사 등록", "시설 예약" 등
- **위험도**: LOW (Autopilot 허용)
- **에이전트**: `@schedule-manager`
- **기능**: 정기 예배 (주일예배, 수요예배, 금요기도회, 새벽기도), 특별 행사 (부활절, 추수감사절, 성탄절, 수련회), 시설 예약 (충돌 자동 감지), 상태 추적 (planned → confirmed → completed → cancelled)
- **주보 연동**: 주간 일정을 주보 생성 시 자동 참조
- **검증**: S1-S6 (ID 형식, 시간 형식, 반복 이벤트 패턴, 시설 이중 예약 감지)

---

## 6. 스크립트 인벤토리

### 6.1 핵심 스크립트

| 스크립트 | 용도 | 주요 인자 |
|---------|------|---------|
| `scripts/start_router.py` | 스마트 라우터 (P1 할루시네이션 봉쇄) | `--state state.yaml` |
| `scripts/show_menu.py` | 상태 기반 메뉴 생성 (상태+알림+메뉴 JSON) | `--state state.yaml --data-dir data/` |
| `scripts/validate_all.py` | 5개 검증 스크립트 통합 실행 (29개 규칙) | `--data-dir data/` |
| `scripts/query_church_data.py` | 결정론적 데이터 조회 (14개 쿼리 함수) | `--data-dir data/ --query {name} --params '{}'` |
| `scripts/validate_claude_md.py` | CLAUDE.md 자기 일관성 검증 | (없음) |
| `scripts/validate_finance_safety.py` | 재정 3중 안전장치 검증 (FS1-FS3) | (없음) |

### 6.2 수신함 파이프라인 스크립트

| 스크립트 | 용도 | 입력 → 출력 |
|---------|------|-----------|
| `scripts/inbox_parser.py` | 3-Tier 파이프라인 오케스트레이터 | `inbox/documents/` → `inbox/staging/` |
| `scripts/tier_a_parser.py` | Excel/CSV 구조 데이터 파서 | `.xlsx`, `.csv` → JSON 스테이징 |
| `scripts/tier_b_parser.py` | Word/PDF 반구조 데이터 파서 | `.docx`, `.pdf` → JSON 스테이징 |
| `scripts/tier_c_parser.py` | 이미지/비전 파서 | `.jpg`, `.png` → JSON 스테이징 |
| `scripts/hitl_confirmation.py` | Human-in-the-Loop 확인 UI | 스테이징 JSON → 승인/수정/거부 |

### 6.3 템플릿 및 생성 스크립트

| 스크립트 | 용도 | 입력 → 출력 |
|---------|------|-----------|
| `scripts/template_engine.py` | 템플릿 YAML → Markdown 문서 생성 | 템플릿 + 데이터 YAML → `.md` |
| `scripts/template_scanner.py` | Scan-and-Replicate (문서 이미지 → YAML 템플릿) | 이미지 → 템플릿 YAML |
| `scripts/generate_seed_data.py` | 시드 데이터 생성 (최초 1회) | 하드코딩 → 6개 YAML 파일 |

### 6.4 데이터 조회 함수 (`query_church_data.py`)

| 쿼리 이름 | 위험도 | 설명 |
|----------|--------|------|
| `finance_monthly_summary` | HIGH | 월별 재정 요약 |
| `finance_budget_variance` | HIGH | 예산 대비 실적 분석 |
| `finance_ytd_summary` | HIGH | 연간 누적 재정 요약 |
| `newcomer_overdue_followups` | MEDIUM | 후속 관리 지연 새신자 |
| `member_birthdays_in_range` | LOW | 기간 내 생일 교인 |
| `member_stats` | LOW | 교인 현황 통계 |
| `newcomer_stats` | LOW | 새신자 현황 통계 |
| `newcomer_by_stage` | LOW | 단계별 새신자 분포 |
| `member_family_resolve` | LOW | 가족 그룹 해석 |
| `next_id` | LOW | 다음 사용 가능 ID 생성 |
| `schedule_for_week` | LOW | 주간 일정 조회 |
| `bulletin_generation_history` | LOW | 주보 생성 이력 |
| `korean_currency_format` | LOW | 한글 금액 변환 |

---

## 7. SOT (Single Source of Truth) 이해

### 7.1 `state.yaml` 구조

`state.yaml`은 시스템의 중앙 상태 파일입니다. **Orchestrator만 쓰기 가능**, 모든 에이전트는 읽기 전용.

```yaml
church:
  name: "소망과사랑의교회"
  denomination: "PCK"
  current_bulletin_issue: 1250
  status: "active"

  data_paths:            # 6개 데이터 파일 경로 레지스트리
    members: "data/members.yaml"
    finance: "data/finance.yaml"
    schedule: "data/schedule.yaml"
    newcomers: "data/newcomers.yaml"
    bulletin: "data/bulletin-data.yaml"
    glossary: "data/church-glossary.yaml"

  features:              # 기능 플래그 (워크플로우 활성화 여부)
    bulletin_generation: true
    newcomer_pipeline: true
    finance_reporting: true
    document_generation: true
    denomination_reports: false    # 향후 확장

  workflow_states:       # 워크플로우별 상태 추적
    bulletin:  { last_generated_issue, last_generated_date, next_due_date, status }
    newcomer:  { total_active, last_check_date, last_report, status }
    finance:   { current_month, next_due_month, last_report_date, outputs, status }
    schedule:  { last_updated, last_report, status }
    document:  { last_generated, last_document_type, generated_samples, status }

  legal_info:            # 법적 정보 (기부금영수증용)
    registration_number: "123-82-01234"
    address: "서울시 마포구 성산로 123"
    representative: "이성훈"
    representative_title: "담임목사"
    phone: "02-1234-5678"
    bank_account: "국민은행 012-345-67-890123"

  config:
    autopilot:
      enabled: false
      finance_override: false     # 항상 false — 재정 Autopilot 영구 비활성화
    backup:
      enabled: true
      backup_dir: "backups/"
    scale:
      max_members: 500            # 설계 용량

  verification_gates:    # 마지막 검증 실행 결과
    members:   { last_run, result, rules }
    finance:   { last_run, result, rules }
    schedule:  { last_run, result, rules }
    newcomers: { last_run, result, rules }
    bulletin:  { last_run, result, rules }
    aggregate: { last_run, total_passed, total_checks }

  agent_sessions:        # 에이전트별 마지막 활동 추적
    bulletin-generator:  { last_active, last_action }
    newcomer-tracker:    { last_active, last_action }
    member-manager:      { last_active, last_action }
    finance-recorder:    { last_active, last_action }
    schedule-manager:    { last_active, last_action }
    document-generator:  { last_active, last_action }
    data-ingestor:       { last_active, last_action }
    template-scanner:    { last_active, last_action }
```

### 7.2 데이터 파일 수정 규칙

**핵심 원칙**: 각 데이터 파일은 지정된 에이전트만 수정할 수 있습니다 (`guard_data_files.py` Hook이 강제).

| 데이터 파일 | 단독 작성자 | 검증 규칙 | 민감도 | 삭제 정책 |
|-----------|-----------|---------|--------|---------|
| `data/members.yaml` | `member-manager` | M1-M7 (7개) | HIGH (PII) | Soft-delete만 |
| `data/finance.yaml` | `finance-recorder` | F1-F7 (7개) | HIGH (재정) | Void-only (절대 삭제 불가) |
| `data/schedule.yaml` | `schedule-manager` | S1-S6 (6개) | LOW | Status cancel |
| `data/newcomers.yaml` | `newcomer-tracker` | N1-N6 (6개) | HIGH (PII) | Soft-delete만 |
| `data/bulletin-data.yaml` | `bulletin-generator` | B1-B3 (3개) | LOW | 호수별 덮어쓰기 |
| `data/church-glossary.yaml` | 모든 에이전트 | — | LOW | Append-only (기존 항목 수정 불가) |

수동 수정이 불가피한 경우, **반드시 검증을 다시 실행**하세요:

```bash
python3 scripts/validate_all.py
```

---

## 8. 검증 스크립트 실행

### 8.1 전체 검증

```bash
cd church-admin
python3 scripts/validate_all.py
```

29개 규칙을 한 번에 검증합니다. 출력 예시:
```
Members:   7/7 PASS (M1-M7)
Finance:   7/7 PASS (F1-F7)
Schedule:  6/6 PASS (S1-S6)
Newcomers: 6/6 PASS (N1-N6)
Bulletin:  3/3 PASS (B1-B3)
━━━━━━━━━━━━━━━━━━━━━━━━━━
Total:     29/29 PASS
```

### 8.2 개별 검증

```bash
# 교인 데이터 검증 (M1-M7)
python3 .claude/hooks/scripts/validate_members.py --data-dir data/

# 재정 데이터 검증 (F1-F7)
python3 .claude/hooks/scripts/validate_finance.py --data-dir data/

# 일정 데이터 검증 (S1-S6)
python3 .claude/hooks/scripts/validate_schedule.py --data-dir data/

# 새신자 데이터 검증 (N1-N6)
python3 .claude/hooks/scripts/validate_newcomers.py --data-dir data/

# 주보 데이터 검증 (B1-B3)
python3 .claude/hooks/scripts/validate_bulletin.py --data-dir data/

# 재정 3중 안전장치 검증 (FS1-FS3)
python3 scripts/validate_finance_safety.py

# CLAUDE.md 자기 일관성 검증
python3 scripts/validate_claude_md.py
```

각 스크립트는 JSON 출력을 제공합니다:
```json
{
  "valid": true,
  "script": "validate_members.py",
  "checks": [
    {"rule": "M1", "name": "ID Uniqueness", "status": "PASS"},
    {"rule": "M2", "name": "Required Fields", "status": "PASS"}
  ],
  "summary": "7/7 checks passed"
}
```

### 8.3 검증 규칙 상세

| 규칙 | 이름 | 검증 내용 |
|------|------|---------|
| **M1** | ID 고유성 | `M\d{3,}` 형식, 중복 없음 |
| **M2** | 필수 필드 | name, status 필수 |
| **M3** | 전화 형식 | `010-NNNN-NNNN` 형식 |
| **M4** | 상태 열거형 | active/inactive/transferred/deceased |
| **M5** | 가족 ID 참조 | family_id 교차 참조 무결성 |
| **M6** | 날짜 유효성 | ISO 8601 형식 |
| **M7** | 통계 산술 | `_stats`가 실제 카운트와 일치 |
| **F1** | ID 형식 | `OFF-YYYY-NNN`, `EXP-YYYY-NNN` |
| **F2** | 금액 양수 | 모든 금액 > 0 (KRW 정수) |
| **F3** | 헌금 합계 | 헌금 합계 = 개별 항목 합 |
| **F4** | 예산 산술 | 예산 계산 정확성 |
| **F5** | 월간 요약 | 월간 요약 = 개별 항목 집계 |
| **F6** | 교인 참조 | 기부자 member_id가 members.yaml에 존재 |
| **F7** | 유형 열거형 | 헌금/지출 유형이 허용된 값 |
| **S1** | 이벤트 ID | 고유 ID 형식 |
| **S2** | 날짜 유효성 | 유효한 날짜 형식 |
| **S3** | 시간 형식 | 예배 시간 형식 |
| **S4** | 시설 가용성 | 예약 가능 여부 |
| **S5** | 시설 충돌 | 이중 예약 감지 |
| **S6** | 반복 이벤트 | 반복 패턴 유효성 |
| **N1** | ID 고유성 | `NW\d+` 형식, 중복 없음 |
| **N2** | 필수 필드 | 필수 정보 존재 |
| **N3** | 여정 단계 | 유효한 단계 열거형 |
| **N4** | 이정표 순서 | 이정표 날짜 순서 |
| **N5** | 교인 참조 | 정착 시 member_id 무결성 |
| **N6** | 후속 관리 | 지연 감지 (14일) |
| **B1** | 날짜 일관성 | 주보 날짜/구조 유효 |
| **B2** | 호수 연속 | 호수 중복/누락 없음 |
| **B3** | 교인 참조 | 생일/기념일 ID가 members.yaml에 존재 |

### 8.4 검증 실패 대응

검증 실패 시:
1. `errors` 배열에서 실패한 규칙과 상세 메시지 확인
2. 해당 데이터 파일의 문제 부분 수정
3. 검증 재실행으로 수정 확인
4. **재정 데이터 검증 실패 시**: 반드시 재정 담당자와 확인 후 수정

---

## 9. 8개 전문 에이전트

### 9.1 에이전트 로스터

| 에이전트 | 역할 | 모델 | 쓰기 대상 | 민감도 |
|---------|------|------|---------|--------|
| `bulletin-generator` | 주간 주보 생성 (16개 변수 영역) | Sonnet | `bulletin-data.yaml`, `bulletins/` | LOW |
| `newcomer-tracker` | 새신자 6단계 여정 관리 | Sonnet | `newcomers.yaml` | HIGH (PII) |
| `member-manager` | 교인 CRUD + 수명주기 + 가족 연결 | Sonnet | `members.yaml` | HIGH (PII) |
| `finance-recorder` | 헌금, 지출, 영수증, 보고서 | Opus | `finance.yaml`, `output/` | HIGH (재정) |
| `schedule-manager` | 예배, 행사, 시설 예약 | Sonnet | `schedule.yaml` | LOW |
| `document-generator` | 증명서, 공문, 회의록 생성 | Sonnet | `docs/generated/` | MEDIUM |
| `data-ingestor` | 3-Tier 수신함 파이프라인 | Opus | `inbox/staging/` | MEDIUM |
| `template-scanner` | 문서 이미지 → YAML 템플릿 변환 | Opus | `templates/` | LOW |

> **모델 배정 근거**: Opus(고추론)는 재정(정확성 최우선), 데이터 파싱(복잡한 변환), 템플릿 분석(비전 분석)에 배정. Sonnet은 템플릿 기반 반복 작업에 배정.

### 9.2 에이전트 정의 파일 위치

모든 에이전트 정의는 `church-admin/.claude/agents/` 디렉터리에 있습니다:

```
.claude/agents/
├── bulletin-generator.md
├── finance-recorder.md
├── member-manager.md
├── newcomer-tracker.md
├── schedule-manager.md
├── document-generator.md
├── data-ingestor.md
└── template-scanner.md
```

---

## 10. 템플릿 시스템

### 10.1 문서 템플릿

4개의 YAML 기반 문서 템플릿이 `templates/` 디렉터리에 있습니다:

| 템플릿 | 문서 유형 | 슬롯 수 | 용지 | 용도 |
|--------|---------|--------|------|------|
| `bulletin-template.yaml` | 주보 (주보) | 16개 | A4 2쪽 | 매주 (52회/년) |
| `worship-template.yaml` | 예배 순서지 | 8-10개 | A4 1쪽 | 매주 (주보 동반) |
| `receipt-template.yaml` | 기부금영수증 | 6개 | A5/A4 | 요청 시 |
| `denomination-report-template.yaml` | 교단 보고서 | 5개 | A4 | 월/분기 (향후) |

### 10.2 Scan-and-Replicate 엔진

기존 문서 이미지를 분석하여 재사용 가능한 YAML 템플릿을 자동 생성합니다:

1. `@template-scanner`에 문서 이미지 제공
2. 비전 분석으로 레이아웃, 고정/변수 영역, 슬롯 유형 추출
3. YAML 템플릿 생성 후 HitL 확인
4. `templates/`에 저장 → `@document-generator`가 사용

**지원 문서 유형**: 주보, 순서지, 영수증, 교단보고서, 증명서, 공문, 회의록 (7종)

---

## 11. 수신함 파이프라인 (3-Tier)

비기술 사용자가 다양한 형식의 파일을 쉽게 시스템에 입력할 수 있습니다.

### 11.1 파이프라인 흐름

```
inbox/documents/에 파일 드롭
        ↓
  확장자 기반 Tier 라우팅
        ↓
  ┌────────────────────────────────────┐
  │ Tier A: Excel/CSV   → 신뢰도 0.95 │
  │ Tier B: Word/PDF    → 신뢰도 0.70 │
  │ Tier C: 이미지       → 신뢰도 0.55 │
  └────────────────────────────────────┘
        ↓
  inbox/staging/ (JSON 스테이징)
        ↓
  hitl_confirmation.py (인간 확인)
        ↓
  ┌──────────────────┐  ┌──────────────┐
  │ 승인 → 데이터 머지 │  │ 거부 → errors │
  └──────────────────┘  └──────────────┘
```

### 11.2 디렉터리 구조

```
inbox/
├── documents/     ← 파일 드롭 영역
├── staging/       ← 파싱 결과 JSON (HitL 대기)
├── processed/     ← 처리 완료 원본
└── errors/        ← 파싱 실패 파일 + .error.json
```

### 11.3 한국어 인코딩 처리

시스템은 자동으로 한국어 인코딩을 감지하고 변환합니다:
- EUC-KR → CP949 → UTF-8-SIG → UTF-8 순서로 시도
- `chardet` 라이브러리로 인코딩 자동 감지

---

## 12. Hook 인프라 이해

시스템은 3개의 Hook이 `church-admin/.claude/settings.json`에 정의되어 **자동으로** 적용됩니다. `git clone`만으로 Hook 인프라가 동작합니다.

### 12.1 Hook 구성

| Hook | 트리거 | 스크립트 | 역할 | Exit Code |
|------|--------|---------|------|-----------|
| **PreToolUse** | Edit/Write 호출 시 | `guard_data_files.py` | 단독 작성자가 아닌 에이전트의 데이터 파일 쓰기 차단 | 0: 허용, 2: 차단 |
| **PostToolUse** | Write 완료 후 | `validate_yaml_syntax.py` | `.yaml` 파일의 YAML 구문 오류 경고 | 0: 정상, 1: 경고 |
| **Setup** | `claude --init` | `setup_church_admin.py` | CA-1~CA-8 인프라 건강 검증 | 0: 통과, 1: 실패 |

### 12.2 Hook 동작 원리

1. **쓰기 시도** → `guard_data_files.py` 자동 실행
2. `CLAUDE_AGENT_NAME` 환경변수를 Sole-Writer Matrix와 대조
3. **일치** → exit code 0 (허용) → `validate_yaml_syntax.py` 구문 검증
4. **불일치** → exit code 2 (**차단**) + stderr 피드백 → 재시도 금지, Orchestrator에게 위임

### 12.3 Hook 문제 진단

| 증상 | 원인 | 해결 |
|------|------|------|
| 에이전트 쓰기가 차단됨 (exit code 2) | `guard_data_files.py`가 비인가 에이전트 감지 | Write Permission Matrix 확인 (§7.2) |
| YAML 구문 경고 | `validate_yaml_syntax.py` 감지 | 해당 YAML 파일 구문 수정 |
| `claude --init` 실패 | CA-1 또는 CA-2 실패 | Python 3.9+ 설치 확인, `pip install pyyaml` |

---

## 13. 4계층 품질 보장 스택

모든 워크플로우 단계는 최대 4계층 검증을 통과해야 진행합니다:

| 계층 | 이름 | 검증자 | 기준 | 실패 시 |
|------|------|--------|------|--------|
| **L0** | Anti-Skip Guard | Hook 코드 (`validate_step_output()`) | 산출물 파일 존재 + ≥100 bytes + 비-공백 | 진행 차단 |
| **L1** | Verification Gate | 에이전트 자기 검증 | `Verification:` 기준 100% 달성 | 최대 10회 재시도 |
| **L1.5** | pACS Self-Rating | 에이전트 Pre-mortem + F/C/L 채점 | pACS = min(F,C,L). RED(< 50) → 재작업 | 재작업 |
| **L2** | Adversarial Review | `@reviewer`/`@fact-checker` | 독립적 적대적 검토 | 재작업 |

> **진행 규칙**: L0은 모든 단계 필수. L1은 `Verification:` 필드 있는 단계만. L1.5는 L1 통과 후. L2는 `Review:` 필드 있는 단계만.

### 13.1 대시보드의 독립 검증

대시보드는 Claude의 출력을 신뢰하지 않고, **Python 코드로 직접 검증**합니다:

1. Claude subprocess 완료 후
2. `post_execution_validator.py`가 해당 `validate_*.py`를 직접 subprocess 실행
3. JSON 결과를 파싱하여 PASS/FAIL 판정
4. 채팅에 인라인 배지로 표시 (P1 검증 통과/실패)

이 검증은 LLM 밖에서 수행되므로 할루시네이션이 불가합니다.

---

## 14. 생성된 샘플 문서

시스템에 포함된 샘플 산출물:

### 14.1 주보

- `bulletins/` — 3개 샘플 주보 + 예배 순서지 (2026년 3월)

### 14.2 공식 문서 (`docs/generated/`)

| 파일 | 문서 유형 |
|------|---------|
| `sample-baptism-certificate.md` | 세례증서 |
| `sample-ordination-certificate.md` | 임직증서 |
| `sample-transfer-certificate.md` | 이명증서 |
| `sample-meeting-minutes.md` | 당회 회의록 |
| `sample-official-letter.md` | 공문 |
| `sample-donation-receipt.md` | 기부금영수증 |

### 14.3 보고서 (`docs/generated/`)

| 파일 | 보고서 유형 |
|------|-----------|
| `2026-02-finance-report.md` | 2월 재정 보고서 |
| `2026-03-finance-report.md` | 3월 재정 보고서 |
| `newcomer-status-report-2026-03.md` | 새신자 현황 보고서 |
| `schedule-monthly-2026-03.md` | 월간 일정 보고서 |
| `member-directory-summary.md` | 교인 디렉터리 요약 |

---

## 15. 교회 용어 사전

`data/church-glossary.yaml`에 50개 이상의 한국어 교회 용어가 정의되어 있습니다. 모든 에이전트가 이 용어를 정규화에 사용합니다.

| 카테고리 | 한국어 용어 | 시스템 식별자 |
|---------|-----------|------------|
| **직분** | 목사, 장로, 집사, 권사, 성도, 구역장 | pastor, elder, deacon, deaconess, member, cell_leader |
| **치리** | 당회, 제직회, 공동의회, 노회 | session, diaconate, general_assembly, presbytery |
| **예배** | 찬양, 기도, 봉헌, 축도, 주보 | praise, prayer, offering, benediction, bulletin |
| **재정** | 십일조, 감사헌금, 건축헌금, 선교헌금, 주일헌금 | tithe, thanksgiving, building, mission, sunday |
| **성례** | 세례, 유아세례, 입교, 성찬식 | baptism, infant_baptism, confirmation, communion |
| **새신자** | 방문자, 등록, 정착, 목양 | visitor, registration, settlement, pastoral_care |
| **문서** | 이명증서, 기부금영수증, 증명서, 회의록 | transfer_cert, donation_receipt, certificate, minutes |

> **교단**: PCK (대한예수교장로회 통합). 교단별 용어 확장을 위한 `denomination-report-template.yaml`이 준비되어 있습니다.

---

## 16. 백업 및 복원

### 16.1 자동 백업

```bash
# 백업 스크립트 실행
./scripts/daily-backup.sh

# cron 설정 (매일 새벽 2시)
crontab -e
# 추가: 0 2 * * * cd /path/to/church-admin && ./scripts/daily-backup.sh
```

백업 대상: `data/` 디렉터리의 모든 YAML 파일 + `bulletins/` + `certificates/` + 보고서
보존 기간: 30일 자동 순환 (`RETENTION_DAYS=30`)
저장 형식: `backups/YYYY-MM-DD-HHMMSS.tar.gz`

### 16.2 수동 복원

```bash
# 최근 백업 확인
ls -la backups/

# 복원
cd backups/
tar xzf 2026-02-28-020000.tar.gz
cp -r data/* ../data/

# 복원 후 반드시 검증
cd ..
python3 scripts/validate_all.py
```

### 16.3 백업 권장 사항

- **일일 자동 백업** 설정 (cron)
- **재정 데이터 변경 전** 수동 백업 추가 실행
- **HIGH 민감도 파일** 백업본은 외부 저장소에 암호화 보관 권장
- `state.yaml`도 함께 백업 (시스템 상태 복원에 필요)

---

## 17. PII 보호 및 보안

### 17.1 민감 파일 보호

다음 파일은 PII를 포함하며 `.gitignore`에 등록되어 있습니다:

| 파일 | 민감 정보 | 보호 수준 |
|------|---------|---------|
| `data/members.yaml` | 이름, 전화번호, 주소 | HIGH |
| `data/finance.yaml` | 기부자명, 금액 | HIGH |
| `data/newcomers.yaml` | 새신자 개인정보 | HIGH |

**이 파일들은 절대 공개 저장소에 커밋하면 안 됩니다.**

### 17.2 마스킹 규칙

- 주민등록번호: `XXXXXX-X*****` (앞 7자리만 표시)
- 시스템 로그의 교인명: 김○○ (성 이외 마스킹)

### 17.3 재정 안전 장치

재정 데이터는 3중 안전 장치로 보호됩니다:
1. **SOT 수준**: `state.yaml` `config.autopilot.finance_override: false`
2. **에이전트 수준**: `finance-recorder.md` 명시적 autopilot 금지
3. **워크플로우 수준**: `monthly-finance-report.md` 모든 쓰기 단계에서 인간 확인 필수

`validate_finance_safety.py`가 이 3중 안전 장치를 FS1-FS3으로 검증합니다.

---

## 18. 기능 확장

### 18.1 새 워크플로우 추가

1. `workflows/` 디렉터리에 새 워크플로우 `.md` 파일 생성 (영어 + 한국어 번역)
2. `state.yaml`의 `features`에 새 기능 플래그 추가
3. `workflow_states`에 워크플로우 상태 추적 항목 추가
4. 필요 시 새 에이전트를 `.claude/agents/`에 추가
5. SKILL.md의 NL 라우팅 테이블에 한국어 명령 패턴 매핑 추가

### 18.2 새 에이전트 추가

1. `.claude/agents/` 디렉터리에 에이전트 `.md` 파일 생성
2. 에이전트 명세 구조 준수: name, model, tools, permissionMode, maxTurns, memory scope
3. 쓰기 대상 파일 있으면 `guard_data_files.py`의 Write Permission Matrix에 추가
4. `state.yaml`의 `agent_sessions`에 추적 항목 추가

### 18.3 새 검증 규칙 추가

1. 해당 `validate_*.py` 스크립트에 규칙 함수 추가
2. `validate_all.py`의 집계에 반영
3. 규칙 ID 형식 준수 (예: M8, F8, S7 등)
4. `church-admin/CLAUDE.md`에 규칙 수 업데이트

### 18.4 새 Slash Command 추가

1. `.claude/commands/` 디렉터리에 새 커맨드 `.md` 파일 생성
2. 커맨드명은 파일명에서 파생 (예: `my-command.md` → `/my-command`)
3. 커맨드 내용에 실행 단계 명시 (Bash 스크립트 호출, 에이전트 호출 등)
4. SKILL.md의 라우팅 테이블에 매핑 추가 (한국어 패턴 → Slash Command)

### 18.5 새 문서 유형 추가

1. 기존 문서 이미지를 `@template-scanner`에 제공
2. 비전 분석으로 레이아웃 추출 → YAML 템플릿 생성
3. HitL 확인 후 `templates/`에 저장
4. `@document-generator`에서 호출 가능

### 18.6 교단 커스터마이제이션

1. `state.yaml`의 `church.denomination` 변경
2. 교단별 문서 템플릿 추가 (`denomination-report-template.yaml` 확장)
3. `church-glossary.yaml`에 교단 고유 용어 추가

### 18.7 용어 사전 확장

`data/church-glossary.yaml`에 직접 추가합니다 (append-only):

```yaml
- korean: "새로운 용어"
  english: "new_term"
  context: "사용 맥락 설명"
  category: "카테고리"
```

---

## 19. 주기적 유지보수

### 19.1 일일 작업

- [ ] 자동 백업 성공 확인 (`backups/` 디렉터리)
- [ ] `inbox/errors/` 디렉터리 확인 (파싱 실패 파일)

### 19.2 주간 작업

- [ ] 전체 검증 실행: `python3 scripts/validate_all.py`
- [ ] `inbox/processed/` 정리 (처리 완료 원본)
- [ ] 새신자 후속 관리 지연 확인

### 19.3 월간 작업

- [ ] 백업 보존 정책 확인 (30일 이상 파일 자동 삭제 확인)
- [ ] `state.yaml` 상태 점검 (verification_gates 마지막 실행 날짜)
- [ ] 데이터 파일 크기 모니터링 (500명 초과 시 구조 변경 검토)
- [ ] 대시보드 로그 정리 (`dashboard-logs/` 오래된 파일 삭제)

### 19.4 건강 검진

> **주의**: `claude --maintenance`는 **저장소 루트**(AgenticWorkflow/)에서 실행해야 합니다. 부모 프레임워크의 `setup_maintenance.py`가 실행됩니다. `church-admin/` 디렉터리에서는 교회 행정 시스템 전용 Setup hook(`setup_church_admin.py`)만 `claude --init`으로 실행할 수 있습니다.

```bash
# 저장소 루트에서 실행 (부모 프레임워크 건강 검진)
cd /path/to/AgenticWorkflow
claude --maintenance

# 교회 행정 시스템 건강 검증 (church-admin 디렉터리에서)
cd church-admin
claude --init
```

부모 프레임워크 `setup_maintenance.py`가 실행하는 검사:
- Stale archives (오래된 아카이브)
- Knowledge-index 무결성
- Work_log 크기
- 문서-코드 동기화

---

## 20. 문제 해결

일반적인 문제 해결은 [`church-admin/docs/troubleshooting.md`](church-admin/docs/troubleshooting.md)를 참조하세요.

### 20.1 시스템 관리자 관점 빈번한 문제

| 증상 | 원인 | 해결 |
|------|------|------|
| 에이전트가 데이터 파일 쓰기 거부됨 | `guard_data_files.py`가 차단 | Write Permission Matrix 확인 — 올바른 에이전트인지 확인 |
| 검증 실패 (`valid: false`) | 데이터 무결성 위반 | `errors` 배열의 상세 메시지 확인 후 수정 |
| inbox 파일 `errors/`로 이동 | 파싱 실패 | 파일 형식 확인; HWP → PDF 변환 필요할 수 있음 |
| 한국어 깨짐 | 인코딩 문제 (EUC-KR/CP949) | 파일을 UTF-8로 재저장 후 재시도 |
| 재정 워크플로우 자동 승인 안 됨 | 설계 의도 — Autopilot 영구 비활성화 | 정상 동작. 재정은 항상 이중 검토 필수 |
| `state.yaml` 파싱 오류 | YAML 구문 오류 | `python3 -c "import yaml; yaml.safe_load(open('state.yaml'))"` |
| 시설 예약 충돌 경고 | S5 검증 규칙 감지 | `schedule.yaml`에서 겹치는 시설 예약 확인 |
| 시작 메뉴가 표시 안 됨 | `start_router.py` 실행 실패 | `python3 scripts/start_router.py --state state.yaml` 직접 실행하여 오류 확인 |
| `/start` 명령 미인식 | `.claude/commands/start.md` 누락 | `ls .claude/commands/` 확인 — 파일 존재 여부 |
| 대시보드가 시작되지 않음 | Streamlit 미설치 또는 포트 충돌 | `pip install streamlit`, 포트 변경: `streamlit run dashboard/app.py --server.port 8502` |
| 대시보드 P1 검증 실패 | 데이터 무결성 위반 (대시보드 독립 검증) | `errors` 배열 확인 — CLI `validate_all.py`와 동일한 검증 규칙 |
| 대시보드 "이미 실행 중" 오류 | 이전 작업이 완료되지 않음 | "새 대화" 버튼 클릭 또는 브라우저 새로고침 |
| 대시보드에서 후속 대화 안 됨 | 세션 ID 유실 | "새 대화"로 새 세션 시작 |
| 주보 미리보기가 비어있음 | `bulletin-data.yaml` 없거나 비어있음 | 시드 데이터 생성: `python3 scripts/generate_seed_data.py` |

### 20.2 긴급 데이터 복원

데이터 손상 시:
1. **즉시 중단**: 시스템 사용 중지
2. **백업 확인**: `ls -la backups/` 최근 백업 확인
3. **복원**: 가장 최근 정상 백업에서 복원
4. **검증**: `python3 scripts/validate_all.py` 실행
5. **확인**: 모든 29개 규칙 PASS 확인 후 재개

---

## 21. 유전된 DNA 인식

이 시스템을 운영할 때, 부모 프레임워크(AgenticWorkflow)로부터 유전된 다음 제약을 인식해야 합니다:

| 유전된 제약 | 운영 영향 |
|----------|---------|
| **품질 절대주의** | "빠르게 대충"은 허용되지 않음 — 모든 산출물은 검증 통과 필수 |
| **단독 작성자 패턴** | 데이터 파일 직접 수동 수정 시 검증 규칙 위반 위험 |
| **재정 Autopilot 영구 비활성화** | 변경 불가 — 3중 강제(SOT + 에이전트 + 워크플로우) |
| **Context Preservation** | 세션 간 작업 맥락이 자동 보존됨 — 세션 중단 후 재개 가능 |
| **P1 결정론적 검증** | AI 판단이 아닌 코드 기반 검증 — 우회 불가 |
| **Mandatory Start Menu** | 시작·인사 시 스마트 라우터 → 모드 선택 → 상태 기반 메뉴 자동 표시 |
| **Hook 인프라** | 3개 Hook이 `.claude/settings.json`에 선언적 정의 — `git clone`만으로 자동 적용 |
| **대시보드 독립 검증** | LLM 밖에서 Python이 직접 P1 검증 — Claude 출력을 맹신하지 않음 |
| **4계층 품질 스택** | L0(파일 존재) → L1(의미 검증) → L1.5(자기 신뢰도) → L2(적대적 검토) |
| **Cold Start 해결** | 대시보드 subprocess에 SOT 상태·검증 기준·도메인 제약 자동 주입 |

---

## 22. 관련 문서

| 문서 | 내용 |
|------|------|
| [`CHURCH-ADMIN-README.md`](CHURCH-ADMIN-README.md) | 시스템 개요 및 핵심 역량 |
| [`CHURCH-ADMIN-ARCHITECTURE-AND-PHILOSOPHY.md`](CHURCH-ADMIN-ARCHITECTURE-AND-PHILOSOPHY.md) | 설계 철학과 아키텍처 상세 |
| [`church-admin/docs/quick-start.md`](church-admin/docs/quick-start.md) | 최종 사용자 빠른 시작 |
| [`church-admin/docs/user-guide.md`](church-admin/docs/user-guide.md) | 최종 사용자 전체 사용법 |
| [`church-admin/docs/it-admin-guide.md`](church-admin/docs/it-admin-guide.md) | IT 관리자 가이드 (운영 관점) |
| [`church-admin/docs/installation-guide.md`](church-admin/docs/installation-guide.md) | 상세 설치 가이드 |
| [`church-admin/docs/troubleshooting.md`](church-admin/docs/troubleshooting.md) | 문제 해결 가이드 |
| [`church-admin/CLAUDE.md`](church-admin/CLAUDE.md) | 시스템 지시서 (에이전트 로스터, SOT 규칙) |

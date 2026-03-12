# 교회 행정 시스템: 아키텍처와 설계 철학

이 문서는 교회 행정 AI 에이전트 자동화 시스템의 **설계 철학**과 **아키텍처 전체 조감도**를 기술한다.
시스템 개요(`CHURCH-ADMIN-README.md`)와 사용법(`CHURCH-ADMIN-USER-MANUAL.md`)을 넘어, **"왜 이렇게 설계했는가"**를 체계적으로 서술하는 문서이다.

> 이 문서는 부모 프레임워크의 [`AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md`](AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md) 구조를 미러링하되,
> 교회 행정 도메인에 특화된 설계 결정과 근거를 기술한다.

---

## 1. 설계 철학 (Design Philosophy)

### 1.1 도메인 주도 아키텍처: 한국 교회 관행이 일등 시민

이 시스템의 근본 설계 원칙은 **한국 교회 관행(Korean church conventions)을 기술적 편의보다 우선**하는 것이다.

교회 행정은 범용 비즈니스 시스템과 근본적으로 다르다. 직분 체계(목사 → 장로 → 집사 → 권사 → 성도), 헌금 분류(십일조, 감사헌금, 특별헌금, 선교헌금), 교단별 문서 양식(예장통합, 예장합동, 기감, 기장, 기하, 기성)은 한국 교회만의 고유 도메인 지식이다.

이 지식은 코드에 하드코딩되는 것이 아니라, **외부화된 구조적 데이터**로 관리된다:

| 도메인 지식 소스 | 형태 | 용도 |
|-------------|------|------|
| `data/church-glossary.yaml` | 50+ 한국 교회 용어 사전 | 자연어 인터페이스 정규화, 에이전트 공통 어휘 |
| `domain-knowledge.yaml` | 20개 엔티티, 15개 관계, 14개 제약 | 시스템 설계의 형식적 온톨로지 |
| `templates/*.yaml` | 4개 문서 템플릿 | 교단별 문서 포맷 (고정/변동 영역 분리) |
| `workflows/*.md` | 5개 워크플로우 | 교회 업무 프로세스의 코드화 |

**설계 함의**: 새로운 교단 지원이나 한국 교회 용어 변경은 **코드 수정 없이** YAML 파일 수정만으로 가능하다.

### 1.2 단독 작성자 패턴 (Sole-Writer Pattern): 데이터 파일당 정확히 한 명의 작성자

교회 행정에서 가장 위험한 시나리오는 **데이터 충돌**이다. 두 에이전트가 동시에 `members.yaml`을 수정하면 교인 정보가 유실될 수 있고, `finance.yaml`이 손상되면 법적 문제(기부금영수증 부정확)로 이어진다.

이를 원천 차단하기 위해 **각 데이터 파일에 단독 작성자(Sole Writer)를 지정**한다:

```
┌──────────────────────────────────────────────────────────────────┐
│                     Write Permission Matrix                       │
│                                                                    │
│   members.yaml ←── member-manager ONLY                            │
│   finance.yaml ←── finance-recorder ONLY                          │
│   schedule.yaml ←── schedule-manager ONLY                         │
│   newcomers.yaml ←── newcomer-tracker ONLY                        │
│   bulletin-data.yaml ←── bulletin-generator ONLY                  │
│   church-glossary.yaml ←── ANY agent (append-only)                │
│   state.yaml ←── Orchestrator/Team Lead ONLY                     │
│                                                                    │
│   Enforcement: guard_data_files.py (PreToolUse hook, exit code 2) │
└──────────────────────────────────────────────────────────────────┘
```

이 패턴은 부모 프레임워크의 **절대 기준 2 (단일 파일 SOT)**의 교회 행정 도메인 발현이다. 데이터베이스의 row-level locking 대신, 파일 단위의 에이전트 단독 소유권으로 구현한다.

### 1.3 위험 수준별 사람-검토 (Human-in-the-Loop by Risk Level)

모든 교회 행정 작업이 같은 위험도를 갖는 것은 아니다. 주보 생성은 오류가 있어도 인쇄 전 교정 가능하지만, 재정 기록의 오류는 세금 영수증(기부금영수증)의 법적 문제로 이어진다.

| 위험 수준 | 검토 패턴 | 대상 워크플로우 | Autopilot |
|----------|---------|------------|-----------|
| **HIGH** | 이중 검토 (재정부장 + 당회장/담임목사) | 재정 보고, 기부금영수증 | **영구 비활성화** |
| **MEDIUM** | 단일 검토 | 새신자 단계 전환, 문서 발급 | 부분 허용 |
| **LOW** | 단일 검토 (Autopilot 가능) | 주보 생성, 일정 관리 | 허용 |

**재정 안전의 3중 강제**:

1. `state.yaml` → `config.autopilot.finance_override: false` (SOT 수준)
2. `finance-recorder.md` → 에이전트 명세에 Autopilot 금지 명시 (에이전트 수준)
3. `monthly-finance-report.md` → 모든 쓰기 단계에 이중 검토 게이트 (워크플로우 수준)

### 1.4 한국어 우선 UX, 영어 우선 처리

사용자(행정 간사, 담임 목사)는 한국어로 명령하고 한국어 결과를 받지만, 내부 AI 처리는 영어로 수행하여 모델 성능을 극대화한다.

```
사용자 → "주보 만들어줘" (한국어)
    ↓
NL Interface → intent: generate_bulletin (정규화)
    ↓
Agent Processing → (영어 기반 추론)
    ↓
Output → 주보 (한국 교회 관행 준수, 한국어 콘텐츠)
```

**41개 한국어 명령 패턴**이 8개 카테고리(주보, 새신자, 교인, 재정, 일정, 문서, 데이터, 시스템)로 매핑된다.

### 1.5 대화형 시작 메뉴 패턴 (Mandatory Start Menu)

CLI 경험이 없는 최종 사용자(행정 간사, 담임 목사)를 위해, **인사말이나 시작 명령 시 자동으로 상태 기반 대화형 메뉴를 표시**한다.

```
사용자 → "시작" / 인사말 / 구체적 지시 없는 입력
    ↓
Step 1: python3 scripts/show_menu.py     ← 상태 수집 (state.yaml + data/ 파일)
    ↓
Step 2: 환영 배너 + 현재 상태 + 주의사항 표시
    ↓
Step 3: AskUserQuestion 대화형 메뉴       ← 2페이지 구성 (3+4 항목)
    ↓
사용자 선택 → 워크플로우/에이전트 라우팅
```

이 패턴은 `CLAUDE.md`에서 **절대 기준과 동등한 우선순위**로 강제된다:
- `show_menu.py`가 `state.yaml`과 6개 데이터 파일을 읽어 현재 상태(마지막 주보 호수, 대기 중인 작업, 알림)를 JSON으로 출력
- 메뉴 항목에 `alert` 필드가 있으면 "!!" 표시로 긴급 사항 강조
- "더보기" 선택 시 두 번째 페이지의 나머지 기능 표시

**설계 근거**: 교회 행정 간사는 개발 배경이 없다. "무엇을 도와드릴까요?"라는 개방형 질문보다, 현재 상태에 기반한 구체적 선택지를 제시하는 것이 오류율을 줄이고 접근성을 높인다. Dead-end(사용자가 막히는 상황)가 발생하면 항상 시작 메뉴로 라우팅된다.

---

## 2. 유전된 DNA와 유전자 발현 (Inherited DNA & Gene Expression)

이 시스템은 AgenticWorkflow 부모의 **전체 게놈**을 구조적으로 내장한다. 그러나 게놈이 같아도 도메인에 따라 **발현 강도**가 다르다 — 마치 같은 DNA에서 심장 세포와 신경 세포가 다르게 발현하듯.

### 2.1 DNA 구성 요소 → 교회 행정 발현

| DNA 구성 요소 | 부모에서의 형태 | 교회 행정에서의 발현 | 발현 강도 |
|-------------|-------------|-----------------|---------|
| **절대 기준 1 (품질)** | 최종 결과물의 품질이 유일한 기준 | 주보 오류 제로, 재정 보고서 산술 정확성 100% | **강** |
| **절대 기준 2 (SOT)** | 단일 파일 + 계층적 메모리 | `state.yaml` + 6개 데이터 파일, 단독 쓰기 에이전트 | **강** (확장 발현) |
| **절대 기준 3 (CCP)** | 코드 변경 전 3단계 프로토콜 | 데이터 파일 수정 전 검증 → 영향 분석 → 변경 실행 | 표준 |
| **3단계 구조** | Research → Planning → Implementation | 모든 5개 워크플로우가 동일 구조 준수 | 표준 |
| **4계층 QA** | L0 → L1 → L1.5 → L2 | 빌드 워크플로우 14단계 전부에 적용 | **강** |
| **P1 봉쇄** | 결정론적 검증 | 29개 규칙의 P1 검증 스크립트 5개 | **강** (도메인 특화) |
| **P2 전문 위임** | 전문 에이전트에 위임 | 8개 전문 에이전트, 각각 고유 도메인 | **강** |
| **안전 Hook** | 위험 명령 차단 | `guard_data_files.py` — 데이터 파일 무단 쓰기 차단 | **강** (도메인 특화) |
| **적대적 리뷰** | Generator-Critic 패턴 | 빌드 단계의 `@reviewer` + `@fact-checker` | 표준 |
| **Context Preservation** | 스냅샷 + Knowledge Archive | 부모 시스템의 인프라를 그대로 활용 | 표준 |
| **HitL** | 사람-검토 게이트 | 10개 HitL 게이트, 3단계 위험 분류 | **강** (도메인 필수) |
| **Mandatory Start Menu** | 해당 없음 (도메인 신규) | 상태 기반 대화형 메뉴 — 절대 기준급 강제 | **도메인 고유** |

### 2.2 도메인 특화 유전자 발현

**P1 (데이터 정제) — 강하게 발현**: 교회 행정의 입력 데이터는 다양한 형태(Excel 헌금 내역, 사진 찍은 새신자 카드, HWP 공문)로 들어온다. 3계층 파이프라인(Tier A/B/C)이 각 형태에 맞는 전처리를 수행한 후 에이전트에 전달한다.

**P2 (전문 위임) — 강하게 발현**: 한국 교회 도메인 전문성(직분 체계, 교단별 양식, 목양적 워크플로우 관행)은 범용 처리로는 불가능하다. 8개 전문 에이전트가 각각의 도메인을 책임진다.

**HitL — 도메인 필수 유전자**: 교회 행정에서 재정 데이터의 사람 검토는 법적 의무이다(소득세법 기부금영수증 발급). 새신자 단계 전환은 목양적 판단을 요구한다. 이는 기술적 선택이 아닌 도메인 제약이다.

---

## 3. 아키텍처 개요 (Architecture Overview)

### 3.1 4계층 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                   사용자 인터페이스 계층                       │
│                                                               │
│   inbox/ 파일 드롭 │ Slash Commands │ 한국어 자연어 인터페이스  │
│   (Excel, PDF,    │ /start         │ "주보 만들어줘"          │
│    이미지)         │ /generate-*    │ "새신자 등록"            │
│                   │ /system-status │ "시작하자"               │
│                   │ /validate-all  │                          │
└────────┬───────────────────┬────────────────┬────────────────┘
         │                   │                │
┌────────▼───────────────────▼────────────────▼────────────────┐
│                  파이프라인 계층 (3-Tier)                      │
│                                                               │
│   Tier A: Excel/CSV   │  Tier B: Word/PDF  │  Tier C: 이미지  │
│   (openpyxl, pandas)  │  (python-docx)     │  (Claude 멀티모달)│
│   신뢰도: 0.95        │  신뢰도: 0.70      │  신뢰도: 0.55    │
│                                                               │
│   → inbox/staging/ (파싱 결과 + 신뢰도 점수)                  │
│   → 사람 확인 게이트 (HitL)                                   │
└────────┬───────────────────┬────────────────┬────────────────┘
         │                   │                │
┌────────▼───────────────────▼────────────────▼────────────────┐
│                   에이전트 계층 (8개 전문 에이전트)             │
│                                                               │
│   bulletin-generator  │  finance-recorder  │  member-manager  │
│   newcomer-tracker    │  schedule-manager  │  document-gen    │
│   data-ingestor       │  template-scanner                     │
│                                                               │
│   각 에이전트: 단독 쓰기 권한 + P1 검증 통과 후 쓰기           │
└────────┬───────────────────┬────────────────┬────────────────┘
         │                   │                │
┌────────▼───────────────────▼────────────────▼────────────────┐
│                  데이터 계층 (YAML SOT)                        │
│                                                               │
│   members.yaml  │ finance.yaml │ schedule.yaml │ newcomers   │
│   bulletin-data │ glossary     │ state.yaml    │ templates/* │
│                                                               │
│   검증: 5개 P1 스크립트 (29개 결정론적 규칙)                   │
│   보호: guard_data_files.py (PreToolUse hook)                 │
│   쓰기: atomic_write_yaml() (flock + temp + rename)           │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 에이전트 의존 관계

```
schedule-manager ─────────────────────────────────┐
                                                   ↓
data-ingestor → [staging JSON] → 사람 검토 → member-manager ←── newcomer-tracker
                                                   ↑                      ↓
template-scanner → [YAML 템플릿]            finance-recorder         (정착 전환)
                        ↓                          ↑                      ↓
                  document-generator         members (교차 참조)    member-manager
                        ↑
                  bulletin-generator ← members (생일) + schedule (예배)
```

### 3.3 데이터 접근 매트릭스

| 에이전트 | members | finance | schedule | newcomers | bulletin | glossary |
|---------|---------|---------|----------|-----------|----------|---------|
| bulletin-generator | R | — | R | — | **W** | A |
| finance-recorder | R | **W** | — | — | — | A |
| member-manager | **W** | — | — | R | — | A |
| newcomer-tracker | R | — | — | **W** | — | A |
| schedule-manager | — | — | **W** | — | R | A |
| document-generator | R | R | — | — | — | A |
| data-ingestor | — | — | — | — | — | A |
| template-scanner | — | — | — | — | — | A |

**W** = 단독 쓰기, **R** = 읽기 전용, **A** = append-only (모든 에이전트 쓰기 가능), **—** = 접근 없음

---

## 4. 데이터 아키텍처 (Data Architecture)

### 4.1 6개 YAML 스키마

모든 데이터는 YAML 파일로 관리된다. JSON이나 SQLite가 아닌 YAML을 선택한 이유:

- **사람이 읽을 수 있다** — 행정 간사가 직접 데이터를 확인·수정 가능
- **Git 친화적** — diff와 merge가 자연스럽다
- **한국어 네이티브** — UTF-8 한국어를 별도 인코딩 없이 지원
- **규모에 적합** — 100-500명 교회에서 YAML 리스트 구조는 충분한 성능

| 스키마 | ID 형식 | 주요 필드 | 삭제 정책 | 유효성 검증 |
|--------|---------|---------|---------|-----------|
| Members | `M\d{3,}` | name, gender, birth_date, status, contact, church.role, family | Soft-delete (`inactive`) | M1-M7 (7개 규칙) |
| Finance | `OFF-YYYY-NNN` / `EXP-YYYY-NNN` | type, items[], total, verified, category, approved_by | Void-only | F1-F7 (7개 규칙) |
| Schedule | `SVC/EVT/FAC-*` | type, date, time, recurrence, status, facility | Status cancel | S1-S6 (6개 규칙) |
| Newcomers | `N\d{3,}` | name, contact, journey_stage, milestones[], shepherd | Soft-delete (`inactive`) | N1-N6 (6개 규칙) |
| Bulletin | (호수 기반) | issue_number, date, sections[], generation_history | 호수별 덮어쓰기 | B1-B3 (3개 규칙) |
| Glossary | (용어 키) | korean, english, context, category | Append-only | — |

### 4.2 P1 검증: 29개 결정론적 규칙

P1 검증은 **AI 판단이 아닌 Python 코드의 결정론적 검사**이다. 에이전트가 데이터를 변경할 때마다, 해당 검증 스크립트가 통과해야 한다.

**Members (M1-M7)**:
- M1: ID 유일성 및 형식 (`M\d{3,}`)
- M2: 필수 필드 존재 (name, status)
- M3: 전화번호 정규식 (`^010-\d{4}-\d{4}$`)
- M4: status 열거값 (`active|inactive|transferred|deceased`)
- M5: family_id 참조 무결성
- M6: 날짜 형식 (`YYYY-MM-DD`)
- M7: `_stats` 산술 정합성

**Finance (F1-F7)**:
- F1: ID 유일성 및 형식
- F2: 금액 양수 검증
- F3: 헌금 합계 일치 (total = sum of items)
- F4: 예산 산술 정합성
- F5: 월별 요약 정합성 (balance = income - expense)
- F6: 카테고리 열거값 검증
- F7: 승인자 필드 필수 (expenses)

**Schedule (S1-S6)**:
- S1: ID 형식 (3종 타입: `SVC`, `EVT`, `FAC`)
- S2: 시간 형식 검증
- S3: 반복 패턴 열거값
- S4: status 열거값
- S5: 시설 예약 겹침 감지
- S6: 날짜 범위 논리적 정합성

**Newcomers (N1-N6)**:
- N1: ID 유일성 및 형식
- N2: 여정 단계 순차적 마일스톤 (`first_visit → attending → small_group → baptism_class → baptized → settled`)
- N3: 날짜 형식
- N4: member_id 참조 (정착 전환 시)
- N5: 교차 파일 정착 일관성 (N-record `settled` ↔ M-record 존재)
- N6: `_stats` 산술 정합성

**Bulletin (B1-B3)**:
- B1: 날짜 일관성
- B2: 호수 순차성 (단조 증가)
- B3: 교인 참조 무결성 (생일 목록 등)

### 4.3 데이터 민감도 분류

```
HIGH (PII)      ← members.yaml, newcomers.yaml
HIGH (Financial) ← finance.yaml
LOW             ← schedule.yaml, bulletin-data.yaml, church-glossary.yaml
```

HIGH 민감도 파일은 `.gitignore`로 공개 저장소 커밋이 차단되며, 백업 시 암호화를 권장한다.

---

## 5. 에이전트 아키텍처 (Agent Architecture)

### 5.1 8개 전문 에이전트

| # | 에이전트 | 역할 | 모델 | 쓰기 대상 | 모델 선택 근거 |
|---|---------|------|------|---------|-------------|
| 1 | `bulletin-generator` | 주보 생성 + 예배 순서 | sonnet | `bulletin-data.yaml` | 패턴 기반 슬롯 채움 — sonnet 충분 |
| 2 | `finance-recorder` | 재정 기록 + 보고서 + 영수증 | opus | `finance.yaml` | 고위험 — 세금 영수증, 법적 정확성 |
| 3 | `member-manager` | 교인 CRUD + 생애주기 | sonnet | `members.yaml` | 구조적 CRUD + 교차 참조 검증 |
| 4 | `newcomer-tracker` | 새신자 여정 파이프라인 | sonnet | `newcomers.yaml` | 단계 관리 + 목양적 판단 게이트 |
| 5 | `schedule-manager` | 예배·행사 조율 + 시설 예약 | sonnet | `schedule.yaml` | 충돌 감지 + 반복 일정 |
| 6 | `document-generator` | 증서·공문·회의록 생성 | sonnet | `docs/generated/` | 템플릿 기반 문서 생성 |
| 7 | `data-ingestor` | inbox/ 파일 파싱 | opus | `inbox/staging/` | 복잡한 다형식 파싱 (Excel, PDF, 이미지) |
| 8 | `template-scanner` | 이미지 → YAML 템플릿 | opus | `templates/` | 비전 + 추론 필요 |

**모델 선택 원칙**: opus는 고위험 데이터(재정)와 복잡한 추론(다형식 파싱, 비전 분석)에만 할당. 나머지는 sonnet으로 처리량과 품질의 균형을 맞춘다.

### 5.2 에이전트 명세 구조

각 에이전트의 `.md` 파일에는 다음이 명시된다:

- **name, description, model** — 정체성과 역량
- **Tools Required** — Read, Write, Edit, Bash 등
- **permissionMode** — `default` 또는 `bypassPermissions` (재정은 항상 `default`)
- **maxTurns** — 실행 턴 상한 (10-25)
- **Memory Scope** — 읽기/쓰기 파일 명시 목록
- **Input/Output Contract** — 구조화된 데이터 형식
- **Specialization Boundary** — "이것은 하지 않는다" 목록 (범위 확장 방지)

### 5.3 Slash Commands (진입점)

5개 Slash Command가 주요 기능의 구조화된 진입점을 제공한다. NL Interface가 자유형 한국어 입력을 라우팅하는 반면, Slash Commands는 **사전 정의된 파이프라인**을 정확히 실행한다.

| Command | 설명 | 실행 단계 | Autopilot |
|---------|------|---------|-----------|
| `/start` | 대화형 시작 메뉴 | `show_menu.py` → 배너 → `AskUserQuestion` | — |
| `/generate-bulletin` | 주보 생성 파이프라인 | 11단계 (일정 확인 → 생성 → 검증 → 검토) | 허용 |
| `/generate-finance-report` | 월별 재정 보고서 | 8단계 (수입/지출 → 보고서 → 이중 검토) | **영구 비활성화** |
| `/system-status` | 시스템 건강 검사 | 5부분 (SOT, 데이터, 검증, 대기 작업, 인프라) | — |
| `/validate-all` | 전체 P1 검증 | `validate_all.py` 실행 → 29개 규칙 결과 | — |

**설계 근거**: Slash Commands는 NL Interface와 상호 보완적이다. "주보 만들어줘"(자연어)와 `/generate-bulletin`(Slash Command)은 동일한 파이프라인을 트리거하지만, Slash Command는 중간 라우팅 단계 없이 직접 실행된다. 시스템 관리자(IT 자원봉사자)는 Slash Commands를, 최종 사용자(행정 간사)는 한국어 자연어를 사용할 수 있다.

---

## 6. 워크플로우 아키텍처 (Workflow Architecture)

### 6.1 5개 독립 워크플로우

각 워크플로우는 부모의 3단계 구조(Research → Planning → Implementation)를 준수하되, 교회 행정 도메인의 특성에 맞게 발현한다.

| 워크플로우 | 주기 | 핵심 에이전트 | 위험 수준 | Autopilot |
|-----------|------|------------|---------|-----------|
| `weekly-bulletin` | 주간 (월요일) | bulletin-generator, schedule-manager | LOW | 허용 |
| `newcomer-pipeline` | 수시 (새 방문자) | newcomer-tracker, member-manager | MEDIUM | 부분 허용 |
| `monthly-finance-report` | 월간 (월말) | finance-recorder, document-generator | HIGH | **영구 비활성화** |
| `document-generator` | 수시 (요청 시) | document-generator, template-scanner | MEDIUM | 허용 |
| `schedule-manager` | 수시 (행사 등록) | schedule-manager | MEDIUM | 허용 |

### 6.2 주보 생성 워크플로우 상세

```
Step 1: 일정 확인 (schedule-manager → schedule.yaml 읽기)
    ↓
Step 2: 데이터 완전성 검사 (bulletin-generator → bulletin-data.yaml 확인)
    ↓
Step 3: 주보 생성 (bulletin-generator → 16개 변동 영역 채움)
    ↓
Step 4: P1 검증 (validate_bulletin.py — B1-B3)
    ↓
Step 5: 사람 검토 ◆ HitL GATE (생성된 주보 검토)
    ↓
Step 6: 확정 (출력: bulletins/YYYY-MM-DD-bulletin.md)
```

### 6.3 3계층 수신함 파이프라인

비기술 사용자(행정 간사 — CLI 경험 없음)의 주요 입력 경로:

```
inbox/{파일}
    │
    ▼
[파일 감지] ← 확장자 + 매직 바이트 분류
    │
    ├── .xlsx/.csv ──→ [Tier A: 구조화 파서]  (신뢰도 0.95)
    │                    openpyxl 열 매핑
    │                    pandas 검증
    │                    chardet 한국어 인코딩 감지
    │
    ├── .docx/.pdf ──→ [Tier B: 반구조 파서]  (신뢰도 0.70)
    │                    python-docx 단락 추출
    │                    Claude Read (복잡 PDF)
    │
    └── .jpg/.png ──→ [Tier C: 비구조 파서]  (신뢰도 0.55)
                        Claude 멀티모달 비전
                        Tesseract OCR 대체
    │
    ▼
[신뢰도 점수] → [P1 검증] → [inbox/staging/]
    │
    ▼
[사람 확인] ◆ HitL GATE
    │
    ▼
[단독 작성 에이전트가 staging 파일 소비]
    │
    ▼
[inbox/processed/] (원본 보존)
```

**HWP 대응**: `.hwp` 파일은 `inbox/errors/`로 라우팅 + PDF 변환 안내를 한국어로 제공한다.

**한국어 인코딩 대비**: 레거시 교회 파일은 EUC-KR/CP949를 빈번하게 사용한다. chardet 감지 → EUC-KR → CP949 → UTF-8-SIG → UTF-8 순차 시도로 대응한다.

### 6.4 스캔-복제 엔진

물리 문서 샘플(사진/스캔)을 재사용 가능한 YAML 템플릿으로 변환한다:

| # | 문서 유형 | 한국어 | 변동 영역 수 | 교단 특화 |
|---|---------|--------|-----------|---------|
| 1 | 주보 | 주보 | 16 | 헤더, 치리 용어 |
| 2 | 기부금영수증 | 기부금영수증 | 8 | 교회명, 사업자등록번호 |
| 3 | 순서지 | 순서지 | 12 | 예전 순서 |
| 4 | 공문 | 공문 | 6 | 당회장 vs 감독 vs 총회장 |
| 5 | 회의록 | 회의록 | 10 | 당회록 vs 제직회의록 |
| 6 | 증서 | 증서 | 5 | 세례 유형, 교회 도장 |
| 7 | 초청장 | 초청장 | 7 | 최소 변형 |

**한국 문서 포맷 관행**:
- 한글 금액 표기: `금 일백이십삼만사천원정` (기부금영수증 법적 요구)
- 직인 위치: 문서 유형별 특정 위치
- 세로쓰기: 전통 요소 (예: 찬송가 보드)
- 날짜 형식: `YYYY년 MM월 DD일`

---

## 7. 안전 아키텍처 (Safety Architecture)

### 7.1 재정 Autopilot 영구 비활성화

교회 재정 데이터는 법적 함의(기부금영수증 — 소득세법 시행령 §80조)를 갖는다. 재정 워크플로우의 자동 승인은 어떤 상황에서도 활성화되지 않는다.

**강제 계층**:

```
[SOT 수준]     state.yaml: config.autopilot.finance_override: false
      ↓
[에이전트 수준]  finance-recorder.md: "Autopilot: permanently disabled"
      ↓
[워크플로우 수준] monthly-finance-report.md: 모든 쓰기에 이중 검토
      ↓
[검증 수준]     guard_data_files.py: finance.yaml 비인가 쓰기 차단
```

### 7.2 Hook 인프라 (`.claude/settings.json`)

3개 Hook이 `.claude/settings.json`에 선언적으로 정의된다. `git clone`만으로 Hook 인프라가 자동 적용된다.

| Hook 이벤트 | 스크립트 | Matcher | 동작 | Exit Code |
|------------|---------|---------|------|----------|
| **PreToolUse** | `guard_data_files.py` | `Edit\|Write` | 단독 작성자 권한 강제 | 0(허용) / 2(차단) |
| **PostToolUse** | `validate_yaml_syntax.py` | `Write` | YAML 구문 사후 검증 | 0(경고 전용) |
| **Setup** (`--init`) | `setup_church_admin.py` | `init` | 인프라 건강 검증 CA-1~CA-8 | — |

```
┌────────────────────────────────────────────────────────────────┐
│                    Hook 실행 흐름                                │
│                                                                  │
│  Edit/Write 도구 호출                                            │
│     ↓                                                            │
│  [PreToolUse] guard_data_files.py                               │
│     ├── CLAUDE_AGENT_NAME 환경변수 확인                          │
│     ├── 대상 파일 vs Write Permission Matrix 대조                │
│     ├── 인가된 에이전트 → exit 0 (실행 허용)                     │
│     └── 비인가 에이전트 → exit 2 (차단) + stderr 피드백         │
│     ↓                                                            │
│  [도구 실행]                                                     │
│     ↓                                                            │
│  [PostToolUse] validate_yaml_syntax.py  (*.yaml 파일만)         │
│     ├── yaml.safe_load() 파싱 시도                               │
│     └── 실패 시 stderr 경고 (exit 0 — 차단하지 않음)            │
└────────────────────────────────────────────────────────────────┘
```

**Safety-first 원칙**: `guard_data_files.py`는 내부 오류 발생 시 exit 0을 반환한다 (절대 차단하지 않음). 이는 Hook 자체의 버그가 정상 작업을 방해하지 않도록 하는 안전 장치이다.

### 7.3 Setup 건강 검증

`setup_church_admin.py` (Setup hook, `claude --init` 트리거):

| 검사 | 내용 | 실패 영향 |
|------|------|---------|
| CA-1 | Python ≥ 3.9 | Fatal (진행 불가) |
| CA-2 | PyYAML 임포트 가능 | Fatal (진행 불가) |
| CA-3 | `data/` 디렉터리 존재 | 자동 생성 |
| CA-4 | 6개 데이터 파일 존재 | 경고 |
| CA-5 | 5개 검증 스크립트 존재 | 경고 |
| CA-6 | `guard_data_files.py` Hook 존재 | 경고 |
| CA-7 | 런타임 디렉터리 존재 | 자동 생성 |
| CA-8 | SOT 파일 파싱 가능 | 경고 |

### 7.4 PII 보호

- HIGH 민감도 파일 3개는 `.gitignore`로 보호
- 주보 표시 시 이름 마스킹: `김철수` → `김○수`, `남궁세연` → `남궁○연`
- 기부금영수증의 주민등록번호 마스킹: `YYMMDD-NNNNNNN` → `YYMMDD-N******`

---

## 8. 품질 보장 (Quality Assurance)

### 8.1 부모로부터 유전된 4계층 QA 스택

이 시스템은 빌드 과정(14단계 워크플로우)에서 부모의 4계층 QA를 완전히 적용받았다:

| 계층 | 이름 | 교회 행정에서의 적용 | 성격 |
|------|------|-----------------|------|
| **L0** | Anti-Skip Guard | 각 단계 산출물 파일 존재 + 100 bytes 이상 | 결정론적 (Hook) |
| **L1** | Verification Gate | 워크플로우의 `Verification` 기준 대비 자기 검증 | 의미론적 (Agent) |
| **L1.5** | pACS Self-Rating | Pre-mortem Protocol → F/C/L 3차원 채점 | 신뢰도 기반 |
| **L2** | Adversarial Review | `@reviewer` + `@fact-checker` 독립 검토 | 적대적 |

### 8.2 운영 시점의 품질 보장

빌드 완료 후 운영 시점에서는:

- **P1 검증 스크립트**: 29개 규칙이 매 데이터 변경 시 실행
- **HitL 게이트**: 10개 검토 포인트가 위험 수준별로 배치
- **데이터 보호 Hook**: `guard_data_files.py`가 비인가 쓰기를 차단
- **자동 백업**: `daily-backup.sh`가 30일 보존 + 자동 순환

### 8.3 통합 테스트 결과

빌드 워크플로우 Step 12에서 수행된 통합 테스트:

- **15/15 검증 기준 통과**
- **29/29 P1 검증 규칙 통과**
- 테스트 범위: 주보 파이프라인, 새신자 파이프라인, 재정 워크플로우, 스캔-복제, 교차 워크플로우 참조, 데이터 무결성, 오류 처리, HitL 게이트, Autopilot 동작, 규모 구조, 한국어 인코딩, 백업/복원, 교인 관리, NL 인터페이스, 일정 관리

상세: [`testing/integration-test-report.md`](testing/integration-test-report.md)

---

## 부록 A: 교차 워크플로우 데이터 의존성

### 주요 교차 파일 의존성

1. **새신자 → 교인 전환** (N5 ↔ M1): `newcomer-tracker`가 `settled` 표시 → `member-manager`가 M-record 생성. N5 검증 규칙이 양방향 일관성 강제.

2. **재정 → 교인 기부자 추적** (F3 ↔ M): `finance-recorder`가 헌금 기록에 `member_id` 참조. F-규칙이 교차 참조 검증.

3. **주보 → 일정 + 교인**: `bulletin-generator`가 `schedule.yaml`에서 예배 시간을, `members.yaml`에서 생일/기념일을 조회.

4. **문서 → 교인 + 재정**: `document-generator`가 증명서용 교인 데이터와 연말 기부금영수증용 재정 데이터를 조회.

---

## 부록 B: 관련 문서

| 문서 | 내용 |
|------|------|
| [`CHURCH-ADMIN-README.md`](CHURCH-ADMIN-README.md) | 시스템 개요 |
| [`CHURCH-ADMIN-USER-MANUAL.md`](CHURCH-ADMIN-USER-MANUAL.md) | 운영·유지보수 매뉴얼 |
| [`church-admin/CLAUDE.md`](church-admin/CLAUDE.md) | 에이전트 로스터, SOT 규칙, 데이터 정책 |
| [`planning/system-architecture.md`](planning/system-architecture.md) | 상세 아키텍처 청사진 |
| [`domain-knowledge.yaml`](domain-knowledge.yaml) | 형식적 도메인 온톨로지 |
| [`AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md`](AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md) | 부모 프레임워크 아키텍처 |

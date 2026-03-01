# 5단계: 시스템 아키텍처 블루프린트
## 교회 행정 AI 에이전틱 워크플로우 자동화 시스템

**생성일**: 2026-02-28
**팀**: `arch-blueprint` (3개 병렬 에이전트)
**입력 소스**: 1단계 (도메인 분석), 2단계 (템플릿 분석), 4단계 (데이터 아키텍처 명세), PRD
**컴포넌트 명세**:
- `step5-agent-architecture.md` — 에이전트 명세 + 기능 워크플로우 블루프린트 (72KB)
- `step5-pipeline-architecture.md` — 데이터 파이프라인 + 스캔-앤-복제 엔진 (98KB)
- `step5-hooks-validation.md` — P1 검증 스크립트 + 훅 + 슬래시 커맨드 (82KB)

---

## 목차

1. [요약](#1-요약)
2. [아키텍처 개요](#2-아키텍처-개요)
3. [에이전트 아키텍처](#3-에이전트-아키텍처)
4. [기능 워크플로우 블루프린트](#4-기능-워크플로우-블루프린트)
5. [데이터 파이프라인 아키텍처](#5-데이터-파이프라인-아키텍처)
6. [스캔-앤-복제 엔진](#6-스캔-앤-복제-엔진)
7. [P1 검증 프레임워크](#7-p1-검증-프레임워크)
8. [Hook 구성](#8-hook-구성)
9. [슬래시 커맨드 명세](#9-슬래시-커맨드-명세)
10. [인간 개입 루프 아키텍처](#10-인간-개입-루프-아키텍처)
11. [Autopilot 적격성 매트릭스](#11-autopilot-적격성-매트릭스)
12. [워크플로우 간 데이터 의존성](#12-워크플로우-간-데이터-의존성)
13. [공유 유틸리티](#13-공유-유틸리티)
14. [구현 로드맵](#14-구현-로드맵)
15. [검증 보고서](#15-검증-보고서)

---

## 1. 요약

[trace:step-1:domain-analysis] [trace:step-4:schema-specs]

이 문서는 한국 중형 교회(100-500명 규모)를 대상으로 하는 교회 행정 AI 에이전틱 워크플로우 자동화 시스템의 전체 시스템 아키텍처를 정의합니다. 아키텍처의 구성은 다음과 같습니다:

- **10개의 전문 에이전트**: 엄격한 쓰기 권한 분리 적용(데이터 파일당 하나의 기록자)
- **4개의 기능 워크플로우 블루프린트**: 유전된 DNA를 포함한 3단계 구조 준수
- **3계층 데이터 수집 파이프라인**: (Excel/CSV → Word/PDF → 이미지) 신뢰도 점수화 포함
- **스캔-앤-복제 엔진**: 7종의 한국 교회 문서 유형 지원
- **4개의 P1 검증 스크립트**: 22개의 결정론적 검사(AI 판단 배제)
- **3개의 Hook 구성**: 데이터 보호, YAML 구문, 인프라 건강을 위한 구성
- **4개의 슬래시 커맨드**: 인간 개입 루프 리뷰 게이트용

### 유전된 DNA

이 아키텍처는 상위 AgenticWorkflow 게놈으로부터 다음을 상속합니다:

| DNA 패턴 | 교회 행정 시스템에서의 적용 |
|------------|---------------------------|
| absolute-criteria | 품질 > 속도; SOT 단일 기록자; 코드 변경 전 CCP |
| sot-pattern | `church-state.yaml` + 6개 데이터 파일, 각각 정확히 하나의 기록 에이전트 보유 |
| 3-phase-structure | 4개 기능 워크플로우 모두 Research → Planning → Implementation 준수 |
| 4-layer-qa | L0 Anti-Skip → L1 Verification → L1.5 pACS → L2 적대적 리뷰 |
| safety-hooks | `guard_data_files.py`가 비인가 YAML 쓰기 차단 |
| adversarial-review | 아키텍처용 `@reviewer`, 데이터 명세용 `@fact-checker` |
| decision-log | 모든 자동 승인 결정을 `autopilot-logs/`에 기록 |
| context-preservation | IMMORTAL 섹션이 세션 경계에서도 생존 |
| cross-step-traceability | 모든 명세가 1단계 도메인 분석 및 4단계 스키마로 추적 가능 |
| domain-knowledge-structure | 스키마 필드가 `domain-knowledge.yaml` 엔티티와 정렬 |

---

## 2. 아키텍처 개요

### 시스템 레이어 다이어그램

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface Layer                   │
│  inbox/ drop zone │ CLI commands │ NL interface (future)  │
└────────────┬───────────────┬───────────────┬─────────────┘
             │               │               │
┌────────────▼───────────────▼───────────────▼─────────────┐
│                  Pipeline Layer (Tier A/B/C)              │
│  data-ingestor │ template-scanner │ confidence scoring    │
└────────────┬───────────────┬───────────────┬─────────────┘
             │               │               │
┌────────────▼───────────────▼───────────────▼─────────────┐
│              Human-in-the-Loop Confirmation               │
│  staging/ preview │ approval gates │ dual-review (finance)│
└────────────┬───────────────┬───────────────┬─────────────┘
             │               │               │
┌────────────▼───────────────▼───────────────▼─────────────┐
│                   Agent Layer (10 agents)                 │
│  bulletin-gen │ finance-rec │ member-mgr │ newcomer-trk  │
│  schedule-mgr │ document-gen │ tester │ onboarding-auth  │
└────────────┬───────────────┬───────────────┬─────────────┘
             │               │               │
┌────────────▼───────────────▼───────────────▼─────────────┐
│                    Data Layer (YAML SOT)                  │
│  members │ finance │ schedule │ newcomers │ bulletin-data │
│  church-glossary │ church-state │ templates/*             │
└────────────┬───────────────────────────────┬─────────────┘
             │                               │
┌────────────▼───────────────────────────────▼─────────────┐
│              Validation & Safety Layer                    │
│  P1 validators (4) │ guard hooks │ atomic writes         │
└──────────────────────────────────────────────────────────┘
```

### 기본 원칙

1. **데이터 파일당 단일 기록자** [trace:step-4:schema-specs]: 각 YAML 데이터 파일에는 정확히 하나의 지정된 기록 에이전트가 있습니다. `guard_data_files.py`(PreToolUse hook, exit code 2가 비인가 쓰기를 차단)에 의해 강제됩니다.

2. **파이프라인은 데이터를 직접 기록하지 않습니다**: 데이터 수집기는 `inbox/staging/`에 스테이징 파일을 생성하며, 지정된 기록 에이전트가 인간 확인 후 이를 소비합니다.

3. **커밋 전 P1 검증**: 모든 데이터 변경은 인간 확인에 도달하기 전에 결정론적 P1 검증을 통과합니다. 유효하지 않은 데이터는 승인 대상으로 제시되지 않습니다.

4. **재정 데이터는 Autopilot에서 영구 제외**: 재정 데이터는 법적 함의가 있습니다(세금영수증, 소득세법). PRD §5.1 F-03에 따라 자동 승인에서 영구 제외됩니다.

5. **한국어 우선 UX, 영어 우선 처리**: 사용자 대면 콘텐츠는 한국어 관례를 준수합니다(주민등록번호 마스킹, 한글 금액 변환, 세로쓰기). 내부 처리는 AI 성능 최적화를 위해 영어를 사용합니다.

---

## 3. 에이전트 아키텍처

[trace:step-1:domain-analysis] [trace:step-4:schema-specs]

*전체 명세: `planning/step5-agent-architecture.md` Part A*

### 3.1 에이전트 인벤토리

| # | 에이전트 이름 | 역할 | 모델 | 쓰기 대상 | 근거 |
|---|-----------|------|-------|--------------|-----------|
| 1 | `bulletin-generator` | 주간 주보 + 예배 순서 | sonnet | `data/bulletin-data.yaml` | 템플릿 실행 — 패턴 기반 슬롯 채우기 |
| 2 | `finance-recorder` | 재정 기록 + 보고서 | opus | `data/finance.yaml` | 높은 위험 — 기부금 영수증, 법적 준수 |
| 3 | `member-manager` | 교적 관리 | sonnet | `data/members.yaml` | 교차 참조 검증이 포함된 구조화된 CRUD |
| 4 | `newcomer-tracker` | 새신자 정착 파이프라인 | sonnet | `data/newcomers.yaml` | 목회적 판단 게이트가 포함된 정착 단계 관리 |
| 5 | `data-ingestor` | inbox/ 파일 파싱 | opus | `inbox/processed/` (스테이징) | 복합 다중 형식 파싱(Excel, PDF, 이미지) |
| 6 | `template-scanner` | 스캔-앤-복제 추출 | opus | `templates/*.yaml` | 문서 분석에 비전 + 추론 능력 필요 |
| 7 | `document-generator` | 증서/공문/영수증 생성 | sonnet | `certificates/`, `letters/` | 교단 인식이 포함된 템플릿 기반 생성 |
| 8 | `church-integration-tester` | 워크플로우 간 검증 | sonnet | `test-reports/` | 데이터 무결성 검사 |
| 9 | `church-onboarding-author` | IT 자원봉사자 문서화 | sonnet | `docs/` | 기술 문서 작성 |
| 10 | `schedule-manager` | 예배/행사 조율 | sonnet | `data/schedule.yaml` | 일정 충돌 감지 + 반복 일정 |

### 3.2 모델 선택 근거

| 모델 | 배정 대상 | 선택 기준 |
|-------|------------|-------------------|
| **opus** | finance-recorder, data-ingestor, template-scanner | 높은 위험의 데이터, 복합 다중 형식 파싱, 비전+추론 |
| **sonnet** | 기타 전체(7개 에이전트) | 패턴 실행, 템플릿 채우기, 구조화된 CRUD — 높은 처리량으로 충분 |

### 3.3 쓰기 권한 매트릭스

[trace:step-4:schema-specs]

| 데이터 파일 | 단독 기록자 | 다른 모든 에이전트 |
|-----------|------------|-----------------|
| `data/members.yaml` | `member-manager` | 읽기 전용 |
| `data/finance.yaml` | `finance-recorder` | 읽기 전용 |
| `data/schedule.yaml` | `schedule-manager` | 읽기 전용 |
| `data/newcomers.yaml` | `newcomer-tracker` | 읽기 전용 |
| `data/bulletin-data.yaml` | `bulletin-generator` | 읽기 전용 |
| `data/church-glossary.yaml` | `template-scanner` | 읽기 전용(추가 전용 업데이트) |
| `church-state.yaml` | Orchestrator/Team Lead 전용 | 읽기 전용 |
| `templates/*.yaml` | `template-scanner` | 읽기 전용 |
| `inbox/staging/*` | `data-ingestor` | 읽기 전용(지정된 기록자가 소비) |

**강제 메커니즘**: `guard_data_files.py`(PreToolUse hook)가 호출 에이전트를 이 매트릭스와 대조 검사합니다. 비인가 쓰기는 exit code 2를 수신합니다(도구 호출 차단).

### 3.4 에이전트 명세 요약

각 에이전트 명세는 다음을 포함합니다(전체 상세는 `step5-agent-architecture.md` 참조):
- **name, description, model** — 식별 및 역량
- **Tools Required** — Read, Write, Edit, Bash 등
- **permissionMode** — `default` 또는 `bypassPermissions`(재정: 항상 `default`)
- **maxTurns** — 제한된 태스크 실행(에이전트당 10-25턴)
- **Memory Scope** — 명시적 읽기/쓰기 파일 목록
- **Input/Output Contract** — 구조화된 데이터 형식 명세
- **When Invoked** — 워크플로우 단계 및 트리거 조건
- **SOT Access Pattern** — 읽기 전용 대 읽기-쓰기 지정
- **Specialization Boundary** — 범위 확장 방지를 위한 명시적 "하지 않는 것" 목록

---

## 4. 기능 워크플로우 블루프린트

[trace:step-1:domain-analysis] [trace:step-2:template-analysis]

*전체 명세: `planning/step5-agent-architecture.md` Part B*

### 4.1 워크플로우 인벤토리

| 워크플로우 | 빈도 | 핵심 에이전트 | 위험 수준 | Autopilot |
|----------|-----------|-----------|------------|-----------|
| `weekly-bulletin` | 주간(월요일 주기) | bulletin-generator, schedule-manager | 낮음 | 적격 |
| `newcomer-pipeline` | 수시(새 방문자) | newcomer-tracker, member-manager | 중간 | 부분적 |
| `monthly-finance-report` | 월간(월말) | finance-recorder, document-generator | 높음 | **영구 비활성** |
| `document-generator` | 수시 | document-generator, template-scanner | 중간 | 적격(대부분의 유형) |

### 4.2 주간 주보 워크플로우

**트리거**: 월요일 아침 준비 주기
**소요 시간**: 자동화 약 15분, 인간 개입 루프 리뷰 게이트 1회
**데이터 소스**: `bulletin-data.yaml`, `schedule.yaml`, `members.yaml`(생일/기념일 필터링)

```
Step 1: Schedule Verification (schedule-manager reads schedule.yaml)
    ↓
Step 2: Data Completeness Check (bulletin-generator checks bulletin-data.yaml)
    ↓
Step 3: Bulletin Generation (bulletin-generator fills 16 variable regions)
    ↓
Step 4: P1 Validation (validate_bulletin.py — B1-B3 checks)
    ↓
Step 5: Human Review ◆ HitL GATE (review generated bulletin)
    ↓
Step 6: Finalization (output: bulletins/YYYY-MM-DD-bulletin.md)
```

**유전된 DNA**: 3단계 구조, 모든 단계에 Verification 필드, pACS 자기 채점, 컨텍스트 보존.

### 4.3 새신자 파이프라인 워크플로우

**트리거**: 새 방문자 데이터 도착(inbox/ 파일 또는 수동 입력)
**소요 시간**: 수일(새신자 정착 과정은 수주/수개월에 걸침)
**정착 단계**: `first_visit` → `attending` → `registered` → `settled`(순차적 마일스톤)

```
Step 1: Data Intake (data-ingestor parses newcomer card)
    ↓
Step 2: Human Confirmation ◆ HitL GATE (verify parsed data accuracy)
    ↓
Step 3: Registration (newcomer-tracker creates N-record)
    ↓
Step 4: Welcome Action Generation (template-driven welcome letter/call list)
    ↓
Step 5: Stage Transition ◆ HitL GATE (pastoral judgment: ready for next stage?)
    ↓
Step 6: Settlement ◆ HitL GATE (create permanent member record → M-record)
```

**교차 파일 이관**: N-record → M-record(newcomer-tracker가 `settled`로 표시, member-manager가 교인 기록 생성). N5 검증 규칙을 통해 양방향 정합성을 검사합니다.

### 4.4 월간 재정 보고서 워크플로우

**트리거**: 월말(익월 1일-5일)
**소요 시간**: 수일(데이터 수집 → 검증 → 보고서 생성)
**중요**: PRD §5.1 F-03에 따라 Autopilot **영구 비활성**

```
Step 1: Data Ingestion ◆◆ HitL DOUBLE REVIEW (financial data accuracy)
    ↓
Step 2: Data Recording ◆◆ HitL DOUBLE REVIEW (commit financial records)
    ↓
Step 3: Monthly Summary (arithmetic aggregation — deterministic)
    ↓
Step 4: Report Generation (monthly financial report)
    ↓
Step 5: Report Review ◆◆ HitL DOUBLE REVIEW (dual approval mandatory)
    ↓
Step 6: Receipt Generation ◆◆ HitL DOUBLE REVIEW (legal tax donation receipts)
```

**이중 리뷰 패턴**: 두 명의 별도 승인자가 필요합니다. 첫 번째 리뷰어가 데이터 정확성을 확인하고, 두 번째 리뷰어(당회장 또는 지정 장로)가 거버넌스 승인을 제공합니다.

### 4.5 문서 생성기 워크플로우

**트리거**: 수시(증서 요청, 공문, 초청장)
**문서 유형**: 2단계 분석에서 도출된 7개 유형 [trace:step-2:template-analysis]

```
Step 1: Template Check (verify template exists for document type)
    ↓
Step 2: Template Setup ◆ HitL GATE (first-time template confirmation)
    ↓
Step 3: Document Generation (template-driven slot filling)
    ↓
Step 4: Document Review ◆ HitL GATE (human reviews generated document)
```

**교단 인식**: 템플릿 시스템은 교단별 헤더와 거버넌스 용어를 지원합니다(예장통합, 예장합동, 기감, 기장, 기하, 기성 — 1단계 도메인 분석 기준 6개 교단).

---

## 5. 데이터 파이프라인 아키텍처

[trace:step-1:data-model] [trace:step-4:schema-specs]

*전체 명세: `planning/step5-pipeline-architecture.md` Parts A-B*

### 5.1 3계층 파이프라인 개요

inbox/ 파이프라인은 비기술 사용자(PRD 페르소나: 행정 간사 김미영, 42세, CLI 경험 없음)를 위한 주요 진입점입니다.

| 계층 | 입력 형식 | 기술 | 기본 신뢰도 | 사용 사례 |
|------|-------------|-----------|-----------------|----------|
| **A** | Excel (.xlsx), CSV (.csv) | openpyxl, pandas, chardet | 0.95 | 헌금내역, 교인명부, 새신자등록카드 |
| **B** | Word (.docx), PDF (.pdf) | python-docx, Claude Read | 0.70 | 심방일지, 회의안건, 공문 |
| **C** | Images (.jpg, .png) | Claude multimodal, Tesseract OCR | 0.55 | 영수증, 명함, 주보 텍스트 |

### 5.2 파이프라인 오케스트레이션 흐름

```
inbox/{file}
    │
    ▼
[File Detection] ← inotify/polling (1-minute interval)
    │
    ▼
[Format Classification] ← extension + magic bytes
    │
    ├── .xlsx/.csv ──→ [Tier A: Structured Parser]
    │                      openpyxl column mapping
    │                      pandas DataFrame validation
    │                      chardet Korean encoding detection
    │
    ├── .docx/.pdf ──→ [Tier B: Semi-Structured Parser]
    │                      python-docx paragraph extraction
    │                      Claude Read for complex PDFs
    │                      Section/heading-based field mapping
    │
    └── .jpg/.png ──→ [Tier C: Unstructured Parser]
                          Claude multimodal vision analysis
                          Tesseract OCR fallback
                          Confidence-scored field extraction
    │
    ▼
[Confidence Scoring] ← per-field + aggregate score
    │
    ▼
[P1 Validation] ← validate_members/finance/schedule/newcomers
    │
    ▼
[Staging] → inbox/staging/{timestamp}-{filename}.yaml
    │
    ▼
[Human Confirmation] ◆ HitL GATE (preview + approve/reject/edit)
    │
    ▼
[Writer Agent] ← designated sole writer consumes staging file
    │
    ▼
[Processed] → inbox/processed/{date}/{filename}
```

### 5.3 디렉터리 구조

```
inbox/
├── documents/           ← Tier A + Tier B input
│   ├── 헌금내역.xlsx       → finance.yaml
│   ├── 새신자등록카드.xlsx  → newcomers.yaml
│   ├── 교인명부.csv        → members.yaml
│   └── 회의안건.pdf        → church-state.yaml
├── images/              ← Tier C input
│   ├── receipt-001.jpg     → finance.yaml
│   └── namecard-kim.jpg    → newcomers.yaml
├── templates/           ← Scan-and-Replicate input
│   └── bulletin-sample.jpg → templates/bulletin-template.yaml
├── staging/             ← Parsed results awaiting confirmation
├── processed/           ← Successfully processed originals
└── errors/              ← Failed processing records
```

### 5.4 신뢰도 점수화 시스템

| 임계값 | 수준 | 조치 | 재정 오버라이드 |
|-----------|-------|--------|-----------------|
| ≥ 0.90 | 높음 | 리뷰를 위해 자동 스테이징 | 여전히 이중 인간 승인 필요 |
| 0.70-0.89 | 중간 | 경고 강조 표시와 함께 스테이징 | 여전히 이중 인간 승인 필요 |
| 0.50-0.69 | 낮음 | 필드별 신뢰도와 함께 스테이징 | 여전히 이중 인간 승인 필요 |
| < 0.50 | 거부 | `inbox/errors/`로 라우팅 | 거부 |

**핵심**: 재정 데이터는 신뢰도 점수와 관계없이 **절대로** 자동 승인되지 않습니다.

### 5.5 한국어 인코딩 처리

레거시 한국 교회 파일은 UTF-8이 아닌 EUC-KR 또는 CP949를 자주 사용합니다. 파이프라인은 한국어 인식 폴백 체인을 사용합니다:

1. chardet 감지 → 신뢰도 > 0.8이면 감지된 인코딩 사용
2. 순차 시도: EUC-KR → CP949 → UTF-8-SIG → UTF-8
3. 최종 폴백: `errors='replace'`(대체 모드)를 적용한 UTF-8

### 5.6 HWP 파일 처리

HWP(한글 워드프로세서)는 한국 교회에서 흔히 사용되지만 pyhwp 라이브러리는 바이너리 형식에 대해 신뢰성이 낮습니다. 전략은 다음과 같습니다:
- `.hwp` 파일 감지 시 → 사용자 안내와 함께 `inbox/errors/`로 라우팅
- 한컴오피스에서의 수동 PDF 내보내기를 위한 한국어 안내 제공
- 내보낸 PDF를 Tier B로 처리

### 5.7 오류 처리

12개 오류 유형이 복구 전략과 함께 정의되어 있습니다(전체 상세는 `step5-pipeline-architecture.md` Part D 참조):

| 오류 유형 | 복구 | 원본 보존 |
|-----------|---------|-------------------|
| 인코딩 실패 | 폴백 체인 → 수동 검토 | 예 |
| 지원하지 않는 형식 | 사용자 안내(HWP → PDF) | 예 |
| 부분 추출 | 필드별 신뢰도와 함께 스테이징 | 예 |
| 검증 실패 | 스테이징에 표시, 인간이 검토 | 예 |
| 손상된 파일 | 메타데이터와 함께 errors/로 라우팅 | 예 |

**원칙**: 명시적 오류 표시 없이 파일이 자동으로 폐기되거나 부분 처리되는 일은 없습니다.

---

## 6. 스캔-앤-복제 엔진

[trace:step-2:template-analysis]

*전체 명세: `planning/step5-pipeline-architecture.md` Part C*

### 6.1 개요

스캔-앤-복제 엔진은 물리적 문서 샘플(사진/스캔)을 재사용 가능한 YAML 템플릿 정의로 변환합니다. 이 템플릿은 document-generator 에이전트가 일관된 출력을 생성하도록 구동합니다.

### 6.2 4단계 프로세스

```
Stage 1: Document Analysis (Claude multimodal)
    → Identifies fixed/variable regions, layout, fonts, seal placement
    │
Stage 2: Template Generation
    → Produces templates/{type}-template.yaml with slot definitions
    │
Stage 3: Human Confirmation ◆ HitL GATE
    → User reviews template, adjusts slot mappings
    │
Stage 4: Document Generation
    → document-generator fills template with data from YAML sources
```

### 6.3 지원 문서 유형

2단계 템플릿 분석의 7개 유형 전체 [trace:step-2:template-analysis]:

| # | 문서 유형 | 한국어 | 가변 영역 | 교단별 차이 |
|---|-------------|--------|-----------------|---------------------|
| 1 | Weekly Bulletin | 주보 | 16개 영역(설교, 기도, 일정, 생일, 광고) | 헤더, 거버넌스 용어 |
| 2 | Tax Donation Receipt | 기부금영수증 | 8개 영역(기부자, 금액, 기간, 한글 숫자 합계) | 교회명, 사업자등록번호 |
| 3 | Worship Order | 순서지 | 12개 영역(예배 항목, 찬송, 성경, 참여자) | 예전 순서 차이 |
| 4 | Official Letter | 공문 | 6개 영역(발신자, 수신자, 제목, 본문, 인장) | 당회장 vs 감독 vs 총회장 |
| 5 | Meeting Minutes | 회의록 | 10개 영역(날짜, 참석자, 안건, 결의, 투표) | 당회록 vs 제직회의록 |
| 6 | Certificate | 증서 | 5개 영역(유형, 이름, 날짜, 발급자, 인장) | 세례 형태, 교회 직인 |
| 7 | Invitation | 초청장 | 7개 영역(행사, 장소, 날짜, 프로그램, 회신) | 최소 변형 |

### 6.4 한국어 서식 관례

2단계 분석에서 도출 [trace:step-2:template-analysis]:
- **한글 숫자 표기**: 금 일백이십삼만사천원정(기부금 영수증에서 법적으로 요구됨)
- **인장 배치**: 직인(공식 인장)이 유형별 특정 문서 위치에 배치
- **세로쓰기 영역**: 전통적 요소에 세로쓰기 사용(예: 찬송가 게시판)
- **날짜 형식**: YYYY년 MM월 DD일(한국 연호는 선택사항)

---

## 7. P1 검증 프레임워크

[trace:step-4:validation-rules]

*전체 명세: `planning/step5-hooks-validation.md` Part A*

### 7.1 검증 스크립트 인벤토리

| 스크립트 | 도메인 | 검사 수 | 규칙 |
|--------|--------|--------|-------|
| `validate_members.py` | 교적 | 6 | M1 (ID), M2 (필수 필드), M3 (전화번호 regex), M4 (상태 enum), M5 (가족 ID), M6 (날짜) |
| `validate_finance.py` | 재정 기록 | 5 | F1 (ID), F2 (금액 양수), F3 (헌금 합계), F4 (예산 산술), F5 (월별 결산) |
| `validate_schedule.py` | 일정 데이터 | 5 | S1 (3개 유형의 ID 형식), S2 (시간 형식), S3 (반복 enum), S4 (상태 enum), S5 (시설 중복) |
| `validate_newcomers.py` | 새신자 기록 | 6 | N1 (ID), N2 (정착 단계), N3 (날짜 형식), N4 (교인 참조), N5 (정착 정합성), N6 (_stats 산술) |

### 7.2 공통 인터페이스

4개 스크립트 모두 다음을 공유합니다:

```bash
python3 church-admin/.claude/hooks/scripts/validate_<domain>.py \
  --data-dir ./church-admin/data/ \
  [--members-file <path>]   # override for cross-ref scripts
  [--fix]                   # auto-fix computed fields (_stats)
```

**JSON 출력 스키마**:
```json
{
  "valid": true|false,
  "script": "validate_<domain>.py",
  "data_file": "data/<domain>.yaml",
  "checks": [
    {"rule": "M1", "name": "ID Uniqueness", "status": "PASS|FAIL", "detail": "..."}
  ],
  "errors": [],
  "warnings": [],
  "summary": "6/6 checks passed"
}
```

**Exit 코드**: 0 = 검증 완료(`valid` 필드 확인), 1 = 치명적 오류. Exit code 2는 사용되지 **않습니다**(PreToolUse hook 전용).

### 7.3 주요 검증 상세

**N2 정착 단계 순차적 마일스톤** [trace:step-4:schema-specs]:
```
first_visit → attending → registered → settled
```
각 단계에는 전제 조건이 있습니다: `attending`은 방문 횟수 ≥ 2 필요, `registered`는 연락처 정보 필요, `settled`는 12주 이상의 출석 필요.

**N5 교차 파일 정착 정합성**:
- 순방향: 새신자 상태가 `settled`이면, `members.yaml`에 대응하는 M-record가 존재해야 합니다
- 역방향: 교인에 `source: newcomer`와 `newcomer_id: N###`이 있으면, N-record의 상태가 `settled`이어야 합니다
- 우아한 저하: `members.yaml`이 사용 불가능하면, N5는 FAIL이 아닌 WARNING을 발생시킵니다

**N6 통계 산술** (4단계 리뷰에서 추가):
- `_stats.total_active`는 `status: active`인 기록의 수와 일치해야 합니다
- `_stats.by_stage.{stage}`는 해당 `journey_stage`를 가진 기록의 수와 일치해야 합니다

**F3 헌금 합계 정합성**:
- 특정 기간의 총 헌금은 개별 헌금 기록의 합계와 일치해야 합니다
- 무효 기록(`status: void`)은 합산에서 제외됩니다

**S5 시설 예약 중복 감지**:
- 동일 시설에 대한 두 예약의 시간 범위가 겹칠 수 없습니다
- 알고리즘: start_time으로 정렬 후, 각 쌍에 대해 중복을 검사합니다

---

## 8. Hook 구성

[trace:step-4:schema-specs]

*전체 명세: `planning/step5-hooks-validation.md` Part B*

### 8.1 Hook 인벤토리

| Hook | 이벤트 | Matcher | Exit 코드 | 목적 |
|------|-------|---------|-----------|---------|
| `guard_data_files.py` | PreToolUse | `Edit\|Write` | 0 (허용) / 2 (차단) | 쓰기 권한 매트릭스 강제 |
| `validate_yaml_syntax.py` | PostToolUse | `Write` | 0 (항상) | 쓰기 시 YAML 구문 검사 |
| `setup_church_admin.py` | Setup | `--init` | 0 (정상) / 1 (치명적) | 인프라 건강 검증 |

### 8.2 guard_data_files.py — 쓰기 권한 가드

**트리거**: `church-admin/data/*.yaml`을 대상으로 하는 모든 Edit 또는 Write 도구 호출
**동작**:
1. 도구 입력에서 대상 파일 경로 추출
2. 쓰기 권한 매트릭스(섹션 3.3)와 대조
3. 컨텍스트에서 호출 에이전트 식별
4. 인가된 기록자이면 → exit 0(허용)
5. 비인가이면 → exit 2(차단) + stderr 피드백 메시지

**특수 사례**:
- `church-glossary.yaml`: 추가 전용 업데이트 허용(기존 항목은 수정 불가)
- `church-state.yaml`: Orchestrator/Team Lead 전용
- `templates/*.yaml`: `template-scanner` 전용

### 8.3 validate_yaml_syntax.py — YAML 구문 검사

**트리거**: church-admin/의 `*.yaml` 파일에 대한 모든 Write
**동작**: 기록된 파일에 `yaml.safe_load()` 실행 → stderr로 구문 오류 보고
**의미론**: 경고 전용(exit code 항상 0). 쓰기를 차단하지 않으며, 수정을 위해 보고합니다.

### 8.4 setup_church_admin.py — 인프라 건강

**트리거**: `claude --init` (Setup 이벤트)
**검사 항목** (CA-1부터 CA-8):

| 검사 | 대상 | 실패 조치 |
|-------|------|---------------|
| CA-1 | Python ≥ 3.8 | 치명적(exit 1) |
| CA-2 | PyYAML 임포트 가능 | 치명적(exit 1) |
| CA-3 | `church-admin/data/` 디렉터리 존재 | 자동 생성 |
| CA-4 | 6개 데이터 파일 전체 존재 | 경고 |
| CA-5 | 4개 검증 스크립트 전체 존재 | 경고 |
| CA-6 | `guard_data_files.py` hook 존재 | 경고 |
| CA-7 | 런타임 디렉터리 존재 | 자동 생성 |
| CA-8 | SOT 파일(`church-state.yaml`) 파싱 가능 | 경고 |

### 8.5 settings.json 통합

3개의 새로운 hook 항목이 기존 상위 AgenticWorkflow hook과 함께 `.claude/settings.json`에 추가됩니다. 모두 `if test -f; then; fi` 가드를 사용하여 church-admin 스크립트가 존재할 때만 hook이 실행됩니다.

---

## 9. 슬래시 커맨드 명세

*전체 명세: `planning/step5-hooks-validation.md` Part C*

### 9.1 커맨드 인벤토리

| 커맨드 | 단계 | 게이트 | 주요 검사 |
|---------|------|------|-----------|
| `/review-research` | 3 | 리서치 검증 | 도메인 커버리지, 용어, 템플릿 분석 완전성 |
| `/approve-architecture` | 6 | 아키텍처 승인 | 스키마 설계, 에이전트 명세, 파이프라인 설계, hook 구성 |
| `/review-m1` | 10 | M1 핵심 기능 | 워크플로우 실행, P1 검증 결과, 통합 테스트 |
| `/final-review` | 14 | 시스템 인수 | 전체 DNA 유전, 모든 P1 스크립트 통과, 문서화 완료 |

### 9.2 Autopilot 동작

Autopilot 모드에서 슬래시 커맨드는 품질 극대화 기본값으로 자동 승인됩니다:
1. 완전한 리뷰 실행(전체 평가 생성, 건너뛰지 않음)
2. 품질 극대화 기본값 승인 적용
3. `autopilot-logs/step-N-decision.md`에 결정 기록
4. 다음 단계로 진행

---

## 10. 인간 개입 루프 아키텍처

[trace:step-1:domain-analysis]

*전체 명세: `planning/step5-agent-architecture.md` Part C*

### 10.1 위험도 분류

| 위험 수준 | 게이트 패턴 | 리뷰 유형 | 재정 오버라이드 |
|-----------|-------------|------------|-----------------|
| **높음** | ◆◆ 이중 리뷰 | 두 명의 별도 승인자 | 항상 높음(무조건) |
| **중간** | ◆ 단일 리뷰 | 한 명의 승인자 | 해당 없음 |
| **낮음** | ◆ 단일 리뷰 | 한 명의 승인자(Autopilot 적격) | 해당 없음 |

### 10.2 게이트 인벤토리

| 게이트 ID | 워크플로우 | 단계 | 위험도 | 리뷰어 |
|---------|----------|------|------|----------|
| HitL-F01 | monthly-finance-report | 1 (데이터 수집) | 높음 | 재정부장 + 당회장 |
| HitL-F02 | monthly-finance-report | 2 (데이터 기록) | 높음 | 재정부장 + 당회장 |
| HitL-F03 | monthly-finance-report | 5 (보고서 검토) | 높음 | 재정부장 + 당회장 |
| HitL-F04 | monthly-finance-report | 6 (영수증 생성) | 높음 | 재정부장 + 당회장 |
| HitL-N01 | newcomer-pipeline | 2 (확인) | 중간 | 새신자 담당 |
| HitL-N02 | newcomer-pipeline | 5 (단계 전환) | 중간 | 담임목사/교육전도사 |
| HitL-D01 | document-generator | 2 (템플릿 설정) | 중간 | 행정 간사 |
| HitL-D02 | document-generator | 4 (문서 검토) | 중간 | 행정 간사 |
| HitL-B01 | weekly-bulletin | 5 (주보 검토) | 낮음 | 행정 간사 |

---

## 11. Autopilot 적격성 매트릭스

[trace:step-4:schema-specs]

*전체 명세: `planning/step5-agent-architecture.md` Part E*

### 11.1 워크플로우 수준

| 워크플로우 | Autopilot | 근거 |
|----------|-----------|---------------|
| `weekly-bulletin` | **적격** | 낮은 위험, 정보성 콘텐츠, 인쇄 시 오류 포착 가능 |
| `newcomer-pipeline` | **부분적** | 등록은 적격, 단계 전환은 목회적 판단 필요 |
| `monthly-finance-report` | **영구 비활성** | 법적/수탁 의무, PRD §5.1 F-03 |
| `document-generator` | **적격**(대부분의 유형) | 템플릿 가드레일, 단일 리뷰 게이트 |

### 11.2 안전 장치

| 안전 장치 | 구현 | 목적 |
|-------|---------------|---------|
| 재정 잠금 | `guard_data_files.py` + 워크플로우 설정 | 재정 Autopilot 영구 비활성 |
| P1 게이트 | `validate_*.py` → `valid: true` 필수 | 검사 실패 시 자동 승인 불가 |
| pACS 하한선 | pACS < 50 → 인간 검토 필수 | RED 영역은 자동 승인 불가 |
| 감사 추적 | `autopilot-logs/` | 완전한 결정 기록 |

---

## 12. 워크플로우 간 데이터 의존성

[trace:step-4:schema-specs]

*전체 명세: `planning/step5-agent-architecture.md` Part D*

### 12.1 데이터 접근 매트릭스

| 에이전트 | members | finance | schedule | newcomers | bulletin-data | glossary |
|-------|---------|---------|----------|-----------|--------------|---------|
| bulletin-generator | R | — | R | — | **W** | R |
| finance-recorder | R | **W** | — | — | — | R |
| member-manager | **W** | — | — | R | — | R |
| newcomer-tracker | R | — | — | **W** | — | R |
| schedule-manager | — | — | **W** | — | R | R |
| document-generator | R | R | — | — | — | R |
| data-ingestor | — | — | — | — | — | R |
| template-scanner | — | — | — | — | — | **W** |
| integration-tester | R | R | R | R | R | R |
| onboarding-author | — | — | — | — | — | R |

**W** = 단독 기록자, **R** = 읽기 전용, **—** = 접근 없음

### 12.2 핵심 교차 파일 의존성

1. **새신자 → 교인 이관** (N5 ↔ M1): `newcomer-tracker`가 `settled`로 표시 → `member-manager`가 M-record를 생성합니다. N5 검증으로 양방향 정합성이 강제됩니다.

2. **재정 → 교인 기부자 추적** (F3 ↔ M): `finance-recorder`가 헌금 기록에서 `member_id`를 참조합니다. F 규칙으로 교차 참조가 검증됩니다.

3. **주보 → 일정 + 교인**: `bulletin-generator`가 예배 시간을 위해 `schedule.yaml`을, 생일/기념일 필터링을 위해 `members.yaml`을 읽습니다.

4. **문서 → 교인 + 재정**: `document-generator`가 증서를 위해 교인 데이터를, 연간 기부금 영수증을 위해 재정 데이터를 읽습니다.

---

## 13. 공유 유틸리티

*전체 명세: `planning/step5-hooks-validation.md` Part D*

### 13.1 atomic_write_yaml()

패턴: `fcntl.flock` + `tempfile.NamedTemporaryFile` + `os.rename`

```python
def atomic_write_yaml(filepath: str, data: dict) -> None:
    """Write YAML atomically using flock + temp file + rename pattern.

    Layer 3 of data integrity architecture [trace:step-4:schema-specs]:
    - flock guards the write phase of the temp file
    - os.rename provides atomic replacement on same filesystem
    - Layer 1 (guard_data_files.py) prevents cross-writer races
    """
```

### 13.2 church_data_utils.py

다음을 포함하는 공유 헬퍼 라이브러리:
- 한국어 인코딩 지원 YAML 로딩
- 교차 파일 교인/가족 ID 조회
- 날짜 검증(한국어 형식 지원)
- 전화번호 검증(완화된 regex: `^010-\d{4}-\d{4}$`)
- ID 형식 검증기(M, F, N, OFF, EXP, SVC, EVT, FAC 패턴)
- 컴파일된 regex 패턴(모듈 수준, 프로세스당 1회)

### 13.3 한글 숫자 변환

```python
def integer_to_korean_numeral(amount: int) -> str:
    """Convert integer to Korean formal numeral notation.

    Example: 1_234_000 → "일백이십삼만사천원정"
    Legally required on tax donation receipts per 소득세법.
    """
```

### 13.4 개인정보 마스킹

```python
def mask_korean_name(name: str) -> str:
    """Mask middle character(s) for bulletin display.
    '김철수' → '김○수', '남궁세연' → '남궁○연'"""

def mask_resident_number(number: str) -> str:
    """Mask Korean resident registration number for receipts.
    'YYMMDD-NNNNNNN' → 'YYMMDD-N******'"""
```

---

## 14. 구현 로드맵

이 아키텍처 블루프린트는 다음에 대한 완전한 구현 명세를 제공합니다:

| 단계 | 내용 | 이 블루프린트의 핵심 입력 |
|------|------|-------------------------------|
| **7** | 인프라 기반 구축 | 디렉터리 구조(§5.3), 시드 데이터 스키마(§3.3), SOT 초기화 |
| **8** | P1 검증 스크립트 | 검증 규칙(§7), JSON 출력 스키마(§7.2), 공유 유틸리티(§13) |
| **9** | M1 핵심 기능 | 에이전트 명세(§3), 워크플로우 블루프린트(§4), 파이프라인 설계(§5) |
| **10** | M1 리뷰 | 통합 테스트 기준, P1 검증 결과 |
| **11** | M2 확장 기능 | 문서 생성기(§4.5), 교단 지원(§6.3), 일정 관리자 |
| **12** | 통합 테스트 | 워크플로우 간 의존성(§12), 전체 P1 검증 스위트 |
| **13** | 문서화 | 온보딩 문서용 에이전트 명세, 사용자 가이드용 파이프라인 개요 |

### 단계별 컨텍스트 주입

| 단계 | 주입 패턴 | 추출할 섹션 |
|------|------------------|-------------------|
| Step 7 | Pattern A (전체) | §3.3 (쓰기 매트릭스), §5.3 (디렉터리), §14 (로드맵) |
| Step 8 | Pattern B (필터링) | §7 (검증), §13 (유틸리티) |
| Step 9 | Pattern B (필터링) | §3 (에이전트), §4 (워크플로우), §5 (파이프라인) |
| Step 11 | Pattern B (필터링) | §4.4-4.5 (재정/문서 워크플로우), §6 (스캔-앤-복제) |

---

## 15. 검증 보고서

### 15.1 5단계 기준 대비 통합 검증

| # | 기준 | 상태 | 근거 |
|---|-----------|--------|----------|
| 1 | 8개 이상의 에이전트 명세 완료(name, description, model, tools, permissionMode, maxTurns, memory scope 포함) | **PASS** | §3에 10개 에이전트 명시(bulletin-generator, finance-recorder, member-manager, newcomer-tracker, data-ingestor, template-scanner, document-generator, church-integration-tester, church-onboarding-author, schedule-manager). 각각 `step5-agent-architecture.md` A.2-A.11에 전체 명세 보유. |
| 2 | 4개 이상의 기능 워크플로우 블루프린트가 3단계 구조를 따르며, 모든 에이전트 단계에 Verification 필드 포함 | **PASS** | §4에 4개 워크플로우(weekly-bulletin, newcomer-pipeline, monthly-finance-report, document-generator). 각각 유전된 DNA 테이블 + 모든 단계에 Verification 기준 보유. 전체 상세는 `step5-agent-architecture.md` B.1-B.4. |
| 3 | inbox/ 파이프라인 설계가 특정 Python 라이브러리와 계층별 컬럼/필드 매핑으로 3개 계층 전체 커버 | **PASS** | §5에서 Tier A(openpyxl, pandas, chardet), Tier B(python-docx, Claude Read), Tier C(Claude multimodal, Tesseract OCR) 커버. 컬럼 매핑은 `step5-pipeline-architecture.md` A.3-A.5. |
| 4 | 스캔-앤-복제 엔진이 2단계 분석의 7개 문서 유형 전체 처리 [trace:step-2:template-analysis] | **PASS** | §6에서 7개 유형 전체 커버(주보, 기부금영수증, 순서지, 공문, 회의록, 증서, 초청장). 4단계 프로세스는 `step5-pipeline-architecture.md` Part C. |
| 5 | 4개 검증 스크립트 명세가 4단계 스키마 설계의 모든 규칙 포함 [trace:step-4:validation-rules] | **PASS** | §7에서 validate_members(M1-M6), validate_finance(F1-F5), validate_schedule(S1-S5), validate_newcomers(N1-N6) 커버. 총 22개 검사. 전체 상세는 `step5-hooks-validation.md` Part A. |
| 6 | 인간 개입 루프 게이트가 올바르게 분류됨: 높은 위험(재정 → 이중 리뷰, Autopilot 비활성), 중간(새신자/문서 → 단일 리뷰), 낮음(주보 → 단일 리뷰, Autopilot 적격) | **PASS** | §10에서 3개 위험 수준, 9개 HitL 게이트 정의. 재정: 이중 리뷰의 높음(HitL-F01~F04). 새신자/문서: 단일 리뷰의 중간(HitL-N01/N02, HitL-D01/D02). 주보: 낮음(HitL-B01, Autopilot 적격). |
| 7 | 교차 단계 추적성: 아키텍처 결정이 도메인 분석 [trace:step-1] 및 스키마 명세 [trace:step-4]로 추적 가능 | **PASS** | 전체에 걸친 추적 마커: [trace:step-1:domain-analysis], [trace:step-1:data-model], [trace:step-1:terminology], [trace:step-2:template-analysis], [trace:step-4:schema-specs], [trace:step-4:validation-rules]. 컴포넌트 명세 전반에 25개 이상의 마커. |
| 8 | 파이프라인 연결: 아키텍처 블루프린트가 7-13단계에 대한 완전한 구현 명세 제공 | **PASS** | §14에서 각 하류 단계를 이 블루프린트의 특정 섹션에 매핑. 단계별 컨텍스트 주입 패턴 정의. |

### 15.2 컴포넌트 검증 요약

| 컴포넌트 | 명세 파일 | 자기 검증 | 기준 |
|-----------|-----------|-------------------|----------|
| 에이전트 아키텍처 | `step5-agent-architecture.md` | 8/8 PASS | 에이전트, 워크플로우, HitL, Autopilot, 쓰기 권한, 추적, 재정 잠금, Verification 필드 |
| 파이프라인 아키텍처 | `step5-pipeline-architecture.md` | 8/8 PASS | 3개 계층, HitL 흐름, 7개 문서 유형, 오류 처리, 검증 통합, 추적, 용어 사전, 신뢰도 점수화 |
| Hook & 검증 | `step5-hooks-validation.md` | 8/8 PASS | 4개 검증기, 결정론적 검사, JSON 출력, 3개 hook, 4개 커맨드, 원자적 쓰기, 가드 통합, exit 코드 |

### 15.3 교차 참조 무결성

3개 컴포넌트 명세 모두 일관되게 참조합니다:
- **데이터 파일명**: members.yaml, finance.yaml, schedule.yaml, newcomers.yaml, bulletin-data.yaml, church-glossary.yaml
- **검증 규칙 ID**: M1-M6, F1-F5, S1-S5, N1-N6(총 22개, N6 추가를 포함한 4단계 명세와 일치)
- **에이전트 이름**: 모든 명세에서 동일한 이름의 10개 에이전트
- **쓰기 권한 매트릭스**: 에이전트 명세, hook 명세, 파이프라인 라우팅 전반에 걸쳐 일관된 단독 기록자 지정
- **전화번호 regex**: `^010-\d{4}-\d{4}$`(4단계 리뷰 수정에 따라 완화)
- **Exit 코드 관례**: PreToolUse hook은 0/2, 검증기는 0/1, 상위 AgenticWorkflow와 일관

---

## 부록 A: 추적 마커 인덱스

| 추적 마커 | 소스 단계 | 참조 위치 |
|-------------|-----------|---------------|
| `[trace:step-1:domain-analysis]` | 1단계 도메인 분석 | §1, §3, §4, §10 |
| `[trace:step-1:data-model]` | 1단계 데이터 모델 | §5 |
| `[trace:step-1:terminology]` | 1단계 용어 사전 | §6.4 |
| `[trace:step-2:template-analysis]` | 2단계 템플릿 분석 | §4, §6 |
| `[trace:step-4:schema-specs]` | 4단계 스키마 명세 | §1, §2, §3, §5, §7, §8, §11, §12, §13 |
| `[trace:step-4:validation-rules]` | 4단계 검증 규칙 카탈로그 | §7 |

---

*이 문서는 `arch-blueprint` 팀(3개 병렬 에이전트: @church-agent-architect, @church-pipeline-designer, @church-hook-designer)이 생성하였으며, Team Lead가 교차 참조 검증을 수행한 후 병합하였습니다.*

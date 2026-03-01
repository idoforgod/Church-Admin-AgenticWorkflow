# 교회 행정 AI 에이전트 자동화 시스템

**한국 중소형 교회(100-500명)를 위한 AI 기반 행정 자동화 시스템.**

주보 제작, 새신자 관리, 재정 보고, 문서 발급, 일정 관리 등 반복적인 교회 행정 업무를 AI 에이전트가 자동 수행하여, 주당 23시간의 수동 행정 업무를 5시간 이하로 줄입니다.

> 이 시스템은 [AgenticWorkflow](README.md) 프레임워크(부모)에서 태어난 **자식 시스템**입니다.
> 부모의 전체 DNA(절대 기준, 품질 보장, 안전장치, 기억 체계)를 구조적으로 내장합니다.

---

## 해결하는 문제

한국 중소형 교회의 행정 간사는 매주 다음과 같은 반복 업무에 시달립니다:

| 업무 | 주당 소요 시간 | 자동화 후 |
|------|-------------|---------|
| 주보 제작 | ~4시간 | ~15분 (AI 생성 + 1회 검토) |
| 새신자 등록·관리 | ~3시간 | ~30분 (파이프라인 자동화) |
| 재정 기록·보고 | ~6시간 | ~2시간 (이중 검토 유지) |
| 증명서·공문 발급 | ~3시간 | ~15분 (템플릿 기반 자동 생성) |
| 일정 관리 | ~2시간 | ~15분 (충돌 자동 감지) |
| 기타 데이터 정리 | ~5시간 | ~1시간 (자동 수집·검증) |
| **합계** | **~23시간** | **~4시간 15분** |

## 핵심 역량

| 역량 | 상세 |
|------|------|
| **5개 독립 워크플로우** | 주보 생성, 새신자 파이프라인, 월별 재정 보고, 문서 발급, 일정 관리 |
| **8개 전문 에이전트** | 각 데이터 파일에 대한 단독 쓰기 권한 — 데이터 충돌 원천 차단 |
| **29개 결정론적 검증 규칙** | P1 검증 스크립트 5개 (Members M1-M7, Finance F1-F7, Schedule S1-S6, Newcomers N1-N6, Bulletin B1-B3) |
| **한국어 자연어 인터페이스** | 41개 한국어 명령 패턴 → 8개 카테고리(주보, 새신자, 교인, 재정, 일정, 문서, 데이터, 시스템) |
| **3계층 수신함 파이프라인** | Tier A: Excel/CSV, Tier B: Word/PDF, Tier C: 이미지 — 자동 파싱 + 신뢰도 점수 |
| **스캔-복제 엔진** | 7종 교회 문서(주보, 영수증, 순서지, 공문, 회의록, 증서, 초청장) 템플릿화 |
| **재정 안전 장치** | 재정 Autopilot 영구 비활성화 — 3중 강제(SOT + 에이전트 + 워크플로우) |
| **한국 교회 용어 사전** | 50+ 용어(직분, 치리, 예배, 재정, 성례, 새신자, 문서) 정규화 |

## 빠른 시작

```bash
# 1. 저장소 클론
git clone https://github.com/idoforgod/AgenticWorkflow.git
cd AgenticWorkflow/church-admin

# 2. Claude Code 실행
claude

# 3. 한국어로 명령
"주보 만들어줘"              # 주보 생성
"새신자 등록"                # 새신자 파이프라인 시작
"이번 달 재정 보고서"         # 월별 재정 보고서
"교인 검색 김철수"            # 교인 검색
"데이터 검증"                # 전체 P1 검증 실행
```

상세 설치 가이드: [`church-admin/docs/quick-start.md`](church-admin/docs/quick-start.md) (한국어: [`quick-start.ko.md`](church-admin/docs/quick-start.ko.md))

## 프로젝트 구조

```
church-admin/
├── CLAUDE.md                    # 시스템 지시서 (에이전트 로스터, SOT 규칙, 데이터 정책)
├── state.yaml                   # SOT (Single Source of Truth) — 시스템 전체 상태
├── data/                        # 6개 YAML 데이터 파일
│   ├── members.yaml             # 교인 명부 (HIGH — PII)
│   ├── finance.yaml             # 재정 기록 (HIGH — 금융)
│   ├── schedule.yaml            # 일정 (LOW)
│   ├── newcomers.yaml           # 새신자 (HIGH — PII)
│   ├── bulletin-data.yaml       # 주보 데이터 (LOW)
│   └── church-glossary.yaml     # 한국 교회 용어 사전 (LOW)
├── .claude/
│   ├── agents/                  # 8개 전문 에이전트 정의
│   │   ├── bulletin-generator.md
│   │   ├── finance-recorder.md
│   │   ├── member-manager.md
│   │   ├── newcomer-tracker.md
│   │   ├── schedule-manager.md
│   │   ├── document-generator.md
│   │   ├── data-ingestor.md
│   │   └── template-scanner.md
│   ├── hooks/scripts/           # P1 검증 + 데이터 보호 Hook
│   └── skills/church-admin/     # 한국어 자연어 인터페이스
├── scripts/                     # 파서, 검증, 백업 스크립트
│   ├── validate_all.py          # 전체 검증 (29개 규칙)
│   ├── tier_a_parser.py         # Excel/CSV 파서
│   ├── tier_b_parser.py         # Word/PDF 파서
│   ├── tier_c_parser.py         # 이미지 파서
│   ├── inbox_parser.py          # 파이프라인 오케스트레이터
│   ├── hitl_confirmation.py     # 사람-검토 게이트
│   ├── template_engine.py       # 문서 템플릿 엔진
│   ├── template_scanner.py      # 스캔-복제 엔진
│   └── daily-backup.sh          # 자동 백업 스크립트
├── workflows/                   # 5개 독립 워크플로우 (영문 + 한국어)
│   ├── weekly-bulletin.md       # 주보 생성
│   ├── newcomer-pipeline.md     # 새신자 관리
│   ├── monthly-finance-report.md # 재정 보고
│   ├── document-generator.md    # 문서 발급
│   └── schedule-manager.md      # 일정 관리
├── templates/                   # 문서 YAML 템플릿
├── inbox/                       # 3계층 파이프라인 수신함
├── docs/                        # 운영 가이드 (영문 + 한국어)
│   ├── quick-start.md
│   ├── user-guide.md
│   ├── installation-guide.md
│   ├── it-admin-guide.md
│   └── troubleshooting.md
├── bulletins/                   # 생성된 주보
├── certificates/                # 생성된 증서
├── letters/                     # 생성된 공문
├── output/                      # 기타 출력물
├── reports/                     # 재정 보고서
├── backups/                     # 자동 백업
└── test-reports/                # 테스트 결과
```

## 데이터 민감도

| 민감도 | 데이터 파일 | 포함 정보 | 정책 |
|--------|-----------|---------|------|
| **HIGH (PII)** | `members.yaml` | 이름, 전화번호, 주소 | `.gitignore` — 공개 금지, Soft-delete only |
| **HIGH (금융)** | `finance.yaml` | 헌금 기록, 기부자 정보 | `.gitignore` — 공개 금지, Void-only 삭제 |
| **HIGH (PII)** | `newcomers.yaml` | 새신자 개인정보 | `.gitignore` — 공개 금지, Soft-delete only |
| LOW | `schedule.yaml` | 예배·행사 일정 | Status cancel |
| LOW | `bulletin-data.yaml` | 주보 콘텐츠 | 호수별 덮어쓰기 |
| LOW | `church-glossary.yaml` | 용어 사전 | Append-only |

> **HIGH 민감도 파일은 절대로 공개 저장소에 커밋하면 안 됩니다.** `.gitignore`로 보호됩니다.

## 유전받은 DNA (Inherited DNA)

이 시스템은 AgenticWorkflow 부모의 **전체 게놈**을 구조적으로 내장합니다:

| DNA 구성 요소 | 교회 행정에서의 발현 |
|-------------|-----------------|
| **절대 기준 (Constitutional Principles)** | 품질 절대주의 → 주보·재정 보고서 오류 제로 |
| **단일 파일 SOT** | `state.yaml` + 6개 데이터 파일, 각각 단독 쓰기 에이전트 |
| **4계층 품질 보장** | L0 Anti-Skip → L1 Verification → L1.5 pACS → L2 Adversarial Review |
| **P1 할루시네이션 봉쇄** | 5개 결정론적 검증 스크립트(29개 규칙) |
| **안전 Hook** | `guard_data_files.py` — 비인가 YAML 쓰기 차단 |
| **적대적 리뷰** | `@reviewer` + `@fact-checker` — 독립적 품질 검증 |
| **Context Preservation** | 스냅샷 + Knowledge Archive + RLM 복원 |
| **코딩 기준점 (CAP)** | CAP-1 사고 우선, CAP-2 단순성, CAP-3 목표 기반, CAP-4 외과적 변경 |

## 구축 과정

이 시스템은 `prompt/workflow.md`에 정의된 **14단계 워크플로우**를 통해 구축되었습니다:

| 단계 | 내용 | 산출물 |
|------|------|--------|
| 1-2 | **Research** — 도메인 분석 + 문서 템플릿 분석 | 도메인 지식, 용어 사전, 템플릿 카탈로그 |
| 3 | 리서치 검토 (human gate) | 승인 |
| 4-5 | **Planning** — 데이터 스키마 설계 + 시스템 아키텍처 | 6개 스키마, 10개 에이전트 스펙, 파이프라인 설계 |
| 6 | 아키텍처 승인 (human gate) | 승인 |
| 7-9 | **Implementation M1** — 인프라 구축 + P1 검증 + 핵심 기능 | 디렉터리, 시드 데이터, 검증 스크립트, 워크플로우 |
| 10 | M1 검토 (human gate) | 승인 |
| 11 | **Implementation M2** — 확장 기능 | 문서 발급, 일정 관리, 교단 지원 |
| 12 | 통합 테스트 | 15/15 PASS |
| 13 | 문서화 | IT 자원봉사자 온보딩 패키지 |
| 14 | 최종 검수 (human gate) | 시스템 인수 완료 |

## 문서 읽기 순서

| 순서 | 문서 | 대상 독자 | 목적 |
|------|------|---------|------|
| 1 | **이 파일 (`CHURCH-ADMIN-README.md`)** | 모든 사람 | 시스템 개요 파악 |
| 2 | [`CHURCH-ADMIN-ARCHITECTURE-AND-PHILOSOPHY.md`](CHURCH-ADMIN-ARCHITECTURE-AND-PHILOSOPHY.md) | 개발자 / IT 담당 | 설계 철학과 아키텍처 이해 |
| 3 | [`CHURCH-ADMIN-USER-MANUAL.md`](CHURCH-ADMIN-USER-MANUAL.md) | 시스템 관리자 | 운영·유지보수 방법 |
| 4 | [`church-admin/docs/quick-start.md`](church-admin/docs/quick-start.md) | 최종 사용자 | 빠른 시작 |
| 5 | [`church-admin/docs/user-guide.md`](church-admin/docs/user-guide.md) | 최종 사용자 | 전체 사용법 |
| 6 | [`church-admin/docs/troubleshooting.md`](church-admin/docs/troubleshooting.md) | 모든 사람 | 문제 해결 |

> **부모 프레임워크 문서와 혼동하지 마세요.**
> `AGENTICWORKFLOW-*.md` 파일은 프레임워크/방법론 문서이고, `CHURCH-ADMIN-*.md` 파일은 이 시스템의 문서입니다.

## 관련 문서

- **부모 프레임워크**: [`README.md`](README.md) → [`AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md`](AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md)
- **빌드 워크플로우**: [`prompt/workflow.md`](prompt/workflow.md)
- **도메인 지식**: [`domain-knowledge.yaml`](domain-knowledge.yaml) (20개 엔티티, 15개 관계, 14개 제약)
- **통합 테스트**: [`testing/integration-test-report.md`](testing/integration-test-report.md) (15/15 PASS)

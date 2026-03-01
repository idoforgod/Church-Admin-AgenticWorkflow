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

교회 행정 AI 시스템은 한국 중소형 교회(100-500명)의 반복 행정 업무를 자동화합니다.

**핵심 구성 요소**:
- 8개 전문 AI 에이전트 (데이터 파일당 단독 작성자)
- 5개 독립 워크플로우 (주보, 새신자, 재정, 문서, 일정)
- 29개 결정론적 데이터 검증 규칙
- 한국어 자연어 인터페이스 (41개 명령 패턴)
- 3계층 수신함 파이프라인 (Excel/CSV, Word/PDF, 이미지)

**대상 교회 규모**: 100-500명 (YAML 리스트 기반 데이터 구조 — 이 규모에서 충분한 성능)

---

## 2. 사전 준비 및 설치

### 2.1 필수 요구사항

| 항목 | 최소 버전 | 확인 방법 |
|------|---------|---------|
| Python | 3.9+ | `python3 --version` |
| PyYAML | 6.0+ | `python3 -c "import yaml; print(yaml.__version__)"` |
| [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) | 최신 | `claude --version` |

### 2.2 선택 요구사항 (파이프라인 기능)

| 항목 | 용도 | 설치 |
|------|------|------|
| openpyxl | Excel 파싱 (Tier A) | `pip install openpyxl` |
| pandas | 데이터 검증 (Tier A) | `pip install pandas` |
| chardet | 한국어 인코딩 감지 | `pip install chardet` |
| python-docx | Word 파싱 (Tier B) | `pip install python-docx` |

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

```
사용자 명령 (한국어) → NL Interface → 워크플로우/에이전트 라우팅
                                            ↓
                                    전문 에이전트 실행
                                            ↓
                                    P1 검증 (29개 규칙)
                                            ↓
                                    HitL 게이트 (위험 수준별)
                                            ↓
                                    데이터 파일 쓰기 (단독 작성자)
```

상세 아키텍처: [`CHURCH-ADMIN-ARCHITECTURE-AND-PHILOSOPHY.md`](CHURCH-ADMIN-ARCHITECTURE-AND-PHILOSOPHY.md)

---

## 4. 시스템 실행

### 4.1 기본 실행

```bash
cd church-admin
claude
```

Claude Code가 `church-admin/CLAUDE.md`를 자동 로드하여 에이전트 로스터, SOT 규칙, 데이터 정책을 적용합니다.

### 4.2 한국어 자연어 명령

시스템은 41개 한국어 명령 패턴을 인식합니다:

**주보 (Bulletin)**:
```
"주보 만들어줘"        → 주보 생성 워크플로우
"주보 미리보기"        → 현재 주보 초안 확인
"주보 항목 수정"       → 주보 데이터 편집
"예배 순서 만들어줘"   → 순서지 생성
```

**새신자 (Newcomer)**:
```
"새신자 등록"          → 새신자 파이프라인 시작
"새신자 현황"          → 새신자 상태 대시보드
"단계 진행"            → 여정 단계 전환 (HitL 필수)
"정착 처리"            → 교인 전환 (HitL 필수)
```

**교인 (Member)**:
```
"교인 검색 김철수"     → 이름으로 교인 검색
"교인 등록"            → 새 교인 등록
"이명 처리"            → 전입/전출 처리
"생일 축하 대상"       → 이번 주 생일 교인 조회
"교인 통계"            → 교인 현황 통계
```

**재정 (Finance)** — 모든 쓰기 작업에 이중 검토 필수:
```
"재정 보고서"          → 월별 재정 보고서 생성
"헌금 내역"            → 헌금 기록 조회
"기부금 영수증 발행"   → 기부금영수증 발급
```

**일정 (Schedule)**:
```
"이번 주 일정"         → 금주 일정 조회
"행사 등록"            → 행사 추가
"시설 예약"            → 시설 예약 (충돌 자동 감지)
```

**문서 (Document)**:
```
"증명서 발급"          → 증명서 생성
"공문 작성"            → 공문 생성
"회의록 작성"          → 회의록 생성
```

**데이터 입력 (Data Import)**:
```
"파일 가져오기"        → inbox 파이프라인 실행
"엑셀 가져오기"        → Tier A 파서
"사진 분석"            → Tier C 파서
```

**시스템 (System)**:
```
"데이터 검증"          → 전체 P1 검증 실행 (29개 규칙)
"시스템 상태"          → 건강 검사
"도움말"               → 사용 가능한 명령 표시
```

---

## 5. SOT (Single Source of Truth) 이해

### 5.1 `state.yaml` 구조

`state.yaml`은 시스템의 중앙 상태 파일입니다. **Orchestrator만 쓰기 가능**, 모든 에이전트는 읽기 전용.

```yaml
church:
  name: "새벽이슬교회 (Morning Dew Church)"
  denomination: "PCK"
  current_bulletin_issue: 1247
  status: "active"

  data_paths:          # 6개 데이터 파일 경로 레지스트리
  features:            # 기능 플래그 (워크플로우 활성화 여부)
  workflow_states:     # 워크플로우별 상태 추적
  config:
    autopilot:
      enabled: false
      finance_override: false   # 항상 false — 재정 Autopilot 영구 비활성화
    backup:
      enabled: true
      backup_dir: "backups/"
    scale:
      max_members: 500          # 설계 용량
  verification_gates:  # 마지막 검증 실행 결과
  agent_sessions:      # 에이전트별 마지막 활동 추적
```

### 5.2 데이터 파일 수정 규칙

**핵심 원칙**: 각 데이터 파일은 지정된 에이전트만 수정할 수 있습니다.

| 데이터 파일 | 단독 작성자 | 수동 수정 가능? |
|-----------|-----------|-------------|
| `data/members.yaml` | member-manager | 비권장 — 검증 규칙 위반 위험 |
| `data/finance.yaml` | finance-recorder | 비권장 — 산술 불일치 위험 |
| `data/schedule.yaml` | schedule-manager | 비권장 |
| `data/newcomers.yaml` | newcomer-tracker | 비권장 |
| `data/bulletin-data.yaml` | bulletin-generator | 비권장 |
| `data/church-glossary.yaml` | 모든 에이전트 | 가능 (append-only) |

수동 수정이 불가피한 경우, **반드시 검증을 다시 실행**하세요:

```bash
python3 scripts/validate_all.py
```

---

## 6. 검증 스크립트 실행

### 6.1 전체 검증

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

### 6.2 개별 검증

```bash
# 교인 데이터 검증
python3 .claude/hooks/scripts/validate_members.py --data-dir data/

# 재정 데이터 검증
python3 .claude/hooks/scripts/validate_finance.py --data-dir data/

# 일정 데이터 검증
python3 .claude/hooks/scripts/validate_schedule.py --data-dir data/

# 새신자 데이터 검증
python3 .claude/hooks/scripts/validate_newcomers.py --data-dir data/

# 주보 데이터 검증
python3 .claude/hooks/scripts/validate_bulletin.py --data-dir data/
```

각 스크립트는 JSON 출력을 제공합니다:
```json
{
  "valid": true,
  "script": "validate_members.py",
  "checks": [
    {"rule": "M1", "name": "ID Uniqueness", "status": "PASS"}
  ],
  "summary": "7/7 checks passed"
}
```

### 6.3 검증 실패 대응

검증 실패 시:
1. `errors` 배열에서 실패한 규칙과 상세 메시지 확인
2. 해당 데이터 파일의 문제 부분 수정
3. 검증 재실행으로 수정 확인
4. **재정 데이터 검증 실패 시**: 반드시 재정 담당자와 확인 후 수정

---

## 7. 백업 및 복원

### 7.1 자동 백업

```bash
# 백업 스크립트 실행
./scripts/daily-backup.sh

# cron 설정 (매일 새벽 2시)
crontab -e
# 추가: 0 2 * * * cd /path/to/church-admin && ./scripts/daily-backup.sh
```

백업 대상: `data/` 디렉터리의 모든 YAML 파일
보존 기간: 30일 자동 순환 (`RETENTION_DAYS=30`)
저장 형식: `backups/YYYY-MM-DD-HHMMSS.tar.gz`

### 7.2 수동 복원

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

### 7.3 백업 권장 사항

- **일일 자동 백업** 설정 (cron)
- **재정 데이터 변경 전** 수동 백업 추가 실행
- **HIGH 민감도 파일** 백업본은 외부 저장소에 암호화 보관 권장
- `state.yaml`도 함께 백업 (시스템 상태 복원에 필요)

---

## 8. 기능 확장

### 8.1 새 워크플로우 추가

1. `workflows/` 디렉터리에 새 워크플로우 `.md` 파일 생성
2. `state.yaml`의 `features`에 새 기능 플래그 추가
3. `workflow_states`에 워크플로우 상태 추적 항목 추가
4. 필요 시 새 에이전트를 `.claude/agents/`에 추가

### 8.2 새 에이전트 추가

1. `.claude/agents/` 디렉터리에 에이전트 `.md` 파일 생성
2. 에이전트 명세 구조 준수: name, model, tools, permissionMode, maxTurns, memory scope
3. 쓰기 대상 파일 있으면 `guard_data_files.py`의 Write Permission Matrix에 추가
4. `state.yaml`의 `agent_sessions`에 추적 항목 추가

### 8.3 새 검증 규칙 추가

1. 해당 `validate_*.py` 스크립트에 규칙 함수 추가
2. `validate_all.py`의 집계에 반영
3. 규칙 ID 형식 준수 (예: M8, F8, S7 등)
4. `church-admin/CLAUDE.md`에 규칙 수 업데이트

### 8.4 용어 사전 확장

`data/church-glossary.yaml`에 직접 추가합니다 (append-only):

```yaml
- korean: "새로운 용어"
  english: "new_term"
  context: "사용 맥락 설명"
  category: "카테고리"
```

---

## 9. 주기적 유지보수

### 9.1 일일 작업

- [ ] 자동 백업 성공 확인 (`backups/` 디렉터리)
- [ ] `inbox/errors/` 디렉터리 확인 (파싱 실패 파일)

### 9.2 주간 작업

- [ ] 전체 검증 실행: `python3 scripts/validate_all.py`
- [ ] `inbox/processed/` 정리 (처리 완료 원본)

### 9.3 월간 작업

- [ ] 백업 보존 정책 확인 (30일 이상 파일 자동 삭제 확인)
- [ ] `state.yaml` 상태 점검 (verification_gates 마지막 실행 날짜)
- [ ] 데이터 파일 크기 모니터링 (500명 초과 시 구조 변경 검토)

### 9.4 건강 검진

```bash
claude --maintenance
```

`setup_maintenance.py`가 실행하는 검사:
- Stale archives (오래된 아카이브)
- Knowledge-index 무결성
- Work_log 크기
- 문서-코드 동기화

---

## 10. 문제 해결

일반적인 문제 해결은 [`church-admin/docs/troubleshooting.md`](church-admin/docs/troubleshooting.md)를 참조하세요.

### 10.1 시스템 관리자 관점 빈번한 문제

| 증상 | 원인 | 해결 |
|------|------|------|
| 에이전트가 데이터 파일 쓰기 거부됨 | `guard_data_files.py`가 차단 | Write Permission Matrix 확인 — 올바른 에이전트인지 확인 |
| 검증 실패 (`valid: false`) | 데이터 무결성 위반 | `errors` 배열의 상세 메시지 확인 후 수정 |
| inbox 파일 `errors/`로 이동 | 파싱 실패 | 파일 형식 확인; HWP → PDF 변환 필요할 수 있음 |
| 한국어 깨짐 | 인코딩 문제 (EUC-KR/CP949) | 파일을 UTF-8로 재저장 후 재시도 |
| 재정 워크플로우 자동 승인 안 됨 | 설계 의도 — Autopilot 영구 비활성화 | 정상 동작. 재정은 항상 이중 검토 필수 |
| `state.yaml` 파싱 오류 | YAML 구문 오류 | `python3 -c "import yaml; yaml.safe_load(open('state.yaml'))"` |
| 시설 예약 충돌 경고 | S5 검증 규칙 감지 | `schedule.yaml`에서 겹치는 시설 예약 확인 |

### 10.2 긴급 데이터 복원

데이터 손상 시:
1. **즉시 중단**: 시스템 사용 중지
2. **백업 확인**: `ls -la backups/` 최근 백업 확인
3. **복원**: 가장 최근 정상 백업에서 복원
4. **검증**: `python3 scripts/validate_all.py` 실행
5. **확인**: 모든 29개 규칙 PASS 확인 후 재개

---

## 11. 유전된 DNA 인식

이 시스템을 운영할 때, 부모 프레임워크(AgenticWorkflow)로부터 유전된 다음 제약을 인식해야 합니다:

| 유전된 제약 | 운영 영향 |
|----------|---------|
| **품질 절대주의** | "빠르게 대충"은 허용되지 않음 — 모든 산출물은 검증 통과 필수 |
| **단독 작성자 패턴** | 데이터 파일 직접 수동 수정 시 검증 규칙 위반 위험 |
| **재정 Autopilot 영구 비활성화** | 변경 불가 — 3중 강제(SOT + 에이전트 + 워크플로우) |
| **Context Preservation** | 세션 간 작업 맥락이 자동 보존됨 — 세션 중단 후 재개 가능 |
| **P1 결정론적 검증** | AI 판단이 아닌 코드 기반 검증 — 우회 불가 |

---

## 12. 관련 문서

| 문서 | 내용 |
|------|------|
| [`CHURCH-ADMIN-README.md`](CHURCH-ADMIN-README.md) | 시스템 개요 및 핵심 역량 |
| [`CHURCH-ADMIN-ARCHITECTURE-AND-PHILOSOPHY.md`](CHURCH-ADMIN-ARCHITECTURE-AND-PHILOSOPHY.md) | 설계 철학과 아키텍처 상세 |
| [`church-admin/docs/quick-start.md`](church-admin/docs/quick-start.md) | 최종 사용자 빠른 시작 |
| [`church-admin/docs/user-guide.md`](church-admin/docs/user-guide.md) | 최종 사용자 전체 사용법 |
| [`church-admin/docs/it-admin-guide.md`](church-admin/docs/it-admin-guide.md) | IT 관리자 가이드 (운영 관점) |
| [`church-admin/docs/troubleshooting.md`](church-admin/docs/troubleshooting.md) | 문제 해결 가이드 |
| [`church-admin/CLAUDE.md`](church-admin/CLAUDE.md) | 시스템 지시서 (에이전트 로스터, SOT 규칙) |

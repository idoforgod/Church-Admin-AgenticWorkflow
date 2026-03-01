# 새신자 파이프라인

첫 방문 등록부터 교적 정착까지 새신자의 전체 여정을 관리하며, 6단계 정착 모델을 통해 모든 새신자가 맞춤형 돌봄을 받도록 보장한다.

## 개요

- **입력**: 새 방문자 등록 (이벤트 기반: xlsx/csv 업로드, 명함 이미지, 또는 수동 입력) + 주간 후속 점검 (정기)
- **출력**: `data/newcomers.yaml`의 새신자 기록, 맞춤형 환영 메시지, 후속 관리 알림, 정착 시 `data/members.yaml`로 이관
- **주기**: 이벤트 기반 (새 등록) + 주간 (매주 월요일 후속 점검)
- **Autopilot**: 활성화 (단, 정착 단계(Journey Stage) 전환 제외 — 여정 진행 결정에는 인간 개입 루프(Human-in-the-Loop) 필요)
- **pACS**: 활성화

---

## 유전된 DNA (부모 게놈)

> 이 워크플로우는 AgenticWorkflow의 전체 게놈을 상속한다.
> 목적은 도메인에 따라 다르지만, 게놈은 동일하다. `soul.md SS0` 참조.

**헌법적 원칙** (새신자 돌봄 도메인에 맞게 적용):

1. **품질 절대주의** -- 환영 메시지는 새신자 이름, 추천 구역 모임, 다음 예배 시간으로 완전히 개인화된다. 범용 템플릿 사용 금지. 모든 정착 단계 전환은 전제 조건 마일스톤 대비 검증된다. 돌봄의 철저함이 유일한 지표이며, 파이프라인 처리 속도는 무관하다.
2. **단일 파일 SOT** -- `data/newcomers.yaml`이 모든 새신자 기록과 여정 상태의 단일 소스 오브 트루스이다. `newcomer-tracker` 에이전트가 유일한 기록자이다. 다른 어떤 에이전트나 스크립트도 이 파일에 쓰지 않는다. `state.yaml`은 워크플로우 수준의 상태(total_active, last_check_date, status)를 추적한다.
3. **코드 변경 프로토콜** -- 여정 정착 단계 전환은 `church_data_utils.py`(`STAGE_TO_REQUIRED_MILESTONES`)에 정의된 엄격한 전제 조건 규칙을 따른다. 모든 전환 전에 확인할 사항: (1) 의도 — 새신자가 어떤 단계로 이동하며 그 이유는 무엇인가, (2) 파급 효과 — 이것이 목양 배정, 구역 모임 명단, 또는 정착 적격성에 영향을 미치는가, (3) 변경 계획 — 마일스톤을 먼저 업데이트하고, 그 다음 단계, 그 다음 `_stats`, 마지막으로 검증을 실행한다.

**상속된 패턴**:

| DNA 구성 요소 | 상속 형태 |
|--------------|----------|
| 3단계 구조 | Research (접수 + 확인) -> Processing (등록 + 환영 + 전환) -> Output (정착) |
| SOT 패턴 | `data/newcomers.yaml` -- 단일 기록자 (`newcomer-tracker`). `state.yaml` -- Orchestrator만 |
| 4계층 QA | L0: newcomers.yaml에 기록 존재. L1: N2 규칙에 따른 마일스톤 순차성. L1.5: pACS 자기 평가. L2: 정착 단계 전환에 대한 인간 승인 |
| P1 할루시네이션 방지 | `validate_newcomers.py` (N1-N6) 새신자 데이터 변경 후 매번 결정론적 검증 |
| P2 전문성 기반 위임 | `data-ingestor` 파싱 담당, `newcomer-tracker` 여정 관리 담당, `member-manager` 정착 대상 담당 |
| Safety Hook | `guard_data_files.py`가 쓰기 권한 강제 -- 지정된 에이전트만 데이터 파일 수정 가능 |
| 적대적 리뷰 | 이 파이프라인에서는 없음 (콘텐츠 생성이 아닌 운영 워크플로우) |
| Decision Log | `autopilot-logs/` -- 자동 승인된 (human) 단계의 투명한 추적 |
| 컨텍스트 보존 | 여정 상태(마일스톤, 단계, 목양 배정)가 세션 간 IMMORTAL 스냅샷 섹션에 보존 |
| 코딩 기준점 (CAP) | CAP-1: 모든 정착 단계 전환 전에 모든 전제 조건 마일스톤 확인. CAP-2: 최소 레코드 필드 -- 추측성 속성 금지. CAP-3: N1-N6 전체 PASS를 진행 전 성공 기준으로 정의. CAP-4: 처리 중인 특정 새신자 레코드만 수정, 관련 없는 레코드 일괄 업데이트 금지 |

**도메인 특화 유전자 발현**:

새신자 파이프라인은 다음 DNA 구성 요소를 가장 강하게 발현한다:

- **SOT 유전자 (우성)**: 6단계 여정 모델은 절대적 데이터 일관성을 요구한다. 새신자의 `journey_stage`와 `journey_milestones`는 항상 완벽하게 일치해야 한다 (N2 규칙). 불일치는 곧 돌봄 공백을 의미한다 -- 새신자가 환영 전화를 받지 못하거나, 준비되지 않은 단계로 조기 진행될 수 있다.
- **P1 유전자 (우성)**: `validate_newcomers.py`는 `newcomers.yaml`에 대한 모든 변경 후 실행된다. N2 검사(마일스톤 전제 조건)가 가장 중요하다 -- 어떤 새신자도 돌봄 단계를 건너뛰지 못하게 하는 연산적 보장이다. 이것은 권고가 아니라 구조적 강제이다.
- **Safety 유전자 (발현)**: PII 데이터(전화번호, kakao_id)는 신중한 처리가 필요하다. 소프트 삭제 전용 정책(status: "inactive")은 목회적 돌봄 연속성을 위해 과거 기록을 보존한다.

---

## Research

### 1. 새신자 데이터 접수

- **Agent**: `@data-ingestor`
- **트리거**: 이벤트 기반 -- `inbox/newcomers/`에 파일 드롭 또는 `/register-newcomer`를 통한 수동 입력
- **전처리**: 입력을 적절한 티어 파서로 라우팅:
  - **Tier A** (xlsx/csv): `scripts/tier_a_parser.py` -- 컬럼 추출: name, gender, birth_year, phone, kakao_id, visit_route, referred_by, first_visit_date
  - **Tier C** (명함 이미지): `scripts/tier_c_parser.py` -- name, phone 및 식별 가능한 세부 정보의 멀티모달 추출
  - **수동**: `/register-newcomer` 슬래시 커맨드를 통한 직접 필드 입력
- **Verification**:
  - [ ] `inbox/staging/`에 `target_data_file: "data/newcomers.yaml"`가 포함된 스테이징 JSON 파일 존재
  - [ ] 추출된 모든 레코드에 필수 필드 포함: `name`, `gender`, `birth_year`, `contact.phone`, `first_visit` 날짜
  - [ ] 전화번호가 `010-XXXX-XXXX` 형식(한국 모바일)과 일치
  - [ ] 날짜 필드가 `YYYY-MM-DD` 형식
  - [ ] 각 레코드의 신뢰도 점수 >= 0.5 (임계값 미만 레코드는 수동 검토 대상으로 표시)
  - [ ] `data/church-glossary.yaml`을 사용한 한국어 용어 정규화 적용 (예: visit_route 용어 표준화)
  - [ ] [trace:step-1:domain-analysis] -- 새신자 돌봄 도메인 필드가 소스 형식에서 올바르게 매핑됨
- **Task**: 지원되는 모든 입력 형식의 수신 새신자 데이터를 인간 검토를 위한 구조화된 스테이징 JSON 파일로 파싱
- **Output**: `inbox/staging/{timestamp}-newcomer-intake.json`
- **후처리**: 성공 시 소스 파일을 `inbox/processed/`로, 실패 시 `inbox/errors/`로 이동
- **Translation**: none

### 2. (human) 파싱된 데이터 확인

- **Action**: Step 1에서 생성된 스테이징 JSON 검토. 각 추출 필드의 정확성 확인. OCR 오류(Tier C) 또는 컬럼 매핑 문제(Tier A) 수정. 각 레코드를 확인 또는 거부.
- **Command**: `/confirm-newcomer`
- **HitL 패턴**: 단일 리뷰 -- 접수 배치당 한 번의 확인
- **Verification**:
  - [ ] 인간이 스테이징 JSON의 각 레코드를 검토함
  - [ ] 확인된 모든 레코드가 인간 검토 후 `confidence >= 0.9` (인간이 수정하거나 확인)
  - [ ] 거부된 레코드에 거부 사유 문서화
  - [ ] `autopilot-logs/step-2-decision.md`에 Decision Log 항목 생성 (Autopilot 모드)

---

## Processing

### 3. 새신자 등록

- **Agent**: `@newcomer-tracker`
- **전처리**: Step 2의 확인된 스테이징 JSON 읽기. 현재 `data/newcomers.yaml`을 로드하여 다음 사용 가능한 ID 결정 (기존 최대 N-번호 + 1).
- **Verification**:
  - [ ] `data/newcomers.yaml`에 `N\d{3,}` 형식과 일치하는 고유 ID를 가진 새 레코드 추가 (N1)
  - [ ] `journey_stage`가 `"first_visit"`로 초기화되고 `first_visit` 마일스톤이 `completed: true`로 표시 (N2)
  - [ ] `first_visit` 날짜가 확인된 접수 날짜와 일치 (N3)
  - [ ] `assigned_to`가 `data/members.yaml`의 유효한 교인 ID를 참조 -- 부서 매칭 기반 목양자 자동 배정 (N4)
  - [ ] `status`가 `"active"`로 설정
  - [ ] `settled_as_member`와 `settled_date` 모두 `null` (N5 일관성)
  - [ ] `_stats.total_active`가 신규 등록 수만큼 증가 (N6)
  - [ ] `_stats.by_stage.first_visit`가 적절히 증가 (N6)
  - [ ] P1 검증 통과: `python3 .claude/hooks/scripts/validate_newcomers.py --data-dir data/`
- **Task**: `data/newcomers.yaml`에 초기 여정 상태를 가진 새신자 레코드를 생성하고, 매칭되는 부서에서 목양자를 자동 배정하며, 6개 마일스톤 추적 필드를 모두 초기화
- **Output**: 새 레코드가 추가된 `data/newcomers.yaml`
- **후처리**: `validate_newcomers.py --data-dir data/` 실행 후 `valid: true` 확인
- **Translation**: none

#### 목양자 자동 배정 알고리즘

`newcomer-tracker`는 다음 우선순위에 따라 목양자(`assigned_to`)를 배정한다:

1. **추천 매칭**: `referred_by`가 설정되어 있으면, 해당 교인에게 배정 (이미 관계가 있음)
2. **부서 + 봉사 영역 매칭**: `data/members.yaml`에서 `church.serving_area`에 "newcomer care" (또는 동등한 용어집 용어)가 포함되고 `church.department`가 새신자의 연령 적합 부서와 일치하는 활동 교인 탐색
3. **부서 폴백**: 새신자 돌봄 전문가가 없으면, 매칭되는 부서의 아무 활동 교인에게 배정
4. **부하 분산**: 후보자 중 현재 새신자 배정이 가장 적은 교인 우선 (status = "active"인 `data/newcomers.yaml`의 `assigned_to` 참조 수 기준)

출생년도별 부서 매핑:

| 출생년도 범위 | 부서 | 한국어 |
|-------------|------|--------|
| 2005년 이후 | Youth | 청년부 |
| 1990-2004 | Young Adult | 청년부 |
| 1960-1989 | Adult | 장년부 |
| 1960년 이전 | Senior | 장년부 |

### 4. 환영 액션 생성

- **Agent**: `@newcomer-tracker`
- **전처리**: 다음 주일예배 시간 확인을 위해 `data/schedule.yaml` 로드. 목양자 연락처 확인을 위해 `data/members.yaml` 로드. 용어 표준화를 위해 `data/church-glossary.yaml` 로드.
- **Verification**:
  - [ ] `output/newcomer-actions/{newcomer_id}-welcome.md`에 환영 메시지 파일 존재
  - [ ] 메시지가 새신자 이름으로 개인화됨 (범용 "Dear visitor" 아님)
  - [ ] 메시지에 담임목사 환영 인사 포함
  - [ ] 메시지에 `data/schedule.yaml`에서 가져온 다음 주일예배 시간 포함 (`SVC-SUN-1` 또는 `SVC-SUN-2`)
  - [ ] 메시지에 연령/지역 알고리즘 기반 구역 모임 추천 포함
  - [ ] 메시지는 텍스트 전용 Markdown -- 외부 링크 없음, 발송 기능 없음 (PRD SS2.5 준수)
  - [ ] `output/newcomer-actions/{newcomer_id}-followup-schedule.md`에 후속 관리 일정 파일 존재
  - [ ] 후속 관리 일정에 3개 체크포인트 포함: +3일(환영 전화), +14일(재방문 점검), +30일(참여 검토)
  - [ ] [trace:step-4:validation-rules] -- 생성 중 데이터 무결성을 위해 N1-N6 검증 규칙 참조됨
- **Task**: 신규 등록된 각 새신자를 위한 맞춤형 환영 메시지 및 후속 관리 알림 일정 생성
- **Output**: `output/newcomer-actions/{newcomer_id}-welcome.md` + `output/newcomer-actions/{newcomer_id}-followup-schedule.md`
- **Translation**: none (메시지는 교회를 위해 한국어로 생성)

#### 환영 메시지 템플릿 구조

```markdown
# Welcome to Morning Dew Church

Dear {newcomer_name},

We are delighted that you visited Morning Dew Church on {first_visit_date}.
{senior_pastor_welcome_greeting}

## Next Sunday Service
- 1st Service: {SVC-SUN-1.time} at {SVC-SUN-1.location}
- 2nd Service: {SVC-SUN-2.time} at {SVC-SUN-2.location}

## Your Shepherd
{assigned_member_name} ({assigned_member_role}) has been assigned as your
shepherd and will be reaching out to you soon.
Contact: {assigned_member_phone}

## Recommended Small Group
Based on your profile, we recommend: {recommended_cell_group}
Department: {assigned_department}

## Your Journey With Us
We look forward to walking alongside you in your faith journey.

---
Generated: {timestamp}
Newcomer ID: {newcomer_id}
```

#### 구역 모임 추천 알고리즘

1. **연령 그룹 매칭**: 새신자 `birth_year`를 부서에 매핑 (Step 3의 표 참조)
2. **지역 매칭**: 새신자 주소가 있으면, 동일 지역의 `data/members.yaml` 교인 기록에서 가장 가까운 `cell_group` 매칭
3. **관심사 매칭**: `visit_route`가 특정 관심사를 나타내면 (예: "청년부 초대"), 해당 부서의 구역 모임에 가중치 부여
4. **폴백**: 배정된 목양자의 구역장이 이끄는 구역 모임 추천

#### 후속 관리 알림 일정

| 체크포인트 | 첫 방문 후 경과일 | 조치 | 담당 |
|-----------|-----------------|------|------|
| 환영 전화 | +3일 | 새신자에게 전화 -- 환영 표현, 질문 응답 | 목양자 (`assigned_to`) |
| 재방문 점검 | +14일 | 새신자의 재방문 여부 확인. 미방문 시 내부 알림 생성. | `newcomer-tracker` (자동화) |
| 참여 검토 | +30일 | 여정 진행 상황 검토. 출석 중이면 구역 모임 소개 추천. | 목양자 + 목사 |

> **중요**: +14일 재방문 점검은 내부 문서(`output/newcomer-actions/{newcomer_id}-revisit-alert.md`)를 생성하며, 외부 알림은 보내지 않는다. 이것은 목양자와 목회 담당자를 위한 알림이다. PRD SS2.5에 따라, 시스템은 외부로 메시지를 발송하지 않는다.

### 5. (human) 정착 단계 전환 처리

- **Agent**: `@newcomer-tracker` (전환 제안서 준비) + 인간 (승인)
- **HitL 패턴**: 전환당 단일 리뷰 -- 각 단계 변경에 명시적 인간 승인 필요
- **전처리**: `data/newcomers.yaml`에서 현재 새신자 레코드 로드. 대상 단계의 모든 전제 조건 마일스톤 확인.
- **Verification**:
  - [ ] 대상 단계가 6단계 모델에서 유효한 다음 단계임 (건너뛰기 금지)
  - [ ] 대상 단계의 모든 전제 조건 마일스톤이 `completed: true`로 표시됨 (N2 규칙 -- 아래 전제 조건 표 참조)
  - [ ] 마일스톤 날짜가 시간순으로 정렬됨 (N3)
  - [ ] 인간이 전환을 검토하고 승인함
  - [ ] `data/newcomers.yaml`에서 `journey_stage`가 새 단계로 업데이트됨
  - [ ] `_stats.by_stage` 카운터가 올바르게 업데이트됨 (N6)
  - [ ] P1 검증 통과: `python3 .claude/hooks/scripts/validate_newcomers.py --data-dir data/`
  - [ ] `autopilot-logs/step-5-decision.md`에 Decision Log 항목 생성 (Autopilot 모드)
- **Task**: 모든 전제 조건 마일스톤이 충족되었는지 확인하고 인간 승인을 받은 후 새신자의 정착 단계 전환 처리
- **Output**: 새로운 `journey_stage` 값으로 업데이트된 `data/newcomers.yaml`
- **후처리**: `validate_newcomers.py --data-dir data/` 실행 후 `valid: true` 확인
- **Translation**: none

#### 6단계 여정 모델

```
first_visit --> attending --> small_group --> baptism_class --> baptized --> settled
```

#### 정착 단계 전환 전제 조건 표

이 표는 새신자가 각 단계로 진행하기 전에 `completed: true`여야 하는 마일스톤을 정의한다. 이 규칙은 `validate_newcomers.py`의 N2 검사로 강제되며, `church_data_utils.py`에 `STAGE_TO_REQUIRED_MILESTONES`로 정의되어 있다.

| 대상 단계 | 필수 마일스톤 (모두 완료되어야 함) |
|----------|-------------------------------|
| `first_visit` | (없음 -- 초기 단계) |
| `attending` | `first_visit` |
| `small_group` | `first_visit`, `welcome_call`, `second_visit` |
| `baptism_class` | `first_visit`, `welcome_call`, `second_visit`, `small_group_intro` |
| `baptized` | `first_visit`, `welcome_call`, `second_visit`, `small_group_intro`, `baptism_class` |
| `settled` | `first_visit`, `welcome_call`, `second_visit`, `small_group_intro`, `baptism_class`, `baptism` |

#### 전환 흐름

각 전환 제안에 대해 `newcomer-tracker` 에이전트는 다음을 수행한다:

1. **CAP-1 (행동 전 확인)**: 새신자 레코드를 읽고 모든 전제 조건 마일스톤 점검
2. **제안서 준비**: 전환 요약 생성:
   - 현재 단계와 대상 단계
   - 마일스톤 완료 상태 (모든 전제 조건 충족 여부, 누락된 것은 무엇인가)
   - 첫 방문 이후 경과일
   - 목양자 평가 (가능한 경우)
3. **인간에게 제시**: `/approve-transition`을 통해 승인을 위한 제안서 표시
4. **CAP-4 (외과적 변경)**: 승인 시 `journey_stage`, 새로 완료된 마일스톤의 `date` 및 `completed` 필드, `_stats.by_stage` 카운터만 업데이트
5. **검증**: N1-N6 검증을 실행하여 데이터 무결성 확인

### 6. 교적 정착

- **Agent**: `@newcomer-tracker` (개시) + `@member-manager` (정착 실행)
- **전처리**: 새신자가 6개 마일스톤 모두 완료한 `settled` 단계에 도달했는지 확인. 새신자 데이터로부터 교인 레코드 템플릿 준비.
- **Verification**:
  - [ ] 새신자의 `journey_stage`가 모든 마일스톤이 완료된 `"settled"` (N2)
  - [ ] `data/newcomers.yaml`에서 새신자 `status`가 `"settled"`로 업데이트됨
  - [ ] `settled_as_member` 필드에 새 교인 ID가 채워짐 (N5)
  - [ ] `settled_date` 필드에 오늘 날짜가 채워짐 (N5)
  - [ ] `@member-manager`에 의해 `data/members.yaml`에 새 교인 레코드 생성:
    - `M\d{3,}` 형식과 일치하는 고유 교인 ID (M1)
    - 새신자 레코드에서 이름, 성별, 연락처 정보 이전
    - `church.registration_date`에 정착 날짜 설정
    - 새신자의 세례 마일스톤 날짜에서 `church.baptism_date` 이전
    - 새신자의 `assigned_department`와 일치하는 `church.department`
    - `history` 항목: `{date: settlement_date, event: "transfer_in", note: "newcomer settlement (N{id} -> M{id})"}`
  - [ ] `data/members.yaml`가 P1 검증 통과: `python3 .claude/hooks/scripts/validate_members.py --data-dir data/`
  - [ ] `data/newcomers.yaml`가 P1 검증 통과: `python3 .claude/hooks/scripts/validate_newcomers.py --data-dir data/`
  - [ ] `state.yaml`의 `workflow_states.newcomer.total_active`가 1 감소
  - [ ] 양쪽 파일의 `_stats`가 재산출 및 검증됨 (N6, M7)
- **Task**: 정착한 새신자를 `data/newcomers.yaml`에서 `data/members.yaml`로 이관하여, 과거 추적을 위해 새신자 레코드를 정착 상태로 보존하면서 완전한 교인 레코드를 생성
- **Output**: 업데이트된 `data/newcomers.yaml` (status: settled) + 업데이트된 `data/members.yaml` (새 교인 레코드)
- **후처리**: `validate_newcomers.py`와 `validate_members.py` 모두 실행하여 교차 파일 일관성 확인
- **Translation**: none

#### 정착 프로토콜

정착 프로세스에는 엄격한 쓰기 경계를 가진 두 에이전트가 관여한다:

```
newcomer-tracker                          member-manager
     |                                         |
     |  1. Verify all milestones completed     |
     |  2. Prepare member record template      |
     |  3. Request settlement ----------------> |
     |                                         |  4. Create member record in members.yaml
     |                                         |  5. Run validate_members.py
     |                                         |  6. Return new member ID
     |  <-------------------------------------- |
     |  7. Update newcomer record:             |
     |     - status: "settled"                 |
     |     - settled_as_member: "{new_id}"     |
     |     - settled_date: "{today}"           |
     |  8. Run validate_newcomers.py           |
     |                                         |
```

**쓰기 경계 강제**:
- `newcomer-tracker`는 `data/newcomers.yaml`에만 기록
- `member-manager`는 `data/members.yaml`에만 기록
- 어느 에이전트도 다른 에이전트의 데이터 파일에 기록하지 않음
- 이 경계는 `guard_data_files.py` Safety Hook으로 강제됨

---

## Claude Code 구성

### 서브에이전트

```yaml
agents:
  newcomer-tracker:
    description: "Manages 6-stage newcomer journey pipeline"
    model: sonnet          # Pattern execution -- well-defined state machine
    tools: [Read, Write, Edit, Bash, Glob, Grep]
    write_permissions:
      - data/newcomers.yaml
      - output/newcomer-actions/
    permissionMode: default
    maxTurns: 20

  data-ingestor:
    description: "Parses files from inbox/ into structured staging JSON"
    model: opus            # Multimodal analysis for Tier C (namecard images)
    tools: [Read, Write, Edit, Bash, Glob, Grep]
    write_permissions:
      - inbox/staging/
      - inbox/processed/
      - inbox/errors/

  member-manager:
    description: "Manages member registry -- settlement target only in this workflow"
    model: sonnet
    tools: [Read, Write, Edit, Bash, Glob, Grep]
    write_permissions:
      - data/members.yaml
```

### SOT (상태 관리)

- **SOT 파일**:
  - `state.yaml` -- 워크플로우 수준 상태 (Orchestrator만 기록)
  - `data/newcomers.yaml` -- 새신자 기록 (`newcomer-tracker` 단일 기록자)
  - `data/members.yaml` -- 교인 기록 (`member-manager` 단일 기록자)
- **쓰기 권한**: 각 데이터 파일에는 정확히 하나의 지정된 기록 에이전트가 있음
- **에이전트 접근**: 모든 에이전트는 모든 데이터 파일을 읽을 수 있음. 쓰기는 에이전트 정의에 따라 제한.
- **품질 조정**: 기본 패턴 적용 -- 정착은 에이전트 간 요청 프로토콜을 사용하므로 교차 쓰기가 불필요

### 슬래시 커맨드

```yaml
commands:
  /register-newcomer:
    description: "Manually register a new visitor with name, phone, visit date"
    triggers: Step 1 (manual input path)

  /confirm-newcomer:
    description: "Review and confirm parsed newcomer data from staging"
    triggers: Step 2

  /approve-transition:
    description: "Review and approve a newcomer stage transition proposal"
    triggers: Step 5

  /newcomer-status:
    description: "Display current newcomer pipeline status -- active count, by-stage breakdown"
    triggers: On-demand

  /weekly-followup:
    description: "Run weekly follow-up check -- identify overdue milestones and generate alerts"
    triggers: Weekly scheduled or on-demand
```

### Hook

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "if test -f \"$CLAUDE_PROJECT_DIR/.claude/hooks/scripts/guard_data_files.py\"; then python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/scripts/guard_data_files.py\"; fi",
            "timeout": 10
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "if echo \"$TOOL_INPUT\" | grep -q 'newcomers.yaml'; then python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/scripts/validate_newcomers.py\" --data-dir \"$CLAUDE_PROJECT_DIR/data/\"; fi",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

### 런타임 디렉터리

```yaml
runtime_directories:
  output/newcomer-actions/:        # Welcome messages, follow-up schedules, revisit alerts
  inbox/newcomers/:                # Incoming newcomer data files (xlsx, csv, images)
  inbox/staging/:                  # Parsed staging JSON for human review
  inbox/processed/:                # Successfully processed source files
  inbox/errors/:                   # Failed parsing -- source files + error reports
  verification-logs/:              # step-N-verify.md (L1 verification results)
  autopilot-logs/:                 # step-N-decision.md (auto-approved decisions)
  pacs-logs/:                      # step-N-pacs.md (pACS self-rating results)
```

### 에러 처리

```yaml
error_handling:
  on_agent_failure:
    action: retry_with_feedback
    max_attempts: 3
    escalation: human

  on_validation_failure:
    action: retry_or_rollback
    retry_with_feedback: true
    rollback_after: 3
    critical_rule: "N2 (milestone prerequisite) failures ALWAYS escalate -- never auto-retry stage transitions"

  on_hook_failure:
    action: log_and_continue

  on_context_overflow:
    action: save_and_recover
    critical_state: "newcomer journey_stage and milestones must be preserved in IMMORTAL snapshot"

  on_settlement_failure:
    action: rollback_newcomer_status
    detail: "If member-manager fails to create member record, newcomer-tracker must NOT update newcomer status to 'settled'. Atomic settlement -- both files updated or neither."
```

### pACS 로그

```yaml
pacs_logging:
  log_directory: "pacs-logs/"
  log_format: "step-{N}-pacs.md"
  dimensions: [F, C, L]
  scoring: "min-score"
  triggers:
    GREEN: ">= 70 -> auto-proceed"
    YELLOW: "50-69 -> proceed with flag"
    RED: "< 50 -> rework or escalate"
  protocol: "AGENTS.md SS5.4"
  domain_calibration:
    F_weight: "critical -- newcomer data must match source exactly"
    C_weight: "high -- all milestones and fields must be populated"
    L_weight: "medium -- stage transitions must follow prerequisite logic"
```

### Autopilot 로그

```yaml
autopilot_logging:
  log_directory: "autopilot-logs/"
  log_format: "step-{N}-decision.md"
  required_fields:
    - step_number
    - checkpoint_type
    - decision
    - rationale
    - timestamp
  template: "references/autopilot-decision-template.md"
  hitl_steps: [2, 5]
  note: "Steps 2 and 5 require human confirmation even in Autopilot mode"
```

---

## 주간 후속 점검 (정기 트리거)

이벤트 기반 새신자 등록 흐름(Steps 1-6) 외에도, 이 워크플로우는 주간 후속 점검을 실행한다:

### 트리거

- **일정**: 매주 월요일 (설정 가능)
- **Command**: `/weekly-followup`
- **Agent**: `@newcomer-tracker`

### 프로세스

1. `data/newcomers.yaml`에서 모든 활동 중인 새신자 로드 (status = "active")
2. 각 활동 중인 새신자에 대해 `first_visit`로부터의 경과일 계산
3. 지연된 마일스톤에 대한 알림 생성:

| 알림 유형 | 조건 | 출력 |
|----------|------|------|
| 환영 전화 지연 | +3일 경과, `welcome_call.completed = false` | `output/newcomer-actions/{id}-alert-welcome-call.md` |
| 재방문 점검 | +14일 경과, `second_visit.completed = false` | `output/newcomer-actions/{id}-revisit-alert.md` |
| 참여 정체 | +30일 경과, 여전히 `first_visit` 또는 `attending` 단계 | `output/newcomer-actions/{id}-alert-engagement.md` |
| 장기 정체 | +90일 동일 단계 (미정착) | `output/newcomer-actions/{id}-alert-plateau.md` |

4. 주간 요약 보고서 생성: `output/newcomer-actions/weekly-summary-{date}.md`
5. 모든 알림은 목회 담당자 검토를 위한 내부 문서 -- 외부 알림 없음

### 주간 요약 보고서 구조

```markdown
# Newcomer Pipeline Weekly Summary -- {date}

## Active Newcomers: {count}

### By Stage
- first_visit: {count}
- attending: {count}
- small_group: {count}
- baptism_class: {count}
- baptized: {count}

### Overdue Alerts
{list of newcomers with overdue milestones}

### Recent Transitions
{newcomers who changed stage in the past 7 days}

### Settlement Candidates
{newcomers at baptized stage with all prerequisites for settled}
```

---

## 데이터 아키텍처 참조

### newcomers.yaml 레코드 스키마

```yaml
- id: "N001"                        # Unique ID (N\d{3,}) -- N1 validated
  name: "Name"                      # Required
  gender: "male|female"             # Required
  birth_year: 1992                  # Required (integer)
  contact:
    phone: "010-XXXX-XXXX"          # Required (Korean mobile format)
    kakao_id: "optional_id"         # Optional
  first_visit: "YYYY-MM-DD"         # Required -- N3 validated
  visit_route: "Category"           # How they found the church
  referred_by: "M001"               # Optional member ID -- N4 cross-referenced
  journey_stage: "first_visit"      # One of 6 stages -- N2 validated
  journey_milestones:                # All 6 milestone tracking fields
    first_visit:
      date: "YYYY-MM-DD"
      completed: true|false
    welcome_call:
      date: "YYYY-MM-DD"|null
      completed: true|false
      notes: "optional notes"
    second_visit:
      date: "YYYY-MM-DD"|null
      completed: true|false
    small_group_intro:
      date: "YYYY-MM-DD"|null
      completed: true|false
    baptism_class:
      date: "YYYY-MM-DD"|null
      completed: true|false
    baptism:
      date: "YYYY-MM-DD"|null
      completed: true|false
  assigned_to: "M023"               # Shepherd member ID -- N4 cross-referenced
  assigned_department: "Department"  # Age-appropriate department
  status: "active|settled|inactive"  # N5 validated with settled fields
  settled_as_member: null|"M252"    # Populated only when settled -- N5
  settled_date: null|"YYYY-MM-DD"   # Populated only when settled -- N5
```

### 교차 파일 참조

```
newcomers.yaml                    members.yaml
  assigned_to: "M023"  --------->  id: "M023" (shepherd)
  referred_by: "M001"  --------->  id: "M001" (referrer)
  settled_as_member: "M252" ---->  id: "M252" (settled member)

state.yaml
  workflow_states.newcomer:
    total_active: {matches _stats.total_active in newcomers.yaml}
    status: "idle|processing"
```

### 검증 규칙 요약 (N1-N6)

| 규칙 | 검사 내용 | 강제 시점 |
|------|----------|----------|
| N1 | ID 고유성 + `N\d{3,}` 형식 | newcomers.yaml에 대한 모든 쓰기 |
| N2 | 여정 단계 유효성 + 모든 전제 조건 마일스톤 완료 | 모든 정착 단계 전환 |
| N3 | 모든 날짜 필드 유효한 `YYYY-MM-DD` | 모든 쓰기 |
| N4 | `referred_by`와 `assigned_to`가 유효한 교인 ID 참조 | 모든 쓰기 (교차 파일) |
| N5 | 정착 일관성: `settled` 상태 <-> `settled_as_member` + `settled_date` | 모든 쓰기 |
| N6 | `_stats` 산술이 실제 레코드 수와 일치 | 모든 쓰기 |

---

## 후처리

각 파이프라인 실행 후 다음 검증 스크립트를 실행한다:

```bash
# P1 Newcomer validation (N1-N6)
python3 .claude/hooks/scripts/validate_newcomers.py --data-dir data/

# P1 Member validation (M1-M7) — when settlement occurs
python3 .claude/hooks/scripts/validate_members.py --data-dir data/

# Cross-step traceability validation (CT1-CT5)
python3 .claude/hooks/scripts/validate_traceability.py --step 9 --project-dir .
```

---

## 추적성 인덱스

이 워크플로우 전반에 사용되는 교차 단계 추적성 마커는 다음과 같다:

| 마커 | 단계 | 설명 |
|------|------|------|
| [trace:step-1:domain-analysis] | Step 1 | 소스 형식으로부터의 새신자 돌봄 도메인 필드 매핑 |
| [trace:step-4:validation-rules] | Step 4 | 환영 메시지 생성 중 참조된 N1-N6 검증 규칙 |
| [trace:step-7:seed-data] | (외부) | 검증 스크립트 개발을 위한 테스트 새신자 데이터 |
| [trace:step-8:validate-newcomers] | (외부) | N1-N6 규칙을 구현하는 `validate_newcomers.py` 스크립트 |

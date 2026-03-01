# 1단계: 종합 도메인 분석 보고서
# 교회 행정 AI 에이전트 워크플로우 자동화 시스템

**생성일**: 2026-02-28
**출처**: PRD.md, data-architecture.md, extensibility-architecture.md, feature-ideation.md, market-analysis.md, moderator-discussion.md
**목적**: 이후 모든 워크플로우 단계의 기반이 되는 도메인 지식

---

## 섹션 1: 엔티티-관계 모델

### 1.1 핵심 데이터 도메인 개요

이 시스템은 YAML 파일 형태로 저장된 6개의 핵심 데이터 도메인과 중앙 SOT(`church-state.yaml`)를 기반으로 동작한다. 모든 데이터는 코드베이스 내에 로컬 저장되며 외부 API를 사용하지 않는다. Orchestrator는 `church-state.yaml`의 유일한 쓰기 주체이며, 각 도메인 파일에는 지정된 쓰기 에이전트가 있다.

```
church-state.yaml (SOT — Orchestrator only)
    ├── data/members.yaml          (교인 명부)
    ├── data/finance.yaml          (재정 데이터)
    ├── data/schedule.yaml         (예배/행사 일정)
    ├── data/newcomers.yaml        (새신자 추적)
    ├── data/bulletin-data.yaml    (주보 소스 데이터)
    └── data/church-glossary.yaml  (교회 용어 사전)
```

### 1.2 엔티티: church-state.yaml (중앙 SOT)

| 필드 | 타입 | 제약 조건 | 설명 |
|-------|------|-------------|-------------|
| `church.name` | string | required, non-empty | 교회 이름 |
| `church.current_bulletin_issue` | integer | ≥ 1, monotonically increasing | 현재 주보 발행 번호 |
| `church.status` | enum | `active` \| `inactive` | 교회 활성 상태 |
| `church.data_paths.members` | string | valid file path | members.yaml 경로 |
| `church.data_paths.finance` | string | valid file path | finance.yaml 경로 |
| `church.data_paths.schedule` | string | valid file path | schedule.yaml 경로 |
| `church.data_paths.newcomers` | string | valid file path | newcomers.yaml 경로 |
| `church.data_paths.bulletin` | string | valid file path | bulletin-data.yaml 경로 |

**쓰기 권한**: Orchestrator 전용 (절대 기준 2 — SOT 패턴).

---

### 1.3 엔티티: members.yaml (교인 명부)

**쓰기 에이전트**: member-manager (교적 관리 에이전트)

#### 최상위 필드

| 필드 | 타입 | 제약 조건 | 설명 |
|-------|------|-------------|-------------|
| `schema_version` | string | semver 형식 (예: "1.0") | 스키마 버전 |
| `last_updated` | date | YYYY-MM-DD | 마지막 수정일 |
| `updated_by` | string | non-empty | 마지막으로 수정한 에이전트 |

#### 교인 레코드 필드

| 필드 | 타입 | 제약 조건 | 설명 |
|-------|------|-------------|-------------|
| `id` | string | unique, format `M\d{3,}`, immutable | 고유 교인 ID |
| `name` | string | required, non-empty | 본명 (한국어) |
| `gender` | enum | `male` \| `female` | 성별 |
| `birth_date` | date | YYYY-MM-DD, 과거 날짜 | 생년월일 |
| `status` | enum | `active` \| `inactive` \| `transferred` \| `deceased` | 교인 상태 |
| `contact.phone` | string | 한국 전화번호 형식 `010-XXXX-XXXX`, nullable | 휴대폰 번호 |
| `contact.email` | string | 유효한 이메일 형식, nullable | 이메일 |
| `contact.address` | string | nullable | 주소 |
| `church.registration_date` | date | YYYY-MM-DD | 교회 등록일 |
| `church.baptism_date` | date | YYYY-MM-DD, nullable | 세례일 |
| `church.baptism_type` | enum | `adult` \| `infant` \| null | 세례 유형 |
| `church.department` | string | nullable | 소속 부서 (예: 장년부, 청년부) |
| `church.cell_group` | string | nullable | 소그룹/구역 이름 |
| `church.role` | enum | `목사` \| `장로` \| `집사` \| `권사` \| `성도` \| null | 직분 |
| `church.serving_area` | list[string] | 각 항목 non-empty | 봉사 영역 목록 |
| `family.family_id` | string | format `F\d{3,}`, nullable | 가족 단위 ID |
| `family.relation` | enum | `household_head` \| `spouse` \| `child` \| `etc` | 가족 내 관계 |
| `history` | list[object] | append-only, 삭제 금지 | 이력 기록 |
| `history[].date` | date | YYYY-MM-DD | 이벤트 날짜 |
| `history[].event` | string | non-empty | 이벤트 유형 (예: `transfer_in`, `role_change`, `baptism`) |
| `history[].note` | string | nullable | 부가 설명 |

#### 산출 필드 (읽기 전용 — validate_members.py가 재계산)

| 필드 | 타입 | 제약 조건 | 설명 |
|-------|------|-------------|-------------|
| `_stats.total_active` | integer | = `status == "active"` 교인 수 | 현재 활동 교인 수 |
| `_stats.total_members` | integer | = 전체 교인 수 | 전체 등록 교인 수 |
| `_stats.last_computed` | date | YYYY-MM-DD | 마지막 집계 일시 |

**삭제 정책**: 교인 레코드는 절대 삭제하지 않는다 — 이력 보존을 위해 `status: "inactive"`를 사용한다 (glossary.yaml 패턴).

---

### 1.4 엔티티: finance.yaml (재정 데이터)

**쓰기 에이전트**: finance-recorder (재정 기록 에이전트)

#### 최상위 필드

| 필드 | 타입 | 제약 조건 | 설명 |
|-------|------|-------------|-------------|
| `schema_version` | string | semver | 스키마 버전 |
| `year` | integer | 4자리 연도 | 회계 연도 |
| `currency` | string | `KRW` | 통화 (한국 원) |

#### 헌금 기록 (Offering Record)

| 필드 | 타입 | 제약 조건 | 설명 |
|-------|------|-------------|-------------|
| `offerings[].id` | string | unique, format `OFF-YYYY-NNN` | 헌금 기록 ID |
| `offerings[].date` | date | YYYY-MM-DD | 헌금 날짜 |
| `offerings[].service` | string | non-empty | 예배 이름 (예: "주일예배 1부") |
| `offerings[].type` | enum | `regular` \| `thanks` \| `special` \| `tithe` | 헌금 유형 |
| `offerings[].items` | list[object] | ≥ 1 item | 헌금 항목별 상세 |
| `offerings[].items[].category` | string | non-empty | 헌금 카테고리 (십일조, 일반헌금, 감사헌금 등) |
| `offerings[].items[].amount` | integer | > 0 | 금액 (원) |
| `offerings[].total` | integer | = sum(items[].amount), 오차 < 1 | 합계 |
| `offerings[].recorded_by` | string | non-empty | 기록자 |
| `offerings[].verified` | boolean | required | 검증 여부 |
| `offerings[].void` | boolean | default false | 무효 처리 여부 |

#### 지출 기록 (Expense Record)

| 필드 | 타입 | 제약 조건 | 설명 |
|-------|------|-------------|-------------|
| `expenses[].id` | string | unique, format `EXP-YYYY-NNN` | 지출 기록 ID |
| `expenses[].date` | date | YYYY-MM-DD | 지출 날짜 |
| `expenses[].category` | enum | `관리비` \| `인건비` \| `사역비` \| `선교비` \| `교육비` \| `기타` | 지출 카테고리 |
| `expenses[].subcategory` | string | non-empty | 세부 항목 |
| `expenses[].amount` | integer | > 0 | 금액 (원) |
| `expenses[].description` | string | nullable | 설명 |
| `expenses[].payment_method` | string | non-empty | 결제 수단 |
| `expenses[].approved_by` | string | non-empty | 승인자 |
| `expenses[].receipt` | boolean | required | 영수증 존재 여부 |
| `expenses[].void` | boolean | default false | 무효 처리 여부 |

#### 연간 예산 (Budget)

| 필드 | 타입 | 제약 조건 | 설명 |
|-------|------|-------------|-------------|
| `budget.fiscal_year` | integer | 4자리 | 회계 연도 |
| `budget.approved_date` | date | YYYY-MM-DD | 승인일 |
| `budget.categories` | dict[string→integer] | 모든 값 > 0 | 카테고리별 예산 |
| `budget.total_budget` | integer | = sum(categories.values()) | 총 예산 |

#### 월별 결산 (Monthly Summary — 에이전트 집계)

| 필드 | 타입 | 제약 조건 | 설명 |
|-------|------|-------------|-------------|
| `monthly_summary[YYYY-MM].total_income` | integer | = 해당 월 유효 헌금 합계 | 월 수입 합계 |
| `monthly_summary[YYYY-MM].total_expense` | integer | = 해당 월 유효 지출 합계 | 월 지출 합계 |
| `monthly_summary[YYYY-MM].balance` | integer | = total_income - total_expense | 월 잔액 |
| `monthly_summary[YYYY-MM].computed_at` | date | YYYY-MM-DD | 집계 시점 |

**삭제 정책**: 항목을 절대 삭제하지 않는다 — `void: true`로 표시한다. void 항목은 monthly_summary에서 제외된다.

---

### 1.5 엔티티: schedule.yaml (예배/행사 일정)

**쓰기 에이전트**: Orchestrator (또는 지정된 일정 에이전트)

#### 정기 예배 (Regular Services)

| 필드 | 타입 | 제약 조건 | 설명 |
|-------|------|-------------|-------------|
| `regular_services[].id` | string | unique, format `SVC-*` | 정기 예배 ID |
| `regular_services[].name` | string | non-empty | 예배 이름 |
| `regular_services[].recurrence` | enum | `weekly` \| `biweekly` \| `monthly` | 반복 주기 |
| `regular_services[].day_of_week` | enum | `sunday` \| `monday` \| ... \| `saturday` | 요일 |
| `regular_services[].time` | string | HH:MM 형식 (24시간제) | 시작 시간 |
| `regular_services[].duration_minutes` | integer | > 0 | 예배 시간 (분) |
| `regular_services[].location` | string | non-empty | 장소 |
| `regular_services[].preacher_rotation` | list[string] | ≥ 1 | 설교자 순환 목록 |
| `regular_services[].worship_leader` | string | nullable | 찬양 인도자/팀 |

#### 특별 행사 (Special Events)

| 필드 | 타입 | 제약 조건 | 설명 |
|-------|------|-------------|-------------|
| `special_events[].id` | string | unique, format `EVT-YYYY-NNN` | 행사 ID |
| `special_events[].name` | string | non-empty | 행사명 |
| `special_events[].date` | date | YYYY-MM-DD | 행사 날짜 |
| `special_events[].time` | string | HH:MM 형식 | 시작 시간 |
| `special_events[].duration_minutes` | integer | > 0 | 소요 시간 |
| `special_events[].location` | string | non-empty | 장소 |
| `special_events[].preacher` | string | nullable | 설교자 |
| `special_events[].description` | string | nullable | 설명 |
| `special_events[].attendance_expected` | integer | > 0, nullable | 예상 참석 인원 |
| `special_events[].preparation` | list[string] | nullable | 준비 사항 목록 |
| `special_events[].status` | enum | `planned` \| `confirmed` \| `completed` \| `cancelled` | 상태 |

#### 시설 예약 (Facility Bookings)

| 필드 | 타입 | 제약 조건 | 설명 |
|-------|------|-------------|-------------|
| `facility_bookings[].id` | string | unique, format `FAC-YYYY-NNN` | 예약 ID |
| `facility_bookings[].facility` | string | non-empty | 시설명 |
| `facility_bookings[].date` | date | YYYY-MM-DD | 예약 날짜 |
| `facility_bookings[].time_start` | string | HH:MM | 시작 시간 |
| `facility_bookings[].time_end` | string | HH:MM, > time_start | 종료 시간 |
| `facility_bookings[].purpose` | string | non-empty | 사용 목적 |
| `facility_bookings[].booked_by` | string | non-empty | 예약자 |
| `facility_bookings[].status` | enum | `confirmed` \| `cancelled` | 상태 |

---

### 1.6 엔티티: newcomers.yaml (새신자 추적)

**쓰기 에이전트**: newcomer-tracker (새신자 추적 에이전트)

#### 새신자 레코드

| 필드 | 타입 | 제약 조건 | 설명 |
|-------|------|-------------|-------------|
| `newcomers[].id` | string | unique, format `N\d{3,}` | 새신자 ID |
| `newcomers[].name` | string | required, non-empty | 이름 |
| `newcomers[].gender` | enum | `male` \| `female` | 성별 |
| `newcomers[].birth_year` | integer | 4자리 연도 | 출생 연도 |
| `newcomers[].contact.phone` | string | 한국 전화번호 형식, nullable | 전화번호 |
| `newcomers[].contact.kakao_id` | string | nullable | 카카오톡 ID |
| `newcomers[].first_visit` | date | YYYY-MM-DD | 첫 방문일 |
| `newcomers[].visit_route` | enum | `지인 초청` \| `전도` \| `온라인 검색` \| `지역사회 행사` \| `기타` | 방문 경로 |
| `newcomers[].referred_by` | string | 교인 ID (M-형식) 또는 null | 초청한 교인 ID |
| `newcomers[].journey_stage` | enum | `first_visit` \| `attending` \| `small_group` \| `baptism_class` \| `baptized` \| `settled` | 정착 단계 |
| `newcomers[].journey_milestones` | object | 단계별 구조화된 이정표 추적 | 단계별 이정표 |
| `newcomers[].journey_milestones.{stage}.date` | date | YYYY-MM-DD, nullable | 완료 날짜 |
| `newcomers[].journey_milestones.{stage}.completed` | boolean | required | 완료 여부 |
| `newcomers[].journey_milestones.{stage}.notes` | string | nullable | 메모 |
| `newcomers[].assigned_to` | string | 교인 ID (M-형식) | 담당 목양자 ID |
| `newcomers[].assigned_department` | string | non-empty | 배정 부서 |
| `newcomers[].status` | enum | `active` \| `settled` \| `inactive` \| `transferred` | 새신자 상태 |
| `newcomers[].settled_as_member` | string | 교인 ID 또는 null | 정착 후 교인 ID |
| `newcomers[].settled_date` | date | YYYY-MM-DD, nullable | 정착 완료일 |

#### 정착 단계 전환 규칙

```
first_visit → attending → small_group → baptism_class → baptized → settled
```

- 각 단계로 이동하려면 이전 모든 이정표의 `completed: true` 가 필수
- 단계 전환에는 담당자의 인적 승인 (`(human)` 체크포인트) 이 필요
- `settled` 단계 도달 시 새신자 레코드는 `settled_as_member` 필드를 통해 `members.yaml`에 연결됨

#### 산출 필드

| 필드 | 타입 | 제약 조건 | 설명 |
|-------|------|-------------|-------------|
| `_stats.total_active` | integer | = `status == "active"` 새신자 수 | 활동 새신자 수 |
| `_stats.by_stage` | dict[string→integer] | 키 = 6개 단계 전체 | 단계별 인원 |
| `_stats.last_computed` | date | YYYY-MM-DD | 마지막 집계 일시 |

---

### 1.7 엔티티: bulletin-data.yaml (주보 소스 데이터)

**쓰기 에이전트**: bulletin-generator (주보 생성 에이전트) — 콘텐츠 담당; Orchestrator — `issue_number` 담당

#### 주보 레코드

| 필드 | 타입 | 제약 조건 | 설명 |
|-------|------|-------------|-------------|
| `bulletin.issue_number` | integer | 단조 증가 | 발행 번호 |
| `bulletin.date` | date | YYYY-MM-DD (일요일) | 주보 날짜 |
| `bulletin.church_name` | string | non-empty | 교회 이름 |
| `bulletin.sermon.title` | string | non-empty | 설교 제목 |
| `bulletin.sermon.scripture` | string | non-empty | 성경 본문 |
| `bulletin.sermon.preacher` | string | non-empty | 설교자 |
| `bulletin.sermon.series` | string | nullable | 설교 시리즈명 |
| `bulletin.sermon.series_episode` | integer | ≥ 1, nullable | 시리즈 회차 |
| `bulletin.worship_order` | list[object] | ≥ 3 items | 예배 순서 |
| `bulletin.worship_order[].order` | integer | 1부터 순차 | 순서 번호 |
| `bulletin.worship_order[].item` | string | non-empty | 순서 항목 (찬양, 기도, 봉헌, 말씀, 축도 등) |
| `bulletin.worship_order[].detail` | string | nullable | 상세 (곡명, 기도자 등) |
| `bulletin.worship_order[].performer` | string | nullable | 담당자 |
| `bulletin.announcements` | list[object] | ≥ 0 | 공지사항 목록 |
| `bulletin.announcements[].id` | string | unique, format `ANN-NNN` | 공지 ID |
| `bulletin.announcements[].category` | string | non-empty | 분류 (행사, 새신자, 선교 등) |
| `bulletin.announcements[].title` | string | non-empty | 공지 제목 |
| `bulletin.announcements[].content` | string | non-empty | 공지 내용 |
| `bulletin.announcements[].priority` | enum | `high` \| `normal` \| `low` | 우선순위 |
| `bulletin.announcements[].expires` | date | YYYY-MM-DD | 만료일 |
| `bulletin.prayer_requests` | list[object] | ≥ 1 | 기도 제목 |
| `bulletin.prayer_requests[].category` | string | non-empty | 분류 (교회, 국가, 선교, 교인) |
| `bulletin.prayer_requests[].content` | string | non-empty | 기도 내용 |
| `bulletin.offering_team` | list[string] | ≥ 1 | 헌금 봉사자 |
| `bulletin.celebrations.birthday` | list[object] | nullable | 생일 교인 |
| `bulletin.celebrations.birthday[].member_id` | string | 유효한 교인 ID | 교인 ID |
| `bulletin.celebrations.birthday[].name` | string | non-empty | 이름 (개인정보 보호: 부분 가림) |
| `bulletin.celebrations.birthday[].date` | string | MM-DD | 생일 |
| `bulletin.celebrations.wedding_anniversary` | list[object] | nullable | 결혼기념일 |
| `bulletin.celebrations.wedding_anniversary[].family_id` | string | 유효한 가족 ID | 가족 ID |
| `bulletin.celebrations.wedding_anniversary[].date` | string | MM-DD | 기념일 |
| `bulletin.next_week.sermon_title` | string | nullable | 다음 주 설교 제목 |
| `bulletin.next_week.scripture` | string | nullable | 다음 주 성경 본문 |
| `bulletin.next_week.special_events` | list[string] | nullable | 다음 주 특별 행사 |

#### 생성 이력

| 필드 | 타입 | 제약 조건 | 설명 |
|-------|------|-------------|-------------|
| `generation_history[].issue` | integer | issue_number와 일치 | 발행 번호 |
| `generation_history[].generated_at` | datetime | ISO 8601 또는 null | 생성 시각 |
| `generation_history[].generated_by` | string | nullable | 생성 에이전트 |
| `generation_history[].output_path` | string | 유효한 경로 또는 null | 산출물 경로 |

---

### 1.8 엔티티: church-glossary.yaml (교회 용어 사전)

**쓰기 에이전트**: 모든 에이전트 (Day-1 초기 시드, append-only)

| 필드 | 타입 | 제약 조건 | 설명 |
|-------|------|-------------|-------------|
| `terms[].korean` | string | unique, non-empty | 한국어 용어 |
| `terms[].english` | string | non-empty | 영어 대응어 |
| `terms[].context` | string | non-empty | 사용 맥락 설명 |

**정책**: 기존 항목은 절대 삭제하지 않는다 — 새 항목만 추가한다.

---

### 1.9 엔티티 간 의존 관계

```
members.yaml ─────────────────────────────────────────┐
  │                                                    │
  │ family.family_id ←──→ family.family_id (同家族)     │
  │                                                    │
  ├── referred_by ← newcomers.yaml (초청 교인 참조)      │
  ├── assigned_to ← newcomers.yaml (담당 목양자 참조)     │
  ├── settled_as_member ← newcomers.yaml (정착 후 링크)  │
  │                                                    │
  ├── member_id ← bulletin-data.yaml (생일 교인)        │
  ├── family_id ← bulletin-data.yaml (결혼기념일)        │
  │                                                    │
  └── approved_by ← finance.yaml (지출 승인자)           │
                                                       │
schedule.yaml ──→ bulletin-data.yaml (예배 순서 참조)    │
                                                       │
newcomers.yaml ──→ members.yaml (정착 시 이관)          │
                                                       │
church-state.yaml ──→ all data files (경로 참조)        │
                                                       │
church-glossary.yaml ──→ all agents (용어 참조)         ┘
```

**핵심 참조 무결성 규칙**:
1. `newcomers[].referred_by` → `members[].id`에 존재하거나 null이어야 함
2. `newcomers[].assigned_to` → `members[].id`에 반드시 존재해야 함
3. `newcomers[].settled_as_member` → 값이 있으면 `members[].id`에 반드시 존재해야 함
4. `bulletin-data.celebrations.birthday[].member_id` → `members[].id`에 반드시 존재해야 함
5. `bulletin-data.celebrations.wedding_anniversary[].family_id` → `members[].family.family_id`에 반드시 존재해야 함
6. 동일 `family_id`를 가진 교인은 반드시 2명 이상이어야 함
7. `finance.expenses[].approved_by` → 승인 권한이 있는 직분이어야 함

---

## 섹션 2: 한국 교회 용어 사전

최소 40개 이상의 용어를 포함하며 예배 유형, 직분, 재정 용어, 문서, 생애주기 관련 항목을 망라한다.

### 2.1 예배 유형 (Service Types)

| # | 한국어 | English | 사용 맥락 |
|---|----------------|---------|-----------------|
| 1 | 주일예배 | Sunday Worship Service | 매주 주일(일요일)에 드리는 정기 예배. 교회의 가장 중요한 예배. 보통 1부, 2부로 나뉨. |
| 2 | 수요예배 | Wednesday Service | 매주 수요일 저녁에 드리는 예배. 성경 공부 또는 기도회 성격. |
| 3 | 금요기도회 | Friday Prayer Meeting | 매주 금요일 밤에 드리는 기도 중심 예배. |
| 4 | 새벽기도회 | Early Morning Prayer | 매일 새벽(보통 5-6시)에 드리는 기도회. 한국 교회 특유의 문화. |
| 5 | 부흥회 | Revival Meeting | 특별 초청 강사를 모시고 수일간 집중적으로 드리는 특별 집회. |
| 6 | 특별예배 | Special Service | 절기(부활절, 성탄절, 추수감사절) 또는 특별 행사 시 드리는 예배. |
| 7 | 합동예배 | Combined/Joint Service | 여러 부서 또는 교회가 합동으로 드리는 예배. |
| 8 | 야외예배 | Outdoor Worship | 교회 밖에서 드리는 예배 (체육대회, 소풍 등과 연계). |

### 2.2 직분 (Church Positions)

| # | 한국어 | English | 사용 맥락 |
|---|----------------|---------|-----------------|
| 9 | 담임목사 | Senior Pastor | 교회의 최고 목회자. 당회장을 겸함. 설교, 성례, 목회 전반 책임. |
| 10 | 부목사 | Associate Pastor | 담임목사를 보좌하는 목사. 특정 부서(청년, 교육 등) 담당. |
| 11 | 전도사 | Evangelist | 목사 안수 전 목회자. 특정 부서 담당 또는 전도 사역. |
| 12 | 장로 | Elder | 교회의 영적 지도자. 당회 구성원. 장립(임직) 후 종신직. |
| 13 | 집사 | Deacon | 봉사직. 교회 운영에 실질적으로 참여하는 평신도 지도자. |
| 14 | 권사 | Deaconess | 여성 직분. 심방(가정방문)과 교인 돌봄 핵심 역할. |
| 15 | 성도 | Church Member (layperson) | 세례받은 교인으로 아직 직분이 없는 일반 교인. |
| 16 | 구역장 | Cell Group Leader | 지역별 소그룹(구역)의 리더. 구역 모임 인도 및 구역원 돌봄. |
| 17 | 목자 | Shepherd (Small Group Leader) | 목장(소그룹) 모임을 인도하는 리더. '목장' 모델을 사용하는 교회에서 사용. |

### 2.3 조직/기관 (Church Organizations & Governance)

| # | 한국어 | English | 사용 맥락 |
|---|----------------|---------|-----------------|
| 18 | 당회 | Session / Church Board | 담임목사(당회장)와 장로들로 구성된 교회 최고 의결기관. 재정, 인사, 성례 결정. |
| 19 | 제직회 | Deacons' Meeting | 목사, 장로, 집사, 권사 전체가 모이는 봉사자 회의. |
| 20 | 공동의회 | Congregational Meeting | 전체 교인이 참여하는 총회. 연간 예산, 목사 청빙 등 중요 안건 의결. |
| 21 | 노회 | Presbytery | 지역 교회들의 연합 기관. 목사 임직, 장로 인준, 교회 분쟁 조정. |
| 22 | 총회 | General Assembly | 교단의 최고 의결기관. 연 1회 소집. 교단 정책, 교세 보고. |

### 2.4 재정 용어 (Financial Terms)

| # | 한국어 | English | 사용 맥락 |
|---|----------------|---------|-----------------|
| 23 | 십일조 | Tithe | 월 수입의 10분의 1을 하나님께 드리는 헌금. 가장 보편적 정기 헌금. |
| 24 | 감사헌금 | Thanksgiving Offering | 특별한 감사 사유(생일, 회복, 합격 등)로 드리는 헌금. |
| 25 | 특별헌금 | Special Offering | 건축, 선교, 긴급 구제 등 특정 목적을 위한 헌금. |
| 26 | 주정헌금 | Sunday/Regular Offering | 매주 예배 시 드리는 일반 헌금. |
| 27 | 선교헌금 | Missions Offering | 국내외 선교사 및 선교 단체 후원을 위한 헌금. |
| 28 | 기부금영수증 | Tax Donation Receipt | 소득세법 시행령 §80①5호에 따라 교인 요청 시 의무 발행하는 영수증. |
| 29 | 사례비 | Pastoral Salary/Honorarium | 목회자에게 지급하는 급여. 당회/장로회 승인 필요. |
| 30 | 관리비 | Maintenance Fees | 교회 시설(전기, 수도, 난방 등) 관리 비용. |

### 2.5 문서/기록 (Documents & Records)

| # | 한국어 | English | 사용 맥락 |
|---|----------------|---------|-----------------|
| 31 | 주보 | Church Bulletin | 매주 주일예배에 배포하는 주간 안내지. 설교 정보, 공지, 기도 제목 포함. |
| 32 | 교적 | Church Register/Roll | 교인 명부. 세례, 입교, 이명 등 교인의 공식 기록. |
| 33 | 이명증서 | Transfer Certificate | 교인이 다른 교회로 적(교적)을 옮길 때 발행하는 공식 서류. |
| 34 | 세례증서 | Baptism Certificate | 세례 사실을 증명하는 공식 문서. 담임목사 서명 필요. |
| 35 | 당회록 | Session Minutes | 당회 회의록. 주요 결정사항 기록. |
| 36 | 공문 | Official Letter | 교회 명의로 발송하는 공식 서한. 직인(교회 도장) 필요. |

### 2.6 목회 활동/생애 주기 (Lifecycle & Pastoral Events)

| # | 한국어 | English | 사용 맥락 |
|---|----------------|---------|-----------------|
| 37 | 심방 | Pastoral Visitation | 목사, 권사가 교인의 가정을 방문하는 목회 활동. 한국 교회 핵심 사역. |
| 38 | 세례 | Baptism | 믿음을 고백하고 물로 세례를 받는 성례. 학습→세례(입교) 순서. |
| 39 | 유아세례 | Infant Baptism | 신앙인 부모가 자녀를 위해 드리는 세례. |
| 40 | 학습 | Catechism/Confirmation Class | 세례 전 필수 교육과정. 교리문답, 신앙 확인. |
| 41 | 입교 | Church Membership | 세례 후 교회의 정식 교인으로 등록되는 절차. |
| 42 | 이명 | Transfer (of membership) | 교인이 다른 교회로 교적을 옮기는 것. 이명증서 발행. |
| 43 | 임직 | Ordination | 장로, 집사, 권사 등 직분을 받는 의식. 고시(시험)와 서약 포함. |
| 44 | 고시 | Examination (for ordination) | 임직 전 신앙 고백과 교리 지식을 확인하는 시험/면접. |
| 45 | 소천 | Passing Away (euphemism) | 교인 사망의 교회 내 완곡 표현. "하나님 곁으로 돌아감." |
| 46 | 구역모임 | Cell/Zone Meeting | 거주 지역별 소그룹 정기 모임. 성경 공부, 교제, 기도. |
| 47 | 절기 | Liturgical Season | 교회력에 따른 특별 시기 (대강절, 사순절, 부활절, 성탄절, 추수감사절). |
| 48 | 봉헌 | Offertory | 예배 중 헌금을 드리는 순서. |
| 49 | 축도 | Benediction | 예배 마지막에 목사가 선포하는 축복 기도. |
| 50 | 대표기도 | Representative Prayer | 예배 중 회중을 대표하여 드리는 기도. 지명된 교인이 수행. |

---

## 섹션 3: 사용자 페르소나 → 기능 매핑

### 3.1 행정 간사 (Administrative Secretary) — 김미영, 42세

**프로필**: 중형 교회(250명 교인), 유일한 전임 행정 직원. HWP/Excel 능숙, CLI 경험 없음.

| 기능 | 빈도 | 우선순위 | 상호작용 방식 |
|---------|-----------|----------|-----------------|
| 주보 자동 생성 (F-01) | 매주 | **Critical** | 설교 정보 제공, 산출물 검토 |
| 새신자 등록 (F-02) | 월 2-5회 | **Critical** | 새신자 카드 입력, 환영 메시지 검토 |
| 월별 재정 보고서 (US-03) | 매월 | **High** | 헌금 Excel 업로드, 보고서 검토 |
| 문서 템플릿 스캔 (F-06) | 최초 설정 + 비정기 | **High** | 기존 양식 스캔, 템플릿 확인 |
| inbox/ 파일 업로드 (F-05) | 매주 | **Critical** | Excel/Word/이미지 파일 드롭 |
| 기부금 영수증 (T1-03) | 연 1회 (연말 일괄) | **High** | 생성된 영수증 검토 및 확인 |
| 공문 초안 작성 (T1-05) | 월 2-5회 | **Medium** | 문서 유형 선택, 초안 검토 |
| 출석 관리 | 매주 | **Medium** | 출석 데이터 입력 |
| 일정 관리 | 매주 | **Medium** | 행사 캘린더 업데이트 |

**핵심 불편사항**: 주보 작성에 주 3시간, 재정 보고서에 월 6시간, 새신자 Excel 수동 추적.
**성공 지표**: 행정 업무 시간을 주 23시간에서 5시간 미만으로 단축.

### 3.2 담임 목사 (Senior Pastor) — 이성훈, 55세

**프로필**: 행정 업무를 겸하는 중형 교회 담임목사. 스마트폰 기본 사용 가능, Excel 미숙, AI에 관심 있으나 직접 사용 경험 없음.

| 기능 | 빈도 | 우선순위 | 상호작용 방식 |
|---------|-----------|----------|-----------------|
| 주보 승인 | 매주 | **Critical** | 최종 주보 검토 및 승인 |
| 새신자 돌봄 파이프라인 감독 (F-02) | 매주 | **Critical** | 단계 전환 승인, 돌봄 조치 검토 |
| 재정 보고서 검토 (US-03) | 매월 | **Critical** | 재정 담당 집사와 함께 이중 검토 |
| 장기 결석 교인 알림 (T1-07) | 매주 | **High** | 결석 목록 검토, 심방 여부 결정 |
| 심방 일정 수립 (T2-11) | 매주 | **High** | 심방 일정 승인 |
| 설교 준비 보조 (T2-05) | 매주 | **Medium** | 주제 제공, 리서치 결과 검토 |
| 교단 보고서 승인 (T2-03) | 연 1회 | **Medium** | 보고서 검토 및 서명 |
| 임직 절차 감독 (T2-08) | 연 1회 | **Low** | 후보자 진행 과정 승인 |

**핵심 불편사항**: "행정 업무가 설교 준비와 목양 시간을 빼앗는다."
**성공 지표**: 행정 업무 주 5시간 이내, 설교 준비 및 심방 주 15시간 이상.
**의사결정 권한**: 시스템 도입에 대한 최종 결정권자.

### 3.3 IT 자원봉사자 (IT Volunteer) — 박준호, 29세

**프로필**: 청년부 IT 자원봉사자. 개발자 또는 IT 전공, CLI 능숙, Git 기본 이해. 주말 봉사.

| 기능 | 빈도 | 우선순위 | 상호작용 방식 |
|---------|-----------|----------|-----------------|
| 시스템 설치 및 설정 | 최초 1회 | **Critical** | 설치 스크립트 실행, 설정 구성 |
| 템플릿 스캔 설정 (F-06) | 최초 1회 | **High** | 초기 템플릿 스캔 보조 |
| 트러블슈팅 및 유지보수 | 비정기 (월 1회) | **High** | 오류 진단, 문서 참조 |
| workflow-generator를 통한 워크플로우 추가 | 비정기 | **Medium** | 자연어로 새 워크플로우 생성 |
| 데이터 백업 검증 | 매월 | **Medium** | 백업 스크립트 정상 작동 확인 |
| 신규 기능을 위한 스키마 확장 | 비정기 | **Low** | 공유 YAML에 선택 필드 추가 |

**핵심 불편사항**: "설치는 간단해야 한다. 유지보수는 거의 없어야 한다."
**성공 지표**: 설치 30분 이내, 유지보수 월 1시간 미만.

### 3.4 재정 담당 집사 (Finance Deacon)

**프로필**: 교회 재정위원회 위원. 재정 투명성과 정확성에 높은 관심.

| 기능 | 빈도 | 우선순위 | 상호작용 방식 |
|---------|-----------|----------|-----------------|
| inbox/를 통한 헌금 데이터 입력 (F-05) | 매주 | **Critical** | 헌금 Excel을 inbox/에 드롭 |
| 월별 재정 보고서 검토 (US-03) | 매월 | **Critical** | 자동 생성 보고서 검토, 산술 이중 확인 |
| 예산 대비 실적 추적 | 매월 | **High** | 예산 비교 섹션 검토 |
| 기부금 영수증 생성 (T1-03) | 연 1회 | **Critical** | 전체 영수증 검토 및 금액 확인 |
| 지출 승인 | 비정기 | **High** | 검토 요청된 지출 승인 |
| 이상 감지 알림 (T2-09) | 매월 | **Medium** | 이상 징후 검토 |

**핵심 불편사항**: 수작업 헌금 집계 오류, 연말 영수증 생성에 과도한 시간 소요.
**성공 지표**: 재정 보고서 산술 오류 제로, 영수증 생성 시간을 2일에서 2시간으로 단축.

---

## 섹션 4: 인간 개입 루프(Human-in-the-Loop) 아키텍처

### 4.1 위험도 분류 매트릭스

| 위험 수준 | 작업 | 검토 방식 | Autopilot 가능 여부 | 근거 |
|------------|-----------|-------------|---------------------|-----------|
| **HIGH** | 재정 기록 | 이중 검토 (재정 담당 집사 + 담임목사) | **불가** | 법적 책임 (세법 §80①5호), 오류 시 신뢰 붕괴 |
| **HIGH** | 기부금 영수증 | 이중 검토 (재정 담당 집사 + 담임목사) | **불가** | 세금 효력을 가진 법적 문서 |
| **HIGH** | 교단 보고서 | 이중 검토 (행정 간사 + 담임목사) | **불가** | 교단 본부에 제출되는 공식 문서 |
| **HIGH** | 교인 상태 변경 (이명, 소천) | 이중 검토 (행정 직원 + 목사) | **불가** | 교적에 남는 영구적·불가역적 변경 |
| **HIGH** | 새신자 → 교인 이관 | 이중 검토 (새신자 담당자 + 목사) | **불가** | 영구적인 교인 신분 변경 |
| **MEDIUM** | 주보 내용 | 단일 검토 (행정 간사 또는 목사) | 저위험 부분만 | 회중에 공개되는 문서, 오류가 바로 노출됨 |
| **MEDIUM** | 새신자 단계 전환 | 단일 검토 (담당 돌봄자) | **불가** | 관계적 단계에 목회적 판단 필요 |
| **MEDIUM** | 공식 문서 (이명증서, 세례증서) | 단일 검토 (행정 간사) | **불가** | 직인/서명 필요 |
| **MEDIUM** | 봉사자 배정 | 단일 검토 (부서장) | **불가** | 사람 관련 일정이라 민감 |
| **MEDIUM** | 행사/일정 변경 | 단일 검토 (행정 간사) | **불가** | 시설 충돌 가능성 |
| **LOW** | 생일/기념일 조회 | 자동 승인 | **가능** | members.yaml에서 읽기 전용 쿼리 |
| **LOW** | 출석 통계 | 자동 승인 | **가능** | 읽기 전용 집계 |
| **LOW** | 용어 사전 항목 추가 | 자동 승인 | **가능** | append-only, 비파괴적 |
| **LOW** | 주보 초안 생성 (검토 전) | 자동 승인 (초안 단계만) | **가능** | 초안 단계에 한함, 최종 확정 전 검토 게이트 존재 |
| **LOW** | 기도 제목 분류 | 자동 승인 (분류만) | **가능** | 자동 분류, 목록은 사람이 검토 |

### 4.2 승인 흐름 다이어그램

**고위험 (재정 예시)**:
```
[AI 에이전트가 보고서 생성]
    → [재정 담당 집사가 산술 + 항목 검토]
        → 승인 → [담임목사가 합계 + 서술 검토]
            → 승인 → [보고서 최종 확정 + 보관]
            → 반려 → [피드백과 함께 AI에 재요청]
        → 반려 → [수정 사항과 함께 AI에 재요청]
```

**중위험 (주보 예시)**:
```
[AI 에이전트가 주보 초안 생성]
    → [행정 간사가 내용 + 레이아웃 검토]
        → 승인 → [주보 최종 확정]
        → 반려 → [AI가 피드백 반영하여 재생성]
```

**저위험 (조회 예시)**:
```
[사용자가 "이번 주 생일 교인 목록" 요청]
    → [AI가 members.yaml 조회]
        → [결과 즉시 반환 — 승인 불필요]
```

### 4.3 Autopilot 범위 정의

| Autopilot 허용 | Autopilot 금지 |
|-------------------|---------------------|
| 주보 초안 생성 | 모든 재정 기록 |
| 기도 제목 분류 | 기부금 영수증 생성 |
| 생일/기념일 추출 | 교인 상태 변경 |
| 출석 데이터 집계 | 새신자 단계 전환 |
| 용어 사전 조회 | 공식 문서 최종 확정 |
| 일정 조회 | 지출 승인 |
| 뉴스레터 콘텐츠 초안 | 교단 보고서 제출 |

**원칙**: 재정 관련 작업은 Autopilot에서 **영구적으로 제외**된다 (PRD §5.1 F-03).

---

## 섹션 5: 검증 규칙 카탈로그

### 5.1 교인 검증 규칙 (M1-M6)

| 규칙 | 검사 조건 | 심각도 | 구현 방법 |
|------|----------------|----------|----------------|
| **M1** | 모든 교인 레코드의 `id` 값이 고유 | FAIL | `len(ids) == len(set(ids))` |
| **M2** | `status`가 다음 중 하나: `active`, `inactive`, `transferred`, `deceased` | FAIL | `status in VALID_STATUSES` |
| **M3** | `birth_date`, `registration_date`, `baptism_date`가 YYYY-MM-DD 형식이고, 과거 날짜의 유효한 달력 날짜 | FAIL | `datetime.strptime(date, "%Y-%m-%d") <= today` |
| **M4** | null이 아닌 모든 `family_id`에 동일한 `family_id`를 가진 교인이 2명 이상 | WARNING | 각 non-null family_id에 대해 `count(family_id) >= 2` |
| **M5** | `role`이 다음 중 하나: `목사`, `장로`, `집사`, `권사`, `성도`, 또는 null | FAIL | `role in VALID_ROLES or role is None` |
| **M6** | `_stats.total_active`가 `status == "active"` 교인의 실제 수와 일치 | FAIL | `computed_count == _stats.total_active` |

### 5.2 재정 검증 규칙 (F1-F5)

| 규칙 | 검사 조건 | 심각도 | 구현 방법 |
|------|----------------|----------|----------------|
| **F1** | 각 헌금 항목: `total == sum(items[].amount)`, 오차 < 1원 | FAIL | `abs(total - sum(amounts)) < 1` |
| **F2** | `monthly_summary`의 각 월: `total_income == 유효 헌금 합계`, `total_expense == 유효 지출 합계`, `balance == total_income - total_expense` | FAIL | 해당 월의 전체 항목에 대한 산술 교차 검증 |
| **F3** | `void: true`인 항목은 모든 `monthly_summary` 계산에서 제외 | FAIL | 집계 전 `void != true` 필터 적용 |
| **F4** | 모든 `amount` 값이 양의 정수 (> 0) | FAIL | `isinstance(amount, int) and amount > 0` |
| **F5** | 시리즈 내 모든 `id` 값이 고유 (`OFF-*` 고유, `EXP-*` 고유) | FAIL | `len(off_ids) == len(set(off_ids))` |

### 5.3 일정 검증 규칙 (S1-S5)

| 규칙 | 검사 조건 | 심각도 | 구현 방법 |
|------|----------------|----------|----------------|
| **S1** | 모든 `date` 필드가 YYYY-MM-DD 형식이고 유효한 달력 날짜 | FAIL | `datetime.strptime(date, "%Y-%m-%d")` |
| **S2** | 모든 `time`, `time_start`, `time_end` 필드가 HH:MM 24시간제 형식 | FAIL | `re.match(r"^([01]\d|2[0-3]):[0-5]\d$", time)` |
| **S3** | 동일 날짜의 동일 `location`에서 시간대가 겹치는 예약/행사 없음 | WARNING | 시간 구간 중복 감지 |
| **S4** | `status`가 다음 중 하나: `planned`, `confirmed`, `completed`, `cancelled` | FAIL | `status in VALID_STATUSES` |
| **S5** | 모든 일정 레코드의 `id` 값이 전체적으로 고유 (SVC-*, EVT-*, FAC-*) | FAIL | 전역 ID 고유성 검사 |

### 5.4 새신자 검증 규칙 (N1-N5)

| 규칙 | 검사 조건 | 심각도 | 구현 방법 |
|------|----------------|----------|----------------|
| **N1** | 모든 새신자 레코드의 `id` 값이 고유 | FAIL | `len(ids) == len(set(ids))` |
| **N2** | `journey_stage`가 6개 유효 단계 중 하나이고, 이전 모든 이정표가 `completed: true` | FAIL | 이정표 교차 검사를 포함한 순서 기반 단계 검증 |
| **N3** | `first_visit`이 YYYY-MM-DD 형식이고, 유효한 과거 날짜 | FAIL | `datetime.strptime(date, "%Y-%m-%d") <= today` |
| **N4** | `referred_by`가 null이 아니면 참조된 ID가 `members.yaml`에 존재 | WARNING | 파일 간 ID 조회 |
| **N5** | `settled_as_member`가 null이 아니면 `status`가 반드시 `"settled"`이고 `settled_date`가 non-null | FAIL | 조건부 필드 일관성 검사 |

### 5.5 주보 검증 규칙 (B1-B3)

| 규칙 | 검사 조건 | 심각도 | 구현 방법 |
|------|----------------|----------|----------------|
| **B1** | 주보에 필수 섹션 전부 포함: `sermon`, `worship_order` (≥3 항목), `announcements`, `prayer_requests` | FAIL | 섹션 존재 + 최소 항목 수 검사 |
| **B2** | `issue_number`가 `generation_history`의 마지막 항목보다 엄격히 큼 | FAIL | 단조 증가 검사 |
| **B3** | `celebrations.birthday`의 모든 `member_id` 참조가 `members.yaml`에 존재; `celebrations.wedding_anniversary`의 모든 `family_id` 참조가 `members.yaml`에 존재 | WARNING | 파일 간 참조 무결성 |

---

## 섹션 6: M1/M2 마일스톤 범위

### 6.1 M1 (1-2개월차): MVP 핵심 — "주보 + 새신자 + inbox/"

| 기능 | 설명 | 출처 | 상태 |
|---------|-------------|--------|--------|
| **주보 자동 생성** (F-01) | 완전한 주보 파이프라인: bulletin-data.yaml + schedule.yaml + members.yaml → Markdown | GREEN Zone (4/4 합의) | **M1 핵심** |
| **새신자 환영 파이프라인** (F-02) | 6단계 정착 추적 기본 구현, 환영 메시지 초안, 담당 변경 알림 | GREEN Zone (4/4 합의) | **M1 핵심** |
| **inbox/ Tier A: Excel/CSV** (F-05) | 파일 드롭 → openpyxl/pandas 파싱 → 인간 확인 후 YAML 반영 | GREEN Zone | **M1 핵심** |
| **inbox/ Tier C: 이미지** (F-05) | 영수증/명함 사진 → Claude 멀티모달 추출 → 인간 확인 후 YAML 반영 | GREEN Zone | **M1 핵심** |
| **스캔-앤-복제: 주보** (F-06) | 기존 주보 스캔 → 레이아웃 추출 → bulletin-template.yaml 생성 | GREEN Zone | **M1 핵심** |
| **교회 용어 사전 v1** (F-04) | Day-1 한국 교회 용어 사전 (≥50개 용어) | GREEN Zone (Tech MUST HAVE) | **M1 핵심** |
| **인간 개입 루프 게이트** (F-03) | 모든 워크플로우 산출물에 검토/승인 게이트 | GREEN Zone (4/4 합의) | **M1 핵심** |
| **IT 자원봉사자 온보딩 패키지** | 설치 스크립트 + "교회 IT 가이드" 문서 | YELLOW Zone (조건부 필수) | **M1 핵심** |
| **검증 스크립트: 교인, 새신자, 일정** | validate_members.py (M1-M6), validate_newcomers.py (N1-N5), validate_schedule.py (S1-S5) | 기술 인프라 | **M1 핵심** |
| **5개 시범 교회 온보딩** | 중형 교회 5곳과의 실제 환경 검증 | 검증 실험 | **M1 핵심** |

### 6.2 M2 (3-4개월차): MVP 확장 — "재정 + 보고서 + 문서"

| 기능 | 설명 | 출처 | 상태 |
|---------|-------------|--------|--------|
| **헌금 집계 + 월별 재정 보고서** (US-03) | 항목별 헌금 집계, 지출 추적, 예산 대비 실적 | YELLOW Zone (inbox/ 파이프라인 선행 필요) | **M2** |
| **기부금 영수증 생성** (T1-03) | 연간 교인별 헌금 합산 → 국세청 양식 형식 | Tier 1 기능, 법적 요건 | **M2** |
| **공문 초안 작성** (T1-05) | 이명증서, 세례증서, 당회 결의문 | Tier 1 기능 | **M2** |
| **예배/행사 일정 자동화** | 캘린더 기반 일정 관리 | YELLOW Zone | **M2** |
| **스캔-앤-복제 확장** | 공문, 증명서, 예배 순서지 | F-06 확장 | **M2** |
| **교단 보고서 템플릿** (1개 교단) | PCKG (예장통합) 보고서 형식 내장 | YELLOW Zone (교단 협력 필요) | **M2** |
| **재정 검증 스크립트** | validate_finance.py (F1-F5) | 기술 인프라 | **M2** |
| **시범 교회 피드백 v2.0** | M1 파일럿 피드백 기반 반복 개선 | 지속 개선 | **M2** |
| **소형 교회 무료 티어 설계** | 기능 서브셋 설계 (주보 + 새신자만) | YELLOW Zone | **M2 설계만** |

### 6.3 명시적 범위 경계

| M1/M2 포함 | Phase 2+ 제외 |
|--------------------|------------------------|
| 주보 자동 생성 | 카카오톡 채널 연동 |
| 새신자 6단계 파이프라인 | 봉사자 배정 최적화 |
| inbox/ 파일 파싱 (Tier A + C) | 완전한 재정 관리 모듈 |
| 스캔-앤-복제 (7개 문서 유형) | 소그룹 관리 자동화 |
| 월별 재정 보고서 (기본) | 교인 DB 직접 연동 |
| 기부금 영수증 (연간 일괄) | SMS/카카오 직접 발송 |
| 공문 초안 작성 | 단일 통합 워크플로우 (영구 제외) |
| 교회 용어 사전 | 이탈 예측 알고리즘 |
| 인간 개입 루프 아키텍처 | 예산 시나리오 시뮬레이션 |
| 검증 스크립트 3개 (M1) + 1개 (M2) | 코호트 분석 |

---

## 섹션 7: inbox/ 3-Tier 파이프라인

### 7.1 아키텍처 개요

```
inbox/
├── documents/              ← Tier A: Structured Files
│   ├── 헌금내역.xlsx          → finance.yaml
│   ├── 새신자등록카드.xlsx     → newcomers.yaml
│   ├── 심방일지.docx          → members.yaml (history)
│   └── 교인명부.csv           → members.yaml
│
├── images/                 ← Tier C: Image Files
│   ├── receipt-001.jpg        → finance.yaml (expense)
│   ├── namecard-kim.jpg       → newcomers.yaml
│   └── bulletin-text.jpg      → bulletin-data.yaml
│
└── templates/              ← Scan-and-Replicate Templates
    ├── bulletin-sample.jpg    → bulletin-template.yaml
    ├── receipt-form.jpg       → receipt-template.yaml
    └── ... (7 document types)
```

### 7.2 Tier A: 구조화 파일 (Excel/CSV)

| 항목 | 내용 |
|--------|--------|
| **입력 형식** | `.xlsx`, `.csv` |
| **처리 방법** | `openpyxl` (Excel), `pandas` (CSV) — 결정론적 파싱 |
| **정확도** | **높음** (95%+) — 헤더가 있는 구조화 데이터 |
| **오류 처리** | 컬럼 매핑 검증, 타입 검사, 누락값 감지 |
| **인간 검토** | 파싱 결과를 사용자에게 보여준 후 확인 받아 YAML 갱신 |
| **실패 처리** | 원본 파일 보존 + 상세 오류 메시지 |
| **입력 예시** | 헌금내역.xlsx (날짜, 이름, 십일조, 감사헌금, 일반헌금 컬럼 포함) |
| **출력 예시** | finance.yaml의 구조화된 헌금 항목 |

### 7.3 Tier B: 문서 파일 (Word/PDF)

| 항목 | 내용 |
|--------|--------|
| **입력 형식** | `.docx`, `.pdf` |
| **처리 방법** | `python-docx` (Word), Claude Read tool (PDF) |
| **정확도** | **중-높음** (85-90%) — 반구조화 문서 |
| **오류 처리** | 섹션 경계 감지, 신뢰도 포함 키-값 추출 |
| **인간 검토** | 추출된 필드를 신뢰도 지표와 함께 표시 후 확인 |
| **실패 처리** | 원본 보존 + 추출된 원문 텍스트 표시 |
| **HWP 안내** | HWP(한글)는 바이너리 형식 — "PDF로 내보내기" 안내 |
| **입력 예시** | 방문 기록이 포함된 심방일지.docx |
| **출력 예시** | members.yaml의 history 항목에 추가 |

### 7.4 Tier C: 이미지 파일 (JPG/PNG)

| 항목 | 내용 |
|--------|--------|
| **입력 형식** | `.jpg`, `.jpeg`, `.png` |
| **처리 방법** | Claude 멀티모달 이미지 분석 (내장, 외부 OCR 불필요) |
| **정확도** | **중간** (75-85%) — 확인 필수 |
| **오류 처리** | 낮은 신뢰도 필드는 `[?]` 표시, 원본 이미지 보존 |
| **인간 검토** | **필수** — YAML 갱신 전 추출된 모든 데이터 확인 |
| **실패 처리** | 부분 추출 결과 + 원본 이미지 경로 표시 |
| **입력 예시: 영수증** | receipt-001.jpg → 추출: 금액, 날짜, 항목, 가맹점 |
| **입력 예시: 명함** | namecard-kim.jpg → 추출: 이름, 전화번호, 직장 |
| **출력 예시** | finance.yaml의 지출 항목 또는 newcomers.yaml의 새신자 항목 |

### 7.5 Tier 공통 원칙

1. **인간 개입 루프 필수**: 모든 Tier에서 YAML 반영 전 사용자 확인 필요
2. **원본 보존**: 입력 파일은 절대 삭제하거나 수정하지 않으며, 확인 후 `inbox/processed/`로 이동
3. **오류 투명성**: 파싱 실패 시 조용히 실패하지 않고 상세 오류 메시지 생성
4. **멱등성**: 동일 파일 재처리 시 중복 항목 생성 금지 (ID 기반 중복 제거)
5. **church-glossary.yaml 통합**: 입력 파일의 한국 교회 용어는 용어 사전 조회로 인식

---

## 섹션 8: 스캔-앤-복제(Scan-and-Replicate) 카탈로그

### 8.1 개요

스캔-앤-복제 기능을 통해 교회는 기존 문서 양식(이미지 또는 PDF)을 업로드하여, 시스템이 레이아웃 구조를 추출하고 고정 영역과 가변 영역을 식별한 뒤 문서 자동 생성에 재사용 가능한 템플릿을 생성할 수 있다.

### 8.2 문서 유형 카탈로그 (7가지 유형)

#### 유형 1: 주보 (Church Bulletin)

| 항목 | 내용 |
|--------|--------|
| **반복 빈도** | 매주 |
| **우선순위 등급** | Tier A (즉시) |
| **템플릿 파일** | `bulletin-template.yaml` |
| **데이터 소스** | `bulletin-data.yaml` + `schedule.yaml` + `members.yaml` |
| **고정 영역** | 교회 이름, 로고 위치, 섹션 헤더 ("예배순서", "광고", "기도제목"), 페이지 레이아웃 |
| **가변 영역** | 설교 제목, 성경 본문, 예배 순서 항목, 공지 내용, 기도 제목, 생일자 이름, 날짜 |
| **출력 형식** | `bulletins/YYYY-MM-DD-bulletin.md` |

#### 유형 2: 기부금 영수증 (Tax Donation Receipt)

| 항목 | 내용 |
|--------|--------|
| **반복 빈도** | 연 1회 (연말 일괄 생성) |
| **우선순위 등급** | Tier A (즉시) |
| **템플릿 파일** | `receipt-template.yaml` |
| **데이터 소스** | `finance.yaml` + `members.yaml` |
| **고정 영역** | 국세청 양식 헤더, 교회 사업자등록번호, 법적 고지 문구, 양식 구조 (국세청 양식) |
| **가변 영역** | 기부자 성명, 주민등록번호, 항목별 기부 금액, 기부 기간, 발행일 |
| **출력 형식** | `certificates/YYYY-receipt-{member_id}.md` |

#### 유형 3: 예배 순서지 (Worship Order Sheet)

| 항목 | 내용 |
|--------|--------|
| **반복 빈도** | 매주 |
| **우선순위 등급** | Tier A (즉시) |
| **템플릿 파일** | `worship-template.yaml` |
| **데이터 소스** | `schedule.yaml` + `bulletin-data.yaml` |
| **고정 영역** | 교회 브랜딩, 섹션 레이아웃 (찬양, 기도, 봉헌, 말씀, 축도), 서식 스타일 |
| **가변 영역** | 찬양 제목, 기도자 이름, 설교 제목/본문, 순서별 상세 항목, 담당자 이름 |
| **출력 형식** | `bulletins/YYYY-MM-DD-worship-order.md` |

#### 유형 4: 교회 공문 (Official Church Letter)

| 항목 | 내용 |
|--------|--------|
| **반복 빈도** | 월 2-5회 |
| **우선순위 등급** | Tier B |
| **템플릿 파일** | `letter-template.yaml` |
| **데이터 소스** | `members.yaml` + `schedule.yaml` |
| **고정 영역** | 교회 레터헤드, 직인 위치, 서명란, 교회 주소, 인사말 형식 |
| **가변 영역** | 수신자 이름/기관, 날짜, 제목, 본문 내용, 참조 번호 |
| **출력 형식** | `certificates/YYYY-MM-DD-letter-{subject}.md` |

#### 유형 5: 회의록 (Meeting Minutes)

| 항목 | 내용 |
|--------|--------|
| **반복 빈도** | 월 1-4회 |
| **우선순위 등급** | Tier B |
| **템플릿 파일** | `minutes-template.yaml` |
| **데이터 소스** | `members.yaml` (참석자) |
| **고정 영역** | 회의명 형식, 참석자 섹션 헤더, 안건 번호 형식, 결의 형식, 서명 섹션 |
| **가변 영역** | 날짜, 참석자 이름, 안건 항목, 토의 내용, 결의 사항, 차기 회의일 |
| **출력 형식** | `reports/YYYY-MM-DD-minutes-{meeting_type}.md` |

#### 유형 6: 세례/입교 증명서 (Baptism/Membership Certificate)

| 항목 | 내용 |
|--------|--------|
| **반복 빈도** | 연 2-4회 |
| **우선순위 등급** | Tier B |
| **템플릿 파일** | `certificate-template.yaml` |
| **데이터 소스** | `members.yaml` (성례 이력) |
| **고정 영역** | 증명서 테두리/프레임 디자인, 교회 직인 위치, 목사 서명란, 증명서 제목, 성경 구절 장식 |
| **가변 영역** | 수령인 이름, 세례일, 세례 유형 (성인/유아), 증명서 번호, 집례 목사 이름, 발행일 |
| **출력 형식** | `certificates/YYYY-{type}-{member_id}.md` |

#### 유형 7: 행사 초청장 (Event Invitation)

| 항목 | 내용 |
|--------|--------|
| **반복 빈도** | 비정기 (계절 행사) |
| **우선순위 등급** | Tier B |
| **템플릿 파일** | `invitation-template.yaml` |
| **데이터 소스** | `schedule.yaml` (행사 상세) |
| **고정 영역** | 교회 브랜딩, 초청 문구 스타일, RSVP 섹션 형식, 약도/교통 섹션 |
| **가변 영역** | 행사명, 날짜/시간, 장소, 프로그램 개요, 특별 게스트, RSVP 마감일 |
| **출력 형식** | `reports/YYYY-MM-DD-invitation-{event}.md` |

### 8.3 스캔-앤-복제 처리 파이프라인

```
Step 1: Upload to inbox/templates/{category}-sample.{jpg|pdf}
    ↓
Step 2: Claude Multimodal Analysis
    ├── Extract layout structure (sections, columns, style hints)
    ├── Identify FIXED areas (church name, logo, headers, legal text)
    └── Identify VARIABLE areas (dates, names, content, amounts)
    ↓
Step 3: Generate {category}-template.yaml
    ├── fixed_elements: list of immutable content with positions
    ├── variable_slots: list of data-bound placeholders with types
    └── layout_hints: section order, alignment, spacing
    ↓
Step 4: Human Confirmation (mandatory first-time)
    ├── "Is this structure correct?"
    └── "Are all variable slots identified correctly?"
    ↓
Step 5: Repeated Auto-Generation
    └── data/*.yaml → template slots → output/{category}/{date}-{name}.md
```

---

## 섹션 9: 완성된 domain-knowledge.yaml

`domain-knowledge.yaml` 파일은 별도 산출물로 생성된다. `planning/domain-knowledge.yaml` 참조.

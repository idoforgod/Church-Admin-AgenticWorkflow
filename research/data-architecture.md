# 교회 행정 AI 시스템 — 자체 데이터 아키텍처 설계

**작성자**: Data Architecture Researcher
**작성일**: 2026-02-27
**기반**: 코드베이스 직접 분석 (`_context_lib.py`, `state.yaml.example`, `glossary.yaml`, `block_destructive_commands.py`, `validate_*.py` 패턴)

---

## 핵심 설계 원칙

이 문서는 외부 API(Google Sheets, Gmail, Calendar MCP) 의존을 **완전히 제거**하고, Claude Code의 기존 패턴만으로 교회 행정 데이터를 관리하는 아키텍처를 설계한다.

**방향 전환 근거:**
- 외부 API 의존 → 네트워크 장애, API 변경, 인증 만료 시 시스템 전체 중단
- 파일 기반 → Claude Code 에이전트가 Read/Edit/Write 도구로 직접 접근, 오프라인 작동, Git 버전 관리

---

## 1. 데이터 저장 형식 비교 분석

### 후보 형식 평가

| 형식 | Claude 에이전트 읽기/쓰기 | 구조적 검증 | 한국어 지원 | Git 친화성 | 쿼리 능력 |
|------|--------------------------|------------|------------|------------|----------|
| **YAML** | 최우수 (Read 도구 직접) | PyYAML 검증 | 완벽 | diff 가독성 높음 | 제한적 |
| **JSON** | 우수 (구조화) | json 모듈 | 완벽 | diff 가독성 낮음 | 제한적 |
| **CSV** | 보통 (행 기반) | 불가 | 인코딩 문제 | diff 가독성 높음 | 없음 |
| **SQLite** | 불가 (바이너리) | 강력 | 완벽 | Git 추적 불가 | SQL 완전 지원 |
| **Markdown** | 최우수 (Read 도구) | 불가 | 완벽 | diff 가독성 최고 | 없음 |

### 결정: YAML 주 포맷 + 특수 목적 Markdown

**YAML 선택 근거:**
1. **코드베이스 일관성**: 이미 `state.yaml`(SOT), `glossary.yaml`(번역 사전)이 YAML. `_context_lib.py`의 `yaml.safe_load()` 패턴 재사용 가능.
2. **에이전트 친화성**: Claude가 Read → Edit → Write 사이클로 직접 조작 가능.
3. **PyYAML 검증**: 기존 `validate_*.py` 패턴처럼 구조적 무결성 검증 스크립트 구축 가능.
4. **한국어**: UTF-8 네이티브 지원, 인코딩 문제 없음.
5. **Git diff 가독성**: 교인 추가/삭제/변경이 사람이 읽을 수 있는 diff로 기록됨.

**Markdown 보조 사용처**: 주보(bulletin), 설교 요약, 행사 공지 등 서술형 콘텐츠.

---

## 2. 기존 코드베이스 패턴 재사용 분석

### 2-1. `state.yaml` SOT 패턴 → 교회 데이터 확장

`state.yaml.example`의 스키마 구조를 그대로 교회 데이터에 적용한다.

**기존 패턴** (`state.yaml.example`):
```yaml
workflow:
  name: "[워크플로우 이름]"
  current_step: 1
  status: "in_progress"
  outputs:
    step-1: "research/collected-data.md"
```

**교회 데이터 확장 패턴** (`church-state.yaml`):
```yaml
church:
  name: "새벽이슬교회"
  current_bulletin_issue: 1247
  status: "active"
  data_paths:
    members: "data/members.yaml"
    finance: "data/finance.yaml"
    schedule: "data/schedule.yaml"
    newcomers: "data/newcomers.yaml"
    bulletin: "data/bulletin-data.yaml"
```

**SOT 원칙 적용**: `church-state.yaml`은 Orchestrator만 수정. 개별 에이전트는 `data/` 디렉토리의 각 파일을 읽기 전용으로 접근하고, 산출물을 별도 경로에 생성.

### 2-2. `_context_lib.py` YAML 읽기/쓰기 패턴 재사용

`_context_lib.py` 501-558번째 줄의 `read_autopilot_state()` 함수 구조를 교회 데이터 읽기에 그대로 적용:

```python
# 기존 패턴 (_context_lib.py:534-557)
def read_church_members(project_dir):
    """Read members data from YAML. Read-only.

    P1 Compliance: All fields are deterministic extractions from YAML.
    SOT Compliance: Read-only file access.
    """
    members_path = os.path.join(project_dir, "data", "members.yaml")

    try:
        import yaml
        with open(members_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            return data.get("members", [])
    except Exception:
        pass
    return []
```

**핵심 재사용 포인트:**
- `yaml.safe_load()` — 안전한 YAML 파싱 (임의 코드 실행 방지)
- `try/except` 보호 — 파일 없거나 파싱 오류 시 안전 기본값 반환
- `encoding="utf-8"` — 한국어 데이터 안전 처리

### 2-3. `glossary.yaml` 관리 패턴 → 교인 명부 패턴

`translations/glossary.yaml`의 단순 키-값 YAML이 아니라, 교인 명부는 **리스트 of 딕셔너리** 구조가 필요:

```yaml
# glossary.yaml (기존) — 단순 키-값
"SOT": "SOT"
"Autopilot": "Autopilot"

# members.yaml (교인 명부) — 리스트 of 딕셔너리
members:
  - id: "M001"
    name: "김철수"
    ...
```

**글로사리에서 배우는 규칙**: `# NEVER remove existing entries — only add new ones.` 주석처럼, 교인 데이터도 삭제 대신 `status: "inactive"`로 처리하여 이력을 보존한다.

### 2-4. `validate_*.py` 패턴 → 교회 데이터 검증 재사용

기존 `validate_pacs.py`, `validate_verification.py` 구조를 그대로 복제:

```python
# 기존 패턴 (validate_pacs.py:8-9)
# Usage:
#     python3 .claude/hooks/scripts/validate_pacs.py --step 3 --project-dir .
# Output: JSON to stdout
#     {"valid": true, "warnings": [], ...}

# 교회 데이터 검증 (신규)
# Usage:
#     python3 .claude/hooks/scripts/validate_members.py --project-dir .
# Output: JSON to stdout
#     {"valid": true, "warnings": [], "member_count": 237}
```

**검증 스크립트 목록 (신규 추가)**:
- `validate_members.py` — 교인 명부 스키마 검증 (필수 필드, ID 유일성, 날짜 형식)
- `validate_finance.py` — 재정 데이터 산술 정합성 (총계 = 항목 합산)
- `validate_schedule.py` — 일정 데이터 날짜/시간 형식 및 충돌 감지
- `validate_newcomers.py` — 새신자 추적 상태 전이 유효성

### 2-5. `block_destructive_commands.py` → 재정 데이터 보호

`block_destructive_commands.py`의 regex 기반 차단 패턴을 교회 재정 데이터 덮어쓰기 방지에 확장:

```python
# 기존 패턴 (block_destructive_commands.py:50-61)
GIT_PATTERNS = [
    (re.compile(r"\bgit\s+push\b.*\s--force(?![-\w])"), "blocked message"),
]

# 교회 데이터 보호 추가 (Write hook에서)
FINANCE_PROTECTION_PATTERNS = [
    # finance.yaml 직접 Write 시 경고 — Orchestrator 검증 후에만 허용
    (re.compile(r"data/finance\.yaml"),
     "Direct finance.yaml write detected. Run validate_finance.py first."),
]
```

---

## 3. 데이터 무결성 및 백업 전략

### 3-1. 파일 기반 무결성 보장

**계층 1 — 쓰기 권한 분리** (절대 기준 2 SOT 패턴 적용):
- `church-state.yaml` — Orchestrator/팀 리드만 수정
- `data/members.yaml` — 교적 담당 에이전트만 수정 (PreToolUse Hook으로 강제)
- `data/finance.yaml` — 재정 담당 에이전트만 수정, `validate_finance.py` 통과 후에만

**계층 2 — P1 결정론적 검증** (기존 `validate_*.py` 패턴):
```python
# validate_finance.py 핵심 로직
def validate_finance_arithmetic(project_dir):
    """Check: sum(items) == total. Deterministic, no AI judgment."""
    data = load_yaml(project_dir, "data/finance.yaml")
    for entry in data.get("offerings", []):
        items_sum = sum(item["amount"] for item in entry.get("items", []))
        declared_total = entry.get("total", 0)
        if abs(items_sum - declared_total) > 0.01:  # 부동소수점 허용 오차
            return False, f"Arithmetic mismatch: {items_sum} != {declared_total}"
    return True, []
```

**계층 3 — Git 원자적 쓰기** (기존 `fcntl` 잠금 패턴):
`_context_lib.py`에서 이미 `fcntl.flock()`을 사용한 원자적 파일 쓰기 패턴을 사용한다. 교회 데이터 쓰기에도 동일 패턴 적용:

```python
import fcntl, tempfile, os

def atomic_write_yaml(path, data):
    """Write YAML atomically using tempfile + rename (P1 pattern from _context_lib.py)."""
    import yaml
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        fcntl.flock(f, fcntl.LOCK_UN)
    os.rename(tmp_path, path)  # 원자적 교체
```

### 3-2. Git 버전 관리 전략

**장점:**
- 모든 데이터 변경이 누가 언제 무엇을 바꿨는지 완전 추적
- 실수로 삭제/수정 시 `git checkout [파일]`로 즉시 복구
- 주보 발행 이력, 재정 결산 이력이 자동으로 연간 아카이브

**단점 및 대응:**
| 한계 | 대응 방안 |
|------|----------|
| 민감 정보(교인 연락처, 헌금액) Git 이력 노출 | `.gitignore`로 `data/` 제외 + 별도 암호화 백업 |
| 대형 교회(1000명+) 시 YAML 파일 크기 증가 | 연도별 파일 분리 (`members-2026.yaml`) |
| 동시 수정 충돌 | SOT 패턴으로 단일 쓰기 에이전트 지정 |

**권장 Git 전략:**
```
# 공개 저장소 (워크플로우 코드만)
.gitignore:
  data/members.yaml
  data/finance.yaml
  data/newcomers.yaml

# 별도 비공개 저장소 or 로컬 백업
# data/ 디렉토리는 암호화 후 별도 백업
```

### 3-3. 백업/복구 전략

```bash
# 일일 자동 백업 스크립트 (cron으로 실행)
#!/bin/bash
BACKUP_DIR="$HOME/church-data-backup/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"
cp data/*.yaml "$BACKUP_DIR/"
echo "Backup completed: $BACKUP_DIR"
```

**복구 프로토콜**: Git 이력에서 특정 날짜 데이터 복원:
```bash
git log --oneline data/finance.yaml  # 이력 조회
git checkout [commit-hash] -- data/finance.yaml  # 특정 시점 복원
```

---

## 4. 실제 데이터 스키마 제안

### 4-1. members.yaml (교인 명부)

```yaml
# data/members.yaml
# SOT Compliance: 교적 담당 에이전트만 수정. Orchestrator가 validate_members.py 통과 후 승인.
# NEVER remove members — use status: "inactive" to preserve history.

schema_version: "1.0"
last_updated: "2026-02-27"
updated_by: "교적담당에이전트"

members:
  - id: "M001"                         # 고유 ID (변경 불가)
    name: "김철수"                      # 본명
    gender: "male"                     # male | female
    birth_date: "1975-03-15"           # YYYY-MM-DD
    status: "active"                   # active | inactive | transferred | deceased

    # 연락처
    contact:
      phone: "010-1234-5678"
      email: "kim@example.com"
      address: "서울시 마포구 합정동 123-4"

    # 교회 정보
    church:
      registration_date: "2015-06-01"  # 등록일
      baptism_date: "2010-04-05"       # 세례일 (null if 미세례)
      baptism_type: "adult"            # adult | infant | null
      department: "장년부"             # 소속 부서
      cell_group: "합정1구역"          # 소그룹/구역
      role: "집사"                     # 직분: 목사 | 장로 | 집사 | 권사 | 성도 | null
      serving_area: ["찬양팀", "주차봉사"]  # 봉사 영역

    # 가족 관계
    family:
      family_id: "F042"               # 가족 단위 ID (같은 가정 묶음)
      relation: "household_head"      # household_head | spouse | child | etc.

    # 이력 (삭제 없이 추가만)
    history:
      - date: "2020-01-05"
        event: "transfer_in"
        note: "○○교회에서 이명"
      - date: "2023-07-01"
        event: "role_change"
        note: "성도 → 집사 임직"

  - id: "M002"
    name: "이영희"
    gender: "female"
    birth_date: "1978-11-22"
    status: "active"
    contact:
      phone: "010-9876-5432"
      email: null
      address: "서울시 마포구 합정동 123-4"
    church:
      registration_date: "2015-06-01"
      baptism_date: "2008-12-25"
      baptism_type: "adult"
      department: "장년부"
      cell_group: "합정1구역"
      role: "집사"
      serving_area: ["교회학교 교사"]
    family:
      family_id: "F042"
      relation: "spouse"
    history: []

# 통계 (에이전트가 집계, 직접 수정 금지 — validate_members.py가 재계산)
_stats:
  total_active: 237
  total_members: 251
  last_computed: "2026-02-27"
```

**검증 규칙** (`validate_members.py` 구현 대상):
- M1: 모든 `id` 유일성
- M2: `status` 허용값 집합 검증
- M3: `birth_date`, `registration_date` YYYY-MM-DD 형식
- M4: `family_id` 참조 무결성 (같은 `family_id`의 구성원이 2명 이상 존재)
- M5: `role` 허용값 집합 검증
- M6: `_stats.total_active` = `status == "active"` 실제 카운트 일치

---

### 4-2. finance.yaml (재정 데이터)

```yaml
# data/finance.yaml
# 재정 데이터 — 산술 정합성은 validate_finance.py가 강제 검증
# NEVER delete entries — mark as voided with void: true

schema_version: "1.0"
year: 2026
currency: "KRW"

# 헌금 기록
offerings:
  - id: "OFF-2026-001"
    date: "2026-01-05"
    service: "주일예배 1부"
    type: "regular"           # regular(일반) | thanks(감사) | special(특별) | tithe(십일조)
    items:
      - category: "십일조"
        amount: 3850000
      - category: "일반헌금"
        amount: 1240000
      - category: "감사헌금"
        amount: 580000
    total: 5670000            # validate_finance.py: sum(items) == total
    recorded_by: "재정담당집사"
    verified: true
    void: false

  - id: "OFF-2026-002"
    date: "2026-01-12"
    service: "주일예배 1부"
    type: "regular"
    items:
      - category: "십일조"
        amount: 4120000
      - category: "일반헌금"
        amount: 1380000
    total: 5500000
    recorded_by: "재정담당집사"
    verified: true
    void: false

# 지출 기록
expenses:
  - id: "EXP-2026-001"
    date: "2026-01-10"
    category: "관리비"       # 관리비 | 인건비 | 사역비 | 선교비 | 교육비 | 기타
    subcategory: "전기요금"
    amount: 245000
    description: "1월 전기요금"
    payment_method: "계좌이체"
    approved_by: "담임목사"
    receipt: true
    void: false

  - id: "EXP-2026-002"
    date: "2026-01-15"
    category: "인건비"
    subcategory: "교역자사례비"
    amount: 2500000
    description: "1월 사례비"
    payment_method: "계좌이체"
    approved_by: "장로회"
    receipt: false
    void: false

# 예산 (연간)
budget:
  fiscal_year: 2026
  approved_date: "2025-12-28"
  categories:
    관리비: 3500000
    인건비: 35000000
    사역비: 12000000
    선교비: 8000000
    교육비: 5000000
    기타: 2000000
  total_budget: 65500000

# 월별 결산 요약 (에이전트가 집계)
monthly_summary:
  "2026-01":
    total_income: 11170000
    total_expense: 2745000
    balance: 8425000
    computed_at: "2026-02-01"
```

**검증 규칙** (`validate_finance.py` 구현 대상):
- F1: `offering.total` = `sum(items[].amount)` 산술 정합성 (절대값 오차 < 1원)
- F2: `monthly_summary` 수치 = 해당 월 offerings/expenses 합산 일치
- F3: `void: true` 항목은 `monthly_summary` 산출에서 제외됨을 검증
- F4: `amount` 모두 양수 정수
- F5: `id` 유일성 (OFF-*, EXP-* 시리즈 별도)

---

### 4-3. schedule.yaml (예배 및 행사 일정)

```yaml
# data/schedule.yaml
# 예배 및 행사 일정 — 날짜 충돌은 validate_schedule.py가 감지

schema_version: "1.0"

# 정기 예배 (고정 패턴)
regular_services:
  - id: "SVC-SUN-1"
    name: "주일예배 1부"
    recurrence: "weekly"
    day_of_week: "sunday"
    time: "09:00"
    duration_minutes: 70
    location: "본당"
    preacher_rotation:     # 설교자 순환 목록
      - "담임목사"
      - "부목사1"
    worship_leader: "찬양팀A"

  - id: "SVC-SUN-2"
    name: "주일예배 2부"
    recurrence: "weekly"
    day_of_week: "sunday"
    time: "11:00"
    duration_minutes: 70
    location: "본당"
    preacher_rotation:
      - "담임목사"
    worship_leader: "찬양팀B"

  - id: "SVC-WED"
    name: "수요예배"
    recurrence: "weekly"
    day_of_week: "wednesday"
    time: "19:30"
    duration_minutes: 60
    location: "본당"
    preacher_rotation:
      - "담임목사"
      - "부목사1"
      - "부목사2"
    worship_leader: null

  - id: "SVC-FRI"
    name: "금요기도회"
    recurrence: "weekly"
    day_of_week: "friday"
    time: "21:00"
    duration_minutes: 90
    location: "기도실"
    preacher_rotation:
      - "담임목사"
    worship_leader: null

# 특별 행사 (비정기)
special_events:
  - id: "EVT-2026-001"
    name: "2026년 신년감사예배"
    date: "2026-01-04"
    time: "11:00"
    duration_minutes: 120
    location: "본당"
    preacher: "담임목사"
    description: "신년을 맞아 하나님께 감사드리는 특별 예배"
    attendance_expected: 350
    preparation:
      - "현수막 제작"
      - "특별 찬양팀 섭외"
      - "식사 준비 (250인분)"
    status: "completed"     # planned | confirmed | completed | cancelled

  - id: "EVT-2026-015"
    name: "부활절 연합예배"
    date: "2026-04-05"
    time: "10:00"
    duration_minutes: 90
    location: "본당"
    preacher: "담임목사"
    description: "부활절 기념 특별 예배"
    attendance_expected: 400
    preparation:
      - "꽃 장식 준비"
      - "달걀 나눔 행사"
    status: "planned"

# 시설 예약 (공간 충돌 방지)
facility_bookings:
  - id: "FAC-2026-001"
    facility: "교육관 3층"
    date: "2026-02-15"
    time_start: "14:00"
    time_end: "17:00"
    purpose: "청년부 수련회 준비 모임"
    booked_by: "청년부 간사"
    status: "confirmed"
```

**검증 규칙** (`validate_schedule.py` 구현 대상):
- S1: `date` YYYY-MM-DD 형식
- S2: `time` HH:MM 형식
- S3: 동일 `location`에서 시간대 겹침 감지 (충돌 경고)
- S4: `status` 허용값 집합 검증
- S5: `id` 유일성

---

### 4-4. newcomers.yaml (새신자 추적)

```yaml
# data/newcomers.yaml
# 새신자 등록 및 정착 추적 — 정착 완료 후 members.yaml로 이관

schema_version: "1.0"

newcomers:
  - id: "N001"
    name: "박민준"
    gender: "male"
    birth_year: 1992
    contact:
      phone: "010-1111-2222"
      kakao_id: "pmj1992"

    # 방문 이력
    first_visit: "2026-02-02"
    visit_route: "지인 초청"   # 지인 초청 | 전도 | 온라인 검색 | 지역사회 행사 | 기타
    referred_by: "M001"       # 초청한 교인 ID (nullable)

    # 정착 단계 추적 (Newcomer Journey)
    journey_stage: "attending"
    # 단계: first_visit → attending → small_group → baptism_class → baptized → settled

    journey_milestones:
      first_visit:
        date: "2026-02-02"
        completed: true
      welcome_call:
        date: "2026-02-03"        # 담당자가 전화한 날
        completed: true
        notes: "반갑게 통화, 다음 주 방문 의사 있음"
      second_visit:
        date: "2026-02-09"
        completed: true
      small_group_intro:
        date: null
        completed: false
      baptism_class:
        date: null
        completed: false
      baptism:
        date: null
        completed: false

    # 담당 목양자
    assigned_to: "M023"           # 새신자 담당 집사 ID
    assigned_department: "청년부"

    # 이관 상태
    status: "active"              # active | settled | inactive | transferred
    settled_as_member: null       # 정착 완료 후 members.yaml ID (예: "M252")
    settled_date: null

  - id: "N002"
    name: "최수진"
    gender: "female"
    birth_year: 1988
    contact:
      phone: "010-3333-4444"
      kakao_id: null
    first_visit: "2026-01-19"
    visit_route: "전도"
    referred_by: null
    journey_stage: "small_group"
    journey_milestones:
      first_visit:
        date: "2026-01-19"
        completed: true
      welcome_call:
        date: "2026-01-20"
        completed: true
        notes: "세 자녀 있음. 주일학교 관심"
      second_visit:
        date: "2026-01-26"
        completed: true
      small_group_intro:
        date: "2026-02-05"
        completed: true
      baptism_class:
        date: null
        completed: false
      baptism:
        date: null
        completed: false
    assigned_to: "M056"
    assigned_department: "장년부"
    status: "active"
    settled_as_member: null
    settled_date: null

# 집계 (validate_newcomers.py가 재계산)
_stats:
  total_active: 12
  by_stage:
    first_visit: 2
    attending: 5
    small_group: 3
    baptism_class: 2
    baptized: 0
    settled: 0
  last_computed: "2026-02-27"
```

**검증 규칙** (`validate_newcomers.py` 구현 대상):
- N1: `id` 유일성
- N2: `journey_stage` 허용값 + `journey_milestones` 완료 상태 정합성 (이전 단계 미완료 시 현재 단계 불가)
- N3: `first_visit` YYYY-MM-DD 형식
- N4: `referred_by`가 null이 아닌 경우 `members.yaml`에 해당 ID 존재 확인
- N5: `settled_as_member`가 존재하면 `status == "settled"` 필수

---

### 4-5. bulletin-data.yaml (주보 소스 데이터)

```yaml
# data/bulletin-data.yaml
# 주보 생성 에이전트의 원천 데이터 — 매주 업데이트

schema_version: "1.0"

bulletin:
  issue_number: 1247
  date: "2026-03-01"             # 주보 날짜 (주일)
  church_name: "새벽이슬교회"

  # 이번 주 설교 정보
  sermon:
    title: "두려움을 넘어선 믿음"
    scripture: "요한복음 6:16-21"
    preacher: "담임목사"
    series: "요한복음 강해 시리즈"
    series_episode: 18

  # 예배 순서 (주일 2부 기준)
  worship_order:
    - order: 1
      item: "찬양"
      detail: "주님 찬양해 (경배와찬양 178)"
      performer: "찬양팀B"
    - order: 2
      item: "기도"
      detail: "대표기도"
      performer: "김○○ 집사"
    - order: 3
      item: "봉헌"
      detail: null
      performer: null
    - order: 4
      item: "말씀"
      detail: "두려움을 넘어선 믿음"
      performer: "담임목사"
    - order: 5
      item: "축도"
      detail: null
      performer: "담임목사"

  # 이번 주 공지사항
  announcements:
    - id: "ANN-001"
      category: "행사"
      title: "3월 구역모임 일정"
      content: "이번 주 수요일 오후 7시, 각 구역별 모임이 있습니다. 구역장의 안내를 따라주세요."
      priority: "high"           # high | normal | low
      expires: "2026-03-04"      # 공지 만료일
    - id: "ANN-002"
      category: "새신자"
      title: "새신자 환영회"
      content: "예배 후 본당 로비에서 새신자 환영 다과 시간이 있습니다."
      priority: "normal"
      expires: "2026-03-01"

  # 이번 주 기도 제목
  prayer_requests:
    - category: "교회"
      content: "3월 부흥회를 위한 성령의 역사 기도"
    - category: "국가"
      content: "나라와 민족을 위한 중보기도"
    - category: "선교"
      content: "파송 선교사 OOO 가정 건강 회복"
    - category: "교인"
      content: "이번 주 수술 예정인 성도들의 빠른 쾌유"

  # 헌금 봉사자 (이번 주)
  offering_team:
    - "박○○ 권사"
    - "최○○ 집사"
    - "황○○ 집사"

  # 생일/기념일 (이번 주)
  celebrations:
    birthday:
      - member_id: "M045"
        name: "홍○○"
        date: "03-03"
    wedding_anniversary:
      - family_id: "F012"
        date: "03-02"

  # 다음 주 예고
  next_week:
    sermon_title: "평화의 왕"
    scripture: "요한복음 6:22-40"
    special_events: []

# 생성 이력
generation_history:
  - issue: 1246
    generated_at: "2026-02-22T14:30:00"
    generated_by: "주보생성에이전트"
    output_path: "bulletins/2026-02-22-bulletin.md"
  - issue: 1247
    generated_at: null           # 아직 미생성
    generated_by: null
    output_path: null
```

---

## 5. 디렉토리 구조

```
Church-Admin-AgenticWorkflow/
├── church-state.yaml                    ← 교회 행정 SOT (Orchestrator만 수정)
│
├── data/                                ← 핵심 교회 데이터 (YAML)
│   ├── members.yaml                     (교인 명부)
│   ├── finance.yaml                     (재정 데이터)
│   ├── schedule.yaml                    (예배/행사 일정)
│   ├── newcomers.yaml                   (새신자 추적)
│   └── bulletin-data.yaml              (주보 소스)
│
├── bulletins/                           ← 생성된 주보 (Markdown)
│   ├── 2026-02-22-bulletin.md
│   └── 2026-03-01-bulletin.md
│
├── reports/                             ← 생성된 보고서
│   ├── 2026-01-finance-report.md
│   └── 2026-02-newcomer-report.md
│
├── .claude/
│   ├── hooks/scripts/
│   │   ├── validate_members.py          ← 신규 (M1-M6)
│   │   ├── validate_finance.py          ← 신규 (F1-F5)
│   │   ├── validate_schedule.py         ← 신규 (S1-S5)
│   │   └── validate_newcomers.py        ← 신규 (N1-N5)
│   └── agents/
│       ├── bulletin-generator.md        ← 주보 생성 전문 에이전트
│       ├── finance-recorder.md          ← 재정 기록 전문 에이전트
│       ├── member-manager.md            ← 교적 관리 전문 에이전트
│       └── newcomer-tracker.md          ← 새신자 추적 전문 에이전트
│
└── .gitignore
    # 민감 데이터 제외 (별도 백업)
    data/members.yaml
    data/finance.yaml
    data/newcomers.yaml
```

---

## 6. 한계와 트레이드오프

### 6-1. 파일 기반 한계

| 한계 | 구체적 임계값 | 대응 방안 |
|------|-------------|----------|
| **교인 수** | 1,000명까지 단일 파일 권장 (YAML 파일 < 500KB) | 1,000명 초과 시 `members-A.yaml` / `members-B.yaml` 알파벳 분리 |
| **재정 이력** | 연간 100-200개 헌금/지출 항목 → 5년 이후 파일 크기 증가 | 연도별 파일 분리 (`finance-2026.yaml`) |
| **동시 접근** | 에이전트 동시 쓰기 시 충돌 | SOT 패턴으로 단일 쓰기 에이전트 지정 + fcntl 잠금 |
| **쿼리 능력** | "특정 구역 교인 전체 조회" 등 복잡 쿼리 어려움 | 에이전트가 Python으로 파싱 후 필터링 (PyYAML + list comprehension) |
| **전문 DB 기능** | 트랜잭션, 롤백, 인덱스 없음 | 원자적 쓰기(tempfile+rename) + Git 이력로 대체 |

**현실적 커버 가능 규모**: **500인 이하 교회**에서 파일 기반이 충분히 작동한다. 500인 이하가 전체 교회의 약 95%를 차지하므로 대부분의 타겟 교회 커버 가능.

### 6-2. 외부 연동 대비 득실

| 항목 | 외부 연동 (Google Sheets/Calendar) | 파일 기반 (이 설계) |
|------|----------------------------------|-------------------|
| **설치 복잡도** | OAuth, API 키, 권한 설정 필요 | 없음 (파일만 있으면 됨) |
| **오프라인 작동** | 불가 | 가능 |
| **데이터 소유권** | Google 서버에 저장 | 교회 로컬 저장 |
| **실시간 협업** | 다수가 동시에 Google Sheets 편집 가능 | 불가 (에이전트 순차 처리) |
| **모바일 접근** | Google Sheets 앱으로 편집 가능 | 불가 (에이전트만 접근) |
| **API 장애** | 서비스 중단 시 사용 불가 | 영향 없음 |
| **비용** | API 초과 시 과금 | 없음 |
| **버전 관리** | 구글 자체 이력 (30일) | Git 무제한 이력 |
| **보안** | 구글 계정 탈취 시 전체 노출 | 로컬 파일 보안에 의존 |

**잃는 것**: 실시간 다중 사용자 협업, 모바일 즉시 편집
**얻는 것**: API 독립성, 데이터 주권, 오프라인 작동, 무제한 Git 이력, 설치 간소화

### 6-3. 이 설계가 적합한 교회 유형

**적합:**
- 100~500인 규모 교회 (핵심 타겟)
- 행정 자동화에 관심 있으나 IT 인프라 팀이 없는 교회
- 주보 생성, 재정 보고, 새신자 추적 자동화가 주요 목적인 교회
- 데이터를 교회 내부에 보관하고 싶은 교회

**부적합:**
- 1,000인 이상 대형 교회 (전문 ChMS 솔루션 필요)
- 실시간으로 여러 사람이 데이터를 동시 편집해야 하는 교회
- 모바일로 교인이 직접 출석 체크/헌금 입력하는 셀프서비스 모델

---

## 7. 구현 우선순위 제안

| 우선순위 | 데이터 | 이유 |
|--------|--------|------|
| **P1 (즉시)** | `members.yaml` | 모든 다른 데이터의 기반 (ID 참조) |
| **P1 (즉시)** | `bulletin-data.yaml` | 매주 반복 업무, 즉각 가치 |
| **P2 (2주차)** | `newcomers.yaml` | 전도/정착 추적 핵심 사역 |
| **P2 (2주차)** | `schedule.yaml` | 주보 생성에 필요 |
| **P3 (1달)** | `finance.yaml` | 민감 데이터, 검증 스크립트 선행 필요 |

**검증 스크립트 개발 순서**: `validate_members.py` → `validate_newcomers.py` → `validate_finance.py` → `validate_schedule.py`

---

## 결론

파일 기반 YAML 아키텍처는 이 코드베이스의 기존 패턴(`state.yaml` SOT, `_context_lib.py` YAML 파싱, `validate_*.py` 검증, `block_destructive_commands.py` 보호)을 최대한 재사용하면서 외부 API 의존을 완전히 제거한다.

500인 이하 교회에서는 파일 기반이 충분하며, 이는 한국 전체 교회의 약 95%에 해당한다. 핵심 타겟인 중형 교회(100~500인) 15,000개를 커버하는 데 기술적 한계가 없다.

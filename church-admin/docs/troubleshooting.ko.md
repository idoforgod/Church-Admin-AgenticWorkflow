# 문제 해결 가이드 — 자주 발생하는 10가지 문제

교회 행정 시스템 사용 중 자주 발생하는 문제에 대한 해결 방법을 안내합니다. 각 문제별로 증상, 원인, 단계별 해결 방법을 포함합니다.

**대상 사용자**: 행정 간사 (1차 문제 해결) 및 IT 자원봉사자 (기술적 해결)

---

## 문제 1: YAML 구문 오류

### 증상
- 오류 메시지: "YAML parse error" 또는 "invalid syntax"
- 데이터 파일이 로드되지 않음
- 검증 시 알 수 없는 오류 발생

### 원인
YAML 파일은 서식에 민감합니다. 흔한 실수는 다음과 같습니다:
- 스페이스 대신 탭 사용 (YAML은 스페이스만 허용)
- 필드명 뒤에 콜론 누락
- 들여쓰기 수준이 맞지 않음

### 해결 방법 (행정 간사)

1. 오류가 발생한 파일을 엽니다
2. 오류 메시지에 표시된 줄 번호를 찾습니다
3. 다음과 같은 흔한 문제를 확인합니다:

```yaml
# WRONG — tab character (invisible but breaks YAML)
	name: "김철수"

# CORRECT — 2 spaces
  name: "김철수"
```

```yaml
# WRONG — missing colon
  name "김철수"

# CORRECT
  name: "김철수"
```

```yaml
# WRONG — misaligned indentation
members:
  - id: "MBR-2026-001"
  name: "김철수"

# CORRECT — name indented under list item
members:
  - id: "MBR-2026-001"
    name: "김철수"
```

### 해결 방법 (IT 자원봉사자)

```bash
python3 -c "import yaml; yaml.safe_load(open('data/members.yaml'))"
```

---

## 문제 2: Excel 파일 파싱 실패

### 증상
- Excel 파일이 `inbox/documents/`에 처리되지 않은 채 남아 있음
- 파일이 `inbox/errors/`로 이동됨
- 오류: "unsupported format" 또는 "parse error"

### 원인
- `.xlsx` 대신 `.xls`(이전 형식) 사용
- 셀 병합이나 복잡한 서식
- 비밀번호로 보호된 파일

### 해결 방법

1. **파일 형식 확인**: `.xlsx`(Excel 통합 문서)로 저장
   - Excel에서 열기 → 다른 이름으로 저장 → "Excel 통합 문서(.xlsx)" 선택

2. **서식 단순화**: 병합된 셀 제거
   - 전체 선택 → 서식 → 셀 → 병합 해제

3. **보호 해제**: 파일에 비밀번호 보호가 없어야 합니다

4. **인코딩 확인**: 한국어 문자는 UTF-8이어야 합니다
   - 다른 이름으로 저장 → 도구 → 웹 옵션 → 인코딩 → UTF-8

---

## 문제 3: 데이터 수정 후 검증 실패

### 증상
- YAML 파일을 직접 수정한 후 검증에서 오류 발생
- "M1 FAIL" 또는 "F3 FAIL" 같은 오류 메시지

### 원인
직접 수정하면서 검증 규칙에 위반되는 데이터가 입력되었습니다:

| 규칙 | 검사 내용 | 흔한 실수 |
|------|----------|----------|
| M1 | 교인 ID 고유성 + 형식 | 중복되거나 잘못된 형식의 ID |
| M3 | 전화번호 형식 (010-NNNN-NNNN) | 하이픈 누락 또는 잘못된 접두사 |
| M4 | 상태 열거형 | 유효하지 않은 상태 값 사용 |
| F2 | 금액이 원화 정수인지 | 금액에 소수점이나 쉼표 포함 |
| S4 | 행사 상태 열거형 | "scheduled" 대신 "planned" 사용 |
| N2 | 단계/마일스톤 일관성 | 단계가 마일스톤과 맞지 않음 |

### 해결 방법

1. 오류 메시지를 읽으세요 — 어떤 규칙과 필드가 실패했는지 알려줍니다
2. 값을 올바른 형식으로 수정합니다
3. 검증을 다시 실행합니다:

```bash
python3 .claude/hooks/scripts/validate_members.py --data-dir data/
```

또는 AI에게 요청하세요: "데이터 검증 오류 도와줘"

---

## 문제 4: 권한 거부 오류

### 증상
- Claude가 파일을 쓰려 할 때 "Permission denied" 발생
- 에이전트가 출력 파일을 생성하지 못함
- 백업 스크립트가 실행되지 않음

### 해결 방법 (IT 자원봉사자)

```bash
# Fix file permissions
chmod 644 data/*.yaml

# Fix directory permissions
chmod 755 data/ inbox/ output/ bulletins/

# Fix backup script
chmod +x scripts/daily-backup.sh
```

---

## 문제 5: 한국어 문자가 올바르게 표시되지 않음

### 증상
- 한국어 텍스트가 `????` 또는 깨진 문자로 표시됨
- 생성된 문서에서 이름이 잘못 표시됨

### 원인
파일이 UTF-8로 저장되지 않았거나, 터미널이 한국어를 지원하지 않습니다.

### 해결 방법

```bash
# Check encoding (IT volunteer)
file -I data/members.yaml
# Expected: text/plain; charset=utf-8
```

- **터미널**: UTF-8로 설정 (터미널 → 환경설정 → 프로파일 → 고급 → UTF-8)
- **파일**: UTF-8 편집기(VS Code)에서 열어 저장

---

## 문제 6: 주보 생성 실패

### 증상
- "이번 주 주보 만들어줘" 실행 시 오류 발생
- 생성된 주보에 빠진 섹션이 있음

### 해결 방법

1. 주보 데이터 검증:
```bash
python3 .claude/hooks/scripts/validate_bulletin.py --data-dir data/
```

2. 필요한 파일이 존재하는지 확인:
```bash
ls data/members.yaml data/schedule.yaml data/bulletin-data.yaml templates/bulletin-template.yaml
```

3. 누락되거나 손상된 파일이 있으면 백업에서 복원

---

## 문제 7: 새신자 파이프라인 단계 전환 안 됨

### 증상
- 새신자가 현재 단계에 머물러 있음
- "Stage transition denied" 메시지

### 원인
전제 조건 마일스톤이 완료되지 않았거나, 사람의 승인이 이루어지지 않았습니다.

### 해결 방법

1. 새신자 현황 확인: "새신자 현황: [이름]"
2. AI가 필요한 마일스톤을 표시합니다
3. 먼저 누락된 마일스톤을 완료합니다
4. 단계 변경에는 반드시 명시적인 사람의 승인이 필요합니다

6단계 정착 과정: `first_visit → attending → small_group → baptism_class → baptized → settled`

---

## 문제 8: 백업 실패

### 증상
- `daily-backup.sh` 실행 시 오류 발생
- 백업 디렉터리가 비어 있음

### 해결 방법 (IT 자원봉사자)

```bash
# Check disk space
df -h

# Run manual backup
chmod +x scripts/daily-backup.sh
./scripts/daily-backup.sh

# Create backup directory if needed
mkdir -p backups/

# Set up cron (daily 2 AM)
crontab -e
# Add: 0 2 * * * cd /path/to/church-admin && ./scripts/daily-backup.sh >> backups/backup.log 2>&1
```

---

## 문제 9: 재정 보고서 이중 리뷰가 작동하지 않음

### 증상
- 재정 보고서가 자동 승인됨 (이것은 **절대** 일어나서는 안 되는 일입니다)

### 해결 방법

이것은 안전에 관련된 중요한 문제입니다. 재정 워크플로우는 Autopilot이 영구적으로 비활성화되어 있습니다.

1. `workflows/monthly-finance-report.md` 10번째 줄을 확인: `Autopilot: disabled`여야 합니다
2. 재정 담당 집사와 담임목사 **모두** 반드시 검토해야 합니다
3. 단일 승인으로 처리가 가능한 상태라면, 작업을 즉시 중단하고 IT 자원봉사자에게 연락하세요

---

## 문제 10: Claude Code가 시작되지 않음

### 증상
- `claude` 명령을 찾을 수 없음
- Claude가 시작되었다가 즉시 종료됨

### 해결 방법 (IT 자원봉사자)

```bash
# Check installation
which claude
claude --version

# Check network (Claude requires internet)
ping api.anthropic.com

# Verify subscription at claude.com
```

---

## 일반적인 문제 해결 절차

어떤 문제든 발생하면:

1. **오류 메시지 읽기** — 대부분 무엇이 잘못되었는지 알려줍니다
2. **검증 실행** — 해당 검증 스크립트 사용
3. **AI에게 물어보기** — "도와줘"를 입력하고 문제를 설명하세요
4. **IT 자원봉사자에게 연락** — 직접 해결할 수 없는 문제의 경우

### IT 자원봉사자에게 연락해야 하는 경우

- 시스템이 전혀 시작되지 않을 때
- 권한 오류가 해결되지 않을 때
- 백업/복원 작업이 필요할 때
- 네트워크 또는 API 문제
- 위 절차를 따라도 반복적으로 오류가 발생할 때

---

## 참고 문서

- [설치 가이드](installation-guide.ko.md) — 시스템 설치
- [사용자 가이드](user-guide.ko.md) — 일상 업무
- [IT 관리자 가이드](it-admin-guide.ko.md) — 고급 유지보수

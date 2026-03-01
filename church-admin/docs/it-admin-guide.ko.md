# IT 관리자 가이드 — 유지보수 및 운영

정기적인 유지보수, 백업 절차, 데이터 이관, 모니터링, 시스템 확장을 다루는 IT 자원봉사자(박준호 페르소나: 개발자/IT 배경)를 위한 기술 가이드입니다.

**대상 사용자**: IT 자원봉사자 (CLI 능숙, Git 경험 있음)
**사전 조건**: [설치 가이드](installation-guide.ko.md)에 따라 시스템 설치 완료

---

## 정기 유지보수

### 일일 작업

| 작업 | 명령 | 주기 |
|------|------|------|
| 자동 백업 | `./scripts/daily-backup.sh` (cron 설정) | 매일 오전 2시 |
| 백업 로그 확인 | `tail backups/backup.log` | 매일 (육안 확인) |

### 주간 작업

| 작업 | 명령 | 주기 |
|------|------|------|
| 전체 데이터 검증 | 4개 검증 스크립트 실행 (아래 참조) | 매주 |
| inbox/errors/ 확인 | `ls inbox/errors/` | 매주 |
| 디스크 사용량 확인 | `du -sh backups/ data/ output/` | 매주 |

### 월간 작업

| 작업 | 명령 | 주기 |
|------|------|------|
| 유지보수 건강 검진 | `claude --maintenance` | 매월 |
| 오래된 백업 정리 | 자동 (30일 보존 정책) | 매월 확인 |
| Claude Code 업데이트 | `claude update` | 업데이트 있을 때 |

---

## 백업 절차

### 자동 일일 백업

백업 시스템은 cron을 통해 매일 오전 2시에 실행됩니다:

```bash
# View current cron configuration
crontab -l

# Expected entry:
# 0 2 * * * cd /path/to/church-admin && ./scripts/daily-backup.sh >> backups/backup.log 2>&1
```

**백업 대상**:
- 모든 `data/*.yaml` 파일 (교적, 재정, 일정, 새신자, 주보 데이터, 교회 용어집)
- 템플릿 디렉터리
- 설정 파일

**보존 정책**: 30일이 지난 백업은 자동으로 삭제됩니다.

### 수동 백업

언제든 백업을 실행할 수 있습니다:

```bash
./scripts/daily-backup.sh
```

### 백업에서 복원

```bash
# List available backups
ls backups/

# Extract a specific backup
cd backups/
tar xzf church-admin-backup-20260301_020000.tar.gz

# Copy restored files to data directory
cp -i 20260301_020000/data/*.yaml ../data/

# Validate restored data
python3 .claude/hooks/scripts/validate_members.py --data-dir data/
python3 .claude/hooks/scripts/validate_finance.py --data-dir data/
python3 .claude/hooks/scripts/validate_schedule.py --data-dir data/
python3 .claude/hooks/scripts/validate_newcomers.py --data-dir data/
```

**중요**: 복원 후에는 반드시 데이터를 검증하여 정합성을 확인하세요.

---

## 데이터 검증 모음

전체 P1 검증 모음을 실행하여 데이터 무결성을 확인합니다:

```bash
# Member data (M1-M7: ID format, required fields, phone, status enum, family refs, dates, stats)
python3 .claude/hooks/scripts/validate_members.py --data-dir data/

# Finance data (F1-F5: ID format, KRW integers, category enum, dates, budget refs)
python3 .claude/hooks/scripts/validate_finance.py --data-dir data/

# Schedule data (S1-S5: ID format, time format, recurrence, status enum, facility overlap)
python3 .claude/hooks/scripts/validate_schedule.py --data-dir data/

# Newcomer data (N1-N6: ID format, stage/milestones, contact, shepherd refs, dates, stats)
python3 .claude/hooks/scripts/validate_newcomers.py --data-dir data/

# Bulletin data (B1-B3: structure, VR references, generation history)
python3 .claude/hooks/scripts/validate_bulletin.py --data-dir data/
```

모든 스크립트는 `summary: "N/N checks passed"` 형식의 JSON을 출력합니다. 실패 항목이 있으면 구체적인 오류 설명이 포함됩니다.

---

## 기존 교회 관리 시스템에서 데이터 이관

### Excel/스프레드시트에서 이관

1. **Excel 파일 준비** — 시스템의 필드 구조에 맞는 열 구성:
   - 교적: id, name, phone, birth_date, role, status, registration_date
   - 재정: offering_id, donor_id, amount, category, date
   - 새신자: id, name, phone, visit_date, journey_stage

2. **파일 넣기** — `inbox/documents/`에 넣기

3. **처리** — Claude를 시작하고 "inbox 처리해줘" 실행

4. **검증** — 검증 모음을 실행하여 가져온 데이터가 올바른지 확인

### 다른 교회 관리 시스템에서 이관

1. **데이터 내보내기** — 기존 시스템에서 CSV 또는 Excel로 내보내기
2. **필드 매핑** — 이 시스템의 스키마에 맞게 필드 대응 (`planning/data-architecture-spec.md` 참조)
3. **가져오기** — inbox를 통하거나 YAML 직접 편집
4. **검증** — 가져오기 후 모든 데이터 검증

### 수동 데이터 입력

소규모 데이터의 경우 YAML 파일을 직접 편집합니다:

```yaml
# data/members.yaml — add a new member
members:
  - id: "MBR-2026-012"          # Unique ID: MBR-YYYY-NNN
    name: "새교인이름"
    phone: "010-1234-5678"       # Korean mobile: 010-NNNN-NNNN
    birth_date: "1990-01-15"     # YYYY-MM-DD
    role: "member"               # member, deacon, elder, pastor
    status: "active"             # active, inactive, transferred, deceased
    registration_date: "2026-03-01"
```

수동 편집 후에는 반드시 검증을 실행하세요.

---

## 시스템 모니터링

### 건강 검진

```bash
# Infrastructure verification
claude --init

# Periodic health check
claude --maintenance
```

### 주요 지표

| 지표 | 정상 상태 | 비정상 시 조치 |
|------|----------|--------------|
| 검증 스크립트: N/N 통과 | 모두 통과 | 오류 메시지에 따라 데이터 수정 |
| inbox/errors/ 비어 있음 | 파일 없음 | 파일 확인 및 재처리 |
| 백업 로그 성공 표시 | 최근 타임스탬프 있음 | cron, 디스크 공간 확인 |
| 데이터 파일 > 0 바이트 | 모두 존재 | 백업에서 복원 |

---

## 보안 고려사항

### 민감 데이터

다음 파일에는 개인 식별 정보(PII)가 포함되어 있으며, git에서 제외되어 있습니다:

| 파일 | 포함 내용 | 보호 방법 |
|------|----------|----------|
| data/members.yaml | 이름, 전화번호, 주소 | .gitignore |
| data/finance.yaml | 헌금 기록, 금액 | .gitignore |
| data/newcomers.yaml | 방문자 개인 정보 | .gitignore |

### 접근 제어

- **에이전트 쓰기 권한**: 각 에이전트는 지정된 데이터 파일에만 쓸 수 있습니다
  - `member-manager` → `data/members.yaml`
  - `finance-recorder` → `data/finance.yaml`, `output/finance-reports/`, `certificates/receipts/`
  - `schedule-manager` → `data/schedule.yaml`
  - `newcomer-tracker` → `data/newcomers.yaml`
  - `bulletin-generator` → `data/bulletin-data.yaml`

- **SOT 쓰기 제한**: Orchestrator만 `state.yaml`을 수정할 수 있습니다

- **재정 안전장치**: 재정 워크플로우에서는 Autopilot이 영구적으로 비활성화되어 있습니다. 이중 사람 검토가 필수입니다.

### 백업 보안

- 백업은 `backups/`에 로컬로 저장됩니다
- 외부에 백업을 보관하는 경우 암호화를 권장합니다:

```bash
# Encrypt a backup
gpg -c backups/church-admin-backup-20260301.tar.gz

# Decrypt when needed
gpg -d backups/church-admin-backup-20260301.tar.gz.gpg > restored-backup.tar.gz
```

---

## 새 기능 추가

### 워크플로우 생성기 사용

`workflow-generator` 스킬을 사용하여 새 워크플로우로 시스템을 확장할 수 있습니다:

```bash
claude
```

그다음:
```
새 워크플로우 만들어줘: [기능 설명]
```

워크플로우 생성기가 다음을 수행합니다:
1. 요구사항 분석
2. 워크플로우 구조 설계 (Research → Planning → Implementation)
3. 부모 시스템의 DNA를 유전받은 workflow.md 생성
4. 필요한 에이전트 정의 생성
5. 검증 규칙 설정

### 새 데이터 필드 추가

1. **스키마 수정**: 해당 `.yaml` 데이터 파일 수정
2. **검증 수정**: 해당 검증 스크립트에 새 규칙 추가
3. **에이전트 수정**: 새 필드를 처리하도록 에이전트 정의 수정
4. **테스트**: 검증을 실행하여 정합성 확인

### 새 템플릿 추가

1. **기존 템플릿 스캔**: `inbox/templates/`에 템플릿 이미지 넣기
2. **또는 직접 생성**: `templates/`에 새 `.yaml` 파일 추가
3. **워크플로우에 등록**: 필요한 경우 문서 생성 워크플로우 수정
4. **검증**: 템플릿 필드가 데이터 스키마와 일치하는지 확인

---

## IT 자원봉사자를 위한 문제 해결

### 디버그 명령

```bash
# Check Python environment
python3 --version
pip3 list | grep -E "pyyaml|openpyxl|pandas|docx"

# Validate all data
for script in validate_members validate_finance validate_schedule validate_newcomers; do
    echo "=== $script ==="
    python3 .claude/hooks/scripts/${script}.py --data-dir data/
done

# Check file permissions
ls -la data/ inbox/ scripts/

# Check disk usage
du -sh backups/ data/ output/ bulletins/

# View recent backup log
tail -20 backups/backup.log
```

### 자주 발생하는 IT 문제

| 문제 | 진단 방법 | 해결 방법 |
|------|----------|----------|
| 스크립트 import 오류 | `python3 -c "import yaml"` | `pip3 install pyyaml` |
| 권한 거부 | `ls -la data/` | `chmod 644 data/*.yaml` |
| Cron 미실행 | `crontab -l` | cron 항목 추가 |
| 디스크 부족 | `df -h` | 오래된 백업, 출력 파일 정리 |
| Git 병합 충돌 | `git status` | 비-PII 파일에서만 충돌 해결 |

---

## 아키텍처 참조

시스템 아키텍처에 대한 자세한 내용은 다음을 참조하세요:
- `planning/system-architecture.md` (프로젝트 루트) — 전체 시스템 설계
- `planning/data-architecture-spec.md` (프로젝트 루트) — 데이터 스키마 명세
- `workflows/` — 모든 워크플로우 정의

### 디렉터리 구조

```
church-admin/
├── data/                    ← YAML data files (PII — gitignored)
├── inbox/                   ← File drop zone (6 subdirectories)
├── scripts/                 ← Parsers and backup script
├── templates/               ← Document templates (4 YAML files)
├── workflows/               ← Workflow definitions (5 + translations)
├── output/                  ← Generated outputs
│   ├── documents/           ← Official letters, certificates
│   └── finance-reports/     ← Monthly reports, receipts
├── bulletins/               ← Generated bulletins
├── backups/                 ← Timestamped backup archives
├── docs/                    ← This documentation
└── .claude/
    ├── agents/              ← 8 AI agent definitions
    ├── hooks/scripts/       ← Validation and safety scripts
    └── skills/              ← NL interface skill
```

---

## 참고 문서

- [설치 가이드](installation-guide.ko.md) — 초기 설치
- [빠른 시작 가이드](quick-start.ko.md) — 첫 주보 만들기
- [사용자 가이드](user-guide.ko.md) — 행정 간사를 위한 일상 업무
- [문제 해결 가이드](troubleshooting.ko.md) — 자주 발생하는 문제

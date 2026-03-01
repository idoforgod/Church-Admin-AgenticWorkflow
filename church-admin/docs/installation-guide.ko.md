# 설치 가이드 — 교회 행정 시스템

IT 자원봉사자(박준호 페르소나: 개발자/IT 배경, CLI 능숙)를 위한 교회 행정 AI 에이전틱 워크플로우 자동화 시스템 설치 및 구성 단계별 안내서입니다.

---

## 사전 준비 사항 점검표

설치를 시작하기 전에 다음 항목이 준비되어 있는지 확인하세요:

| 요구 사항 | 버전 | 확인 명령 | 비고 |
|----------|------|----------|------|
| Python | 3.10+ | `python3 --version` | macOS: 기본 설치 또는 `brew install python3` |
| PyYAML | 최신 | `pip3 install pyyaml` | 핵심 데이터 형식 라이브러리 |
| openpyxl | 최신 | `pip3 install openpyxl` | inbox/ 1단계 Excel 파일 파싱용 |
| pandas | 최신 | `pip3 install pandas` | 보고서 데이터 처리용 |
| python-docx | 최신 | `pip3 install python-docx` | 문서 생성(증서, 공문 등) |
| Git | 2.0+ | `git --version` | 저장소 관리 |
| Claude Code | 최신 | `claude --version` | AI 에이전트 런타임 — Anthropic 구독 필요 |

### Claude Code 구독

이 시스템은 활성화된 [Claude Code](https://claude.com/claude-code) 구독이 필요합니다. 구독을 통해 다음 기능을 사용할 수 있습니다:
- Claude AI 모델 접근(Opus/Sonnet)을 통한 에이전트 실행
- 검증 및 안전을 위한 Hook 인프라
- 서브에이전트 및 팀 조율 기능

---

## 1단계: 저장소 복제

```bash
# Navigate to your preferred installation directory
cd ~/Documents

# Clone the repository
git clone <repository-url> church-admin-system
cd church-admin-system
```

---

## 2단계: Python 의존성 설치

```bash
# Install all required packages
pip3 install pyyaml openpyxl pandas python-docx

# Verify installations
python3 -c "import yaml; import openpyxl; import pandas; import docx; print('All dependencies OK')"
```

예상 출력: `All dependencies OK`

---

## 3단계: 교회 행정 디렉터리로 이동

```bash
cd church-admin
```

이 디렉터리가 모든 교회 행정 작업의 기본 작업 디렉터리입니다.

---

## 4단계: 초기 설정 검증 실행

```bash
claude --init
```

이 명령은 `setup_init.py` Hook을 실행하여 다음 항목을 검증합니다:

1. **Python 버전** — 3.10 이상 확인
2. **스크립트 구문** — 19개 이상의 Hook 스크립트가 오류 없이 파싱되는지 확인
3. **디렉터리 구조** — 필요한 디렉터리가 존재하거나 자동 생성:
   - `verification-logs/`
   - `pacs-logs/`
   - `review-logs/`
   - `autopilot-logs/`
   - `translations/`
   - `diagnosis-logs/`
4. **PyYAML 사용 가능 여부** — 모든 데이터 작업에 필수
5. **SOT 무결성** — `state.yaml` 구조 검증 (파일이 존재하는 경우)

### 예상 출력

```
Setup Init — Infrastructure Health Check
✓ Python 3.12.x
✓ 19/19 scripts OK
✓ Runtime directories OK
✓ PyYAML available
✓ SOT schema valid
```

검사 항목 중 하나라도 실패하면, 출력에 해당 문제가 구체적으로 표시됩니다. 해결 방법은 [문제 해결 가이드](troubleshooting.ko.md)를 참조하세요.

---

## 5단계: 데이터 파일 확인

모든 시드 데이터 파일이 존재하고 유효한지 확인합니다:

```bash
# Check data file existence
ls -la data/

# Expected files:
# members.yaml       (sample member records)
# finance.yaml        (sample financial data)
# schedule.yaml       (sample worship schedule)
# newcomers.yaml      (sample newcomer records)
# bulletin-data.yaml  (bulletin configuration)
# church-glossary.yaml (church terminology reference)
```

모든 데이터 파일에 대해 P1 검증을 실행합니다:

```bash
# Validate member data (M1-M7)
python3 .claude/hooks/scripts/validate_members.py --data-dir data/

# Validate finance data (F1-F7)
python3 .claude/hooks/scripts/validate_finance.py --data-dir data/

# Validate schedule data (S1-S6)
python3 .claude/hooks/scripts/validate_schedule.py --data-dir data/

# Validate newcomer data (N1-N6)
python3 .claude/hooks/scripts/validate_newcomers.py --data-dir data/
```

모든 스크립트가 오류 없이 `X/X checks passed`를 보고해야 합니다.

---

## 6단계: 에이전트 구성 확인

```bash
# List all agents
ls .claude/agents/

# Expected agents:
# bulletin-generator.md
# data-ingestor.md
# document-generator.md
# finance-recorder.md
# member-manager.md
# newcomer-tracker.md
# schedule-manager.md
# template-scanner.md
```

---

## 7단계: Inbox 인프라 확인

```bash
# Check inbox directories
ls inbox/

# Expected subdirectories:
# documents/   — Word/PDF files for parsing
# errors/      — Invalid files quarantined here
# images/      — Namecard/document images
# processed/   — Successfully processed files
# staging/     — Files awaiting processing
# templates/   — Template images for scan-and-replicate
```

---

## 8단계: 첫 실행 테스트

Claude Code를 시작하여 시스템이 정상적으로 응답하는지 확인합니다:

```bash
claude
```

Claude Code가 시작되면 간단한 명령을 입력해 보세요:

```
주보 미리보기
```

자연어 인터페이스가 정상 작동하면, Claude가 `data/bulletin-data.yaml`을 읽어 현재 주보 데이터 요약을 표시합니다.

---

## 설치 후 점검표

- [ ] Python 3.10 이상 설치 및 확인 완료
- [ ] Python 패키지 5개 모두 설치 완료 (pyyaml, openpyxl, pandas, python-docx)
- [ ] 저장소 복제 및 `church-admin/` 디렉터리 접근 가능
- [ ] `claude --init` 모든 검사 통과
- [ ] `data/`에 데이터 파일 6개 존재
- [ ] 모든 P1 검증 스크립트 통과 (29/29 규칙)
- [ ] `.claude/agents/`에 에이전트 파일 8개 존재
- [ ] inbox 디렉터리 6개 존재
- [ ] Claude Code가 시작되고 한국어 명령에 응답

---

## 민감 데이터 주의사항

다음 파일에는 개인 식별 정보(PII)가 포함되어 있으며, git에서 제외되어 있습니다:

- `data/members.yaml` — 교인 이름, 전화번호, 주소
- `data/finance.yaml` — 기부자 이름이 포함된 헌금 기록
- `data/newcomers.yaml` — 새신자 개인 정보

이 파일들은 `.gitignore`에 등록되어 있으며, 공개 저장소에 **절대** 커밋해서는 안 됩니다. 데이터 보호를 위해 반드시 백업 시스템(`scripts/daily-backup.sh`)을 사용하세요.

---

## 다음 단계

- [빠른 시작 가이드](quick-start.ko.md) — 30분 만에 첫 주보 만들기
- [사용자 가이드](user-guide.ko.md) — 행정 간사를 위한 일상 업무 안내
- [IT 관리자 가이드](it-admin-guide.ko.md) — 지속적 유지보수 작업

---
description: "Hook 인프라 검증 결과 분석 및 문제 해결"
---

## Setup Init 검증 결과 분석

`.claude/hooks/setup.init.log` 파일을 분석하고 문제를 해결합니다.

### 분석 프로토콜:

**1단계 — 로그 읽기:**
`.claude/hooks/setup.init.log`를 Read tool로 읽으세요.
파일이 없으면 사용자에게 안내: "`claude --init`으로 Setup Hook을 먼저 실행해야 합니다."

**2단계 — 심각도별 분류:**
- **CRITICAL**: Context Preservation System이 작동하지 않는 문제. 즉시 해결 필요.
- **WARNING**: 작동은 하지만 성능이 저하되는 문제. 해결을 권장.
- **INFO**: 정상 항목. 보고만.

**3단계 — CRITICAL 문제 해결:**
| 문제 | 해결 방법 |
|------|----------|
| Script syntax error | 해당 스크립트를 Read → 구문 오류 위치 확인 → 수정 제안 |
| Script not found | 파일 누락 원인 조사. git status 확인 |
| context-snapshots/ 생성 실패 | 권한 문제 확인 (ls -la .claude/) |
| Python version < 3 | Python 3 설치 안내 |
| verification-logs/ 미존재 | 디렉터리 생성 제안 (워크플로우 실행 시 필요) |
| pacs-logs/ 미존재 | 디렉터리 생성 제안 (pACS 활성 워크플로우 시 필요) |
| autopilot-logs/ 미존재 | 디렉터리 생성 제안 (Autopilot 모드 시 필요) |

**4단계 — WARNING 문제 해결:**
| 문제 | 해결 방법 |
|------|----------|
| PyYAML 미설치 | `pip install pyyaml` 실행 제안 (사용자 확인 후) |
| .gitignore 누락 | `.gitignore`에 `.claude/context-snapshots/` 추가 제안 |
| sessions/ 생성 실패 | 상위 디렉터리 권한 확인 |
| SOT write safety 경고 | Hook 스크립트에서 SOT 파일명+쓰기 패턴 공존 감지. 해당 스크립트:줄번호 확인 → SOT 읽기 전용 원칙(절대 기준 2) 위반 여부 분석 |

**5단계 — 최종 보고:**
구조화된 형식으로 결과를 보고하세요:
```
## Setup Init 결과

### 검증 요약
- 전체: N개 항목
- 통과: N개
- 실패: N개 (CRITICAL: N, WARNING: N)

### 해결한 문제
- [문제 내용] → [해결 방법] → [결과]

### 남은 문제 및 권장 조치
- [문제 내용] → [권장 조치]

### Context Preservation System 상태
- [정상 / 성능 저하 / 작동 불가]
```

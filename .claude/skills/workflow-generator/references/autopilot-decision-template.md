# Autopilot Decision Log Template

Autopilot 모드에서 `(human)` 단계가 자동 승인될 때 생성하는 Decision Log의 표준 템플릿.

## 파일 위치

```
autopilot-logs/step-{N}-decision.md
```

## 필수 필드

| 필드 | 설명 | 예시 |
|------|------|------|
| `Step` | 워크플로우 단계 번호 | `3` |
| `Checkpoint Type` | 자동 승인된 체크포인트 유형 | `(human) — 인사이트 검토 및 선정` |
| `Decision` | 자동 승인 시 선택한 옵션/행동 | `상위 5개 인사이트 전체 선정` |
| `Rationale` | 선택 근거 (절대 기준 1 기반) | `품질 극대화를 위해 포괄적 선정` |
| `Timestamp` | 결정 시각 | `2026-02-16 14:30:00` |

## 선택 필드

| 필드 | 설명 |
|------|------|
| `Alternatives Considered` | 검토했으나 선택하지 않은 대안과 기각 사유 |
| `Output Verified` | 이전 단계 산출물 검증 결과 (파일 경로, 크기) |
| `SOT Updated` | SOT에 기록한 필드 목록 |
| `Source` | 로그 생성 주체 (Claude / Hook safety net) |
| `pACS Score` | 해당 단계 pACS 점수 (AGENTS.md §5.4) |
| `pACS Weak Dimension` | Min-score 차원 (F/C/L) 및 약점 설명 |

## 표준 템플릿

```markdown
# Decision Log — Step {N}

- **Step**: {N}
- **Checkpoint Type**: (human) — {단계 설명}
- **Decision**: {선택한 옵션/행동}
- **Rationale**: {절대 기준 1 기반 선택 근거}
- **Timestamp**: {YYYY-MM-DD HH:MM:SS}
- **Alternatives Considered**:
  - {대안 1} → {기각 사유}
  - {대안 2} → {기각 사유}
- **Output Verified**: {이전 단계 산출물 검증 결과}
- **SOT Updated**: {갱신한 SOT 필드 목록}
- **pACS Score**: {pACS 점수} → {GREEN|YELLOW|RED}
- **pACS Weak Dimension**: {F|C|L} — {약점 설명}
```

## 구체적 예시

### Slash Command 자동 승인

```markdown
# Decision Log — Step 3

- **Step**: 3
- **Checkpoint Type**: (human) — 인사이트 검토 및 선정
- **Decision**: 상위 5개 인사이트 전체 선정 (포괄성 극대화)
- **Rationale**: 절대 기준 1 — 품질 극대화를 위해 인사이트를 제외하지 않고
  모두 포함하여 Planning Phase에서 우선순위를 정하는 방식 선택.
  특정 인사이트를 미리 제외하면 정보 손실 위험.
- **Timestamp**: 2026-02-16 14:30:00
- **Alternatives Considered**:
  - 상위 3개만 선정 → 정보 손실 위험으로 기각
  - 카테고리별 1개씩 선정 → 카테고리 분류가 불완전하여 기각
- **Output Verified**: step-2 insights-list.md (8,320 bytes) — OK
- **SOT Updated**: auto_approved_steps: [3], current_step: 4
- **pACS Score**: 78 → GREEN
- **pACS Weak Dimension**: F — 인사이트 2건의 데이터 출처 미확인
```

### AskUserQuestion 자동 응답

```markdown
# Decision Log — Step 6

- **Step**: 6
- **Checkpoint Type**: (human) — 개요 검토 및 피드백
- **Decision**: 개요 승인 — 구조와 깊이 모두 충분
- **Rationale**: 절대 기준 1 — 개요가 7개 섹션으로 주제를 포괄적으로 커버하며,
  각 섹션에 구체적 하위 항목이 명시되어 있어 수정 없이 진행해도
  최종 결과물 품질에 기여.
- **Timestamp**: 2026-02-16 15:45:00
- **Alternatives Considered**:
  - 섹션 추가 요청 → 현재 구조가 이미 포괄적이므로 불필요
  - 순서 재배치 → 논리적 흐름이 이미 적절
- **Output Verified**: step-5 article-outlines.md (5,120 bytes) — OK
- **SOT Updated**: auto_approved_steps: [3, 6], current_step: 7
- **pACS Score**: 82 → GREEN
- **pACS Weak Dimension**: C — 섹션 3의 하위 항목 세분화 여지 있음
```

## 런타임 연동

- **Primary**: Claude(Orchestrator)가 `(human)` 단계 처리 시 직접 생성
- **Secondary**: Stop hook(`generate_context_summary.py`)이 누락 감지 시 안전망으로 자동 생성
- Hook이 생성한 로그에는 `Source: Hook safety net` 표기
- Claude가 이미 생성한 로그는 Hook이 덮어쓰지 않음 (`os.path.exists` 확인)

## Translation 단계 처리

`Translation: @translator`인 단계가 자동 승인될 때:

- **Decision**: `@translator` 서브에이전트를 호출하여 영어 산출물을 한국어로 번역
- **Rationale**: 절대 기준 1 — 영어 산출물의 품질을 유지하면서 한국어 접근성 확보
- **추가 검증**: 번역 파일(`*.ko.md`) 존재 + 비어있지 않음 + `translations/glossary.yaml` 갱신 확인
- **SOT 기록**: `outputs.step-N-ko`에 번역 경로 기록

## 절대 기준 준수

| 절대 기준 | 적용 |
|----------|------|
| **절대 기준 1 (품질)** | Rationale 필드에서 품질 극대화 근거 명시 필수 |
| **절대 기준 2 (SOT)** | Decision Log는 `autopilot-logs/`에 저장 (SOT 외부). SOT에는 `auto_approved_steps`만 기록 |
| **절대 기준 3 (CCP)** | N/A — Decision Log는 코드가 아닌 실행 기록 |

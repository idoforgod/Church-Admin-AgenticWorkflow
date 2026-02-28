# Context Injection Patterns for Sub-Agents

워크플로우에서 Sub-agent 또는 Agent Team에 컨텍스트를 전달하는 3가지 패턴.
입력 데이터의 규모와 정보 밀도에 따라 최적의 패턴을 선택한다.

> **선택 기준은 품질이다.** 속도나 토큰 비용이 아닌, 최종 결과물의 품질을 가장 높이는 패턴을 선택한다.

---

## Pattern A: Full Delegation (기본)

에이전트에게 파일 경로만 전달하고, 에이전트가 직접 읽어서 처리.

```markdown
### 2. 자료 분석
- **Agent**: `@analyzer`
- **Input**: `research/collected-data.md` (파일 경로 전달)
- **Task**: 파일을 직접 읽고 핵심 인사이트 도출
- **Output**: `analysis/insights.md`
```

**적합한 경우:**
- 입력 파일 1-3개, 각각 소규모 (< 50KB)
- 에이전트가 전체 맥락을 필요로 하는 경우
- 정보 밀도: O(1) — 핵심 정보가 입력 크기와 무관

**Sub-agent vs Agent Team:**
- **Sub-agent**: 단일 전문가가 맥락을 유지하며 깊이 있게 분석할 때
- **Agent Team**: 해당 없음 (소규모 입력에는 과도한 구조)

---

## Pattern B: Filtered Delegation (RLM Code-based Filtering)

Pre-processing 스크립트가 입력에서 관련 부분만 추출하여 에이전트에게 전달.

```markdown
### 2. 타겟 섹션 분석
- **Pre-processing**: `scripts/extract_sections.py`
  - 입력: `raw-document.md` (200KB)
  - 처리: 정규식으로 "## Results" ~ "## Discussion" 섹션만 추출
  - 출력: `temp/filtered-sections.md` (15KB)
- **Agent**: `@deep-analyzer`
- **Input**: `temp/filtered-sections.md` (정제된 입력)
- **Task**: 추출된 섹션에서 심층 분석 수행
- **Output**: `analysis/section-analysis.md`
- **Post-processing**: `scripts/validate_references.py`
  - 분석 결과의 참조가 원본과 일치하는지 검증
```

**적합한 경우:**
- 대규모 입력 (> 50KB), 그중 관련 부분은 일부
- 에이전트가 특정 패턴/섹션에 집중해야 하는 경우
- 정보 밀도: O(N) — 핵심 정보가 입력 크기에 비례

**Pre-processing 스크립트 설계 (P1 준수):**

| 필터링 유형 | Python에서 처리 | 에이전트에서 처리 |
|-----------|---------------|----------------|
| 날짜/키워드 필터 | O | X |
| 섹션 추출 (정규식) | O | X |
| 중복 제거 (hash) | O | X |
| 포맷 변환 (HTML→MD) | O | X |
| 의미적 관련성 판단 | X | O |
| 품질/중요도 평가 | X | O |

**Sub-agent vs Agent Team:**
- **Sub-agent**: 필터링된 데이터에 대해 깊은 맥락 유지가 중요할 때
- **Agent Team**: 여러 유형의 필터링 결과를 각각 다른 전문가가 분석할 때

---

## Pattern C: Recursive Decomposition (RLM Recursive Sub-call)

Orchestrator가 입력을 N개 청크로 분할하고, 각 청크를 병렬 에이전트에게 위임 후 결과를 병합.

```markdown
### 2. (team) 대규모 문서 분석
- **Pre-processing**: `scripts/chunk_document.py`
  - 입력: `corpus/full-dataset.md` (500KB)
  - 처리: 논리적 단위로 N개 청크 분할 (섹션/챕터 경계 존중)
  - 출력: `temp/chunk-001.md` ~ `temp/chunk-010.md`
- **Team**: `analysis-pipeline`
- **Tasks**:
  - `@analyst-1`: `temp/chunk-001.md` ~ `temp/chunk-003.md` 분석
  - `@analyst-2`: `temp/chunk-004.md` ~ `temp/chunk-006.md` 분석
  - `@analyst-3`: `temp/chunk-007.md` ~ `temp/chunk-010.md` 분석
- **Join**: 모든 분석 완료 후 Team Lead가 결과 병합
- **Post-processing**: `scripts/merge_analyses.py`
  - 청크별 분석 결과를 종합
  - 중복 발견 제거, 교차 참조 연결
- **Output**: `analysis/comprehensive-report.md`
```

**적합한 경우:**
- 초대규모 입력 (> 200KB), 전체를 한 에이전트가 처리 불가
- 분할 가능한 구조 (챕터, 섹션, 레코드 등)
- 정보 밀도: O(N²) — 교차 참조가 필요한 고밀도 데이터

**청크 분할 전략 (P1 준수):**

```python
# scripts/chunk_document.py 설계 원칙
#
# 1. 논리적 경계 존중: 문장/단락 중간에서 자르지 않음
# 2. 오버랩 허용: 청크 간 경계에서 1-2 단락 중복 → 맥락 유실 방지
# 3. 메타데이터 보존: 각 청크에 원본 위치 정보 포함
# 4. 크기 균형: 청크 간 크기 편차 최소화
```

**Sub-agent vs Agent Team:**
- **Sub-agent**: 청크 간 의존성이 강할 때 순차적으로 처리 (맥락 전달 정확성 우선)
- **Agent Team**: 청크가 독립적일 때 병렬 처리 (각 전문가가 자기 영역에 100% 집중)

**SOT 필수 사항 (Agent Team 사용 시):**
- Team Lead만 SOT(state.yaml)에 쓰기
- 각 팀원은 분석 결과를 산출물 파일로 생성
- Team Lead가 산출물을 종합하여 SOT 갱신

---

## 패턴 선택 가이드

```
입력 크기 < 50KB → Pattern A (Full Delegation)
입력 크기 50-200KB + 관련 부분 특정 가능 → Pattern B (Filtered)
입력 크기 > 200KB 또는 분할 필요 → Pattern C (Recursive)
```

> **절대 기준 1 우선**: 위 가이드는 기본 권장사항이다. 입력이 작더라도 Pattern B의 필터링이 에이전트의 분석 정확도를 높인다면 Pattern B를 사용한다. 항상 **최종 결과물의 품질**이 선택 기준이다.

---

## Translation 고려사항 (English-First 실행)

AGENTS.md §5.2에 따라, 워크플로우 실행은 영어로 수행하고 텍스트 산출물은 `@translator` 서브에이전트가 한국어로 번역한다. 각 패턴별 Translation 처리 방식이 다르다.

### 패턴별 Translation 매핑

| 패턴 | Translation 시점 | Glossary 관리 | 비고 |
|------|-----------------|--------------|------|
| **Pattern A** | 단계 완료 후 `@translator` 1회 호출 | 단일 파일 — 충돌 없음 | 가장 단순 |
| **Pattern B** | 필터링된 산출물에 대해 `@translator` 호출 | 단일 파일 — 충돌 없음 | Pre-processing 산출물은 번역 불필요 |
| **Pattern C** | **Join 후** 병합된 최종 산출물에 `@translator` 호출 | `translations/glossary.yaml` 공유 필수 | 아래 상세 참조 |

### Pattern C: 청크 간 용어 일관성

병렬 에이전트가 독립 청크를 처리할 때, 각 에이전트가 같은 도메인 용어를 다르게 번역하면 최종 결과물의 일관성이 깨진다.

**해결 전략: Join-then-Translate**

```markdown
### N. (team) 대규모 문서 분석
- **Team**: `analysis-pipeline`
- **Tasks**: (각 analyst가 영어로 분석 수행)
- **Join**: Team Lead가 영어 결과를 병합 → `analysis/report.md`
- **Translation**: `@translator`
  - Input: `analysis/report.md` (병합된 영어 최종본)
  - Glossary: `translations/glossary.yaml` (도메인 용어 일관성)
  - Output: `analysis/report.ko.md`
```

**핵심 규칙:**
1. 개별 청크를 따로 번역하지 않는다 — 병합 후 1회 번역이 용어 일관성을 보장
2. `translations/glossary.yaml`에 도메인 핵심 용어를 사전 정의하여 `@translator`에 전달
3. 중간 산출물(temp/ 디렉터리)은 번역 대상에서 제외 — 최종 산출물만 번역

**예외: 청크별 번역이 필요한 경우**

드물게 각 청크의 중간 산출물 자체가 사용자에게 전달되는 경우(예: 챕터별 독립 배포), 각 에이전트에게 공유 glossary를 전달하여 일관성을 유지한다:

```markdown
- **Tasks**:
  - `@analyst-1`: chunk-001~003 분석 + `@translator` (glossary 참조)
  - `@analyst-2`: chunk-004~006 분석 + `@translator` (glossary 참조)
- **Glossary**: `translations/glossary.yaml` (모든 에이전트가 동일 glossary 읽기 전용 참조)
```

---

## RLM 이론적 근거

이 3가지 패턴은 Recursive Language Models (MIT CSAIL, 2025) 논문의 핵심 패턴에 대응한다:

| RLM 패턴 | Context Injection 대응 | 핵심 원리 |
|---------|----------------------|----------|
| Direct context access | Pattern A: Full Delegation | 소규모 입력을 직접 처리 |
| Code-based Filtering | Pattern B: Filtered Delegation | 코드로 관련 부분만 선별 후 LM에 전달 |
| Recursive Sub-call + Chunking | Pattern C: Recursive Decomposition | 입력을 분할, 재귀적 sub-LM 호출로 처리 |

> **핵심 원칙**: "프롬프트를 신경망에 직접 넣지 말고, 외부 환경의 객체로 취급하여 프로그래밍적으로 탐색하라."
> 모든 패턴에서 Python(결정론적)이 데이터를 정제하고, AI(확률론적)가 정제된 데이터에서 판단에 집중한다 (P1 원칙).

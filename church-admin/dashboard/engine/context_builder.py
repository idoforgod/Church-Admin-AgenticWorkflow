"""
Context Builder — Claude Code subprocess에 품질 극대화 컨텍스트 주입.

Cold Start 문제 해결:
  각 `claude -p` subprocess는 zero context로 시작한다.
  이전 실행 결과, 현재 SOT 상태, 검증 기준, 도메인 제약을
  모르는 채로 작업하면 품질이 저하된다.

  Context Builder는 `--append-system-prompt`를 통해
  필수 컨텍스트를 사전 주입하여 첫 번째 시도부터
  최고 품질 산출물을 생성하도록 유도한다.

설계 원칙:
  1. 읽기 전용 — state.yaml, dashboard-logs/ 읽기만 (SOT 규율 준수)
  2. 기존 코드 재활용 — sot_watcher.get_current_state() 활용
  3. card_key 기반 라우팅 — 워크플로우별 맞춤 컨텍스트
  4. RLM 패턴 — 부모 시스템의 restore_context.py와 동일한 역할
"""

from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path

import yaml


# ──────────────────────────────────────────────────────────────────
# Validator Script Map — card_key → 검증 스크립트 경로 + 인자
#
# D-7 의도적 중복: post_execution_validator.py VALIDATOR_MAP과 병행 관리
# 한쪽 변경 시 반드시 대응 쪽 동기화 필요
# ──────────────────────────────────────────────────────────────────

VALIDATOR_SCRIPTS: dict[str, dict] = {
    "bulletin": {
        "script": ".claude/hooks/scripts/validate_bulletin.py",
        "args": "--data-dir data/ --members-file data/members.yaml",
    },
    "newcomer": {
        "script": ".claude/hooks/scripts/validate_newcomers.py",
        "args": "--data-dir data/ --members-file data/members.yaml",
    },
    "member": {
        "script": ".claude/hooks/scripts/validate_members.py",
        "args": "--data-dir data/",
    },
    "finance": {
        "script": ".claude/hooks/scripts/validate_finance.py",
        "args": "--data-dir data/",
        "extra": (
            "CRITICAL: Finance has autopilot PERMANENTLY DISABLED.\n"
            "All financial outputs require double human review "
            "(재정 담당 집사 + 담임 목사).\n"
            "Void-only deletion policy — never remove financial records."
        ),
    },
    "schedule": {
        "script": ".claude/hooks/scripts/validate_schedule.py",
        "args": "--data-dir data/",
    },
}

# 규칙 추출 캐시 — 프로세스 수명 동안 유지 (스크립트 파일은 실행 중 변경되지 않음)
_rules_cache: dict[str, str] = {}


def _extract_rules_from_validator(project: Path, card_key: str) -> str:
    """
    검증 스크립트의 docstring에서 규칙 설명을 결정론적으로 추출.

    하드코딩된 규칙 설명 대신 실제 스크립트에서 AST 파싱으로 추출하여
    D-7 드리프트를 원천 제거한다.

    Python AST로 파싱 — LLM 무개입, 결정론적.
    """
    if card_key in _rules_cache:
        return _rules_cache[card_key]

    config = VALIDATOR_SCRIPTS.get(card_key)
    if not config:
        return ""

    script_path = project / config["script"]
    if not script_path.exists():
        return ""

    try:
        source = script_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        docstring = ast.get_docstring(tree)
    except (OSError, SyntaxError):
        return ""

    if not docstring:
        return ""

    # "Rules:" 섹션 추출
    lines: list[str] = []
    in_rules = False
    for line in docstring.split("\n"):
        stripped = line.strip()
        if stripped.startswith("Rules:"):
            in_rules = True
            continue
        if in_rules:
            # 빈 줄이나 "Exit codes:" 등 다른 섹션 시작에서 중단
            if stripped and not stripped.startswith(("Exit", "Usage")):
                lines.append(f"  {stripped}")
            elif not stripped and lines:
                # 빈 줄은 규칙 간 구분으로 유지
                continue
            else:
                break

    if not lines:
        return ""

    # 실행 명령 추가
    run_cmd = f"python3 {config['script']} {config['args']}"
    result_parts = [
        f"P1 Validation Rules (extracted from {Path(config['script']).name}):",
        *lines,
        f"Run: {run_cmd}",
    ]

    # 추가 제약 (finance의 autopilot 등)
    extra = config.get("extra")
    if extra:
        result_parts.append("")
        result_parts.append(extra)

    result = "\n".join(result_parts)
    _rules_cache[card_key] = result
    return result


_VALIDATE_ALL_TEXT = (
    "Run ALL validators:\n"
    "  python3 scripts/validate_all.py\n"
    "All 29+ deterministic rules across 5 scripts must PASS."
)

# ──────────────────────────────────────────────────────────────────
# Domain Rules — card_key별 도메인 제약
# ──────────────────────────────────────────────────────────────────

DOMAIN_RULES: dict[str, str] = {
    "bulletin": (
        "Domain Constraints:\n"
        "- Sole writer for data/bulletin-data.yaml: @bulletin-generator\n"
        "- Output: bulletins/{date}-bulletin.md + bulletins/{date}-worship-order.md\n"
        "- 16 Variable Regions (VR-BUL-01 ~ VR-BUL-16) must ALL be populated\n"
        "- Issue number must be monotonically increasing\n"
        "- Bulletin date MUST be a Sunday\n"
        "- Cross-references: members.yaml (birthday), schedule.yaml (services)\n"
        "- Normalize Korean terms using data/church-glossary.yaml\n"
        "- No placeholder text: every field must contain real data"
    ),
    "newcomer": (
        "Domain Constraints:\n"
        "- Sole writer for data/newcomers.yaml: @newcomer-tracker\n"
        "- 6-stage pipeline: new → visiting → regular → settled → inactive\n"
        "- Stage 5 (settled): handoff to @member-manager for member registration\n"
        "- Assigned member (담당 성도) cross-ref against members.yaml\n"
        "- PII data: newcomers.yaml is .gitignore'd\n"
        "- Soft-delete only: never remove newcomer records"
    ),
    "member": (
        "Domain Constraints:\n"
        "- Sole writer for data/members.yaml: @member-manager\n"
        "- PII data: members.yaml is .gitignore'd\n"
        "- Soft-delete only: set status to 'inactive' or 'transferred'\n"
        "- Family grouping: family_id links household members\n"
        "- 직분 (roles): 목사, 장로, 집사, 권사, 성도, 구역장\n"
        "- Phone format: 010-NNNN-NNNN\n"
        "- _stats must match actual counts"
    ),
    "finance": (
        "Domain Constraints:\n"
        "- Sole writer for data/finance.yaml: @finance-recorder\n"
        "- AUTOPILOT PERMANENTLY DISABLED\n"
        "- Double human review required (재정 담당 집사 + 담임 목사)\n"
        "- Void-only deletion: set void: true, never remove records\n"
        "- All amounts: positive integers in KRW (no decimals)\n"
        "- Offering categories: 십일조, 감사헌금, 특별헌금, 선교헌금, "
        "건축헌금, 주일헌금, 기타\n"
        "- Expense categories: 관리비, 인건비, 사역비, 선교비, 교육비, 기타\n"
        "- Korean numeral conversion for donation receipts\n"
        "- Legal compliance: 소득세법 제34조"
    ),
    "schedule": (
        "Domain Constraints:\n"
        "- Sole writer for data/schedule.yaml: @schedule-manager\n"
        "- Facility conflict detection: no double-booking\n"
        "- Recurring events: weekly services (regular_services)\n"
        "- Special events: one-time or seasonal\n"
        "- Status: scheduled → confirmed → completed → cancelled"
    ),
    "document": (
        "Domain Constraints:\n"
        "- Output: docs/generated/ directory\n"
        "- Document types: baptism_certificate, transfer_letter, "
        "meeting_minutes, official_letter\n"
        "- Template-driven: templates/*.yaml\n"
        "- Cross-references: members.yaml, schedule.yaml"
    ),
}

# ──────────────────────────────────────────────────────────────────
# Sole-Writer Map — 에이전트별 쓰기 권한 (guard_data_files.py 동기)
# ──────────────────────────────────────────────────────────────────

SOLE_WRITER_MAP: dict[str, str] = {
    "bulletin": "bulletin-generator",
    "newcomer": "newcomer-tracker",
    "member": "member-manager",
    "finance": "finance-recorder",
    "schedule": "schedule-manager",
    "document": "document-generator",
}


def build_context(
    card_key: str | None,
    project_dir: str | Path,
    state: dict | None = None,
) -> str:
    """
    워크플로우 실행 전 품질 극대화 컨텍스트를 빌드.

    --append-system-prompt에 전달할 문자열을 반환.
    모든 데이터는 읽기 전용으로 접근 (SOT 규율 준수).

    Args:
        card_key: 워크플로우 카드 키 (bulletin, finance, etc.)
                  None이면 NL 자유 입력 — 범용 컨텍스트만.
        project_dir: church-admin/ 경로
        state: 사전 로드된 state.yaml dict (없으면 직접 읽기)

    Returns:
        시스템 프롬프트에 추가할 컨텍스트 문자열
    """
    project = Path(project_dir)
    sections: list[str] = []

    # state.yaml 로드
    if state is None:
        state = _load_state(project)

    # A. SOT 현재 상태
    sot_section = _inject_sot_summary(state)
    if sot_section:
        sections.append(sot_section)

    # B. 이전 실행 이력
    history_section = _inject_run_history(project, card_key)
    if history_section:
        sections.append(history_section)

    # C. 검증 기준 (AST 동적 추출 — D-7 드리프트 원천봉쇄)
    if card_key:
        verification_section = _inject_verification_criteria(card_key, project)
        if verification_section:
            sections.append(verification_section)

    # D. 도메인 제약
    if card_key:
        domain_section = _inject_domain_rules(card_key, state)
        if domain_section:
            sections.append(domain_section)

    if not sections:
        return ""

    header = (
        "=== CONTEXT INJECTION (Dashboard Context Builder) ===\n"
        "The following context is pre-loaded to maximize output quality.\n"
        "This data is read-only — do not modify state.yaml directly.\n"
    )
    return header + "\n\n".join(sections)


# ──────────────────────────────────────────────────────────────────
# Sub-functions
# ──────────────────────────────────────────────────────────────────


def _inject_sot_summary(state: dict) -> str:
    """A. state.yaml 현재 상태를 요약 주입."""
    if not state:
        return ""

    church = state.get("church", {})
    lines: list[str] = ["--- A. Current SOT State ---"]

    # 교회 기본 정보
    name = church.get("name", "")
    denom = church.get("denomination", "")
    if name:
        lines.append(f"Church: {name}")
    if denom:
        lines.append(f"Denomination: {denom}")

    # 워크플로우 상태
    ws = church.get("workflow_states", {})
    if ws:
        lines.append("\nWorkflow States:")
        for wf_key, wf_state in ws.items():
            status = wf_state.get("status", "?")
            detail_parts: list[str] = [f"status={status}"]

            if wf_key == "bulletin":
                issue = wf_state.get("last_generated_issue")
                due = wf_state.get("next_due_date")
                if issue:
                    detail_parts.append(f"last_issue=#{issue}")
                if due:
                    detail_parts.append(f"next_due={due}")

            elif wf_key == "finance":
                month = wf_state.get("current_month")
                if month:
                    detail_parts.append(f"current_month={month}")

            elif wf_key == "newcomer":
                active = wf_state.get("total_active")
                if active is not None:
                    detail_parts.append(f"active={active}")

            lines.append(f"  {wf_key}: {', '.join(detail_parts)}")

    # 검증 게이트 요약
    vg = church.get("verification_gates", {})
    agg = vg.get("aggregate", {})
    if agg:
        passed = agg.get("total_passed", 0)
        total = agg.get("total_checks", 0)
        last_run = agg.get("last_run", "")
        lines.append(
            f"\nValidation: {passed}/{total} passed"
            + (f" (last: {last_run})" if last_run else "")
        )

    # 에이전트 세션
    agents = church.get("agent_sessions", {})
    active_agents = [
        (name, info)
        for name, info in agents.items()
        if info.get("last_active") is not None
    ]
    if active_agents:
        lines.append("\nRecent Agent Activity:")
        for agent_name, info in active_agents:
            lines.append(
                f"  @{agent_name}: {info.get('last_action', '?')} "
                f"(at {info.get('last_active', '?')})"
            )

    # 설정
    config = church.get("config", {})
    autopilot = config.get("autopilot", {})
    if autopilot:
        lines.append(
            f"\nAutopilot: {'enabled' if autopilot.get('enabled') else 'disabled'}"
            + (", finance_override=false" if not autopilot.get("finance_override") else "")
        )

    return "\n".join(lines)


def _inject_run_history(
    project: Path,
    card_key: str | None,
    max_entries: int = 5,
) -> str:
    """B. dashboard-logs/에서 이전 실행 이력 주입."""
    log_dir = project / "dashboard-logs"
    if not log_dir.exists():
        return ""

    log_files = sorted(log_dir.glob("*.yaml"), reverse=True)
    if not log_files:
        return ""

    lines: list[str] = ["--- B. Previous Run History ---"]
    count = 0

    for log_file in log_files:
        if count >= max_entries:
            break
        try:
            data = yaml.safe_load(log_file.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue
        except (OSError, yaml.YAMLError):
            continue

        # card_key가 지정된 경우 관련 로그만 필터링
        prompt = data.get("prompt", "")
        if card_key and not _prompt_matches_card(prompt, card_key):
            continue

        status = data.get("status", "?")
        started = data.get("started_at", "?")
        error = data.get("error")
        session_id = data.get("session_id")
        tool_count = data.get("tool_count", 0)

        entry = f"  [{str(started)[:16]}] "
        entry += f"status={status}"
        if tool_count:
            entry += f", tools={tool_count}"
        if session_id:
            entry += f", session={session_id[:12]}"
        if error:
            entry += f"\n    error: {error[:200]}"

        lines.append(entry)
        count += 1

    if count == 0:
        return ""

    if count > 0:
        lines.append(
            f"\n  ({count} recent run{'s' if count > 1 else ''} shown, "
            f"newest first)"
        )

    return "\n".join(lines)


def _inject_verification_criteria(card_key: str, project: Path) -> str:
    """
    C. 워크플로우별 검증 기준 주입.

    검증 스크립트의 docstring에서 규칙을 AST로 추출.
    하드코딩 제거 → D-7 드리프트 원천봉쇄.
    """
    if card_key == "validate":
        rules = _VALIDATE_ALL_TEXT
    else:
        rules = _extract_rules_from_validator(project, card_key)

    if not rules:
        return ""

    lines = [
        "--- C. Verification Criteria ---",
        f"Workflow: {card_key}",
        "",
        rules,
        "",
        "IMPORTANT: Run validation AFTER completing the task. "
        "All checks must PASS before reporting completion.",
        "",
        "NOTE: The dashboard will independently run this validator after execution. "
        "Do not skip or fabricate validation results.",
    ]
    return "\n".join(lines)


def _inject_domain_rules(card_key: str, state: dict) -> str:
    """D. 워크플로우별 도메인 제약 주입."""
    rules = DOMAIN_RULES.get(card_key)
    if not rules:
        return ""

    lines = [
        "--- D. Domain Rules ---",
        f"Workflow: {card_key}",
        "",
        rules,
    ]

    # Sole-writer 정보 추가
    writer = SOLE_WRITER_MAP.get(card_key)
    if writer:
        lines.append(f"\nDesignated Agent: @{writer}")
        lines.append(
            "SOT Discipline: state.yaml is read-only. "
            "Only the Orchestrator writes to state.yaml."
        )

    # 데이터 파일 경로 (state.yaml에서)
    data_paths = state.get("church", {}).get("data_paths", {})
    if data_paths and card_key in data_paths:
        lines.append(f"Data File: {data_paths[card_key]}")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────────────────────────


def _load_state(project: Path) -> dict:
    """state.yaml 읽기 (읽기 전용)."""
    state_path = project / "state.yaml"
    try:
        text = state_path.read_text(encoding="utf-8")
        return yaml.safe_load(text) or {}
    except (OSError, yaml.YAMLError):
        return {}


def _prompt_matches_card(prompt: str, card_key: str) -> bool:
    """프롬프트가 특정 card_key와 관련있는지 판별."""
    # 간단한 키워드 매칭 — command_bridge.py의 NL_ROUTES와 동일 도메인
    keyword_map: dict[str, list[str]] = {
        "bulletin": ["주보", "bulletin"],
        "newcomer": ["새신자", "newcomer"],
        "member": ["교인", "member"],
        "finance": ["재정", "finance", "헌금"],
        "schedule": ["일정", "schedule", "행사"],
        "document": ["문서", "document", "증명서"],
        "validate": ["검증", "validate"],
        "status": ["상태", "status"],
    }
    keywords = keyword_map.get(card_key, [card_key])
    prompt_lower = prompt.lower()
    return any(kw in prompt_lower for kw in keywords)

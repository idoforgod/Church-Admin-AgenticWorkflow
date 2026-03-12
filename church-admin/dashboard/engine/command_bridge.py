"""
Command Bridge — 사용자 입력을 기존 명령어 체계로 변환.

핵심 설계 결정:
  자체 프롬프트 템플릿을 관리하지 않는다.

  이유:
    1. .claude/commands/generate-bulletin.md (38줄)가 이미 상세한
       실행 지시를 포함 — 3줄짜리 프롬프트로 대체하면 품질 하락
    2. 프롬프트 중복 시 shotgun surgery — 원본 변경 시 대시보드 동기화 필요
    3. Claude Code는 SKILL.md의 41개 NL 패턴을 자동 인식

  따라서:
    - 카드 선택 → 기존 NL 트리거 패턴을 그대로 전달
    - NL 입력 → 원본 텍스트를 그대로 전달 (SKILL.md가 라우팅)
"""

from __future__ import annotations

import re

# ──────────────────────────────────────────────────────────────────
# 카드 키 → Claude Code에 전달할 프롬프트
#
# 이 문자열은 church-admin/CLAUDE.md 및 SKILL.md에 정의된
# 트리거 패턴과 일치해야 한다.
#
# D-7 의도적 중복: SKILL.md NL 트리거 패턴과 병행 관리
# 한쪽 변경 시 반드시 대응 쪽도 동기화 필요
# 기존 트리거 패턴 (SKILL.md에서 확인):
#   "주보 만들어줘" → weekly-bulletin workflow
#   "새신자 현황"   → newcomer dashboard
#   "재정 보고서"   → monthly-finance-report workflow
#   etc.
# ──────────────────────────────────────────────────────────────────

CARD_PROMPTS: dict[str, str] = {
    "bulletin":   "주보 만들어줘",
    "newcomer":   "새신자 현황 보여줘",
    "member":     "교인 관리",
    "finance":    "재정 보고서 만들어줘",
    "schedule":   "이번 주 일정 보여줘",
    "document":   "문서 발급",
    "validate":   "데이터 검증 실행해줘",
    "status":     "시스템 상태 보여줘",
}

# 카드 메타데이터 (UI 표시용)
CARD_META: dict[str, dict] = {
    "bulletin":   {"label": "주보 생성",     "icon": "📰", "risk": "low"},
    "newcomer":   {"label": "새신자 관리",    "icon": "👋", "risk": "medium"},
    "member":     {"label": "교인 관리",     "icon": "👥", "risk": "medium"},
    "finance":    {"label": "재정 보고서",    "icon": "💰", "risk": "high",
                   "note": "이중 승인 필요"},
    "schedule":   {"label": "일정 관리",     "icon": "📅", "risk": "low"},
    "document":   {"label": "문서 발급",     "icon": "📄", "risk": "medium"},
    "validate":   {"label": "데이터 검증",    "icon": "✅", "risk": "low"},
    "status":     {"label": "시스템 상태",    "icon": "🔧", "risk": "low"},
}

# HitL 워크플로우 1단계(초안) 프롬프트
# D-7 의도적 중복: SKILL.md NL 트리거 패턴과 병행 관리
# 한쪽 변경 시 반드시 대응 쪽 동기화 필요
HITL_DRAFT_PROMPTS: dict[str, str] = {
    "finance": (
        "재정 보고서 초안을 작성해줘. "
        "보고서 파일을 생성하되, 최종 SOT 갱신과 확정 처리는 하지 마세요. "
        "초안 작성까지만 진행하세요."
    ),
}


# NL 패턴 → 카드 키 (라우팅 힌트용 — 실제 실행은 SKILL.md가 수행)
NL_ROUTES: list[tuple[str, str]] = [
    (r"주보.*만들|주보.*생성|bulletin",            "bulletin"),
    (r"새신자.*등록|새신자.*현황|새신자.*관리",       "newcomer"),
    (r"교인.*검색|교인.*등록|교인.*관리|교인.*수정",   "member"),
    (r"재정.*보고|재정.*리포트|헌금.*내역",           "finance"),
    (r"일정|스케줄|행사.*등록|시설.*예약",            "schedule"),
    (r"증명서|문서.*발급|공문|이명증서|회의록",        "document"),
    (r"검증|validate|유효성",                       "validate"),
    (r"시스템.*상태|system.*status|상태.*확인",      "status"),
    (r"생일|축하.*대상",                            "member"),
    (r"기부금.*영수증|영수증.*발급",                  "finance"),
    (r"정착.*처리|settlement",                      "newcomer"),
    (r"파일.*가져오기|엑셀.*가져오기|사진.*분석",       "newcomer"),
]


def build_prompt(user_input: str, params: dict | None = None) -> str:
    """
    사용자 입력 → Claude Code에 전달할 프롬프트.

    카드 선택: CARD_PROMPTS에서 매핑된 NL 트리거 반환
    NL 입력:  원본 텍스트를 그대로 반환 (SKILL.md가 정밀 라우팅)

    Args:
        user_input: 카드 키 ("bulletin") 또는 자연어 ("주보 만들어줘")
        params: 추가 파라미터 (날짜, 이름 등)

    Returns:
        Claude Code -p에 전달할 프롬프트 문자열
    """
    # 카드 선택인 경우
    if user_input in CARD_PROMPTS:
        prompt = CARD_PROMPTS[user_input]
        if params:
            param_str = ", ".join(f"{k}: {v}" for k, v in params.items())
            prompt = f"{prompt} ({param_str})"
        return prompt

    # NL 입력 — 그대로 전달 (SKILL.md가 라우팅)
    # 파라미터가 있으면 추가
    if params:
        param_str = ", ".join(f"{k}: {v}" for k, v in params.items())
        return f"{user_input} ({param_str})"

    return user_input


def detect_card_key(user_input: str) -> str | None:
    """
    NL 입력에서 카드 키를 감지 (UI 하이라이트 용도).

    실제 실행 라우팅은 하지 않음 — SKILL.md에 위임.
    대시보드에서 어떤 카드가 활성화되었는지 표시하기 위한 힌트만 제공.
    """
    text = user_input.lower().strip()
    for pattern, card_key in NL_ROUTES:
        if re.search(pattern, text, re.IGNORECASE):
            return card_key
    return None


def is_hitl_workflow(card_key: str) -> bool:
    """HitL 게이트가 필요한 워크플로우인지 판별."""
    meta = CARD_META.get(card_key, {})
    return meta.get("risk") == "high"


def get_hitl_draft_prompt(card_key: str) -> str | None:
    """HitL 워크플로우의 1단계(초안) 프롬프트 반환. 비-HitL이면 None."""
    return HITL_DRAFT_PROMPTS.get(card_key)


def get_card_list() -> list[dict]:
    """UI에 표시할 카드 목록 반환."""
    return [
        {"key": key, **meta}
        for key, meta in CARD_META.items()
    ]

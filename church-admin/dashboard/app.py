"""
Church Admin Dashboard — Streamlit 메인 앱.

설계 원칙:
  1. 대시보드는 자체 상태를 갖지 않는다 (SOT = state.yaml)
  2. 진행 감지는 SOT 폴링 (텍스트 파싱 금지 — P1 결정론)
  3. 프롬프트는 기존 명령어 체계에 위임 (shotgun surgery 방지)
  4. Claude Code는 백그라운드 subprocess로 실행 (UI 블로킹 방지)
  5. 기존 코드 수정 0건 — dashboard/만 신규 추가

실행:
    cd church-admin
    streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import streamlit as st

# dashboard/ 를 모듈로 import 하기 위해 경로 추가
DASHBOARD_DIR = Path(__file__).parent
PROJECT_DIR = DASHBOARD_DIR.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from dashboard.engine.claude_runner import ClaudeRunner
from dashboard.engine.sot_watcher import SOTWatcher
from dashboard.engine.command_bridge import (
    build_prompt,
    detect_card_key,
    get_card_list,
    get_hitl_draft_prompt,
    is_hitl_workflow,
)
from dashboard.engine.context_builder import build_context
from dashboard.engine.post_execution_validator import validate_after_execution
from dashboard.components.status_panel import render_status_panel
from dashboard.components.progress_panel import (
    render_progress_panel,
    render_result_summary,
)
from dashboard.components.result_panel import render_result_panel
from dashboard.components.hitl_panel import render_hitl_dialog

# ─── 페이지 설정 ───
st.set_page_config(
    page_title="교회 행정 시스템",
    page_icon="⛪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── 세션 상태 초기화 ───
# Streamlit은 위젯 상호작용마다 전체 스크립트를 재실행.
# 이 객체들은 st.session_state에 보관하여 재실행 간 유지.
if "runner" not in st.session_state:
    st.session_state.runner = ClaudeRunner(PROJECT_DIR)
if "watcher" not in st.session_state:
    st.session_state.watcher = SOTWatcher(PROJECT_DIR)
if "sot_events" not in st.session_state:
    st.session_state.sot_events = []
if "active_card" not in st.session_state:
    st.session_state.active_card = None
if "hitl_state" not in st.session_state:
    # None | {"step": "waiting", "session_id": "...", "title": "..."}
    st.session_state.hitl_state = None
if "pending_hitl" not in st.session_state:
    # None | {"card_key": "...", "label": "..."} — HitL 전환 대기
    st.session_state.pending_hitl = None
if "last_card_key" not in st.session_state:
    # 마지막 실행한 card_key (post-execution 검증용)
    st.session_state.last_card_key = None
if "validation_result" not in st.session_state:
    # PostExecutionValidator 결과 (할루시네이션 봉쇄)
    st.session_state.validation_result = None

runner: ClaudeRunner = st.session_state.runner
watcher: SOTWatcher = st.session_state.watcher


# ═══════════════════════════════════════════════════════════════
#  HEADER: 교회 이름 + 모드 선택
# ═══════════════════════════════════════════════════════════════

# 상태 요약 캐싱 — SOT 변경 시에만 subprocess 재호출 (HIGH-2 수정)
if "summary_mtime" not in st.session_state:
    st.session_state.summary_mtime = -1.0
    st.session_state.summary_cache = {}

try:
    _cur_mtime = watcher.state_path.stat().st_mtime
except OSError:
    _cur_mtime = 0.0

if _cur_mtime != st.session_state.summary_mtime:
    st.session_state.summary_cache = watcher.get_status_summary()
    st.session_state.summary_mtime = _cur_mtime

summary = st.session_state.summary_cache
church_name = summary.get("church_name", "교회 행정 시스템")

header_col1, header_col2 = st.columns([5, 2])
with header_col1:
    st.title(f"⛪ {church_name}")
with header_col2:
    mode = st.selectbox(
        "실행 모드",
        ["표준", "ULW (최대 철저함)"],
        label_visibility="collapsed",
        disabled=runner.is_running,
    )

st.divider()


# ═══════════════════════════════════════════════════════════════
#  SECTION 1: 현재 상태 요약
# ═══════════════════════════════════════════════════════════════

render_status_panel(summary)
st.divider()


# ═══════════════════════════════════════════════════════════════
#  SECTION 2: 기능 카드 + 명령 입력 (실행 중이 아닐 때만)
# ═══════════════════════════════════════════════════════════════

if not runner.is_running and runner.status != "completed" and not st.session_state.hitl_state:

    st.subheader("기능 선택")

    cards = get_card_list()
    cols = st.columns(4)

    for i, card in enumerate(cards):
        with cols[i % 4]:
            label = f"{card['icon']} {card['label']}"
            if card.get("note"):
                label += f"\n({card['note']})"

            if st.button(
                label,
                key=f"card_{card['key']}",
                use_container_width=True,
            ):
                st.session_state.active_card = card["key"]
                st.session_state.sot_events = []

    st.divider()

    # NL 명령 입력
    nl_input = st.chat_input("명령어를 입력하세요 (예: 주보 만들어줘)")

    # ── 실행 트리거 ──
    trigger = None

    if st.session_state.active_card:
        trigger = st.session_state.active_card
        st.session_state.active_card = None

    if nl_input:
        trigger = nl_input

    if trigger:
        prompt = build_prompt(trigger)

        # ULW 모드 처리 — 프롬프트에 직접 포함하여 detect_ulw_mode() 감지 보장
        ulw_active = mode.startswith("ULW") or (
            isinstance(trigger, str) and "ulw" in trigger.lower()
        )
        if ulw_active:
            prompt = f"ulw {prompt}"

        # HitL 워크플로우 판별
        card_key = trigger if trigger in [c["key"] for c in cards] else detect_card_key(trigger or "")
        hitl = card_key is not None and is_hitl_workflow(card_key)

        # HitL이면 초안 전용 프롬프트 사용 (CRITICAL-1+2 수정)
        if hitl:
            draft_prompt = get_hitl_draft_prompt(card_key)
            if draft_prompt:
                prompt = f"ulw {draft_prompt}" if ulw_active else draft_prompt
            st.session_state.pending_hitl = {
                "card_key": card_key,
                "label": next(
                    (c["label"] for c in cards if c["key"] == card_key),
                    card_key,
                ),
            }

        # card_key 보존 (post-execution 검증용)
        st.session_state.last_card_key = card_key
        st.session_state.validation_result = None

        # 품질 극대화 컨텍스트 빌드 (Cold Start 해결)
        context = build_context(
            card_key=card_key,
            project_dir=PROJECT_DIR,
            state=watcher.get_current_state(),
        )

        try:
            runner.start(
                prompt=prompt,
                system_prompt_extra=context if context else None,
            )
            st.session_state.sot_events = []
            st.rerun()
        except RuntimeError as e:
            st.error(str(e))


# ═══════════════════════════════════════════════════════════════
#  SECTION 3: 진행 상황 (실행 중일 때)
# ═══════════════════════════════════════════════════════════════

if runner.is_running:
    # SOT 폴링으로 진행 이벤트 수집
    new_events = watcher.poll()
    st.session_state.sot_events.extend(new_events)

    render_progress_panel(
        sot_events=st.session_state.sot_events,
        stream_state=runner.stream_state,
        is_running=True,
    )

    # 취소 버튼
    if st.button("🛑 작업 취소", type="secondary"):
        runner.cancel()
        st.session_state.pending_hitl = None
        st.rerun()

    # 2초 후 재폴링
    time.sleep(2)
    st.rerun()


# ═══════════════════════════════════════════════════════════════
#  SECTION 4: 결과 표시 (완료/실패 후)
# ═══════════════════════════════════════════════════════════════

if not runner.is_running and runner.status in ("completed", "failed"):

    # 최종 SOT 이벤트 수집
    final_events = watcher.poll()
    st.session_state.sot_events.extend(final_events)

    # ── Post-Execution 독립 검증 (할루시네이션 봉쇄) ──
    # LLM이 아닌 Python이 직접 P1 검증 실행
    if runner.status == "completed" and st.session_state.validation_result is None:
        vr = validate_after_execution(
            card_key=st.session_state.last_card_key,
            project_dir=PROJECT_DIR,
            started_at=runner.started_at,
        )
        # vr이 None이면 검증 불필요 — False sentinel로 반복 실행 방지
        st.session_state.validation_result = vr if vr is not None else False

    # HitL 전환 체크 — 완료 직후, 승인 대기로 전환 (CRITICAL-1+2 수정)
    pending = st.session_state.get("pending_hitl")
    if runner.status == "completed" and pending:
        st.session_state.hitl_state = {
            "step": "waiting",
            "session_id": runner.stream_state.session_id,
            "title": pending.get("label", "결과 검토"),
            "card_key": pending.get("card_key", ""),
        }
        st.session_state.pending_hitl = None
        # 캐시 무효화 — HitL 패널에서 최신 상태 표시
        st.session_state.summary_mtime = -1.0
        st.rerun()

    # 일반 완료 (비-HitL 또는 HitL 승인 완료 후)
    if not st.session_state.hitl_state:
        # 실패 시 pending_hitl 정리
        if runner.status == "failed" and st.session_state.get("pending_hitl"):
            st.session_state.pending_hitl = None

        # 결과 요약
        render_result_summary(
            sot_events=st.session_state.sot_events,
            stream_state=runner.stream_state,
            status=runner.status,
            error=runner.error,
        )

        # P1 검증 결과 (기계적 신호 — 할루시네이션 봉쇄)
        vr = st.session_state.validation_result
        if vr:
            if vr.all_passed:
                st.success(f"P1 독립 검증 통과: {vr.summary}")
            else:
                st.error(f"P1 독립 검증 실패: {vr.summary}")
                with st.expander("검증 상세 결과", expanded=True):
                    for check in vr.checks:
                        if check.passed:
                            st.markdown(f"PASS: **{check.name}** — {check.details}")
                        else:
                            st.markdown(f"FAIL: **{check.name}** — {check.details}")
                            for err in check.errors[:5]:
                                st.markdown(f"  - {err}")

        # 산출물 파일 렌더링
        if runner.status == "completed":
            render_result_panel(
                project_dir=str(PROJECT_DIR),
                started_at=runner.started_at,
                fallback_text=runner.stream_state.result_text,
            )

        st.divider()

        # 새 작업 시작 버튼
        if st.button("새 작업 시작", type="primary"):
            st.session_state.runner = ClaudeRunner(PROJECT_DIR)
            st.session_state.sot_events = []
            st.session_state.active_card = None
            st.session_state.hitl_state = None
            st.session_state.pending_hitl = None
            st.session_state.last_card_key = None
            st.session_state.validation_result = None
            st.session_state.summary_mtime = -1.0
            st.rerun()


# ═══════════════════════════════════════════════════════════════
#  SECTION 5: HitL 승인 대기 상태
# ═══════════════════════════════════════════════════════════════

if st.session_state.hitl_state and st.session_state.hitl_state.get("step") == "waiting":
    hitl = st.session_state.hitl_state

    # 산출물 파일 찾기
    output_files = []
    for dir_name in ["output/finance-reports", "docs/generated"]:
        d = PROJECT_DIR / dir_name
        if d.exists():
            output_files.extend(sorted(d.rglob("*.md"))[-3:])

    decision = render_hitl_dialog(
        title=hitl.get("title", "승인 필요"),
        result_text=runner.stream_state.result_text,
        output_files=output_files,
        approval_stage=hitl.get("stage", ""),
        validation_result=st.session_state.validation_result,
    )

    if decision:
        if decision == "approve":
            # 승인 → Claude에게 확정 지시 (--resume)
            session_id = runner.stream_state.session_id
            st.session_state.hitl_state = None
            st.session_state.runner = ClaudeRunner(PROJECT_DIR)

            runner_new = st.session_state.runner
            runner_new.start(
                prompt="승인되었습니다. 최종 확정 처리를 진행하세요.",
                resume_session=session_id if session_id else None,
            )
            st.rerun()

        elif decision == "reject":
            st.session_state.hitl_state = None
            st.session_state.runner = ClaudeRunner(PROJECT_DIR)
            st.warning("작업이 반려되었습니다.")
            st.rerun()

        elif decision.startswith("revise:"):
            comment = decision[7:]
            session_id = runner.stream_state.session_id
            st.session_state.hitl_state = None
            st.session_state.runner = ClaudeRunner(PROJECT_DIR)

            runner_new = st.session_state.runner
            runner_new.start(
                prompt=f"수정 요청: {comment}. 보고서를 수정해주세요.",
                resume_session=session_id if session_id else None,
            )
            st.rerun()


# ═══════════════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════════════


@st.cache_data(ttl=300)
def _get_claude_version() -> str:
    """Claude Code 버전 조회 (5분 캐시)."""
    import subprocess as _sp
    try:
        result = _sp.run(
            ["claude", "--version"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip().split()[-1] if result.returncode == 0 else "?"
    except Exception:
        return "?"


st.divider()
footer_col1, footer_col2 = st.columns(2)
with footer_col1:
    st.caption("교회 행정 시스템 Dashboard v0.1")
with footer_col2:
    st.caption(f"SOT: state.yaml | 실행 엔진: Claude Code CLI v{_get_claude_version()}")

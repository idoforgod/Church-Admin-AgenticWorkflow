"""
Progress Panel — 작업 진행 상황 표시 컴포넌트.

두 가지 소스의 진행 정보를 결합:
  1. SOT 이벤트 (주): state.yaml 변경에서 파생 — 결정론적
  2. 도구 이벤트 (보조): stream-json tool_use — 활동 표시용
"""

from __future__ import annotations

import streamlit as st

from dashboard.engine.sot_watcher import ProgressEvent
from dashboard.engine.stream_parser import StreamState, get_latest_tool_display


def render_progress_panel(
    sot_events: list[ProgressEvent],
    stream_state: StreamState,
    is_running: bool,
):
    """
    진행 상황을 SOT 이벤트 + 도구 활동으로 표시.

    Args:
        sot_events: SOTWatcher.poll()로 누적된 이벤트
        stream_state: ClaudeRunner.stream_state
        is_running: 현재 실행 중인지
    """
    with st.container(border=True):
        if is_running:
            st.subheader("⏳ 작업 진행 중...")
        else:
            st.subheader("📋 작업 기록")

        # SOT 이벤트 표시 (주 진행 표시)
        if sot_events:
            for evt in sot_events:
                icon = _category_icon(evt.category)
                st.write(f"{icon} {evt.description}")
        elif is_running:
            st.caption("SOT 갱신 대기 중...")

        # 도구 활동 표시 (보조 — SOT 갱신 사이)
        if is_running:
            tool_display = get_latest_tool_display(stream_state)
            if tool_display:
                st.caption(f"🔧 현재: {tool_display}")

            tool_count = len(stream_state.tool_events)
            if tool_count > 0:
                st.caption(f"도구 호출 {tool_count}회 수행됨")


def render_result_summary(
    sot_events: list[ProgressEvent],
    stream_state: StreamState,
    status: str,
    error: str,
):
    """
    작업 완료 후 결과 요약 표시.

    Args:
        sot_events: 전체 SOT 이벤트
        stream_state: 최종 스트림 상태
        status: "completed" | "failed"
        error: 에러 메시지 (failed인 경우)
    """
    with st.container(border=True):
        if status == "completed":
            st.subheader("✅ 작업 완료")
        elif status == "failed":
            st.subheader("❌ 작업 실패")
            if error:
                st.error(error[:500])
        else:
            st.subheader(f"작업 상태: {status}")

        # SOT 이벤트 타임라인
        if sot_events:
            for evt in sot_events:
                icon = _category_icon(evt.category)
                st.write(f"{icon} {evt.description}")

        # 도구 사용 통계
        tool_count = len(stream_state.tool_events)
        if tool_count > 0:
            st.caption(f"총 {tool_count}회 도구 호출")


def _category_icon(category: str) -> str:
    """이벤트 카테고리별 아이콘."""
    return {
        "workflow_status": "📊",
        "validation": "✅",
        "output": "📄",
        "agent": "🤖",
    }.get(category, "•")

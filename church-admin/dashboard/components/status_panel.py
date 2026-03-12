"""
Status Panel — 교회 현재 상태 표시 컴포넌트.

show_menu.py의 JSON 출력을 Streamlit 위젯으로 렌더링.
데이터 수집 로직을 중복 구현하지 않음 — show_menu.py에 위임.
"""

from __future__ import annotations

import streamlit as st


def render_status_panel(summary: dict):
    """
    교회 현재 상태를 metric 카드와 경고로 표시.

    Args:
        summary: SOTWatcher.get_status_summary()의 반환값
                 (show_menu.py JSON 또는 fallback)
    """
    if "error" in summary and not summary.get("status"):
        st.error(f"상태 조회 실패: {summary['error']}")
        return

    status = summary.get("status", {})

    # 메트릭 카드 행
    col1, col2, col3, col4 = st.columns(4)

    members = status.get("members", {})
    newcomers = status.get("newcomers", {})
    bulletin = status.get("bulletin", {})
    validation = status.get("validation", {})

    with col1:
        active = members.get("active", "?")
        total = members.get("total", "?")
        st.metric("교인", f"{active}명", delta=f"전체 {total}명")

    with col2:
        nc_active = newcomers.get("active", "?")
        overdue_count = len(newcomers.get("overdue", []))
        delta_text = f"{overdue_count}명 후속 필요" if overdue_count else "정상"
        delta_color = "inverse" if overdue_count else "normal"
        st.metric(
            "새신자", f"{nc_active}명",
            delta=delta_text, delta_color=delta_color,
        )

    with col3:
        last_issue = bulletin.get("last_issue", "?")
        last_date = bulletin.get("last_date", "")
        has_next = bulletin.get("has_next_bulletin", False)
        delta_text = "다음 주보 준비됨" if has_next else "다음 주보 미생성"
        delta_color = "normal" if has_next else "inverse"
        st.metric(
            "최근 주보", f"제{last_issue}호",
            delta=delta_text, delta_color=delta_color,
        )

    with col4:
        passed = validation.get("total_passed", 0)
        total_checks = validation.get("total_checks", 0)
        all_pass = (passed == total_checks and total_checks > 0)
        st.metric(
            "데이터 검증", f"{passed}/{total_checks}",
            delta="전체 통과" if all_pass else "확인 필요",
            delta_color="normal" if all_pass else "inverse",
        )

    # 경고 표시
    alerts = summary.get("alerts", [])
    if alerts:
        for alert in alerts:
            st.warning(f"⚠ {alert.get('message_ko', alert.get('message_en', ''))}")

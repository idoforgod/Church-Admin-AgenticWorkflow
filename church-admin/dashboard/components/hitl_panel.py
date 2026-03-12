"""
HitL Panel — Human-in-the-Loop 승인 UI 컴포넌트.

HitL이 필요한 워크플로우(재정 보고서 등)에서
단계 사이에 사용자 승인을 받기 위한 UI.

설계 결정:
  HitL은 워크플로우 분할 실행으로 처리.
  1단계: Claude가 보고서 생성 (확정 안 함)
  2단계: 대시보드에서 사용자 검토 + 승인
  3단계: Claude가 확정 처리 (--resume로 이어서)

할루시네이션 봉쇄:
  P1 검증 결과를 기계적 신호로 표시하여,
  사용자가 검증 없이 산출물만 보고 승인하는 것을 방지.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from dashboard.engine.post_execution_validator import ValidationResult


def render_hitl_dialog(
    title: str,
    result_text: str,
    output_files: list[Path],
    approval_stage: str = "",
    validation_result: "ValidationResult | None" = None,
) -> str | None:
    """
    승인 다이얼로그 표시.

    Args:
        title: 승인 제목 (예: "재정 보고서 검토")
        result_text: Claude 실행 결과 텍스트 (요약)
        output_files: 생성된 산출물 파일 경로
        approval_stage: 승인 단계 표시 (예: "1/2 (재정 담당 집사)")
        validation_result: P1 검증 결과 (기계적 검증 신호)

    Returns:
        "approve" | "reject" | "revise:코멘트" | None (대기 중)
    """
    with st.container(border=True):
        st.subheader(f"승인 필요: {title}")

        if approval_stage:
            st.caption(f"승인 단계: {approval_stage}")

        # ── P1 검증 결과 (기계적 신호) ──
        if validation_result:
            _render_validation_signal(validation_result)

        st.divider()

        # 결과 요약 표시
        if result_text:
            st.markdown(result_text[:3000])

        # 산출물 미리보기
        for f in output_files:
            if f.exists():
                with st.expander(f"{f.name}"):
                    try:
                        content = f.read_text(encoding="utf-8")
                        st.markdown(content[:5000])
                    except (OSError, UnicodeDecodeError):
                        st.warning("파일을 읽을 수 없습니다.")

        st.divider()

        # 승인/반려 버튼
        # P1 FAIL이면 경고 표시 (버튼은 비활성화하지 않음 — 사용자 최종 판단)
        approve_disabled = False
        if validation_result and not validation_result.all_passed:
            st.warning(
                "P1 검증에 실패한 항목이 있습니다. "
                "승인 전 검증 결과를 확인하세요."
            )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "승인",
                type="primary",
                use_container_width=True,
                key="hitl_approve",
                disabled=approve_disabled,
            ):
                return "approve"

        with col2:
            if st.button(
                "반려",
                use_container_width=True,
                key="hitl_reject",
            ):
                return "reject"

        # 수정 요청
        comment = st.text_area(
            "수정 요청 사항 (선택)",
            placeholder="수정이 필요한 부분을 설명해주세요...",
            key="hitl_comment",
        )
        if st.button("수정 요청", use_container_width=True, key="hitl_revise"):
            if comment.strip():
                return f"revise:{comment.strip()}"
            else:
                st.warning("수정 요청 사항을 입력해주세요.")

    return None


def _render_validation_signal(validation_result: "ValidationResult"):
    """
    P1 검증 결과를 기계적 신호로 렌더링.

    LLM 출력이 아닌 Python 검증 스크립트 실행 결과이므로
    결정론적 판정 — 할루시네이션 불가.
    """
    if validation_result.all_passed:
        st.success(f"P1 검증 통과: {validation_result.summary}")
    else:
        st.error(f"P1 검증 실패: {validation_result.summary}")

    with st.expander("검증 상세 결과", expanded=not validation_result.all_passed):
        for check in validation_result.checks:
            if check.passed:
                st.markdown(f"  PASS: **{check.name}** — {check.details}")
            else:
                st.markdown(f"  FAIL: **{check.name}** — {check.details}")
                for err in check.errors[:5]:
                    st.markdown(f"    - {err}")

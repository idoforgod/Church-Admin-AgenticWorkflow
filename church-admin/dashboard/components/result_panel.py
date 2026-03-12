"""
Result Panel — 최종 산출물 렌더링 컴포넌트.

산출물 파일을 직접 읽어서 마크다운으로 렌더링.
Claude의 텍스트 출력이 아닌 실제 파일을 표시.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import streamlit as st


# 산출물이 생성될 수 있는 디렉터리
OUTPUT_DIRS = [
    "bulletins",
    "output",
    "output/finance-reports",
    "docs/generated",
    "certificates",
    "reports",
]


def render_result_panel(
    project_dir: str | Path,
    started_at: str,
    fallback_text: str = "",
):
    """
    실행 이후 생성/수정된 산출물 파일을 찾아서 렌더링.

    Args:
        project_dir: church-admin/ 경로
        started_at: 실행 시작 시각 (ISO format) — 이후 파일만 표시
        fallback_text: 산출물 파일이 없을 때 표시할 텍스트 (stream result)
    """
    project = Path(project_dir)
    start_ts = _parse_iso(started_at)

    recent_files = _find_recent_outputs(project, start_ts)

    if recent_files:
        st.subheader("📄 생성된 산출물")

        for file_path in recent_files:
            rel_path = file_path.relative_to(project)
            file_size = file_path.stat().st_size

            with st.expander(
                f"📄 {rel_path} ({_human_size(file_size)})",
                expanded=(len(recent_files) <= 2),
            ):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    st.markdown(content)
                except (OSError, UnicodeDecodeError):
                    st.warning("파일을 읽을 수 없습니다.")

    elif fallback_text:
        st.subheader("📋 실행 결과")
        st.markdown(fallback_text[:5000])

    else:
        st.info("산출물 파일이 감지되지 않았습니다.")


def _find_recent_outputs(
    project: Path,
    start_ts: float,
) -> list[Path]:
    """실행 시작 이후에 생성/수정된 산출물 파일 목록."""
    recent: list[Path] = []

    for dir_name in OUTPUT_DIRS:
        output_dir = project / dir_name
        if not output_dir.exists():
            continue

        for f in output_dir.rglob("*"):
            if not f.is_file():
                continue
            # 마크다운, YAML, 텍스트 파일만
            if f.suffix not in (".md", ".yaml", ".yml", ".txt"):
                continue
            try:
                if f.stat().st_mtime > start_ts:
                    recent.append(f)
            except OSError:
                continue

    return sorted(recent, key=lambda p: p.stat().st_mtime, reverse=True)


def _parse_iso(iso_str: str) -> float:
    """ISO 타임스탬프를 Unix timestamp로 변환."""
    if not iso_str:
        return 0.0
    try:
        return datetime.fromisoformat(iso_str).timestamp()
    except (ValueError, TypeError):
        return 0.0


def _human_size(size_bytes: int) -> str:
    """바이트 수를 사람이 읽기 쉬운 형태로."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

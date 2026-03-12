"""
Stream Parser — stream-json 이벤트에서 도구 사용 이벤트를 추출.

Claude Code의 --output-format stream-json 출력에서
tool_use 이벤트만 추출하여 보조 진행 감지에 사용.

주 진행 감지는 SOTWatcher (state.yaml 폴링)가 담당.
이 파서는 보조 수단 — SOT 갱신 사이의 "진행 중" 표시용.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ToolEvent:
    """Claude Code가 호출한 도구 이벤트."""
    tool_name: str
    timestamp: str
    input_preview: str = ""  # 도구 입력 일부 (파일 경로 등)


@dataclass
class StreamState:
    """stream-json 파싱 누적 상태."""
    session_id: str = ""
    result_text: str = ""
    tool_events: list[ToolEvent] = field(default_factory=list)
    is_complete: bool = False
    exit_code: int | None = None
    _current_tool: str = ""
    _current_input_json: str = ""


def parse_line(line: str, state: StreamState) -> StreamState:
    """
    stream-json의 한 줄을 파싱하여 상태를 갱신.

    Args:
        line: stdout에서 읽은 한 줄 (JSON)
        state: 누적 상태 객체

    Returns:
        갱신된 state (동일 객체)
    """
    line = line.strip()
    if not line:
        return state

    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return state

    event_type = event.get("type", "")

    # 세션 초기화
    if event_type == "system" and event.get("subtype") == "init":
        state.session_id = event.get("session_id", "")
        return state

    # 스트리밍 이벤트
    if event_type == "stream_event":
        inner = event.get("event", {})
        inner_type = inner.get("type", "")

        # 도구 사용 시작
        if inner_type == "content_block_start":
            block = inner.get("content_block", {})
            if block.get("type") == "tool_use":
                state._current_tool = block.get("name", "")
                state._current_input_json = ""

        # 도구 입력 스트리밍 (파일 경로 등 추출)
        elif inner_type == "content_block_delta":
            delta = inner.get("delta", {})
            if delta.get("type") == "input_json_delta":
                state._current_input_json += delta.get("partial_json", "")

        # 도구 사용 종료
        elif inner_type == "content_block_stop":
            if state._current_tool:
                # 도구 입력에서 파일 경로 추출 시도
                input_preview = _extract_file_path(state._current_input_json)
                state.tool_events.append(ToolEvent(
                    tool_name=state._current_tool,
                    timestamp=datetime.now().isoformat(),
                    input_preview=input_preview,
                ))
                state._current_tool = ""
                state._current_input_json = ""

    # 최종 결과
    if event_type == "result":
        state.result_text = event.get("result", "")
        state.is_complete = True

    return state


def _extract_file_path(input_json_str: str) -> str:
    """도구 입력 JSON에서 file_path 또는 command를 추출."""
    if not input_json_str:
        return ""
    try:
        data = json.loads(input_json_str)
        # Edit/Write/Read: file_path
        if "file_path" in data:
            return data["file_path"]
        # Bash: command (첫 80자)
        if "command" in data:
            cmd = data["command"]
            return cmd[:80] + ("..." if len(cmd) > 80 else "")
        # Grep/Glob: pattern
        if "pattern" in data:
            return data["pattern"]
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    return ""


def get_latest_tool_display(state: StreamState) -> str | None:
    """가장 최근 도구 이벤트를 사람이 읽을 수 있는 형태로 반환."""
    if not state.tool_events:
        return None

    latest = state.tool_events[-1]
    tool = latest.tool_name
    preview = latest.input_preview

    # 한국어 도구 이름 매핑
    tool_labels = {
        "Read": "파일 읽기",
        "Write": "파일 쓰기",
        "Edit": "파일 수정",
        "Bash": "명령 실행",
        "Glob": "파일 검색",
        "Grep": "내용 검색",
        "Agent": "에이전트 호출",
        "Skill": "스킬 실행",
    }

    label = tool_labels.get(tool, tool)
    if preview:
        return f"{label}: {preview}"
    return label

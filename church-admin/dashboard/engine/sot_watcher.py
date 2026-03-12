"""
SOT Watcher — state.yaml 폴링 기반 결정론적 진행 감지.

설계 원칙:
  - Claude 텍스트 출력을 파싱하지 않음 (비결정론적 → P1 위반)
  - state.yaml의 구조화된 필드 변경만 감시 (결정론적)
  - show_menu.py를 subprocess로 호출하여 상태 요약 (기존 코드 재활용)

사용 패턴:
    watcher = SOTWatcher("/path/to/church-admin")
    events = watcher.poll()  # state.yaml 변경 시 이벤트 반환
    summary = watcher.get_status_summary()  # show_menu.py JSON
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml


@dataclass
class ProgressEvent:
    """SOT 변경에서 파생된 진행 이벤트."""

    timestamp: str
    category: str       # workflow_status | validation | output | agent
    workflow: str        # bulletin | newcomer | finance | ...
    description: str     # 한국어 설명
    detail: dict         # 원본 데이터


class SOTWatcher:
    """
    state.yaml을 주기적으로 읽어서 변경을 감지.

    대시보드는 자체 상태를 갖지 않는다 (설계 원칙 1).
    진행 상황은 SOT의 실제 변경에서만 파생된다.
    """

    WORKFLOW_LABELS: dict[str, str] = {
        "bulletin": "주보",
        "newcomer": "새신자",
        "finance": "재정",
        "schedule": "일정",
        "document": "문서",
    }

    STATUS_LABELS: dict[str, str] = {
        "idle": "대기",
        "in_progress": "진행 중",
        "completed": "완료",
        "error": "오류",
    }

    def __init__(self, project_dir: str | Path):
        self.project_dir = Path(project_dir)
        self.state_path = self.project_dir / "state.yaml"
        self._prev_state = self._read()
        self._prev_mtime = self._mtime()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def poll(self) -> list[ProgressEvent]:
        """
        state.yaml이 변경되었으면 diff 계산, 이벤트 목록 반환.
        변경 없으면 빈 리스트 — mtime으로 빠른 탈출.
        """
        current_mtime = self._mtime()
        if current_mtime == self._prev_mtime:
            return []

        current = self._read()
        if not current:
            return []

        events: list[ProgressEvent] = []

        events.extend(self._diff_workflow_states(current))
        events.extend(self._diff_verification_gates(current))
        events.extend(self._diff_agent_sessions(current))

        self._prev_state = current
        self._prev_mtime = current_mtime
        return events

    def get_status_summary(self) -> dict:
        """
        show_menu.py를 실행하여 현재 상태 요약 반환.

        기존 show_menu.py를 재활용 — 프롬프트 템플릿과 동일하게
        상태 수집 로직을 중복 구현하지 않는다.
        """
        try:
            result = subprocess.run(
                [
                    "python3", "scripts/show_menu.py",
                    "--state", "state.yaml",
                    "--data-dir", "data/",
                ],
                capture_output=True,
                text=True,
                cwd=str(self.project_dir),
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
            pass

        # Fallback: state.yaml 직접 읽기
        return self._fallback_summary()

    def get_current_state(self) -> dict:
        """state.yaml 현재 내용 반환 (읽기 전용)."""
        return self._read()

    # ------------------------------------------------------------------
    # Diff 로직
    # ------------------------------------------------------------------

    def _diff_workflow_states(self, current: dict) -> list[ProgressEvent]:
        """워크플로우 상태 변경 감지."""
        events: list[ProgressEvent] = []

        cur_ws = current.get("church", {}).get("workflow_states", {})
        prev_ws = self._prev_state.get("church", {}).get("workflow_states", {})

        for wf_key, cur_wf in cur_ws.items():
            prev_wf = prev_ws.get(wf_key, {})
            label = self.WORKFLOW_LABELS.get(wf_key, wf_key)

            # status 변경
            old_status = prev_wf.get("status")
            new_status = cur_wf.get("status")
            if new_status and new_status != old_status:
                events.append(ProgressEvent(
                    timestamp=datetime.now().isoformat(),
                    category="workflow_status",
                    workflow=wf_key,
                    description=(
                        f"{label}: "
                        f"{self.STATUS_LABELS.get(old_status, old_status or '?')} → "
                        f"{self.STATUS_LABELS.get(new_status, new_status)}"
                    ),
                    detail={"old": old_status, "new": new_status},
                ))

            # 주보 호수 변경
            if wf_key == "bulletin":
                old_issue = prev_wf.get("last_generated_issue")
                new_issue = cur_wf.get("last_generated_issue")
                if new_issue and new_issue != old_issue:
                    events.append(ProgressEvent(
                        timestamp=datetime.now().isoformat(),
                        category="output",
                        workflow="bulletin",
                        description=f"주보 제{new_issue}호 생성 완료",
                        detail={"issue": new_issue, "date": cur_wf.get("last_generated_date")},
                    ))

            # 재정 outputs 변경
            if wf_key == "finance":
                cur_outputs = set((cur_wf.get("outputs") or {}).keys())
                prev_outputs = set((prev_wf.get("outputs") or {}).keys())
                for month in cur_outputs - prev_outputs:
                    events.append(ProgressEvent(
                        timestamp=datetime.now().isoformat(),
                        category="output",
                        workflow="finance",
                        description=f"{month} 재정 보고서 생성 완료",
                        detail={"month": month, "path": cur_wf["outputs"][month]},
                    ))

        return events

    def _diff_verification_gates(self, current: dict) -> list[ProgressEvent]:
        """검증 게이트 변경 감지."""
        events: list[ProgressEvent] = []

        cur_vg = current.get("church", {}).get("verification_gates", {})
        prev_vg = self._prev_state.get("church", {}).get("verification_gates", {})

        # 개별 게이트
        for gate_key in cur_vg:
            if gate_key == "aggregate":
                continue
            cur_gate = cur_vg[gate_key]
            prev_gate = prev_vg.get(gate_key, {})
            if cur_gate.get("last_run") != prev_gate.get("last_run"):
                events.append(ProgressEvent(
                    timestamp=datetime.now().isoformat(),
                    category="validation",
                    workflow=gate_key,
                    description=f"검증 ({gate_key}): {cur_gate.get('result', '?')}",
                    detail=cur_gate,
                ))

        # 집계
        agg = cur_vg.get("aggregate", {})
        prev_agg = prev_vg.get("aggregate", {})
        if agg.get("last_run") != prev_agg.get("last_run"):
            events.append(ProgressEvent(
                timestamp=datetime.now().isoformat(),
                category="validation",
                workflow="system",
                description=(
                    f"전체 검증: "
                    f"{agg.get('total_passed', 0)}/{agg.get('total_checks', 0)} 통과"
                ),
                detail=agg,
            ))

        return events

    def _diff_agent_sessions(self, current: dict) -> list[ProgressEvent]:
        """에이전트 활동 감지."""
        events: list[ProgressEvent] = []

        cur_ag = current.get("church", {}).get("agent_sessions", {})
        prev_ag = self._prev_state.get("church", {}).get("agent_sessions", {})

        for agent_name, cur_session in cur_ag.items():
            prev_session = prev_ag.get(agent_name, {})
            cur_active = cur_session.get("last_active")
            prev_active = prev_session.get("last_active")

            if cur_active and cur_active != prev_active:
                events.append(ProgressEvent(
                    timestamp=datetime.now().isoformat(),
                    category="agent",
                    workflow=agent_name,
                    description=(
                        f"에이전트 @{agent_name}: "
                        f"{cur_session.get('last_action', '활동')}"
                    ),
                    detail=cur_session,
                ))

        return events

    # ------------------------------------------------------------------
    # 내부 유틸
    # ------------------------------------------------------------------

    def _read(self) -> dict:
        try:
            text = self.state_path.read_text(encoding="utf-8")
            return yaml.safe_load(text) or {}
        except (OSError, yaml.YAMLError):
            return {}

    def _mtime(self) -> float:
        try:
            return self.state_path.stat().st_mtime
        except OSError:
            return 0.0

    def _fallback_summary(self) -> dict:
        """show_menu.py 실패 시 state.yaml에서 최소 정보 추출."""
        state = self._read()
        church = state.get("church", {})
        ws = church.get("workflow_states", {})
        vg = church.get("verification_gates", {}).get("aggregate", {})

        return {
            "church_name": church.get("name", "교회 행정 시스템"),
            "status": {
                "members": {"active": "?", "total": "?"},
                "newcomers": {"active": "?", "total": "?", "overdue": []},
                "bulletin": {
                    "last_issue": ws.get("bulletin", {}).get("last_generated_issue", "?"),
                    "last_date": ws.get("bulletin", {}).get("last_generated_date", ""),
                    "next_sunday": "",
                    "has_next_bulletin": False,
                },
                "finance": {
                    "has_prev_month_report": False,
                    "last_report_date": ws.get("finance", {}).get("last_report_date", ""),
                },
                "validation": {
                    "total_passed": vg.get("total_passed", 0),
                    "total_checks": vg.get("total_checks", 0),
                },
            },
            "alerts": [],
            "menu": [],
            "menu_page1": [],
            "menu_page2": [],
        }

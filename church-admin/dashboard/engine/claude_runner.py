"""
Claude Runner — Claude Code CLI subprocess 실행기.

검증된 플래그만 사용 (claude --help 출력에서 확인):
  -p, --output-format, --allowedTools, --permission-mode,
  --resume, --continue, --append-system-prompt, --verbose,
  --max-budget-usd

사용하지 않는 플래그 (미검증):
  --max-turns (존재하지 않음)

설계 결정:
  - subprocess.Popen (비동기) — Streamlit UI 블로킹 방지
  - stream-json 출력 — tool_use 이벤트로 보조 진행 감지
  - cwd=project_dir — Claude Code가 CLAUDE.md, hooks 자동 로드
  - 동시 실행 방지 — threading.Lock으로 단일 프로세스 보장
  - 실행 로그 — dashboard-logs/에 YAML로 감사 추적
"""

from __future__ import annotations

import json
import subprocess
import threading
from datetime import datetime
from pathlib import Path

import yaml

from .stream_parser import StreamState, parse_line


class ClaudeRunner:
    """
    Claude Code CLI를 백그라운드 subprocess로 실행.

    사용 패턴:
        runner = ClaudeRunner("/path/to/church-admin")
        request_id = runner.start("주보 만들어줘")

        while runner.is_running:
            state = runner.stream_state  # 실시간 도구 이벤트
            time.sleep(1)

        result = runner.stream_state  # 최종 결과
    """

    LOG_DIR = "dashboard-logs"

    ALLOWED_TOOLS = ",".join([
        "Read", "Write", "Edit", "Bash", "Glob", "Grep",
        "Agent", "Skill", "AskUserQuestion",
    ])

    def __init__(self, project_dir: str | Path):
        self.project_dir = Path(project_dir).resolve()
        self._process: subprocess.Popen | None = None
        self._stream_state = StreamState()
        self._lock = threading.Lock()
        self._status: str = "idle"  # idle | running | completed | failed
        self._error: str = ""
        self._request_id: str = ""
        self._started_at: str = ""
        self._completed_at: str = ""
        self._cancelled: bool = False

    # ------------------------------------------------------------------
    # Public Properties
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._status == "running"

    @property
    def status(self) -> str:
        with self._lock:
            return self._status

    @property
    def error(self) -> str:
        with self._lock:
            return self._error

    @property
    def request_id(self) -> str:
        return self._request_id

    @property
    def started_at(self) -> str:
        return self._started_at

    @property
    def stream_state(self) -> StreamState:
        """현재 스트리밍 상태 (도구 이벤트, 세션 ID, 결과 텍스트)."""
        return self._stream_state

    # ------------------------------------------------------------------
    # Public Methods
    # ------------------------------------------------------------------

    def start(
        self,
        prompt: str,
        resume_session: str | None = None,
        system_prompt_extra: str | None = None,
        max_budget_usd: float | None = None,
    ) -> str:
        """
        Claude Code를 백그라운드에서 시작. 즉시 request_id 반환.

        Args:
            prompt: 실행할 프롬프트 (기존 NL 트리거 또는 자유 텍스트)
            resume_session: 이전 세션 이어서 (--resume session_id)
            system_prompt_extra: 추가 시스템 프롬프트 (ULW 모드 등)
            max_budget_usd: 비용 제한 (--max-budget-usd)

        Returns:
            request_id (타임스탬프 기반)

        Raises:
            RuntimeError: 이미 실행 중인 프로세스가 있을 때
        """
        if self.is_running:
            raise RuntimeError(
                "이미 실행 중인 작업이 있습니다. 완료 후 다시 시도하세요."
            )

        request_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        self._request_id = request_id
        self._status = "running"
        self._error = ""
        self._cancelled = False
        self._started_at = datetime.now().isoformat()
        self._completed_at = ""
        self._stream_state = StreamState()

        # 명령 구성 — 검증된 플래그만 사용
        cmd = [
            "claude", "-p", prompt,
            "--output-format", "stream-json",
            "--verbose",
            "--allowedTools", self.ALLOWED_TOOLS,
            "--permission-mode", "auto",
        ]

        if resume_session:
            cmd.extend(["--resume", resume_session])

        if system_prompt_extra:
            cmd.extend(["--append-system-prompt", system_prompt_extra])

        if max_budget_usd is not None:
            cmd.extend(["--max-budget-usd", str(max_budget_usd)])

        # 실행 로그 기록 (감사 추적)
        log_file = self._write_log(request_id, {
            "request_id": request_id,
            "prompt": prompt,
            "resume_session": resume_session,
            "system_prompt_extra": system_prompt_extra,
            "status": "running",
            "started_at": self._started_at,
        })

        # 백그라운드 스레드에서 실행
        thread = threading.Thread(
            target=self._run_process,
            args=(cmd, log_file),
            daemon=True,
        )
        thread.start()

        return request_id

    def cancel(self):
        """실행 중인 프로세스를 종료."""
        with self._lock:
            if self._process and self._process.poll() is None:
                self._process.terminate()
                self._cancelled = True
                self._status = "failed"
                self._error = "사용자에 의해 취소됨"

    # ------------------------------------------------------------------
    # Background Execution
    # ------------------------------------------------------------------

    def _run_process(self, cmd: list[str], log_file: Path | None):
        """백그라운드에서 프로세스 실행 + stream-json 파싱."""
        proc = None
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.project_dir),
                text=True,
                bufsize=1,
            )

            with self._lock:
                self._process = proc

            # stdout에서 stream-json 이벤트를 라인 단위로 읽기
            if proc.stdout:
                for line in proc.stdout:
                    parse_line(line, self._stream_state)

            proc.wait()

            # 완료 처리
            self._completed_at = datetime.now().isoformat()

            with self._lock:
                if not self._cancelled:
                    if proc.returncode == 0:
                        self._status = "completed"
                    else:
                        self._status = "failed"
                        if proc.stderr:
                            self._error = proc.stderr.read()[:2000]

        except Exception as e:
            self._completed_at = datetime.now().isoformat()
            with self._lock:
                if not self._cancelled:
                    self._status = "failed"
                    self._error = str(e)

        finally:
            with self._lock:
                self._process = None

            # 로그 갱신
            if log_file:
                self._update_log(log_file, {
                    "status": self._status,
                    "exit_code": proc.returncode if proc else None,
                    "completed_at": self._completed_at,
                    "session_id": self._stream_state.session_id,
                    "tool_count": len(self._stream_state.tool_events),
                    "error": self._error[:500] if self._error else None,
                })

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _write_log(self, request_id: str, data: dict) -> Path | None:
        """실행 로그 파일 작성."""
        try:
            log_dir = self.project_dir / self.LOG_DIR
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / f"{request_id}.yaml"
            log_file.write_text(
                yaml.dump(data, allow_unicode=True, default_flow_style=False),
                encoding="utf-8",
            )
            return log_file
        except OSError:
            return None

    def _update_log(self, log_file: Path, updates: dict):
        """실행 로그 파일 갱신."""
        try:
            data = yaml.safe_load(log_file.read_text(encoding="utf-8")) or {}
            data.update(updates)
            log_file.write_text(
                yaml.dump(data, allow_unicode=True, default_flow_style=False),
                encoding="utf-8",
            )
        except (OSError, yaml.YAMLError):
            pass

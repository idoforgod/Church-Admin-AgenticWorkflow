"""
Post-Execution Validator — subprocess 완료 후 독립적 P1 검증.

할루시네이션 원천봉쇄:
  Claude subprocess가 exit code 0으로 종료해도,
  그것이 "산출물이 유효하다"를 의미하지 않는다.
  Claude가 검증을 실행했다고 주장할 수 있지만,
  실제로 실행했는지, 통과했는지는 확인할 수 없다.

  이 모듈은 LLM 밖에서 Python 코드로 직접 검증한다.
  대시보드가 기존 P1 검증 스크립트(validate_*.py)를
  독립 subprocess로 실행하여 결과를 기계적으로 판정한다.

설계 원칙:
  1. 읽기 전용 — SOT, 데이터 파일 읽기만 (SOT 규율 준수)
  2. 기존 코드 재활용 — validate_*.py를 그대로 subprocess 실행
  3. LLM 무개입 — Python 코드만으로 PASS/FAIL 판정
  4. 부모 시스템 정합 — L0 Anti-Skip Guard + L1 Verification Gate 동등물
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class CheckResult:
    """개별 검증 항목 결과."""

    name: str           # 검증 이름 (예: "L0: 산출물 존재", "P1: B1-B3")
    passed: bool        # PASS/FAIL
    details: str = ""   # 상세 메시지
    errors: list[str] = field(default_factory=list)  # 실패한 개별 항목


@dataclass
class ValidationResult:
    """전체 검증 결과."""

    card_key: str
    checks: list[CheckResult] = field(default_factory=list)
    validated_at: str = ""

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def summary(self) -> str:
        passed = sum(1 for c in self.checks if c.passed)
        total = len(self.checks)
        return f"{passed}/{total} 통과"

    def __post_init__(self):
        if not self.validated_at:
            self.validated_at = datetime.now().isoformat()


# ──────────────────────────────────────────────────────────────────
# card_key → 검증 스크립트 경로 + 인자
#
# D-7 의도적 중복: CLAUDE.md의 Validation Infrastructure 섹션,
# context_builder.py의 VALIDATION_RULES와 병행 관리.
# 한쪽 변경 시 반드시 대응 쪽 동기화 필요.
# ──────────────────────────────────────────────────────────────────

VALIDATOR_MAP: dict[str, dict] = {
    "bulletin": {
        "script": ".claude/hooks/scripts/validate_bulletin.py",
        "args": ["--data-dir", "data/", "--members-file", "data/members.yaml"],
        "output_dirs": ["bulletins"],
        "output_suffix": [".md"],
    },
    "newcomer": {
        "script": ".claude/hooks/scripts/validate_newcomers.py",
        "args": ["--data-dir", "data/", "--members-file", "data/members.yaml"],
        "output_dirs": [],
        "output_suffix": [],
    },
    "member": {
        "script": ".claude/hooks/scripts/validate_members.py",
        "args": ["--data-dir", "data/"],
        "output_dirs": [],
        "output_suffix": [],
    },
    "finance": {
        "script": ".claude/hooks/scripts/validate_finance.py",
        "args": ["--data-dir", "data/"],
        "output_dirs": ["output/finance-reports", "docs/generated"],
        "output_suffix": [".md"],
    },
    "schedule": {
        "script": ".claude/hooks/scripts/validate_schedule.py",
        "args": ["--data-dir", "data/"],
        "output_dirs": [],
        "output_suffix": [],
    },
    "document": {
        "script": None,  # 전용 검증 스크립트 없음
        "args": [],
        "output_dirs": ["docs/generated"],
        "output_suffix": [".md"],
    },
    "validate": {
        # "데이터 검증" 카드 자체가 검증이므로, 후처리 검증 불필요
        "script": None,
        "args": [],
        "output_dirs": [],
        "output_suffix": [],
    },
}


def validate_after_execution(
    card_key: str | None,
    project_dir: str | Path,
    started_at: str,
) -> ValidationResult | None:
    """
    subprocess 완료 후 독립적 검증 수행.

    LLM이 아닌 Python 코드가 직접 실행.
    기존 validate_*.py 스크립트를 subprocess로 호출하여
    결과 JSON을 파싱 — 할루시네이션 원천봉쇄.

    Args:
        card_key: 워크플로우 카드 키 (None이면 검증 건너뜀)
        project_dir: church-admin/ 경로
        started_at: 실행 시작 시각 (ISO format) — 이후 파일만 L0 검증

    Returns:
        ValidationResult 또는 None (검증 불필요 시)
    """
    if not card_key or card_key not in VALIDATOR_MAP:
        return None

    project = Path(project_dir)
    config = VALIDATOR_MAP[card_key]
    result = ValidationResult(card_key=card_key)

    # ── L0: 산출물 파일 존재 + 최소 크기 ──
    if config["output_dirs"]:
        l0_check = _check_output_exists(
            project=project,
            output_dirs=config["output_dirs"],
            output_suffix=config["output_suffix"],
            started_at=started_at,
        )
        result.checks.append(l0_check)

    # ── L1: P1 검증 스크립트 실행 ──
    if config["script"]:
        p1_check = _run_p1_validator(
            project=project,
            script=config["script"],
            args=config["args"],
        )
        result.checks.append(p1_check)

    # 검증 항목이 없으면 None
    if not result.checks:
        return None

    return result


def _check_output_exists(
    project: Path,
    output_dirs: list[str],
    output_suffix: list[str],
    started_at: str,
    min_size: int = 100,
) -> CheckResult:
    """
    L0 Anti-Skip Guard 동등물.

    산출물 파일이 실제로 존재하고, 최소 크기를 만족하는지 확인.
    결정론적 Python 코드 — LLM 무개입.
    """
    start_ts = _parse_iso(started_at)
    found_files: list[str] = []
    errors: list[str] = []

    for dir_name in output_dirs:
        output_dir = project / dir_name
        if not output_dir.exists():
            continue

        for f in output_dir.rglob("*"):
            if not f.is_file():
                continue
            if output_suffix and f.suffix not in output_suffix:
                continue

            try:
                if f.stat().st_mtime > start_ts:
                    size = f.stat().st_size
                    rel = str(f.relative_to(project))

                    if size < min_size:
                        errors.append(
                            f"L0b FAIL: {rel} ({size} bytes < {min_size} min)"
                        )
                    elif f.read_text(encoding="utf-8").strip() == "":
                        errors.append(f"L0c FAIL: {rel} is whitespace-only")
                    else:
                        found_files.append(rel)
            except (OSError, UnicodeDecodeError):
                continue

    if not found_files and not errors:
        errors.append("L0a FAIL: 실행 이후 생성된 산출물 파일 없음")

    passed = len(found_files) > 0 and len(errors) == 0

    details = ""
    if found_files:
        details = f"산출물 {len(found_files)}건: {', '.join(found_files[:5])}"
    if errors:
        details += (" | " if details else "") + "; ".join(errors)

    return CheckResult(
        name="L0: 산출물 존재 검증",
        passed=passed,
        details=details,
        errors=errors,
    )


def _run_p1_validator(
    project: Path,
    script: str,
    args: list[str],
    timeout: int = 30,
) -> CheckResult:
    """
    P1 검증 스크립트를 직접 실행.

    기존 validate_*.py를 subprocess로 호출하여
    JSON 출력을 파싱 — 결정론적 판정.

    LLM이 아닌 Python 코드가 실행하므로,
    "Claude가 검증을 실행했다고 주장"하는 할루시네이션 불가.
    """
    script_path = project / script
    if not script_path.exists():
        return CheckResult(
            name=f"P1: {Path(script).stem}",
            passed=False,
            details=f"검증 스크립트 없음: {script}",
            errors=[f"스크립트 {script} 미존재"],
        )

    cmd = ["python3", str(script_path)] + args

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(project),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name=f"P1: {Path(script).stem}",
            passed=False,
            details=f"검증 타임아웃 ({timeout}s)",
            errors=["타임아웃"],
        )
    except OSError as e:
        return CheckResult(
            name=f"P1: {Path(script).stem}",
            passed=False,
            details=f"실행 오류: {e}",
            errors=[str(e)],
        )

    # 검증 스크립트는 JSON 출력 (exit code 0 + valid 필드)
    if proc.returncode != 0:
        # Fatal error in validator itself
        return CheckResult(
            name=f"P1: {Path(script).stem}",
            passed=False,
            details=f"검증 스크립트 실행 오류 (exit {proc.returncode}): {proc.stderr[:500]}",
            errors=[proc.stderr[:500] if proc.stderr else f"exit code {proc.returncode}"],
        )

    # Parse JSON output
    try:
        output = json.loads(proc.stdout)
    except (json.JSONDecodeError, TypeError):
        return CheckResult(
            name=f"P1: {Path(script).stem}",
            passed=False,
            details=f"JSON 파싱 실패: {proc.stdout[:300]}",
            errors=["검증 출력이 유효한 JSON 아님"],
        )

    # Extract results
    # 검증 스크립트 JSON 형식:
    #   {"valid": bool, "checks": [{"rule": "B1", "status": "PASS"|"FAIL",
    #    "name": "...", "errors": [...]}], "summary": "3/3 checks passed"}
    valid = output.get("valid", False)
    checks = output.get("checks", [])

    errors: list[str] = []
    for check in checks:
        # status 필드: "PASS" | "FAIL" (validate_*.py 표준 형식)
        check_status = check.get("status", "PASS")
        if check_status != "PASS":
            rule = check.get("rule", "?")
            check_name = check.get("name", "?")
            check_errors = check.get("errors", [])
            for err in check_errors[:3]:  # 체크당 최대 3개 에러
                errors.append(f"{rule} ({check_name}): {err}")
            if not check_errors:
                errors.append(f"{rule} ({check_name}): FAIL")

    passed_count = sum(
        1 for c in checks if c.get("status", "PASS") == "PASS"
    )
    total_count = len(checks)

    return CheckResult(
        name=f"P1: {Path(script).stem}",
        passed=valid,
        details=f"{passed_count}/{total_count} checks passed",
        errors=errors,
    )


def _parse_iso(iso_str: str) -> float:
    """ISO 타임스탬프를 Unix timestamp로 변환."""
    if not iso_str:
        return 0.0
    try:
        return datetime.fromisoformat(iso_str).timestamp()
    except (ValueError, TypeError):
        return 0.0

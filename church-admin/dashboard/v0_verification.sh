#!/usr/bin/env bash
# =============================================================================
# V0 선결 검증 테스트
#
# 대시보드 구현 전에 claude -p 모드의 핵심 전제를 검증한다.
# 별도 터미널에서 실행: bash dashboard/v0_verification.sh
#
# 이 스크립트는 church-admin/ 디렉터리에서 실행해야 한다.
# =============================================================================

set -euo pipefail

cd "$(dirname "$0")/.."
PROJECT_DIR="$(pwd)"

PASS=0
FAIL=0
WARN=0

header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

pass() {
    echo "  ✅ PASS: $1"
    PASS=$((PASS + 1))
}

fail() {
    echo "  ❌ FAIL: $1"
    FAIL=$((FAIL + 1))
}

warn() {
    echo "  ⚠️  WARN: $1"
    WARN=$((WARN + 1))
}

# =============================================================================
# 검증 1: -p 모드에서 Hook (guard_data_files.py) 차단 테스트
# =============================================================================
header "검증 1: PreToolUse Hook 차단 (guard_data_files.py)"
echo "  목적: -p 모드에서 exit code 2 기반 Hook이 정상 작동하는지 확인"
echo "  테스트: finance.yaml에 무단 쓰기 시도 → Hook이 차단해야 함"
echo ""

V1_OUTPUT=$(claude -p "data/finance.yaml 파일의 맨 끝에 'dashboard_test: true'라는 줄을 추가하라. 반드시 Edit 또는 Write 도구를 사용하라." \
    --output-format json \
    --permission-mode auto 2>&1 || true)

# finance.yaml에 dashboard_test가 추가되었는지 확인
if grep -q "dashboard_test" data/finance.yaml 2>/dev/null; then
    fail "Hook이 차단하지 못함 — finance.yaml에 무단 쓰기 발생"
    # 롤백
    sed -i '' '/dashboard_test/d' data/finance.yaml 2>/dev/null || true
else
    # Hook이 차단했거나 Claude가 자기 수정했는지 확인
    if echo "$V1_OUTPUT" | grep -qi "block\|guard\|sole.writer\|unauthorized\|차단\|권한"; then
        pass "Hook이 무단 쓰기를 차단함 (exit code 2 또는 Claude 자기 수정)"
    else
        # 파일이 변경되지 않았지만 차단 메시지도 없는 경우
        warn "finance.yaml 미변경이나 차단 메시지 미확인 — 수동 검토 필요"
        echo "  출력 (첫 500자):"
        echo "$V1_OUTPUT" | head -c 500
    fi
fi

# =============================================================================
# 검증 2: -p 모드에서 Sub-agent (Agent tool) 작동 확인
# =============================================================================
header "검증 2: Sub-agent (Agent tool) 작동"
echo "  목적: -p 모드에서 Agent tool이 정상 호출되는지 확인"
echo ""

V2_OUTPUT=$(claude -p "bulletin-generator 에이전트를 호출하여 data/bulletin-data.yaml의 현재 issue_number를 확인하고 보고하라." \
    --output-format json \
    --allowedTools "Read,Agent,Glob" \
    --permission-mode auto 2>&1 || true)

if echo "$V2_OUTPUT" | grep -qi "1247\|issue.number\|호수"; then
    pass "Sub-agent가 정상 작동하여 bulletin 데이터를 읽었음"
else
    if echo "$V2_OUTPUT" | grep -qi "agent\|error\|fail"; then
        warn "Sub-agent 호출 실패 가능 — 수동 검토 필요"
    else
        warn "결과에서 기대값(1247) 미확인 — 수동 검토 필요"
    fi
    echo "  출력 (첫 500자):"
    echo "$V2_OUTPUT" | head -c 500
fi

# =============================================================================
# 검증 3: -p 모드에서 Skill/Command 인식 확인
# =============================================================================
header "검증 3: Skill/Command 패턴 인식"
echo "  목적: -p 모드에서 '시작' 트리거가 show_menu.py를 실행하는지 확인"
echo ""

V3_OUTPUT=$(claude -p "시스템 상태 보여줘" \
    --output-format json \
    --allowedTools "Read,Bash,Glob,Grep" \
    --permission-mode auto 2>&1 || true)

if echo "$V3_OUTPUT" | grep -qi "새벽이슬\|Morning.Dew\|교인\|members\|검증\|validation\|29/29\|passed"; then
    pass "Skill/Command 패턴이 인식되어 시스템 상태를 반환함"
else
    warn "시스템 상태 정보 미확인 — 수동 검토 필요"
    echo "  출력 (첫 500자):"
    echo "$V3_OUTPUT" | head -c 500
fi

# =============================================================================
# 검증 4: --resume 세션 연속성 확인
# =============================================================================
header "검증 4: --resume 세션 연속성"
echo "  목적: 세션 ID로 이전 대화를 이어받을 수 있는지 확인"
echo ""

# 4a: 첫 번째 호출 — 세션 ID 캡처
V4A_OUTPUT=$(claude -p "state.yaml을 읽어서 교회 이름만 알려줘. 다른 설명 없이 이름만." \
    --output-format json \
    --allowedTools "Read" \
    --permission-mode auto 2>&1 || true)

SESSION_ID=$(echo "$V4A_OUTPUT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('session_id', ''))
except:
    print('')
" 2>/dev/null || true)

if [ -z "$SESSION_ID" ]; then
    warn "세션 ID를 추출할 수 없음 — JSON 파싱 실패"
    echo "  출력 (첫 300자):"
    echo "$V4A_OUTPUT" | head -c 300
else
    echo "  세션 ID: $SESSION_ID"

    # 4b: 두 번째 호출 — 세션 이어서
    V4B_OUTPUT=$(claude -p "방금 읽은 교회 이름이 무엇이었는지 다시 알려줘." \
        --resume "$SESSION_ID" \
        --output-format json \
        --allowedTools "Read" \
        --permission-mode auto 2>&1 || true)

    if echo "$V4B_OUTPUT" | grep -qi "새벽이슬\|Morning.Dew"; then
        pass "--resume로 이전 세션 컨텍스트가 유지됨"
    else
        warn "이전 세션 컨텍스트 유지 미확인 — 수동 검토 필요"
        echo "  출력 (첫 300자):"
        echo "$V4B_OUTPUT" | head -c 300
    fi
fi

# =============================================================================
# 결과 요약
# =============================================================================
header "V0 검증 결과 요약"
echo ""
echo "  PASS: $PASS"
echo "  FAIL: $FAIL"
echo "  WARN: $WARN"
echo ""

if [ $FAIL -gt 0 ]; then
    echo "  ⛔ FAIL이 있습니다. 대시보드 구현 전에 해결이 필요합니다."
    echo "     FAIL 항목의 대안을 검토하세요."
elif [ $WARN -gt 0 ]; then
    echo "  ⚠️  WARN이 있습니다. 출력을 수동 검토하세요."
    echo "     대부분의 경우 구현을 진행할 수 있습니다."
else
    echo "  ✅ 모든 검증 통과. 대시보드 구현을 진행하세요."
fi
echo ""

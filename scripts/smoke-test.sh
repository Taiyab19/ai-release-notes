#!/usr/bin/env bash
# =============================================================
# smoke-test.sh — Post-deployment smoke tests
# Usage: bash scripts/smoke-test.sh <env> <base_url>
# =============================================================

set -euo pipefail

ENV=${1:-dev}
BASE_URL=${2:-"http://localhost:5000"}
PASS=0; FAIL=0

GREEN='\033[0;32m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'
log()     { echo -e "${BLUE}[SMOKE]${NC} $1"; }
pass()    { echo -e "${GREEN}  ✔ PASS${NC} — $1"; ((PASS++)); }
fail()    { echo -e "${RED}  ✘ FAIL${NC} — $1"; ((FAIL++)); }

log "======================================================"
log " Smoke Tests — $ENV @ $BASE_URL"
log "======================================================"

# Test helper
check() {
  local label=$1
  local url=$2
  local expected_code=${3:-200}
  local actual_code
  actual_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")
  if [[ "$actual_code" == "$expected_code" ]]; then
    pass "$label (HTTP $actual_code)"
  else
    fail "$label — expected HTTP $expected_code, got $actual_code"
  fi
}

# ── Smoke test suite ──────────────────────────────────────────
log "Running smoke tests..."

check "Root endpoint is reachable"        "${BASE_URL}/"             200
check "Health endpoint returns 200"       "${BASE_URL}/health"       200
check "Readiness probe returns 200"       "${BASE_URL}/ready"        200
check "Version endpoint returns 200"      "${BASE_URL}/version"      200
check "Payment endpoint accepts POST"     "${BASE_URL}/payment/process" 202

# ── Response content checks ───────────────────────────────────
log "Checking response content..."

HEALTH_BODY=$(curl -s --max-time 10 "${BASE_URL}/health" 2>/dev/null || echo "{}")
if echo "$HEALTH_BODY" | grep -q '"status":"healthy"'; then
  pass "Health response contains status:healthy"
else
  fail "Health response missing status:healthy — got: $HEALTH_BODY"
fi

# ── Response time check ───────────────────────────────────────
log "Checking response time SLA (< 2s)..."
RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" --max-time 10 "${BASE_URL}/health" 2>/dev/null || echo "9999")
THRESHOLD=2.0
if (( $(echo "$RESPONSE_TIME < $THRESHOLD" | bc -l 2>/dev/null || echo 0) )); then
  pass "Response time ${RESPONSE_TIME}s < ${THRESHOLD}s SLA threshold"
else
  fail "Response time ${RESPONSE_TIME}s exceeds ${THRESHOLD}s SLA threshold"
fi

# ── Summary ───────────────────────────────────────────────────
echo ""
log "======================================================"
log " SMOKE TEST RESULTS — $ENV"
log " Passed : $PASS"
log " Failed : $FAIL"
log " Total  : $((PASS + FAIL))"
log "======================================================"

if [[ "$FAIL" -gt 0 ]]; then
  echo -e "${RED}Smoke tests FAILED — $FAIL test(s) failed. Rollback may be triggered.${NC}"
  exit 1
else
  echo -e "${GREEN}All smoke tests PASSED — $ENV deployment is healthy.${NC}"
  exit 0
fi

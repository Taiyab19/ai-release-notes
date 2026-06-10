#!/usr/bin/env bash
# health-check.sh — SLA health monitoring post-deployment
set -euo pipefail
BASE_URL=${1:-"http://localhost:5000"}
BLUE='\033[0;34m'; GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${BLUE}[HEALTH]${NC} $1"; }
pass() { echo -e "${GREEN}  ✔${NC} $1"; }
fail() { echo -e "${RED}  ✘${NC} $1"; }

log "Running health checks on $BASE_URL"
CHECKS_PASS=0; CHECKS_FAIL=0

# Response time SLA
RESP=$(curl -s -o /dev/null -w "%{time_total}" --max-time 10 "$BASE_URL/health" 2>/dev/null || echo "9999")
if (( $(echo "$RESP < 2.0" | bc -l 2>/dev/null || echo 0) )); then
  pass "Response time: ${RESP}s (SLA: <2.0s)"; ((CHECKS_PASS++))
else
  fail "Response time: ${RESP}s EXCEEDS SLA of 2.0s"; ((CHECKS_FAIL++))
fi

# Endpoint availability
for endpoint in "/health" "/ready" "/version"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$BASE_URL$endpoint" 2>/dev/null || echo "000")
  if [[ "$CODE" == "200" ]]; then
    pass "Endpoint $endpoint → HTTP $CODE"; ((CHECKS_PASS++))
  else
    fail "Endpoint $endpoint → HTTP $CODE"; ((CHECKS_FAIL++))
  fi
done

log "Health check summary: $CHECKS_PASS passed, $CHECKS_FAIL failed"
[[ "$CHECKS_FAIL" -eq 0 ]] && exit 0 || exit 1

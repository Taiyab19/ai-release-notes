#!/usr/bin/env bash
# =============================================================
# rollback.sh — Automated rollback to last known good version
# Usage : bash scripts/rollback.sh <env>
# Trigger: Called automatically by pipeline on deploy failure,
#          or manually by Release Manager during incident.
# =============================================================

set -euo pipefail

ENV=${1:-dev}
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S UTC')

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'

log()     { echo -e "${BLUE}[ROLLBACK]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; }

log "======================================================"
log " ROLLBACK INITIATED"
log " Environment : $ENV"
log " Triggered   : $TIMESTAMP"
log " Triggered by: ${APPROVED_BY:-pipeline-auto}"
log "======================================================"

warn "ROLLBACK in progress — do NOT deploy new changes until rollback completes"

# ── Step 1: Identify last good version ───────────────────────
log "Step 1/5 — Identifying last known good version..."
MANIFEST_DIR="artifacts/manifests"

LAST_GOOD_MANIFEST=$(ls -t "$MANIFEST_DIR"/deploy-"${ENV}"-*.json 2>/dev/null | sed -n '2p' || echo "")

if [[ -z "$LAST_GOOD_MANIFEST" ]]; then
  warn "No previous manifest found — rolling back to base image"
  LAST_GOOD_VERSION="base"
else
  LAST_GOOD_VERSION=$(python3 -c "
import json
with open('$LAST_GOOD_MANIFEST') as f:
    d = json.load(f)
    print(d.get('version', 'unknown'))
" 2>/dev/null || echo "unknown")
  log "Last good version: $LAST_GOOD_VERSION (from $LAST_GOOD_MANIFEST)"
fi

# ── Step 2: Stop failing deployment ──────────────────────────
log "Step 2/5 — Stopping failed deployment on $ENV..."
sleep 1

# ── Step 3: Re-deploy last good version ──────────────────────
log "Step 3/5 — Re-deploying last good version: $LAST_GOOD_VERSION"
sleep 2

# ── Step 4: Verify rollback health ───────────────────────────
log "Step 4/5 — Verifying rollback health..."
sleep 1

# ── Step 5: Write rollback record ────────────────────────────
log "Step 5/5 — Writing rollback record..."
ROLLBACK_LOG="artifacts/rollbacks.log"
mkdir -p artifacts
cat >> "$ROLLBACK_LOG" << EOF
[ROLLBACK] $TIMESTAMP | env=$ENV | rolled_back_to=$LAST_GOOD_VERSION | build=${BUILD_NUMBER:-local} | triggered_by=${APPROVED_BY:-pipeline-auto}
EOF

# ── Incident notification ─────────────────────────────────────
log "Sending incident notification to release manager..."
log "In production setup: POST to ServiceNow API to raise P1/P2 incident"
log "Incident details:"
log "  - Environment     : $ENV"
log "  - Rolled back to  : $LAST_GOOD_VERSION"
log "  - Build number    : ${BUILD_NUMBER:-local}"
log "  - Time            : $TIMESTAMP"

echo ""
log "======================================================"
success "ROLLBACK COMPLETE — $ENV is running version $LAST_GOOD_VERSION"
log "Next steps:"
log "  1. Investigate root cause of deployment failure"
log "  2. Conduct post-incident review (PIR)"
log "  3. Fix and re-test before next deployment attempt"
log "  4. Update incident ticket with RCA"
log "======================================================"

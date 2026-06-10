#!/usr/bin/env bash
# =============================================================
# deploy.sh — Environment-aware deployment script
# Usage: bash scripts/deploy.sh <env> <artifact_name> <version>
# Envs : dev | staging | production
# =============================================================

set -euo pipefail

ENV=${1:-dev}
ARTIFACT=${2:-"app-latest"}
VERSION=${3:-"0.0.0"}
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S UTC')

# ── Colour output ─────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'

log()     { echo -e "${BLUE}[DEPLOY]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ── Validate environment ──────────────────────────────────────
case "$ENV" in
  dev|staging|production) ;;
  *) error "Invalid environment: '$ENV'. Must be dev | staging | production" ;;
esac

log "======================================================"
log " Deployment started"
log " Environment : $ENV"
log " Artifact    : $ARTIFACT"
log " Version     : $VERSION"
log " Timestamp   : $TIMESTAMP"
log "======================================================"

# ── Pre-deployment checks ─────────────────────────────────────
log "Running pre-deployment checks..."

if [[ "$ENV" == "production" ]]; then
  warn "PRODUCTION deployment — verifying approval flag..."
  if [[ -z "${APPROVED_BY:-}" ]]; then
    warn "APPROVED_BY not set — ensure CAB approval was recorded in pipeline"
  else
    log "Approved by: ${APPROVED_BY}"
  fi
fi

# ── Simulate deployment steps ─────────────────────────────────
log "Step 1/5 — Pulling artifact: $ARTIFACT"
sleep 1
log "Step 2/5 — Stopping current service on $ENV"
sleep 1
log "Step 3/5 — Deploying new version $VERSION"
sleep 2
log "Step 4/5 — Running database migrations (if any)"
sleep 1
log "Step 5/5 — Starting service on $ENV"
sleep 1

# ── Write deployment manifest ─────────────────────────────────
MANIFEST_DIR="artifacts/manifests"
mkdir -p "$MANIFEST_DIR"
cat > "$MANIFEST_DIR/deploy-${ENV}-${VERSION}.json" << EOF
{
  "environment":  "$ENV",
  "artifact":     "$ARTIFACT",
  "version":      "$VERSION",
  "deployed_at":  "$TIMESTAMP",
  "deployed_by":  "${APPROVED_BY:-ci-pipeline}",
  "build_number": "${BUILD_NUMBER:-local}",
  "status":       "success"
}
EOF

log "Deployment manifest written: $MANIFEST_DIR/deploy-${ENV}-${VERSION}.json"
success "Deployment to $ENV COMPLETE — version $VERSION is live"

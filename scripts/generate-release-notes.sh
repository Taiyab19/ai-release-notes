#!/usr/bin/env bash
# generate-release-notes.sh — Auto-generate release notes from Git log
set -euo pipefail

VERSION=${VERSION:-$(git describe --tags --always 2>/dev/null || echo "1.0.0")}
DATE=$(date '+%Y-%m-%d')
PREV_TAG=$(git describe --tags --abbrev=0 HEAD~1 2>/dev/null || echo "")

cat << EOF
# Release Notes — v${VERSION}
**Release date:** ${DATE}
**Environment:** Production
**Approved by:** ${APPROVED_BY:-Release Manager}

---

## Changes in this release

EOF

if [[ -n "$PREV_TAG" ]]; then
  git log "${PREV_TAG}..HEAD" --pretty=format:"- %s (%an)" 2>/dev/null || \
    echo "- See Git commit history for full change list"
else
  git log --oneline -10 --pretty=format:"- %s (%an)" 2>/dev/null || \
    echo "- Initial release"
fi

cat << EOF

---

## Deployment details
| Field         | Value                      |
|---------------|----------------------------|
| Version       | ${VERSION}                 |
| Build number  | ${BUILD_NUMBER:-local}     |
| Deploy date   | ${DATE}                    |
| Environment   | Production                 |
| Pipeline      | Jenkins CI/CD              |

---

## Post-deployment checklist
- [ ] Smoke tests passed
- [ ] Health checks green
- [ ] SLA thresholds within bounds
- [ ] Monitoring dashboards checked
- [ ] Release manager sign-off received
EOF

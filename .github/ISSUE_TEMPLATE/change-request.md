---
name: Change Request
about: Raise a change request for production deployment
title: "[CHG] payment-service v{VERSION} — {DATE}"
labels: change-request
assignees: ''
---

## Change Request

| Field              | Value                    |
|--------------------|--------------------------|
| Application        | payment-service          |
| Version            | {VERSION}                |
| Change type        | Standard / Normal        |
| Risk               | Low / Medium / High      |
| Deployment window  | {DATE} {TIME}            |
| Rollback time      | < 15 minutes             |

## Description
<!-- What is being deployed and why? -->

## Impact
<!-- Who/what is affected? Any downtime expected? -->

## Rollback Plan
<!-- How do we revert if something goes wrong? -->

## Go/No-Go Criteria
- [ ] Tests passing
- [ ] Staging verified
- [ ] On-call confirmed
- [ ] Stakeholders notified

## Approvals
- [ ] Release Manager
- [ ] Application Owner
- [ ] CAB (if Normal change)

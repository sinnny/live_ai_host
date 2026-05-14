# Checklist — Compliance runbook

| | |
|---|---|
| FSD | [`../../fsd/compliance_runbook.md`](../../fsd/compliance_runbook.md) |
| Phase | Phase 3 (legal-counsel-dependent) |
| Language | English source — KO at [`../ko/compliance_runbook.md`](../ko/compliance_runbook.md) |

---

## Tech stack
- Versioned rule corpus in git + legal review process

---

## §1. Standing roles
- [ ] Legal counsel retainer agreement
- [ ] Compliance owner designated
- [ ] Engineering rotation defined

## §2. Quarterly review cycle
- [ ] Pull latest 표시광고법/식품위생법/화장품법 amendments
- [ ] Review production audit log FP/FN rates
- [ ] Update rule corpus + few-shots
- [ ] Re-run labeled eval
- [ ] Staging → production deploy

## §3. Incident response
- [ ] EMERGENCY_LOOP triggered logged
- [ ] Root cause: rule gap vs runtime gap
- [ ] Regression test added
- [ ] Disclosure to seller + legal as needed

## §4. Troubleshooting
- Repeated regressions in same category → root-cause prompt engineering, not just adding examples

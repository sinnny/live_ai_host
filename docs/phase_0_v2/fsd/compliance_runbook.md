# Function Spec — Compliance runbook

| | |
|---|---|
| Status | Skeleton v1 (Phase 3 — speculative; legal counsel required) |
| Phase | Phase 3 |
| Component | Operational runbook for maintaining Korean 표시광고법 + vertical-specific rules in `compliance_pre_check.md` and `llm_moderator.md` |
| Source documents | [`../../prd.md`](../../prd.md) §4.5 |
| Open dependencies | Legal counsel retainer; quarterly rule review cadence |
| Last updated | 2026-05-13 |

---

## 1. Purpose

Defines the human + process side of compliance: who updates the rules, how often, what change-control looks like, how legal changes propagate to runtime.

---

## 2. Roles

- **Legal counsel** (external): reviews rule changes, advises on enforcement updates
- **Compliance owner** (internal, TBD): owns the rule corpus, schedules quarterly reviews
- **Engineering**: implements rule corpus changes in [`compliance_pre_check.md`](compliance_pre_check.md) + [`llm_moderator.md`](llm_moderator.md)

---

## 3. Rule corpus structure

Same as [`compliance_pre_check.md`](compliance_pre_check.md) §5 + extensions:
- Versioned (semver)
- Tracked in git
- Per-vertical sub-corpus (food → cosmetics → ...)
- Change-log noting legal basis for each rule

---

## 4. Change-control workflow

1. Legal change identified (regulator update, new case law, etc.).
2. Compliance owner drafts rule update with legal basis.
3. Legal counsel reviews.
4. Engineering implements: prompt update + few-shot examples + eval set update.
5. Staging deploy: rerun labeled eval; verify regressions caught.
6. Production deploy.

---

## 5. Quarterly review

- Pull latest 표시광고법 / 식품위생법 amendments.
- Review false-positive / false-negative rates from production audit log.
- Schedule rule-corpus refresh if rates drift.

---

## 6. Incident response

When a violation makes it to broadcast:
1. EMERGENCY_LOOP triggered (manual or automated).
2. Audit log captured; root-cause analysis.
3. Determine: rule gap (compliance_pre_check missed) or runtime gap (moderator missed)?
4. Add the specific case to eval set as regression test.
5. Disclose to seller, legal counsel if material.

---

## 7. References

- [`compliance_pre_check.md`](compliance_pre_check.md), [`llm_moderator.md`](llm_moderator.md) — runtime touchpoints
- Korean 표시광고법, 식품위생법, 화장품법 (cosmetics vertical)

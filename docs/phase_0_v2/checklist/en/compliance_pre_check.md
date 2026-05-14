# Checklist — Pre-broadcast compliance check

| | |
|---|---|
| Purpose | Audit broadcast scripts for 표시광고법 + vertical compliance before going live |
| FSD | [`../../fsd/compliance_pre_check.md`](../../fsd/compliance_pre_check.md) |
| Phase | Phase 2 (depends on legal consultation) |
| Language | English source — KO at [`../ko/compliance_pre_check.md`](../ko/compliance_pre_check.md) |

---

## Tech stack (at a glance)

- **Claude Sonnet 4.6** — audit LLM
- Rules corpus inline in prompt
- (Optional) regex pre-filter
- **Infra**: API calls, no GPU

Full table: [`../../fsd/compliance_pre_check.md`](../../fsd/compliance_pre_check.md) §2

---

## §1. Prerequisites

- [ ] [`../../fsd/compliance_pre_check.md`](../../fsd/compliance_pre_check.md) read
- [ ] **Legal consultation completed** on 표시광고법 + 식품위생법 rule set
- [ ] Rules corpus drafted and reviewed by counsel
- [ ] `ANTHROPIC_API_KEY` set

## §2. Build rule corpus

- [ ] Inline categories from FSD §5 in prompt
- [ ] Vertical-specific rules (food first)
- [ ] Few-shot violation examples for each category

## §3. Labeled eval

- [ ] 30 hand-labeled scripts (mix of clean + violation)
- [ ] Run eval; verify 100% catch on high-severity, ≥ 90% on medium
- [ ] False positive ≤ 15%

## §4. Integration

- [ ] Wire into broadcast pre-launch flow: scripts must pass before "approve to go live"
- [ ] Flagged segments returned to author for revision

## §5. Status board

| Step | Status |
|---|---|
| §1 Prerequisites (incl. legal) | ⬜ |
| §2 Rule corpus | ⬜ |
| §3 Labeled eval | ⬜ |
| §4 Integration | ⬜ |

## §6. Troubleshooting

| Issue | Response |
|---|---|
| Missing violations on eval | strengthen prompt with more few-shots in that category |
| Excessive false positives | tune rules to be more specific; add "permitted exceptions" examples |
| Legal scope changes | update corpus, re-run eval, deploy |

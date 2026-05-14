# Checklist — `make_voice_v2` (per-seller voice clone)

| | |
|---|---|
| FSD | [`../../fsd/make_voice_v2.md`](../../fsd/make_voice_v2.md) |
| Phase | Phase 3 (speculative; legal-dependent) |
| Language | English source — KO at [`../ko/make_voice_v2.md`](../ko/make_voice_v2.md) |

---

## Tech stack
- CosyVoice 2 cloning + uploader UI + consent capture

---

## §1. Prerequisites (pre-activation)
- [ ] Korean PIPA consultation complete (voice = biometric data)
- [ ] Consent workflow + retention policy locked
- [ ] Seller contract indemnification clauses drafted
- [ ] Right-to-delete workflow designed

## §2. Implementation (when activated)
- [ ] Build upload + consent UI
- [ ] Implement voice extraction + cloning
- [ ] Quality gate (manual review)
- [ ] Commit to tenant scope

## §3. Operations
- [ ] Right-to-delete tested end-to-end
- [ ] Quarterly retention audit

## §4. Troubleshooting
- Cloned voice misrepresents speaker → quality gate catches; iterate or reject
- PIPA audit requests → audit log + signed consent retrieval

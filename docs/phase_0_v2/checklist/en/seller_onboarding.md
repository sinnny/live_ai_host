# Checklist — Seller onboarding

| | |
|---|---|
| FSD | [`../../fsd/seller_onboarding.md`](../../fsd/seller_onboarding.md) |
| Phase | Phase 3 (UX informed by first 10 broadcasts) |
| Language | English source — KO at [`../ko/seller_onboarding.md`](../ko/seller_onboarding.md) |

---

## Tech stack
- Next.js + FastAPI (extends [`operator_dashboard.md`](operator_dashboard.md)) + OAuth + PDP scraper

---

## §1. Pre-activation
- [ ] First 10 broadcasts complete
- [ ] UX learnings captured (what tripped up early sellers?)
- [ ] Platform SSO (Naver / Kakao) availability confirmed

## §2. Onboarding flow (per FSD §3)
- [ ] SSO sign-up (Google v1 → Naver/Kakao as platforms activate)
- [ ] Tenant tier selection
- [ ] Mascot selection from library
- [ ] First product addition (PDP URL or photo upload)
- [ ] Script preview
- [ ] First broadcast schedule
- [ ] Pre-gen complete notification
- [ ] Approval → live

## §3. Acceptance test
- [ ] Time signup → first broadcast scheduled ≤ 1 hour
- [ ] Zero sales involvement for brand tier

## §4. Identity verification
- [ ] 사업자 등록증 verification flow (likely required for revenue-share platforms)
- [ ] Document upload + manual review or service integration

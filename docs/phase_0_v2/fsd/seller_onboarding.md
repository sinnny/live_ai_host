# Function Spec — Seller onboarding

| | |
|---|---|
| Status | Skeleton v1 (Phase 3 — depends on first 10 broadcasts to inform UX) |
| Phase | Phase 3 |
| Component | Self-serve seller onboarding flow + SSO with Naver/Kakao |
| Source documents | [`../../prd.md`](../../prd.md) §1.3 |
| Open dependencies | First-pilot UX learnings; platform partnership SSO availability |
| Last updated | 2026-05-13 |

---

## 1. Purpose

Per PRD §1.3 success criterion: "A brand seller should be able to log in, paste a product URL, and have a broadcast ready to launch within the system's pre-generation SLA — without sales involvement for routine broadcasts."

This FSD specifies the onboarding flow that makes that possible.

---

## 2. Tech stack

| Aspect | Tool |
|---|---|
| SSO | OAuth (Google v1; Naver / Kakao Phase 3) |
| Onboarding UI | Next.js |
| Backend | FastAPI |
| Product ingestion | PDP scraper + manual upload |

---

## 3. Onboarding steps (proposed)

1. Sign up via SSO (Google → Naver/Kakao when platform partnerships activate)
2. Choose tenant tier (brand vs platform-managed-sub-account)
3. Choose mascot from library (Daramzzi v1; multi-mascot in Phase 3)
4. Add first product(s) via PDP URL paste or photo upload
5. Auto-generate first script preview
6. Schedule first broadcast
7. Receive broadcast pre-gen complete notification
8. Approve broadcast → goes live on schedule

---

## 4. Success criteria

- Time from signup to first broadcast scheduled: ≤ 1 hour
- No sales involvement required for tiers below platform
- Self-serve product addition (no manual data entry by us)

---

## 5. Open

- Identity verification: do sellers need 사업자 등록증 verification before live broadcasts (likely yes for revenue-share platforms)?
- Onboarding-call vs purely automated: optional concierge for first broadcast?

---

## 6. References

- [`../../prd.md`](../../prd.md) §1.3
- [`operator_dashboard.md`](operator_dashboard.md) — overlapping UI surface
- [`multi_tenancy.md`](multi_tenancy.md) — RBAC model

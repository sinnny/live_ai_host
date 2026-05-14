# Function Spec — Naver 쇼핑라이브 platform integration

| | |
|---|---|
| Status | Skeleton v1 (Phase 3 — partnership-gated; API access pending) |
| Phase | Phase 3 (Sprint 5+ per [`../../prd.md`](../../prd.md) §1.1) |
| Component | Naver 쇼핑라이브 as a broadcast destination (RTMP + chat ingest) |
| Source documents | [`../../prd.md`](../../prd.md) §1.1, §4.3.6 |
| Open dependencies | Business development partnership with Naver; API access; whitelisting |
| Last updated | 2026-05-13 |

---

## 1. Purpose

Add Naver 쇼핑라이브 as a RTMP destination + chat source. Required for first paid pilots with Korean sellers who depend on Naver's commerce flow.

---

## 2. Tech stack

| Aspect | Notes |
|---|---|
| RTMP push | Naver provides RTMP endpoint per broadcast (similar to YouTube model) |
| Chat ingest | Naver Shopping Live chat API (custom; not documented publicly) |
| Auth | Partnership-issued credentials |
| Compliance | Naver-specific platform rules (likely supplementing 표시광고법) |

---

## 3. Open: known unknowns

- Exact RTMP URL format
- Chat API authentication mechanism
- Allowed bit rates / resolution
- Ad-disclosure UI requirements
- Tenant onboarding flow (do sellers connect their Naver account to our system, or does our tenancy directly push to Naver streams?)

---

## 4. Integration plan (high level, pending partnership)

1. Business development → partnership agreement signed.
2. Technical onboarding with Naver eng team.
3. Implement RTMP push + chat ingest connectors.
4. Compliance review for Naver-specific rules.
5. Pilot with 1-2 food sellers.
6. GA across food vertical.

---

## 5. References

- [`rtmp_output.md`](rtmp_output.md) — RTMP base
- [`chat_ingest.md`](chat_ingest.md) — chat base
- Naver 쇼핑라이브 documentation (partnership-gated)

# Function Spec — Kakao 쇼핑 라이브 platform integration

| | |
|---|---|
| Status | Skeleton v1 (Phase 3 — closed API, business development required) |
| Phase | Phase 3 (v2 per [`../../prd.md`](../../prd.md) §1.1) |
| Component | Kakao 쇼핑 라이브 as a broadcast destination |
| Source documents | [`../../prd.md`](../../prd.md) §1.1 |
| Open dependencies | Kakao business development; API access |
| Last updated | 2026-05-13 |

---

## 1. Purpose

Add Kakao 쇼핑 라이브 as a destination. Same general shape as [`naver_platform.md`](naver_platform.md) but Kakao-specific.

---

## 2. Open unknowns

- API access process (Kakao has historically been more closed than Naver)
- Bitrate / quality requirements
- Chat ingest mechanism (Kakao Talk integration?)
- Pricing / revenue sharing model

---

## 3. Path forward

Closed API + opaque BD process. Likely 6+ month timeline after Naver integration is stable. Prioritize after Naver is live + producing revenue.

---

## 4. References

- [`naver_platform.md`](naver_platform.md) — sibling Korean platform
- [`rtmp_output.md`](rtmp_output.md), [`chat_ingest.md`](chat_ingest.md)

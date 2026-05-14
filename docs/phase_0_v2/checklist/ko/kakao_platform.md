# Checklist (KO) — Kakao 쇼핑 라이브 통합

| | |
|---|---|
| FSD | [`../../fsd/kakao_platform.md`](../../fsd/kakao_platform.md) |
| Phase | Phase 3 — v2 |
| 언어 정보 | 영어 원본 [`../en/kakao_platform.md`](../en/kakao_platform.md) — 이 문서는 한국어 번역 |

---

## 기술 스택
- Kakao 발급 엔드포인트 (파트너십 의존; 폐쇄 API)

---

## §1. 비즈니스 개발 (활성화 전)
- [ ] Kakao BD 대화 시작 (Naver live 이후)
- [ ] 파트너십 계약 체결
- [ ] 기술 온보딩 스케줄

## §2. 구현
- [ ] RTMP 커넥터
- [ ] Chat ingest 커넥터 (KakaoTalk 통합?)
- [ ] 컴플라이언스: Kakao 별 플랫폼 룰
- [ ] [`pricing_billing.md`](pricing_billing.md) 에 가격 / 매출 분배 통합

## §3. 파일럿
- [ ] 셀러 1-2개를 Kakao 경로로
- [ ] 첫 방송 E2E

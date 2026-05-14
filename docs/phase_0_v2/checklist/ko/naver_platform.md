# Checklist (KO) — Naver 쇼핑라이브 통합

| | |
|---|---|
| FSD | [`../../fsd/naver_platform.md`](../../fsd/naver_platform.md) |
| Phase | Phase 3 — Sprint 5+ |
| 언어 정보 | 영어 원본 [`../en/naver_platform.md`](../en/naver_platform.md) — 이 문서는 한국어 번역 |

---

## 기술 스택
- Naver 발급 RTMP 엔드포인트 + chat API (파트너십 의존)

---

## §1. 비즈니스 개발 (활성화 전)
- [ ] 파트너십 대화 시작
- [ ] 파트너십 계약 체결
- [ ] Naver 엔지니어팀과 기술 컨택 확립

## §2. 기술 통합
- [ ] Naver API 문서 + 자격증명 수령
- [ ] Naver RTMP 커넥터 구현 ([`rtmp_output.md`](rtmp_output.md) 확장)
- [ ] Naver chat ingest 구현 ([`chat_ingest.md`](chat_ingest.md) 확장)
- [ ] Naver 별 광고 공시 UI

## §3. 파일럿
- [ ] 식품 셀러 1-2개를 Naver 경로로 온보딩
- [ ] Naver 쇼핑라이브에서 첫 방송 end-to-end
- [ ] Naver 별 규칙 컴플라이언스 검토

## §4. 트러블슈팅
- API 접근 취소 → 파트너십 에스컬레이션
- Naver 별 컴플라이언스 플래그 → 룰 코퍼스 업데이트

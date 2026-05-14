# Checklist (KO) — 셀러 온보딩

| | |
|---|---|
| FSD | [`../../fsd/seller_onboarding.md`](../../fsd/seller_onboarding.md) |
| Phase | Phase 3 (첫 10개 방송에서 UX 학습) |
| 언어 정보 | 영어 원본 [`../en/seller_onboarding.md`](../en/seller_onboarding.md) — 이 문서는 한국어 번역 |

---

## 기술 스택
- Next.js + FastAPI ([`operator_dashboard.md`](operator_dashboard.md) 확장) + OAuth + PDP scraper

---

## §1. 사전 준비
- [ ] 첫 10개 방송 완료
- [ ] UX 학습 캡처 (초기 셀러가 어디서 막혔는가?)
- [ ] 플랫폼 SSO (Naver / Kakao) 가용성 확인

## §2. 온보딩 흐름 (FSD §3)
- [ ] SSO 회원가입 (v1 Google → 플랫폼 활성화 시 Naver/Kakao)
- [ ] 테넌트 tier 선택
- [ ] 라이브러리에서 마스코트 선택
- [ ] 첫 제품 추가 (PDP URL 또는 사진 업로드)
- [ ] 스크립트 미리보기
- [ ] 첫 방송 스케줄
- [ ] 사전 생성 완료 알림
- [ ] 승인 → 라이브

## §3. 수용 테스트
- [ ] 가입 → 첫 방송 스케줄 시간 ≤ 1시간
- [ ] 브랜드 tier 에서 영업 개입 0

## §4. 신원 검증
- [ ] 사업자 등록증 검증 흐름 (매출 분배 플랫폼은 필요할 가능성)
- [ ] 문서 업로드 + 수동 검토 또는 서비스 통합

# Checklist (KO) — `make_mascot_v2` (셀러 셀프서비스)

| | |
|---|---|
| FSD | [`../../fsd/make_mascot_v2.md`](../../fsd/make_mascot_v2.md) |
| Phase | Phase 3 (speculative) |
| 언어 정보 | 영어 원본 [`../en/make_mascot_v2.md`](../en/make_mascot_v2.md) — 이 문서는 한국어 번역 |

---

## 기술 스택
- [`make_mascot.md`](make_mascot.md) 상속 + Next.js UI + 테넌트 스코프 큐

---

## §1. 사전 준비 (활성화 전)
- [ ] 시스템 마스코트로 첫 10개 방송 완료
- [ ] 셀러별 마스코트 수요 확인 (고객 피드백)
- [ ] 법률: AI 생성 캐릭터 IP 소유권 명확화
- [ ] 비용 모델: 마스코트별 청구 vs 번들

## §2. 구현 (활성화 시)
- [ ] `make_mascot` config 일반화 — CLI → API 입력 매개변수화
- [ ] 셀러용 UI (마스코트 위저드) 구축
- [ ] 승인 게이트 워크플로우를 셀러 대시보드에 노출
- [ ] 테넌트 스코프 스토리지 prefix

## §3. 품질 게이트
- [ ] 브랜드 일관성 검토 (수동)
- [ ] 라이브 방송에서 마스코트 사용 가능해지기 전 게시 게이트

## §4. 트러블슈팅
- 셀러 정의 brief 가 off-brand 마스코트 생성 → brief 예제로 코칭; 수동 오버라이드

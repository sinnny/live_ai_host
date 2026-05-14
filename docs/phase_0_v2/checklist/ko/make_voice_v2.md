# Checklist (KO) — `make_voice_v2` (셀러별 음성 클로닝)

| | |
|---|---|
| FSD | [`../../fsd/make_voice_v2.md`](../../fsd/make_voice_v2.md) |
| Phase | Phase 3 (speculative; 법률 의존) |
| 언어 정보 | 영어 원본 [`../en/make_voice_v2.md`](../en/make_voice_v2.md) — 이 문서는 한국어 번역 |

---

## 기술 스택
- CosyVoice 2 cloning + 업로더 UI + 동의 수집

---

## §1. 사전 준비 (활성화 전)
- [ ] 한국 PIPA 자문 완료 (음성 = 생체정보)
- [ ] 동의 워크플로우 + 보관 정책 lock
- [ ] 셀러 계약 면책 조항 작성
- [ ] 삭제 권리 워크플로우 설계

## §2. 구현 (활성화 시)
- [ ] 업로드 + 동의 UI 구축
- [ ] 음성 추출 + 클로닝 구현
- [ ] 품질 게이트 (수동 검토)
- [ ] 테넌트 스코프에 commit

## §3. 운영
- [ ] 삭제 권리 end-to-end 테스트
- [ ] 분기별 보관 감사

## §4. 트러블슈팅
- 클로닝된 음성이 화자 왜곡 → 품질 게이트가 catch; 반복 또는 거부
- PIPA 감사 요청 → 감사 로그 + 서명 동의 retrieval

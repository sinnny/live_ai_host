# Checklist (KO) — 컴플라이언스 운영 매뉴얼

| | |
|---|---|
| FSD | [`../../fsd/compliance_runbook.md`](../../fsd/compliance_runbook.md) |
| Phase | Phase 3 (법률 자문 의존) |
| 언어 정보 | 영어 원본 [`../en/compliance_runbook.md`](../en/compliance_runbook.md) — 이 문서는 한국어 번역 |

---

## 기술 스택
- git 의 버전 관리된 룰 코퍼스 + 법률 검토 프로세스

---

## §1. 상시 역할
- [ ] 법률 자문 retainer 계약
- [ ] 컴플라이언스 책임자 지정
- [ ] Engineering 로테이션 정의

## §2. 분기별 검토 사이클
- [ ] 최신 표시광고법/식품위생법/화장품법 개정 pull
- [ ] 프로덕션 감사 로그의 FP/FN 비율 검토
- [ ] 룰 코퍼스 + few-shot 업데이트
- [ ] 라벨된 평가 재실행
- [ ] 스테이징 → 프로덕션 배포

## §3. 사고 대응
- [ ] EMERGENCY_LOOP 트리거 로그
- [ ] 근본 원인: 룰 갭 vs 런타임 갭
- [ ] 회귀 테스트 추가
- [ ] 필요 시 셀러 + 법률 공시

## §4. 트러블슈팅
- 동일 카테고리에서 반복 회귀 → 예제 추가가 아닌 근본 원인 프롬프트 엔지니어링

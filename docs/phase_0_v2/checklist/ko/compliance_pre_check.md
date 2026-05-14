# Checklist (KO) — 사전 방송 컴플라이언스 체크

| | |
|---|---|
| 목적 | 라이브 전 방송 스크립트의 표시광고법 + 버티컬 컴플라이언스 audit |
| FSD | [`../../fsd/compliance_pre_check.md`](../../fsd/compliance_pre_check.md) |
| Phase | Phase 2 (법률 자문 의존) |
| 언어 정보 | 영어 원본 [`../en/compliance_pre_check.md`](../en/compliance_pre_check.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **Claude Sonnet 4.6** — audit LLM
- 프롬프트 내 인라인 룰 코퍼스
- (선택) 사전 regex 필터
- **인프라**: API 호출, GPU 없음

상세: [`../../fsd/compliance_pre_check.md`](../../fsd/compliance_pre_check.md) §2

---

## §1. 사전 준비

- [ ] [`../../fsd/compliance_pre_check.md`](../../fsd/compliance_pre_check.md) 읽기
- [ ] **법률 자문 완료** — 표시광고법 + 식품위생법 룰 셋
- [ ] 룰 코퍼스 작성 + 변호인 검토
- [ ] `ANTHROPIC_API_KEY` 설정

## §2. 룰 코퍼스 빌드

- [ ] FSD §5 의 카테고리 프롬프트에 인라인
- [ ] 버티컬별 룰 (식품 먼저)
- [ ] 각 카테고리에 위반 few-shot 예제

## §3. 라벨링된 평가

- [ ] hand-labeled 스크립트 30개 (clean + 위반 혼합)
- [ ] 평가 실행; high-severity 100% catch, medium ≥ 90% 확인
- [ ] False positive ≤ 15%

## §4. 통합

- [ ] 방송 사전 출시 흐름에 wire: "라이브 승인" 전에 스크립트 통과 필수
- [ ] 플래그 세그먼트는 작성자에게 수정 요청 반환

## §5. 진행 상태 보드

| 단계 | 상태 |
|---|---|
| §1 사전 준비 (법률 포함) | ⬜ |
| §2 룰 코퍼스 | ⬜ |
| §3 라벨링된 평가 | ⬜ |
| §4 통합 | ⬜ |

## §6. 트러블슈팅

| 이슈 | 대응 |
|---|---|
| 평가에서 위반 누락 | 해당 카테고리에 few-shot 강화 |
| 과도한 false positive | 룰을 더 구체적으로; "허용 예외" 예제 추가 |
| 법률 범위 변경 | 코퍼스 업데이트, 재평가, 배포 |

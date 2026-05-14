# Checklist (KO) — 가격 + 청구

| | |
|---|---|
| 목적 | 방송당 비용 추적 및 테넌트 인보이스 생성 |
| FSD | [`../../fsd/pricing_billing.md`](../../fsd/pricing_billing.md) |
| Phase | Phase 2 (가격 모델 결정 의존) |
| 언어 정보 | 영어 원본 [`../en/pricing_billing.md`](../en/pricing_billing.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- 자체 Python — 비용 집계기
- **Stripe Invoicing** (managed) 또는 **Toss Payments** (KR-native)
- `observability.md` + `audit_log.md` 에서 읽음
- **인프라**: 백엔드 호스트의 cron job

상세: [`../../fsd/pricing_billing.md`](../../fsd/pricing_billing.md) §2

---

## §1. 사전 준비

- [ ] [`../../fsd/pricing_billing.md`](../../fsd/pricing_billing.md) 읽기
- [ ] **가격 모델 lock** (PRD §8 OQ #5 founder 결정)
- [ ] Stripe 또는 Toss 계정 셋업
- [ ] Webhook 엔드포인트 구성

## §2. 비용 속성

- [ ] 매일 cron 이 observability + audit log 에서 방송당 비용 집계
- [ ] 테넌트별 rollup
- [ ] 클라우드 청구서와 수동 reconciliation (목표: ±5% 정확도)

## §3. 인보이스 생성

- [ ] 월간 cron 이 Stripe/Toss 통해 인보이스 emit
- [ ] 테넌트 청구 연락처에 이메일 배달
- [ ] 결제 webhook 이 `billing_state` 업데이트

## §4. 진행 상태 보드

| 단계 | 상태 |
|---|---|
| §1 사전 준비 (가격 결정 포함) | ⬜ |
| §2 비용 속성 | ⬜ |
| §3 인보이스 생성 | ⬜ |

## §5. 트러블슈팅

| 이슈 | 대응 |
|---|---|
| 비용 속성 drift > 5% | 라인별 비용 reconciliation; 누락된 GPU-hour 추적 확인 |
| 인보이스 이메일 bounce | 백업 청구 연락처 유지 |
| 결제 webhook 미수신 | webhook 재시도 + 수동 reconciliation 스크립트 구현 |

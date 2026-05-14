# Checklist (KO) — Observability 스택

| | |
|---|---|
| 목적 | 필수 대시보드 + 알림 포함 Prometheus + Grafana + OpenTelemetry 구축 |
| FSD | [`../../fsd/observability.md`](../../fsd/observability.md) |
| Phase | Phase 2 |
| 언어 정보 | 영어 원본 [`../en/observability.md`](../en/observability.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **Prometheus** (Apache 2.0) — 메트릭
- **Grafana** OSS (AGPL) — 대시보드
- **OpenTelemetry** SDK + collector (Apache 2.0)
- **Jaeger** 또는 **Tempo** (Apache 2.0) — trace 백엔드
- **인프라**: managed (Grafana Cloud) 또는 self-host

상세: [`../../fsd/observability.md`](../../fsd/observability.md) §2

---

## §1. 사전 준비

- [ ] [`../../fsd/observability.md`](../../fsd/observability.md) 읽기
- [ ] Prometheus + Grafana + trace 백엔드 프로비저닝

## §2. 계측

- [ ] FSD §3 에 따라 각 Phase 1 에이전트가 Prometheus 메트릭 emit
- [ ] OpenTelemetry trace 가 Redis 헤더로 전파
- [ ] 모든 chat→frame 턴에 trace ID 할당

## §3. 대시보드

- [ ] Operator 대시보드 (지연, FSM, 에이전트 health)
- [ ] Engineering 대시보드 (단계별 p50/p95/p99, GPU)
- [ ] Cost 대시보드 (LLM 토큰, GPU-hours)
- [ ] Compliance 대시보드 (moderator verdicts)

## §4. 알림

- [ ] FSD §6 의 6개 알림 구성
- [ ] 알림 경로 테스트 (Slack/email/SMS webhook)

## §5. 진행 상태 보드

| 단계 | 상태 |
|---|---|
| §1 사전 준비 | ⬜ |
| §2 계측 | ⬜ |
| §3 대시보드 | ⬜ |
| §4 알림 | ⬜ |

## §6. 트러블슈팅

| 이슈 | 대응 |
|---|---|
| 메트릭 누락 | Prometheus scrape target 확인 |
| Trace 불완전 | Redis 브리지 통한 컨텍스트 전파 확인 |
| 알림 false positive | 1주 관찰 윈도우로 임계값 튜닝 |

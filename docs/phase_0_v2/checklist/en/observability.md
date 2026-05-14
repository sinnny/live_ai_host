# Checklist — Observability stack

| | |
|---|---|
| Purpose | Stand up Prometheus + Grafana + OpenTelemetry with essential dashboards + alerts |
| FSD | [`../../fsd/observability.md`](../../fsd/observability.md) |
| Phase | Phase 2 |
| Language | English source — KO at [`../ko/observability.md`](../ko/observability.md) |

---

## Tech stack (at a glance)

- **Prometheus** (Apache 2.0) — metrics
- **Grafana** OSS (AGPL) — dashboards
- **OpenTelemetry** SDK + collector (Apache 2.0)
- **Jaeger** or **Tempo** (Apache 2.0) — trace backend
- **Infra**: managed (Grafana Cloud) or self-hosted

Full table: [`../../fsd/observability.md`](../../fsd/observability.md) §2

---

## §1. Prerequisites

- [ ] [`../../fsd/observability.md`](../../fsd/observability.md) read
- [ ] Prometheus + Grafana + trace backend provisioned

## §2. Instrumentation

- [ ] Each Phase 1 agent emits Prometheus metrics per FSD §3
- [ ] OpenTelemetry traces propagate via Redis headers
- [ ] Trace ID populated on every chat→frame turn

## §3. Dashboards

- [ ] Operator dashboard built (latency, FSM, agent health)
- [ ] Engineering dashboard built (p50/p95/p99 per stage, GPU)
- [ ] Cost dashboard built (LLM tokens, GPU-hours)
- [ ] Compliance dashboard built (moderator verdicts)

## §4. Alerts

- [ ] Configure 6 alerts per FSD §6
- [ ] Test alert paths (Slack/email/SMS via webhook)

## §5. Status board

| Step | Status |
|---|---|
| §1 Prerequisites | ⬜ |
| §2 Instrumentation | ⬜ |
| §3 Dashboards | ⬜ |
| §4 Alerts | ⬜ |

## §6. Troubleshooting

| Issue | Response |
|---|---|
| Missing metrics | check Prometheus scrape targets |
| Traces incomplete | verify context propagation across Redis bridge |
| Alert false positives | tune thresholds with 1-week observation window |

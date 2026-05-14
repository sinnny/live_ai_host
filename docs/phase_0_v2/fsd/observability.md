# Function Spec — Observability (Prometheus + Grafana + OpenTelemetry)

| | |
|---|---|
| Status | Spec v1 (Phase 2) |
| Phase | Phase 2 |
| Component | Runtime telemetry: metrics, traces, dashboards, alerts |
| Source documents | [`../../prd.md`](../../prd.md) §5.3 |
| Last updated | 2026-05-13 |

---

## 1. Purpose

Per-stage latency tracking, agent health, infrastructure metrics. Distinct from `audit_log.md` (which is per-event for compliance/debug); this is for ops + SLA monitoring.

---

## 2. Technology stack

| Stage | Tool | License |
|---|---|---|
| Metrics | **Prometheus** | Apache 2.0 |
| Dashboards | **Grafana** OSS edition | AGPL |
| Tracing | **OpenTelemetry** SDK + collector | Apache 2.0 |
| Tracing backend | Jaeger (default) or Tempo | Apache 2.0 |
| App errors | Sentry (self-hosted) or simpler log-based alerting | BSD |

---

## 3. Metric inventory (essential)

| Metric | Type | Description |
|---|---|---|
| `broadcast_latency_ms{stage}` | histogram | per-stage latency from `broadcast_orchestrator.md` traces |
| `agent_up{agent}` | gauge | 1 if agent recently health-pinged |
| `llm_api_calls_total{model, status}` | counter | – |
| `llm_token_usage_total{model, mode}` | counter | for cost attribution |
| `tts_queue_depth` | gauge | backpressure signal |
| `rtmp_dropouts_total` | counter | – |
| `gpu_memory_used_bytes` | gauge | per-GPU |
| `gpu_utilization_pct` | gauge | – |

---

## 4. Traces

Single trace per chat→frame_out turn, spanning chat_ingest → moderator → director → host → moderator → tts → renderer → compositor → rtmp.

OpenTelemetry trace_id propagated via Redis headers across agents.

---

## 5. Dashboards (Grafana)

| Dashboard | Audience |
|---|---|
| Operator | active broadcast latency, FSM state, agent health |
| Engineering | per-stage p50/p95/p99, error rates, GPU utilization |
| Cost | LLM token usage by model + tenant, GPU-hours |
| Compliance | moderator verdicts by category, false-positive estimates |

---

## 6. Alerting

| Alert | Condition | Severity |
|---|---|---|
| Broadcast latency p95 > 2s | sustained 5 min | P1 (page) |
| Agent down | 3 missed pings | P1 |
| RTMP disconnect during broadcast | any | P1 |
| GPU OOM | any | P1 |
| LLM error rate > 5% | sustained 2 min | P2 |
| Disk > 85% | any | P3 |

---

## 7. References

- [`../../prd.md`](../../prd.md) §5.3
- All Phase 1 sibling FSDs (each emits metrics + traces)
- Prometheus / Grafana / OpenTelemetry docs

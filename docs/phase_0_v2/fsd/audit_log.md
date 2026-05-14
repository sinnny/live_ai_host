# Function Spec — Audit log (ClickHouse)

| | |
|---|---|
| Status | Spec v1 (Phase 2) |
| Phase | Phase 2 |
| Component | High-cardinality event log for broadcasts — every comment, decision, verdict, audio chunk |
| Source documents | [`../../prd.md`](../../prd.md) §4.5, §5.3 |
| Last updated | 2026-05-13 |

---

## 1. Purpose

Capture every meaningful event in a broadcast for post-hoc replay, compliance review, debugging. Postgres handles the relational core ([`data_model.md`](data_model.md)); ClickHouse handles the high-volume per-line events.

---

## 2. Technology stack

| Stage | Tool | License |
|---|---|---|
| Event store | **ClickHouse** | Apache 2.0 |
| Producer client | `clickhouse-driver` Python | MIT |
| Schema migrations | inline DDL versioning | – |

---

## 3. Tables

### 3.1 `broadcast_events`

```
broadcast_id String,
event_id UUID,
timestamp DateTime64(3),
event_type Enum('comment_in','moderator_in','director_decision','host_draft','moderator_audit','tts_chunk','frame_meta','rtmp_status','agent_health'),
agent String,
payload JSON,
tenant_id UUID,
trace_id String,
duration_ms UInt32

PARTITION BY toYYYYMM(timestamp)
ORDER BY (broadcast_id, timestamp)
```

### 3.2 `decision_audit`

Materialized view filtered to decision-relevant events for compliance review:

```
broadcast_id, event_id, timestamp,
verdict, reason, severity,
input_summary, output_summary
```

---

## 4. Ingestion

- Agents publish events to Redis topic `broadcast.audit.<id>`.
- Ingester service buffers + bulk inserts to ClickHouse (10-second flush window).
- Backpressure: if ClickHouse slow, buffer in Redis with bounded size; alert if buffer > threshold.

---

## 5. Query patterns

- Replay broadcast: SELECT all events for `broadcast_id` ORDER BY timestamp.
- Compliance review: `decision_audit` filtered by `severity >= 'medium'`.
- Latency analysis: GROUP BY `event_type` aggregating `duration_ms`.

---

## 6. Retention

- Hot: 90 days (configurable per tenant).
- Cold: archive to S3 as Parquet, 1 year.

---

## 7. References

- [`../../prd.md`](../../prd.md) §4.5, §5.3
- [`broadcast_orchestrator.md`](broadcast_orchestrator.md), [`llm_moderator.md`](llm_moderator.md) — primary event producers
- ClickHouse docs

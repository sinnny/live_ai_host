# Checklist — Audit log (ClickHouse)

| | |
|---|---|
| Purpose | Bring up ClickHouse + ingester for broadcast event logging |
| FSD | [`../../fsd/audit_log.md`](../../fsd/audit_log.md) |
| Phase | Phase 2 |
| Language | English source — KO at [`../ko/audit_log.md`](../ko/audit_log.md) |

---

## Tech stack (at a glance)

- **ClickHouse** (Apache 2.0) — event store
- **clickhouse-driver** Python (MIT)
- **Redis** — buffer + producer pipe
- **Infra**: ClickHouse on dedicated VM or managed (ClickHouse Cloud)

Full table: [`../../fsd/audit_log.md`](../../fsd/audit_log.md) §2

---

## §1. Prerequisites

- [ ] [`../../fsd/audit_log.md`](../../fsd/audit_log.md) read
- [ ] ClickHouse instance provisioned
- [ ] Connection details in env

## §2. Schema

- [ ] Create `broadcast_events` table per FSD §3.1
- [ ] Create `decision_audit` materialized view per §3.2
- [ ] Verify partitioning + ORDER BY

## §3. Ingester service

- [ ] Subscribe to Redis topic `broadcast.audit.<id>`
- [ ] Buffer for 10 sec, bulk insert
- [ ] Handle ClickHouse backpressure: bounded Redis buffer, alert if full

## §4. Replay test

- [ ] Run a test broadcast end-to-end
- [ ] Query ClickHouse to replay events for that broadcast
- [ ] Verify completeness vs expected event count

## §5. Status board

| Step | Status |
|---|---|
| §1 Prerequisites | ⬜ |
| §2 Schema | ⬜ |
| §3 Ingester | ⬜ |
| §4 Replay test | ⬜ |

## §6. Troubleshooting

| Issue | Response |
|---|---|
| ClickHouse insert errors | check schema versioning; rotate to new table on incompatible change |
| Buffer fills up | scale ingester; increase ClickHouse insert capacity |
| Replay missing events | check producer instrumentation across agents |

# Checklist — Broadcast orchestrator (live FSM)

| | |
|---|---|
| Purpose | Drive a live 4-hour broadcast end-to-end coordinating all Phase 1 agents |
| FSD | [`../../fsd/broadcast_orchestrator.md`](../../fsd/broadcast_orchestrator.md) |
| Evolves from | [`orchestrator.md`](orchestrator.md) (prototype offline) |
| Phase | Phase 1 |
| Language | English source — KO at [`../ko/broadcast_orchestrator.md`](../ko/broadcast_orchestrator.md) |

---

## Tech stack (at a glance)

- **transitions** Python (MIT) — FSM
- **Redis** Pub/Sub + Streams — event bus
- **Celery + Redis broker** (BSD/MIT) — job queue at MVP scale
- **FastAPI** (MIT) — coordination API
- (Phase 2) **Temporal** (MIT) — production reliability replacement
- **Infra**: runs on L40S, low overhead

Full table: [`../../fsd/broadcast_orchestrator.md`](../../fsd/broadcast_orchestrator.md) §2

---

## Session resume

FSM state persisted to Redis every tick. On restart, reads state and resumes. If Redis lost: broadcast unrecoverable, schedule new.

---

## §1. Prerequisites

- [ ] All Phase 1 sibling components' checklists complete:
  - [ ] [`chat_ingest.md`](chat_ingest.md) ✓
  - [ ] [`llm_moderator.md`](llm_moderator.md) ✓
  - [ ] [`llm_director.md`](llm_director.md) ✓
  - [ ] [`llm_host.md`](llm_host.md) ✓
  - [ ] [`rag.md`](rag.md) ✓
  - [ ] [`tts_streaming.md`](tts_streaming.md) ✓
  - [ ] [`renderer_live.md`](renderer_live.md) ✓
  - [ ] [`compositor_obs.md`](compositor_obs.md) ✓
  - [ ] [`rtmp_output.md`](rtmp_output.md) ✓
- [ ] Broadcast schedule YAML prepared (per FSD §7)
- [ ] Redis + Celery worker running

---

## §2. FSM unit tests

- [ ] Run: `pytest broadcast_orchestrator/tests/test_fsm.py`
- [ ] Verify all valid transitions pass
- [ ] Verify invalid transitions are rejected

---

## §3. Dry-run a 10-min broadcast

- [ ] Run with all agents mocked: `python broadcast_orchestrator.py start --dry-run --schedule schedule.yaml`
- [ ] Verify FSM progresses: INIT → WARMUP → FULL_MASCOT → ... → DONE
- [ ] No deadlocks

---

## §4. End-to-end 10-min live (test_3 Gate 1)

- [ ] Bring up all agents (each per its checklist)
- [ ] Run: `python broadcast_orchestrator.py start --broadcast-id <id> --schedule schedule.yaml`
- [ ] Inject scripted comments via `chat_injector.py`
- [ ] Capture local RTMP output
- [ ] Measure end-to-end latency per [`../prototype_spec.md`](../prototype_spec.md)-equivalent gate

---

## §5. Recovery drills

- [ ] Kill `llm_host` mid-broadcast — orchestrator should transition to EMERGENCY_LOOP, restart agent, transition back
- [ ] Repeat for `llm_director`, `llm_moderator`, `tts_streaming`, `renderer_live`
- [ ] Verify each recovery ≤ 30s

---

## §6. 4-hour stability (test_3 Gate 2)

- [ ] Start broadcast for 4 hours on unlisted YouTube
- [ ] Monitor:
  - [ ] FSM state distribution
  - [ ] Agent health pings
  - [ ] Audit log completeness
  - [ ] RTMP stability
  - [ ] Latency drift over time
- [ ] Apply Gate G2 pass criteria (per deferred test_3_spec.md §6.3)

---

## §7. Status board

| Step | Status | Notes |
|---|---|---|
| §1 Prerequisites | ⬜ Pending | all 9 siblings ready |
| §2 FSM unit tests | ⬜ Pending | – |
| §3 Dry-run | ⬜ Pending | – |
| §4 Gate 1 (latency) | ⬜ Pending | p95 ≤ 1.5s |
| §5 Recovery drills | ⬜ Pending | each recovery ≤ 30s |
| §6 Gate 2 (4-hr) | ⬜ Pending | per test_3_spec |

---

## §8. Troubleshooting

| Issue | Cause | Response |
|---|---|---|
| Deadlock in FSM | Director loops on same action | review prompt; add state-awareness examples |
| Agent restart loops | underlying bug not transient | escalate; pause auto-restart |
| Redis OOM | event flood | check chat ingest rate; add Redis maxmemory eviction |
| Latency drift over hours | LLM cache expiry | use Anthropic extended cache (1-hr TTL) |
| All agents healthy but no output | bus topic misconfig | check Redis subscriber lists with `CLIENT LIST` |

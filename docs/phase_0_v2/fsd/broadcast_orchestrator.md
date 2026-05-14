# Function Spec — Broadcast orchestrator (live FSM)

| | |
|---|---|
| Status | Spec v1 (Phase 1 / test_3) |
| Phase | Phase 1 |
| Component | Live broadcast state machine and inter-agent coordinator |
| Source documents | [`../../prd.md`](../../prd.md) §4 (overall), §4.3 (live runtime) |
| Evolves from | [`orchestrator.md`](orchestrator.md) (prototype offline pipeline) |
| Last updated | 2026-05-13 |

---

## 1. Purpose and scope

### 1.1 What this FSD defines

The central nervous system of a live broadcast. Manages:
- Broadcast lifecycle (start, run, end)
- FSM state: `FULL_MASCOT | PIP | SCRIPTED_CLIP | EMERGENCY_LOOP`
- Coordination across agents (Director / Host / Moderator / TTS / Renderer / Compositor)
- Event routing via Redis topics
- Audit log emission

### 1.2 Out of scope

- The decision logic of what happens next (delegated to `llm_director.md`)
- Generating content (delegated to `llm_host.md`)
- Filtering (delegated to `llm_moderator.md`)
- Persistence / multi-broadcast queuing (delegated to `data_model.md` + Temporal in Phase 2)

### 1.3 Success criterion for test_3

1. Drives a 4-hour broadcast end-to-end with zero stuck states.
2. Recovers from each agent's transient failures per their FSDs.
3. Audit log captures every Director decision + Moderator verdict.

---

## 2. Technology stack (locked)

| Stage | Tool | License | Why |
|---|---|---|---|
| FSM | `transitions` Python | MIT | declarative, mature |
| Event bus | Redis Pub/Sub + Streams | – | decoupled, multi-consumer |
| Job persistence (MVP) | Celery + Redis broker | BSD/MIT | sufficient at MVP scale |
| Job persistence (production) | Temporal | MIT | production-grade reliability — Phase 2 swap |
| HTTP coordination API | FastAPI | MIT | – |

---

## 3. State machine

### 3.1 States

| State | Description |
|---|---|
| `INIT` | broadcast scheduled, not started |
| `WARMUP` | LLM caches warming, agents starting |
| `FULL_MASCOT` | mascot is the focal element |
| `PIP` | mascot small overlay, B-roll fullscreen |
| `SCRIPTED_CLIP` | pre-rendered clip playing |
| `EMERGENCY_LOOP` | "잠시만 기다려 주세요" interstitial |
| `ENDING` | wrap-up beats, sign-off line |
| `DONE` | broadcast complete, RTMP closed |

### 3.2 Transitions

```
INIT → WARMUP (on schedule_start)
WARMUP → FULL_MASCOT (when caches warm + RTMP up)
FULL_MASCOT ↔ PIP ↔ SCRIPTED_CLIP (per Director decisions)
* → EMERGENCY_LOOP (on agent failure / operator button)
EMERGENCY_LOOP → FULL_MASCOT (on resume / repair)
FULL_MASCOT → ENDING (on schedule_end)
ENDING → DONE (after sign-off)
```

---

## 4. Inputs

- Broadcast schedule (start time, end time, products, mascot)
- Live events from agents (chat comments, Director decisions, Moderator verdicts, agent health pings)

---

## 5. Outputs

- FSM state changes published to Redis `broadcast.fsm.<id>`
- Tick events to Director: `broadcast.tick.<id>` every 5-10s
- State-change events to renderer: WebSocket
- Scene-change events to compositor: obs-websocket
- Audit events: `broadcast.audit.<id>` (consumed by `audit_log.md`)

---

## 6. Architecture (live runtime composition)

```
broadcast_orchestrator (this FSD)
  ├── tick scheduler (5-10s)
  ├── FSM (transitions library)
  ├── agent health monitor
  └── event router (Redis)

Coordinates:
  chat_ingest → llm_moderator → llm_director → llm_host → llm_moderator (audit) → tts_streaming → renderer_live → compositor_obs → rtmp_output
```

---

## 7. Execution

```bash
python broadcast_orchestrator.py start \
  --broadcast-id bc_2026_05_13_001 \
  --schedule-file broadcasts/bc_.../schedule.yaml \
  --redis-url redis://localhost:6379/0
```

`schedule.yaml`:
```yaml
broadcast_id: bc_2026_05_13_001
title: 다람찌 첫 시연
mascot: daramzzi
start_at: 2026-05-14T20:00:00+09:00
end_at: 2026-05-14T22:00:00+09:00
products: [kimchi_01, ramyun_01, gochujang_01]
voice_ref: voice/daramzzi_ref.wav
rtmp_dest: ${RTMP_DEST_URL}
```

---

## 8. Quality criteria

| Criterion | Method | Threshold |
|---|---|---|
| 4-hr run with no deadlocks | live monitoring | 0 |
| Agent failure recovery | inject kill on each agent | recovery ≤ 30s |
| EMERGENCY_LOOP trigger latency | manual button → scene change | ≤ 2s |
| Audit log completeness | post-broadcast review | 100% of decisions/verdicts captured |

---

## 9. Failure modes

| Mode | Symptom | Response |
|---|---|---|
| Agent dies (any one of chat/moderator/director/host/tts/renderer) | health ping timeout | transition to EMERGENCY_LOOP, restart agent, transition back |
| Redis unavailable | event routing fails | orchestrator persists local state, retries Redis; if persistent, fail safe and end broadcast |
| Cascading retries flood | LLM rate limit | circuit breaker per agent — open circuit for 30s, fall through to silent |
| Clock skew between agents | A/V sync drift | NTP-sync the host; alert if skew > 50ms |

---

## 10. Cost and time

| Item | Estimate |
|---|---|
| Orchestrator overhead | negligible (~$0.10/broadcast) |
| Per 2-hr broadcast total (this + all agents) | ~$13-20 per [`../../prd.md`](../../prd.md) §5.2 |

---

## 11. Session continuity

- Orchestrator state persisted to Redis (FSM state, current product, elapsed time) every tick.
- On restart, reads state from Redis and resumes from current state.
- If Redis is also down, broadcast is unrecoverable — schedule a new broadcast.

---

## 12. References

- [`../../prd.md`](../../prd.md) §4
- All Phase 1 sibling FSDs (chat_ingest, llm_*, rag, tts_streaming, renderer_live, compositor_obs, rtmp_output)
- [`orchestrator.md`](orchestrator.md) — prototype version this evolves from
- `transitions` library docs

# Checklist — Director agent (Claude Haiku 4.5)

| | |
|---|---|
| Purpose | Bring up the Director agent for beat-level FSM decisions |
| FSD | [`../../fsd/llm_director.md`](../../fsd/llm_director.md) |
| Phase | Phase 1 |
| Language | English source — KO at [`../ko/llm_director.md`](../ko/llm_director.md) |

---

## Tech stack (at a glance)

- **Claude Haiku 4.5** (proprietary, paid) — LLM
- **anthropic** Python SDK (MIT)
- Anthropic prompt cache — 90% discount on cached persona+bible context
- **Redis** — event bus
- **Infra**: API calls from anywhere; no GPU needed

Full table: [`../../fsd/llm_director.md`](../../fsd/llm_director.md) §2

---

## Session resume

Stateless per call — full broadcast state is passed in each tick. Restart re-subscribes to Redis topic.

---

## §1. Prerequisites

- [ ] [`../../fsd/llm_director.md`](../../fsd/llm_director.md) read
- [ ] `ANTHROPIC_API_KEY` set
- [ ] System prompt written (`prompts/director_haiku.md`) including:
  - [ ] Bible §6 pacing rules (cheek-stuff cycles, 사장님 references, hoarding gags)
  - [ ] FSM transition rules
  - [ ] Few-shot decision examples
- [ ] Test set of 20 hand-labeled broadcast states + expected next actions

---

## §2. Offline eval

- [ ] Run: `python llm_director.py eval --test-set test_sets/director/`
- [ ] Verify ≥ 90% agreement with hand-labeled expected
- [ ] Review disagreements — some may be legitimate alternatives, but persistent disagreements need prompt iteration

---

## §3. Latency check

- [ ] Warm-up call
- [ ] Run 50 calls; verify p95 ≤ 200ms

---

## §4. Serve

- [ ] Run: `python llm_director.py serve --redis-url redis://localhost:6379/0 --in-topic broadcast.tick.<id> --out-topic director.decision.<id>`
- [ ] Verify first decision in Redis

---

## §5. Pacing check (during test_3 4-hr run)

- [ ] Sample 30 minutes of decisions; verify bible §6 cycles are roughly respected (±20% on cheek-stuff frequency etc.)

---

## §6. Status board

| Step | Status | Notes |
|---|---|---|
| §1 Prerequisites | ⬜ Pending | – |
| §2 Offline eval | ⬜ Pending | ≥ 90% agreement |
| §3 Latency check | ⬜ Pending | p95 ≤ 200ms |
| §4 Serve | ⬜ Pending | – |
| §5 Pacing check | ⬜ Pending | post-G2 |

---

## §7. Troubleshooting

| Issue | Cause | Response |
|---|---|---|
| Same action repeated despite state change | prompt weak on state-awareness | strengthen examples covering similar states with different best actions |
| Suggests violating action | OK — Moderator catches it | not Director's job |
| Latency over budget | cache cold | warm up first |
| Tick events not arriving | orchestrator not publishing | check broadcast_orchestrator logs |

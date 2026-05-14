# Function Spec — Operator dashboard (Next.js + FastAPI)

| | |
|---|---|
| Status | Spec v1 (Phase 2 / MVP production) |
| Phase | Phase 2 |
| Component | Read-only observability + EMERGENCY_LOOP button for the founder during pilot broadcasts |
| Source documents | [`../../prd.md`](../../prd.md) §3.2 |
| Last updated | 2026-05-13 |

---

## 1. Purpose

Per the PRD's "no live human operator" stance, this dashboard exists for observability + a single safety button — not for live operation. Built minimally; UI complexity is intentionally low.

---

## 2. Technology stack (locked)

| Stage | Tool | License |
|---|---|---|
| Backend | **FastAPI** | MIT |
| Frontend | **Next.js** (React) | MIT |
| Live state push | WebSocket via FastAPI | – |
| Auth | OAuth (Google/Naver for tenant SSO) | – |
| Data source | reads Redis + Postgres | – |

---

## 3. Pages / features

| Page | Purpose |
|---|---|
| Broadcast list | upcoming/active/past broadcasts for this tenancy |
| Active broadcast view | stream preview (RTMP-pulled), current scene, current product, last 10 spoken lines, moderation flag count, latency telemetry, EMERGENCY_LOOP button |
| Asset library | mascots, voices, backgrounds (read-only in v1) |
| Audit log | per-broadcast events from `audit_log.md` |

---

## 4. The button

`EMERGENCY_LOOP`: posts to broadcast_orchestrator → forces FSM transition to EMERGENCY_LOOP → interstitial plays, RTMP halts. Confirmation modal required (no fat-finger).

---

## 5. Quality criteria

| Criterion | Threshold |
|---|---|
| Page load | < 2s on broadband |
| Live state update | ≤ 500ms from event |
| Button → effect | ≤ 2s |
| Mobile responsive | yes (founder may use phone) |

---

## 6. Out of scope (v1)

- Editing broadcasts mid-flight
- Live chat reply (auto-Director handles this)
- Multi-broadcast control panel
- Analytics dashboard (separate, `analytics_dashboard.md` post-MVP)

---

## 7. References

- [`../../prd.md`](../../prd.md) §3.2
- [`broadcast_orchestrator.md`](broadcast_orchestrator.md) — backend control surface
- [`audit_log.md`](audit_log.md) — event source

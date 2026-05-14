# Checklist — Operator dashboard

| | |
|---|---|
| Purpose | Stand up Next.js + FastAPI operator console with EMERGENCY_LOOP button |
| FSD | [`../../fsd/operator_dashboard.md`](../../fsd/operator_dashboard.md) |
| Phase | Phase 2 |
| Language | English source — KO at [`../ko/operator_dashboard.md`](../ko/operator_dashboard.md) |

---

## Tech stack (at a glance)

- **FastAPI** (MIT) — backend
- **Next.js** + React (MIT) — frontend
- **WebSocket** — live state push
- **OAuth** — auth (Google + Naver SSO)
- **Infra**: Vercel/Render for frontend; FastAPI on same backend host

Full table: [`../../fsd/operator_dashboard.md`](../../fsd/operator_dashboard.md) §2

---

## §1. Prerequisites

- [ ] [`../../fsd/operator_dashboard.md`](../../fsd/operator_dashboard.md) read
- [ ] [`data_model.md`](data_model.md) DB initialized
- [ ] [`broadcast_orchestrator.md`](broadcast_orchestrator.md) exposes WS endpoint
- [ ] OAuth credentials (Google for v1, Naver for platform tier)

## §2. Backend

- [ ] FastAPI routes: `/broadcasts`, `/broadcasts/<id>`, `/broadcasts/<id>/ws`, `/broadcasts/<id>/emergency`
- [ ] OAuth integration tested
- [ ] WebSocket bridges Redis events → browser

## §3. Frontend

- [ ] Pages built: broadcast list, active broadcast view, asset library, audit log
- [ ] EMERGENCY_LOOP button with confirmation modal
- [ ] Mobile responsive

## §4. End-to-end test

- [ ] Run a test broadcast
- [ ] Observe state updates live in dashboard
- [ ] Click EMERGENCY_LOOP → broadcast halts within 2s

## §5. Status board

| Step | Status |
|---|---|
| §1 Prerequisites | ⬜ |
| §2 Backend | ⬜ |
| §3 Frontend | ⬜ |
| §4 E2E test | ⬜ |

## §6. Troubleshooting

| Issue | Response |
|---|---|
| WS disconnects | reconnect with backoff |
| OAuth callback fails | check redirect URI matches |
| Dashboard slow | reduce WS update frequency on bg state |

# Checklist — Naver 쇼핑라이브 integration

| | |
|---|---|
| FSD | [`../../fsd/naver_platform.md`](../../fsd/naver_platform.md) |
| Phase | Phase 3 — Sprint 5+ |
| Language | English source — KO at [`../ko/naver_platform.md`](../ko/naver_platform.md) |

---

## Tech stack
- Naver-issued RTMP endpoint + chat API (partnership-gated)

---

## §1. Business development (pre-activation)
- [ ] Partnership conversation initiated
- [ ] Partnership agreement signed
- [ ] Technical contact established with Naver eng

## §2. Technical integration
- [ ] Receive Naver API docs + credentials
- [ ] Implement Naver RTMP connector (extends [`rtmp_output.md`](rtmp_output.md))
- [ ] Implement Naver chat ingest (extends [`chat_ingest.md`](chat_ingest.md))
- [ ] Naver-specific ad disclosure UI

## §3. Pilot
- [ ] 1-2 food sellers onboarded on Naver path
- [ ] First broadcast end-to-end on Naver 쇼핑라이브
- [ ] Compliance review for Naver-specific rules

## §4. Troubleshooting
- API access revocation → partnership escalation
- Naver-specific compliance flagged → rule corpus update

# Checklist (KO) — Operator dashboard

| | |
|---|---|
| 목적 | EMERGENCY_LOOP 버튼 포함 Next.js + FastAPI operator 콘솔 구축 |
| FSD | [`../../fsd/operator_dashboard.md`](../../fsd/operator_dashboard.md) |
| Phase | Phase 2 |
| 언어 정보 | 영어 원본 [`../en/operator_dashboard.md`](../en/operator_dashboard.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **FastAPI** (MIT) — 백엔드
- **Next.js** + React (MIT) — 프론트엔드
- **WebSocket** — 라이브 상태 push
- **OAuth** — auth (Google + Naver SSO)
- **인프라**: Vercel/Render 프론트엔드; 같은 백엔드 호스트의 FastAPI

상세: [`../../fsd/operator_dashboard.md`](../../fsd/operator_dashboard.md) §2

---

## §1. 사전 준비

- [ ] [`../../fsd/operator_dashboard.md`](../../fsd/operator_dashboard.md) 읽기
- [ ] [`data_model.md`](data_model.md) DB 초기화 완료
- [ ] [`broadcast_orchestrator.md`](broadcast_orchestrator.md) 가 WS 엔드포인트 노출
- [ ] OAuth 자격증명 (v1 Google, platform tier Naver)

## §2. 백엔드

- [ ] FastAPI 라우트: `/broadcasts`, `/broadcasts/<id>`, `/broadcasts/<id>/ws`, `/broadcasts/<id>/emergency`
- [ ] OAuth 통합 테스트
- [ ] WebSocket 이 Redis 이벤트 → 브라우저 브리지

## §3. 프론트엔드

- [ ] 페이지 구축: 방송 리스트, 활성 방송 뷰, 자산 라이브러리, 감사 로그
- [ ] EMERGENCY_LOOP 버튼 + 확인 모달
- [ ] 모바일 반응형

## §4. End-to-end 테스트

- [ ] 테스트 방송 실행
- [ ] 대시보드에서 상태 업데이트 실시간 관찰
- [ ] EMERGENCY_LOOP 클릭 → 2초 내 방송 정지

## §5. 진행 상태 보드

| 단계 | 상태 |
|---|---|
| §1 사전 준비 | ⬜ |
| §2 백엔드 | ⬜ |
| §3 프론트엔드 | ⬜ |
| §4 E2E 테스트 | ⬜ |

## §6. 트러블슈팅

| 이슈 | 대응 |
|---|---|
| WS 끊김 | 백오프 재연결 |
| OAuth 콜백 실패 | redirect URI 일치 확인 |
| 대시보드 느림 | bg 상태에서 WS 업데이트 빈도 축소 |

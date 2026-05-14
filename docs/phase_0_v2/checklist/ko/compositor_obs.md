# Checklist (KO) — Compositor (OBS Studio)

| | |
|---|---|
| 목적 | test_3 방송용 OBS compositor 구성 |
| FSD | [`../../fsd/compositor_obs.md`](../../fsd/compositor_obs.md) |
| Phase | Phase 1 |
| 언어 정보 | 영어 원본 [`../en/compositor_obs.md`](../en/compositor_obs.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **OBS Studio** (GPL) — compositor
- **obs-websocket** 플러그인 (GPL) — JSON-RPC 제어
- **FFmpeg + NVENC** (LGPL) — encoder
- 브라우저 소스 (CEF) — 채팅 / 제품 카드 overlay
- **인프라**: xvfb (headless X) 포함 RunPod L40S — OBS GUI 필요

상세: [`../../fsd/compositor_obs.md`](../../fsd/compositor_obs.md) §2

---

## 세션 재개

OBS 프로파일이 source of truth. 재시작 시 상태 재적용. obs-websocket 컨트롤러는 백오프로 재연결.

---

## §1. 사전 준비

- [ ] [`../../fsd/compositor_obs.md`](../../fsd/compositor_obs.md) 읽기
- [ ] OBS Studio Docker 이미지 또는 L40S 호스트에 설치
- [ ] obs-websocket 플러그인 설치 + 활성화
- [ ] xvfb 설치: `apt install xvfb`
- [ ] OBS 프로파일 준비: `daramzzi_broadcast.json`, 4개 씬 (FULL_MASCOT, PIP, SCRIPTED_CLIP, EMERGENCY_LOOP)

---

## §2. 프로파일 + 씬 스모크

- [ ] GUI 로 1회 OBS 실행: `xvfb-run -a obs --profile daramzzi_broadcast`
- [ ] 브라우저 (RunPod VNC 등) 에서 각 씬에 올바른 소스 포함 확인
- [ ] 위치/크기 조정; 프로파일 저장

---

## §3. obs-websocket 연결

- [ ] OBS WebSocket 설정: port 4455, 비밀번호 설정
- [ ] 실행: `python compositor_obs.py probe --obs-url ws://localhost:4455 --password <pw>`
- [ ] 씬 리스팅이 예상과 일치 확인

---

## §4. 프로그래밍 방식 씬 전환 테스트

- [ ] 실행: `python compositor_obs.py scene-switch --to PIP`
- [ ] 200ms 내 씬 전환 확인 (화면 캡처로 측정)

---

## §5. Encoder + RTMP 테스트

- [ ] OBS RTMP push 를 로컬 nginx-rtmp 로 구성 ([`rtmp_output.md`](rtmp_output.md))
- [ ] OBS 에서 스트리밍 시작
- [ ] 로컬에서 ffplay 로 풀; 1080p30 H.264/AAC 확인

---

## §6. 컨트롤러로 Serve

- [ ] 실행: `python compositor_obs.py serve --redis-url redis://localhost:6379/0 --in-topic broadcast.fsm.<id> --obs-url ws://localhost:4455`
- [ ] orchestrator 의 FSM 상태 변경 트리거; 씬 변경 확인

---

## §7. 진행 상태 보드

| 단계 | 상태 | 비고 |
|---|---|---|
| §1 사전 준비 | ⬜ 대기 | – |
| §2 프로파일 스모크 | ⬜ 대기 | – |
| §3 WS 연결 | ⬜ 대기 | – |
| §4 씬 전환 | ⬜ 대기 | ≤ 200ms |
| §5 Encoder + RTMP | ⬜ 대기 | – |
| §6 컨트롤러 Serve | ⬜ 대기 | – |

---

## §8. 트러블슈팅

| 이슈 | 원인 | 대응 |
|---|---|---|
| 시작 시 OBS 크래시 | xvfb 없음 / display 잘못됨 | `DISPLAY=:99 xvfb-run -a obs` |
| 씬 전환 미수신 | obs-websocket 인증 실패 | 커넥터의 비밀번호 확인 |
| NVENC 미사용 | 드라이버/라이선스 | OBS encoder 설정에서 libx264 폴백 |
| 브라우저 소스 빈 화면 | 컨테이너에서 URL 미접근 | 호스트 네트워킹 사용 또는 로컬 파일로 브라우저 소스 포함 |

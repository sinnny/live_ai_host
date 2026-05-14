# Checklist (KO) — 렌더러 라이브 모드 (three.js)

| | |
|---|---|
| 목적 | 방송용 렌더러 라이브 실행: WebSocket 상태, 스트림 오디오, 가상 웹캠 출력 |
| FSD | [`../../fsd/renderer_live.md`](../../fsd/renderer_live.md) |
| 확장 베이스 | [`renderer.md`](renderer.md) (오프라인 베이스) |
| Phase | Phase 1 |
| 언어 정보 | 영어 원본 [`../en/renderer_live.md`](../en/renderer_live.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

[`renderer.md`](renderer.md) 와 동일 + 추가:

- **websockets** Python (BSD) — 상태 변경 채널
- 인라인 라이브 viseme 분류기 (amplitude 또는 스트리밍 Rhubarb)
- **v4l2loopback** (GPL, Linux) — 가상 웹캠 출력
- **인프라**: v4l2 모듈 포함 RunPod L40S

상세: [`../../fsd/renderer_live.md`](../../fsd/renderer_live.md) §2

---

## 세션 재개

방송에 바인딩. WS 재연결 시 orchestrator 에서 상태 받아옴.

---

## §1. 사전 준비

- [ ] [`../../fsd/renderer.md`](../../fsd/renderer.md) 오프라인 모드 검증 완료
- [ ] [`../../fsd/renderer_live.md`](../../fsd/renderer_live.md) 읽기
- [ ] 아틀라스 빌드 ([`make_mascot.md`](make_mascot.md) 체크리스트)
- [ ] v4l2loopback 커널 모듈 로드: `lsmod | grep v4l2loopback`
- [ ] 가상 웹캠 디바이스 생성: `ls -la /dev/video10`

---

## §2. Static + 합성 스모크 (오프라인 체크리스트 재사용)

- [ ] [`renderer.md`](renderer.md) §2.1 + §2.2 스모크 테스트 통과

---

## §3. WebSocket 상태 변경 테스트

- [ ] 라이브 렌더러 시작: `python renderer_cli.py live --atlas mascot/daramzzi/atlas/ --websocket-port 8765 --output /dev/video10`
- [ ] 테스트 클라이언트를 ws://localhost:8765 에 연결
- [ ] 상태 변경 이벤트 전송; 50ms 내 crossfade 확인
- [ ] /dev/video10 을 `ffplay /dev/video10` 로 읽어 프레임 흐름 확인

---

## §4. 오디오 chunk 통합 테스트

- [ ] 사전 녹음된 PCM chunk 를 Redis 통해 in-topic 에 파이프
- [ ] 발화 중 입 열림, 침묵 중 닫힘 확인
- [ ] 오디오-viseme 지연 ≤ 50ms

---

## §5. 4시간 안정성

- [ ] 합성 1msg/분 상태 변경 + 연속 오디오로 4시간 렌더러 실행
- [ ] GPU 메모리 모니터링: 4시간 동안 ≤ 100MB drift
- [ ] 60 fps 유지 확인

---

## §6. 진행 상태 보드

| 단계 | 상태 | 비고 |
|---|---|---|
| §1 사전 준비 | ⬜ 대기 | – |
| §2 Static 스모크 | ⬜ 대기 | – |
| §3 WS 상태 테스트 | ⬜ 대기 | – |
| §4 오디오 통합 | ⬜ 대기 | – |
| §5 4시간 안정성 | ⬜ 대기 | Gate 2 용 |

---

## §7. 트러블슈팅

| 이슈 | 원인 | 대응 |
|---|---|---|
| 실행 중 WS 끊김 | 네트워크 blip | 마지막 상태 유지; 백오프 재연결 |
| 오디오 chunk 미도착 | TTS 미발행 | tts_streaming 로그 확인 |
| 스트림 중 브라우저 OOM | 프레임당 누수 | 렌더러 재시작; orchestrator 가 상태 재전송 |
| /dev/video10 없음 | v4l2loopback 미로드 | `sudo modprobe v4l2loopback` |

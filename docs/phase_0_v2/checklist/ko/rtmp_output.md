# Checklist (KO) — RTMP 출력

| | |
|---|---|
| 목적 | RTMP push 구성 (Gate 1 용 로컬 nginx-rtmp, Gate 2 용 YouTube Live) |
| FSD | [`../../fsd/rtmp_output.md`](../../fsd/rtmp_output.md) |
| Phase | Phase 1 |
| 언어 정보 | 영어 원본 [`../en/rtmp_output.md`](../en/rtmp_output.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **nginx-rtmp-module** (BSD-2) — 로컬 RTMP 수신
- **FFmpeg flv muxer** (LGPL) — OBS 호출, 표준
- **RTMPS** — YouTube 프로덕션 push 용
- **인프라**: L40S 호스트의 nginx (Gate 1) + YouTube Live (Gate 2)

상세: [`../../fsd/rtmp_output.md`](../../fsd/rtmp_output.md) §2

---

## 세션 재개

방송당 single-shot. 재실행 시 새 스트림 시작.

---

## §1. 사전 준비 (Gate 1 — 로컬)

- [ ] [`../../fsd/rtmp_output.md`](../../fsd/rtmp_output.md) 읽기
- [ ] rtmp 모듈 포함 nginx 설치: `apt install libnginx-mod-rtmp` (또는 컴파일)
- [ ] nginx 설정에 rtmp 블록 (FSD §5.1)
- [ ] L40S 에서 포트 1935 접근 가능

---

## §2. 로컬 nginx-rtmp dry run

- [ ] nginx 시작: `sudo systemctl start nginx`
- [ ] 포트 확인: `sudo ss -tlnp | grep 1935`
- [ ] OBS 에서 `rtmp://localhost:1935/live/test` 로 push
- [ ] ffplay 로 pull: `ffplay rtmp://localhost:1935/live/test` — 영상 재생 확인

---

## §3. 사전 준비 (Gate 2 — YouTube)

- [ ] YouTube Studio 에서 비공개 방송 생성
- [ ] RTMPS URL + 스트림 키 복사
- [ ] env 설정: `RTMP_DEST_URL=rtmps://a.rtmp.youtube.com/live2/<key>`

---

## §4. YouTube push 테스트

- [ ] OBS 스트림 설정에 YouTube RTMPS URL + 키 구성
- [ ] OBS 에서 스트리밍 시작
- [ ] YouTube Studio 에서 30초 내 "스트림 수신 중" 확인
- [ ] "Go Live" 클릭; 비공개 방송 end-to-end 재생 확인

---

## §5. 안정성 체크 (Gate 2 4시간 운행 중)

- [ ] RTMP 연결 모니터링: nginx 로그가 10초마다 keepalive 표시
- [ ] OBS 로그에서 disconnect 감시
- [ ] 비트레이트가 5 Mbps 목표의 10% 이내 유지

---

## §6. 진행 상태 보드

| 단계 | 상태 | 비고 |
|---|---|---|
| §1 로컬 사전 준비 | ⬜ 대기 | – |
| §2 로컬 dry run | ⬜ 대기 | – |
| §3 YouTube 사전 준비 | ⬜ 대기 | – |
| §4 YouTube push 테스트 | ⬜ 대기 | – |
| §5 안정성 체크 | ⬜ 대기 | Gate 2 용 |

---

## §7. 트러블슈팅

| 이슈 | 원인 | 대응 |
|---|---|---|
| nginx 포트 1935 차단 | 방화벽 | 로컬 포트 개방 또는 loopback 만 사용 |
| YouTube 스트림 키 거부 | 키 만료 | Studio 에서 갱신, env 업데이트 |
| TLS handshake 실패 | RTMPS 이슈 | OBS RTMPS 지원 확인; 인증서 확인 |
| 비트레이트 하향 적응 | 네트워크 jitter | OBS rate_control=cbr; 업링크 확인 |

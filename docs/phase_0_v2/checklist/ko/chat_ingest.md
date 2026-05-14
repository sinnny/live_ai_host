# Checklist (KO) — Chat ingest (YouTube Live)

| | |
|---|---|
| 목적 | test_3 방송용 pytchat 기반 채팅 인제스트 구성 |
| FSD | [`../../fsd/chat_ingest.md`](../../fsd/chat_ingest.md) |
| Phase | Phase 1 |
| 언어 정보 | 영어 원본 [`../en/chat_ingest.md`](../en/chat_ingest.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **pytchat** (MIT) — YouTube Live 채팅 폴링
- **Redis** Pub/Sub (Valkey BSD-3 / RSALv2) — 이벤트 버스
- **jsonschema** (MIT) — 이벤트 검증
- **인프라**: broadcast_orchestrator 와 동일 Docker 컨테이너

상세: [`../../fsd/chat_ingest.md`](../../fsd/chat_ingest.md) §2

---

## 세션 재개

Stateless 인제스트. 마지막 확인된 `comment_id` 만 Redis 에 저장. 재시작 시 현재 플랫폼 위치부터 재개.

---

## §1. 사전 준비

- [ ] [`../../fsd/chat_ingest.md`](../../fsd/chat_ingest.md) 읽기
- [ ] YouTube Live 비공개 방송 생성
- [ ] YouTube Studio 에서 Video ID 복사
- [ ] (선택) Rate limit 발생 시 YouTube Data API 키 (`YOUTUBE_API_KEY`)
- [ ] Redis 실행 + 접근 가능

---

## §2. 설치 + 스모크 테스트

- [ ] Docker 이미지에 `pip install pytchat`
- [ ] `python -c "import pytchat; print(pytchat.__version__)"` 성공
- [ ] 공개 라이브에서 스모크 테스트: `python chat_ingest.py --video-id <public_live> --dry-run` — stdout 에 댓글 출력

---

## §3. 테스트 방송 연결

- [ ] YouTube Studio 에서 라이브 시작
- [ ] 실행: `python chat_ingest.py --platform youtube --broadcast-id <id> --video-id <yt_video_id> --redis-url redis://localhost:6379/0`
- [ ] 테스트 댓글이 Redis 에 도착하는지 확인: `redis-cli SUBSCRIBE chat.comments.<id>`

---

## §4. 복원력 체크

- [ ] 네트워크 잠시 끊기 (`sudo ifdown eth0; sleep 5; sudo ifup eth0`) — 인제스트 재연결, 크래시 없음
- [ ] 인제스트 프로세스 재시작 — 현재 위치부터 재개 (이전 댓글 재생 안됨; 문서화된 한계)

---

## §5. 진행 상태 보드

| 단계 | 상태 | 비고 |
|---|---|---|
| §1 사전 준비 | ⬜ 대기 | – |
| §2 설치 + 스모크 | ⬜ 대기 | – |
| §3 방송 연결 | ⬜ 대기 | – |
| §4 복원력 체크 | ⬜ 대기 | – |

---

## §6. 트러블슈팅

| 이슈 | 원인 | 대응 |
|---|---|---|
| YouTube 403/429 | rate limit | 백오프 (내장); 지속 시 API 키 추가 |
| `LiveChatAsync` 가 즉시 종료 신호 반환 | 아직 라이브 아님 | Studio 에서 "live" 상태 대기 |
| 댓글의 유니코드 경고 | 깨진 이모지 | drop, 계속 |
| 재연결 폭주 | 네트워크 flapping | 백오프 30s 캡 (내장) |

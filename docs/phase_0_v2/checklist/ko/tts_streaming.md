# Checklist (KO) — TTS 스트리밍 모드

| | |
|---|---|
| 목적 | 라이브 방송용 CosyVoice 2 스트리밍 TTS 구동 |
| FSD | [`../../fsd/tts_streaming.md`](../../fsd/tts_streaming.md) |
| 확장 베이스 | [`tts.md`](tts.md) (오프라인 베이스) |
| Phase | Phase 1 |
| 언어 정보 | 영어 원본 [`../en/tts_streaming.md`](../en/tts_streaming.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

[`tts.md`](tts.md) 와 동일 + 추가:

- **CosyVoice 2 스트리밍 API** (Apache 2.0)
- **Redis** 바이너리 publish (50ms PCM chunk)
- (대안) **websockets** Python (BSD) — 렌더러 직접 연결
- **인프라**: RunPod L40S (오프라인 TTS 와 동일)

상세: [`../../fsd/tts_streaming.md`](../../fsd/tts_streaming.md) §2

---

## 세션 재개

음성 ref 는 시작 시 1회 로드, 메모리 상주. 스트림별 상태는 accumulator 버퍼만. 재시작 시 Redis in-topic 재구독.

---

## §1. 사전 준비

- [ ] [`../../fsd/tts.md`](../../fsd/tts.md) 오프라인 모드 검증 완료 (체크리스트 완료)
- [ ] [`../../fsd/tts_streaming.md`](../../fsd/tts_streaming.md) 읽기
- [ ] 음성 레퍼런스 존재: `voice/daramzzi_ref.wav`
- [ ] Redis 실행 중

---

## §2. 스트리밍 모드 dry run

- [ ] 고정 한국어 문장을 단일 페이로드로 스트리밍 API 에 전달
- [ ] 첫 PCM 패킷이 요청 후 ≤ 150ms 도착 확인
- [ ] 마지막 패킷이 `is_final=true` 확인

---

## §3. 지연 시간 p95 체크

- [ ] 다양한 길이로 30회 스트리밍 합성 호출
- [ ] TTFA p95 ≤ 150ms 확인
- [ ] 오디오 연속성: stitched 재생이 부드러움 (gap 없음)

---

## §4. Backpressure 테스트

- [ ] downstream 소비자를 인위적으로 느리게
- [ ] 오래된 chunk 가 graceful drop 되는지 확인 (크래시 없음)
- [ ] 과부하 중 오디오 글리치 OK; 자동 복구

---

## §5. Serve

- [ ] 실행: `python tts_streaming.py serve --redis-url redis://localhost:6379/0 --in-topic host.tokens.<id> --out-topic tts.audio.<id> --voice-ref voice/daramzzi_ref.wav`
- [ ] Host → TTS → renderer 로 chunk 흐름 확인

---

## §6. 진행 상태 보드

| 단계 | 상태 | 비고 |
|---|---|---|
| §1 사전 준비 | ⬜ 대기 | 오프라인 TTS 우선 |
| §2 스트리밍 dry run | ⬜ 대기 | TTFA ≤ 150ms |
| §3 지연 p95 | ⬜ 대기 | – |
| §4 Backpressure | ⬜ 대기 | – |
| §5 Serve | ⬜ 대기 | – |

---

## §7. 트러블슈팅

| 이슈 | 원인 | 대응 |
|---|---|---|
| TTFA > 150ms | 텍스트 accumulator 임계값 너무 높음 | min-chars-before-synth 낮춤 |
| 스트림 중 오디오 갭 | downstream 느림 | backpressure 처리 확인 |
| 음성 ref 로드 시 OOM | VRAM 부족 | 시작 시 preload 만, 상주 유지 |
| 오디오에 감정 태그 | 태그 stripper 실패 | regex / inline 태그 핸들러 확인 |

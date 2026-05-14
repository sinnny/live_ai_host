# Checklist (KO) — 방송 orchestrator (라이브 FSM)

| | |
|---|---|
| 목적 | 모든 Phase 1 에이전트를 조정하여 라이브 4시간 방송 end-to-end 실행 |
| FSD | [`../../fsd/broadcast_orchestrator.md`](../../fsd/broadcast_orchestrator.md) |
| 진화 베이스 | [`orchestrator.md`](orchestrator.md) (프로토타입 오프라인) |
| Phase | Phase 1 |
| 언어 정보 | 영어 원본 [`../en/broadcast_orchestrator.md`](../en/broadcast_orchestrator.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **transitions** Python (MIT) — FSM
- **Redis** Pub/Sub + Streams — 이벤트 버스
- **Celery + Redis broker** (BSD/MIT) — MVP 규모 작업 큐
- **FastAPI** (MIT) — 조정 API
- (Phase 2) **Temporal** (MIT) — 프로덕션 신뢰성 대체
- **인프라**: L40S 에서 실행, 오버헤드 낮음

상세: [`../../fsd/broadcast_orchestrator.md`](../../fsd/broadcast_orchestrator.md) §2

---

## 세션 재개

FSM 상태는 매 tick Redis 에 저장. 재시작 시 상태 읽고 재개. Redis 손실 시: 방송 복구 불가, 새 방송 스케줄.

---

## §1. 사전 준비

- [ ] Phase 1 모든 형제 컴포넌트의 체크리스트 완료:
  - [ ] [`chat_ingest.md`](chat_ingest.md) ✓
  - [ ] [`llm_moderator.md`](llm_moderator.md) ✓
  - [ ] [`llm_director.md`](llm_director.md) ✓
  - [ ] [`llm_host.md`](llm_host.md) ✓
  - [ ] [`rag.md`](rag.md) ✓
  - [ ] [`tts_streaming.md`](tts_streaming.md) ✓
  - [ ] [`renderer_live.md`](renderer_live.md) ✓
  - [ ] [`compositor_obs.md`](compositor_obs.md) ✓
  - [ ] [`rtmp_output.md`](rtmp_output.md) ✓
- [ ] 방송 스케줄 YAML 준비 (FSD §7)
- [ ] Redis + Celery worker 실행 중

---

## §2. FSM 단위 테스트

- [ ] 실행: `pytest broadcast_orchestrator/tests/test_fsm.py`
- [ ] 모든 유효 전환 통과 확인
- [ ] 무효 전환 거부 확인

---

## §3. 10분 방송 dry-run

- [ ] 모든 에이전트 mock 으로 실행: `python broadcast_orchestrator.py start --dry-run --schedule schedule.yaml`
- [ ] FSM 진행: INIT → WARMUP → FULL_MASCOT → ... → DONE 확인
- [ ] 데드락 없음

---

## §4. 10분 end-to-end 라이브 (test_3 Gate 1)

- [ ] 모든 에이전트 가동 (각자의 체크리스트별로)
- [ ] 실행: `python broadcast_orchestrator.py start --broadcast-id <id> --schedule schedule.yaml`
- [ ] `chat_injector.py` 로 스크립트된 댓글 주입
- [ ] 로컬 RTMP 출력 캡처
- [ ] [`../prototype_spec.md`](../prototype_spec.md) 등가 gate 의 end-to-end 지연 측정

---

## §5. 복구 훈련

- [ ] 방송 중 `llm_host` kill — orchestrator 가 EMERGENCY_LOOP 로 전환, 에이전트 재시작, 복귀
- [ ] `llm_director`, `llm_moderator`, `tts_streaming`, `renderer_live` 각각 반복
- [ ] 각 복구 ≤ 30s 확인

---

## §6. 4시간 안정성 (test_3 Gate 2)

- [ ] 비공개 YouTube 에서 4시간 방송 시작
- [ ] 모니터링:
  - [ ] FSM 상태 분포
  - [ ] 에이전트 health ping
  - [ ] 감사 로그 완전성
  - [ ] RTMP 안정성
  - [ ] 시간에 따른 지연 drift
- [ ] Gate G2 합격 기준 적용 (deferred test_3_spec.md §6.3 참조)

---

## §7. 진행 상태 보드

| 단계 | 상태 | 비고 |
|---|---|---|
| §1 사전 준비 | ⬜ 대기 | 9개 형제 모두 준비 |
| §2 FSM 단위 테스트 | ⬜ 대기 | – |
| §3 Dry-run | ⬜ 대기 | – |
| §4 Gate 1 (지연) | ⬜ 대기 | p95 ≤ 1.5s |
| §5 복구 훈련 | ⬜ 대기 | 각 복구 ≤ 30s |
| §6 Gate 2 (4시간) | ⬜ 대기 | test_3_spec 따름 |

---

## §8. 트러블슈팅

| 이슈 | 원인 | 대응 |
|---|---|---|
| FSM 데드락 | Director 가 같은 액션 루프 | 프롬프트 검토; 상태 인식 예제 추가 |
| 에이전트 재시작 루프 | 일시적이지 않은 버그 | 에스컬레이트; auto-restart 일시정지 |
| Redis OOM | 이벤트 폭주 | chat ingest 속도 체크; Redis maxmemory eviction 추가 |
| 시간 경과에 따른 지연 drift | LLM 캐시 만료 | Anthropic extended cache (1시간 TTL) 사용 |
| 모든 에이전트 정상이나 출력 없음 | 버스 토픽 잘못 구성 | `CLIENT LIST` 로 Redis 구독자 리스트 확인 |

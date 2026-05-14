# Checklist (KO) — Moderator agent (Claude Haiku 4.5)

| | |
|---|---|
| 목적 | test_3 용 양방향 필터링 Moderator agent 구동 |
| FSD | [`../../fsd/llm_moderator.md`](../../fsd/llm_moderator.md) |
| Phase | Phase 1 |
| 언어 정보 | 영어 원본 [`../en/llm_moderator.md`](../en/llm_moderator.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **Claude Haiku 4.5** (proprietary, paid) — LLM
- **anthropic** Python SDK (MIT)
- Anthropic prompt cache — 시스템 프롬프트 90% 할인
- **Redis** — 이벤트 버스
- **인프라**: 어디서든 API 호출; GPU 불필요

상세: [`../../fsd/llm_moderator.md`](../../fsd/llm_moderator.md) §2

---

## 세션 재개

방송마다 별도 Moderator 인스턴스. 재시작 시 Redis 토픽 재구독. 시스템 프롬프트 캐시는 재시작 후 첫 호출 시 재구축 (콜드 호출 1회).

---

## §1. 사전 준비

- [ ] [`../../fsd/llm_moderator.md`](../../fsd/llm_moderator.md) 읽기
- [ ] env 에 `ANTHROPIC_API_KEY` 설정
- [ ] 시스템 프롬프트 작성 + 검토 (`prompts/moderator_haiku.md`)
- [ ] 테스트셋 준비:
  - [ ] 댓글 30개 라벨 (spam/abuse/off-topic/clean)
  - [ ] 호스트 라인 20개 라벨 (가격 환각/스펙 환각/표시광고법 위반/profanity/존댓말 breaking/캐릭터 breaking/clean)
- [ ] Redis 실행 중

---

## §2. 프롬프트 + few-shot 오프라인 평가

- [ ] 평가 실행: `python llm_moderator.py eval --test-set test_sets/moderator/`
- [ ] **댓글 분류**: 라벨 셋에서 정확도 ≥ 95%
- [ ] **호스트 audit (가장 중요)**: 위반 20개 셋에서 **false negative = 0**
- [ ] **호스트 audit false positive**: ≤ 10%
- [ ] FN > 0 이면: 위반 few-shot 추가하여 프롬프트 반복, 재평가

---

## §3. 지연 시간 체크

- [ ] 워밍업 호출 (시스템 프롬프트 캐싱): 더미 호출 1회
- [ ] 다양한 입력으로 100회 연속 호출
- [ ] p95 지연 ≤ 100ms 확인

---

## §4. Serve

- [ ] 실행: `python llm_moderator.py serve --redis-url redis://localhost:6379/0 --in-topic chat.comments.<id>,host.draft.<id> --out-topic moderator.verdict.<id>`
- [ ] 로그 추적: `tail -f logs/moderator.log`
- [ ] 첫 verdict 가 Redis 에 도착하는지 확인

---

## §5. 진행 상태 보드

| 단계 | 상태 | 비고 |
|---|---|---|
| §1 사전 준비 | ⬜ 대기 | – |
| §2 오프라인 평가 | ⬜ 대기 | FN 0 필수 |
| §3 지연 체크 | ⬜ 대기 | p95 ≤ 100ms |
| §4 Serve | ⬜ 대기 | – |

---

## §6. 트러블슈팅

| 이슈 | 원인 | 대응 |
|---|---|---|
| host audit FN > 0 | 프롬프트 약함 | 위반 few-shot 추가, 재평가 |
| 지연 스파이크 | 캐시 미스 | 캐시 워밍업, 캐시 히트율 모니터링 |
| Malformed JSON 출력 | LLM creativity | 프롬프트 내 출력 스키마 강화, 실패 시 1회 재시도 |
| Anthropic 429 | rate limit | exponential backoff (내장) |

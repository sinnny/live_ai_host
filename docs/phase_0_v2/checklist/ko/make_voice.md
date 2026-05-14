# Checklist (KO) — `make_voice` (음성 프로필 파이프라인)

| | |
|---|---|
| 목적 | 새 캐릭터용 CosyVoice 2 음성 레퍼런스 생성 |
| FSD | [`../../fsd/make_voice.md`](../../fsd/make_voice.md) |
| Phase | Phase 2 |
| 언어 정보 | 영어 원본 [`../en/make_voice.md`](../en/make_voice.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **Claude Sonnet 4.6** — 설명 → 음성 프롬프트 후보
- **CosyVoice 2** (Apache 2.0) — 내장 한국어 여성 프리셋으로 후보 ref 합성
- **인프라**: RunPod L40S

상세: [`../../fsd/make_voice.md`](../../fsd/make_voice.md) §2

---

## §1. 사전 준비

- [ ] [`../../fsd/make_voice.md`](../../fsd/make_voice.md) 읽기
- [ ] CosyVoice 2 가중치 로드
- [ ] 음성 설명 준비

## §2. 후보 생성

- [ ] 실행: `./make_voice --description "..." --character <name> --output-dir voices/<name>/`
- [ ] 후보 ref 5개 생성

## §3. 청취 + 선택

- [ ] founder 가 5개 모두 청취
- [ ] best 선택; `ref.wav` 로 저장
- [ ] 만족스러운 게 없으면 re-roll (다른 설명 / 프리셋)

## §4. 진행 상태 보드

| 단계 | 상태 | 비용 |
|---|---|---|
| §1 사전 준비 | ⬜ | – |
| §2 생성 | ⬜ | $0.05 |
| §3 청취 + 선택 | ⬜ | – |

## §5. 트러블슈팅

| 이슈 | 대응 |
|---|---|
| 5개 모두 비슷함 | 설명 확장; 다른 프롬프트 구조로 re-roll |
| 너무 어른스럽거나 어림 | 연령 디스크립터 조정 |
| 한국어 부자연 | 프리셋 확인; 일부 프리셋은 KR 학습, 일부 아님 |

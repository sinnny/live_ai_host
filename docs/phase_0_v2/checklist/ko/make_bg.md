# Checklist (KO) — `make_bg` (배경 생성)

| | |
|---|---|
| 목적 | 한 vibe 에 대해 20개 배경 (스틸 + 애니메이션 루프) 생성 |
| FSD | [`../../fsd/make_bg.md`](../../fsd/make_bg.md) |
| Phase | Phase 2 |
| 언어 정보 | 영어 원본 [`../en/make_bg.md`](../en/make_bg.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **Claude Sonnet 4.6** — vibe → 20개 프롬프트
- **Qwen-Image** (Apache 2.0) — 스틸
- **AnimateDiff + SDXL** (Apache 2.0 / OpenRAIL-M) — 애니메이션 루프
- **FFmpeg** (LGPL) — seamless-loop 처리 + muxing
- **인프라**: RunPod L40S 야간 배치

상세: [`../../fsd/make_bg.md`](../../fsd/make_bg.md) §2

---

## §1. 사전 준비

- [ ] [`../../fsd/make_bg.md`](../../fsd/make_bg.md) 읽기
- [ ] L40S 실행, Qwen-Image + AnimateDiff 가중치 로드
- [ ] Vibe 디스크립터 결정

## §2. 배치 실행

- [ ] 실행: `./make_bg --count 20 --vibe "..." --animated-fraction 0.3 --output-dir backgrounds/<vibe>/`
- [ ] 야간 대기 (~2시간)

## §3. 검토

- [ ] 스틸: 배치 내 시각적 일관성
- [ ] 루프: seamless 경계 (가시적 cut 없음)
- [ ] Manifest 유효

## §4. 진행 상태 보드

| 단계 | 상태 | 비용 |
|---|---|---|
| §1 사전 준비 | ⬜ | – |
| §2 배치 실행 | ⬜ | ~$3-5 |
| §3 검토 | ⬜ | – |

## §5. 트러블슈팅

| 이슈 | 대응 |
|---|---|
| 루프 경계에 가시 pop | FFmpeg crossfade pass 로 재실행 |
| 스틸이 다른 vibe | vibe 프롬프트 강화; 어색한 sub-batch 재실행 |
| AnimateDiff OOM | 배치 크기 줄이고 순차 실행 |

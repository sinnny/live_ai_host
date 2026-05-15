# 실시간 인터랙션 레이어 — 계획서

| | |
|---|---|
| Document type | Planning artifact — realtime interaction layer for chat response |
| Trigger | post_mortem_1 §5 path-forward "실시간 레이어 별도 과제" 분기 |
| Scope | 채팅 → 호스트 음성+영상 응답까지의 실시간 파이프라인 설계 + 검증 계획 |
| Status | Draft — B1 결과와 무관하게 진행 가능 |
| Last updated | 2026-05-14 |

---

## 1. 문제 정의 (질문 분해)

**원래 질문:** "실시간 렌더를 어떻게 풀 건데?"
**진짜 질문:** "채팅에 호스트가 응답하는 동안 시청자가 '진짜 라이브'라고 느끼게 하려면 뭐가 필요한가?"

세부 요구사항 (founder가 말한 그대로):
1. **말할 땐 입 벌리고, 안 말할 땐 닫혀야** — 기본적 mouth O/X 동기화
2. **표정도 있어야** — 정적 캐릭터 X, 최소 2-3개 표정 변화
3. **얼마나 어긋날지 우려** — lip-sync 정확도 의문

→ 이 세 가지가 **최소 합격선**. EchoMimic의 풀-quality 한국어 lip-sync는 목표가 아님.

---

## 2. 진짜 제약은 오디오 latency

| 지표 | 임계값 | 근거 |
|---|---|---|
| Chat msg → 응답 음성 시작 | **<2초** | 시청자 인내 한계. 사람도 그 정도 걸림. |
| 음성 시작 → 영상 응답 시작 | **<200ms** | "입 벌리기 시작"이 음성 시작에 맞아야 |
| Phoneme 단위 lip-sync 정확도 | **N/A** | 카툰 캐릭터는 80% 어긋나도 "AI 캐릭터"로 읽힘 (PRD §1.2) |

**결론:** 우리가 풀어야 할 건 *"오디오를 빠르게 만들고 + 입을 그 타이밍에 여닫기"*. 한국어 발음마다 정확한 입 모양을 맞추는 게 아님.

---

## 3. 추천 아키텍처 — R-Solo (EchoMimic 사전 렌더 루프 합성)

### 3.1 발상

B1 결과가 시사하는 것: **EchoMimic은 같은 seed에서 다양한 prompt/audio로 생성하면 정체성을 잘 보존함** (sprite-puppet v2가 망한 이유 — 독립 LoRA 생성 — 가 여기선 발생 안 함).

→ EchoMimic으로 **여러 종류의 짧은 루프**를 미리 만들어두고, 런타임에는 현재 상태에 맞춰 swap만 하면 됨. **새 모델 도입 0, 위험도 0.**

### 3.2 사전 렌더할 루프 라이브러리

| 루프 | 길이 | 입력 | 의도 |
|---|---|---|---|
| `idle_neutral` | 5-8초 (loop) | seed + silent (또는 호흡 wav) + "calm idle, looking around, blinking softly" prompt | 기본 상태 — 채팅 읽는 척, 듣는 척 |
| `talking_neutral` | 5-8초 (loop) | seed + 한국어 짧은 발화 wav + "speaking naturally with mouth dynamics" prompt | 말하는 중 — 입 모양 다양하게 움직임 |
| `talking_smile` | 5-8초 (loop) | 위 + "warm smile" prompt | 긍정 응답 ("맛있어요!") |
| `talking_excited` | 5-8초 (loop) | seed + 활기찬 발화 wav + "excited, energetic" prompt | 놀람/감사 ("우와! 진짜요?") |
| `idle_wave` | 3-5초 (one-shot) | seed + "waving hand greeting" | 인사 — 새 시청자 진입 시 |
| `idle_thinking` | 5-8초 (loop) | seed + "thinking, looking up thoughtfully" | LLM 응답 생성 중 (1-2초 lag 동안) |

총 6개 × 평균 7초 = ~42초의 렌더 분량. EchoMimic Flash 8초 = ~20분 인퍼런스 × 6 = **약 2시간 사전 렌더**. 한 번만 만들면 됨.

### 3.3 런타임 합성

```
┌─────────────────────────────────────────────────────────┐
│ State Machine                                            │
│                                                          │
│  ┌──────────┐  chat arrives  ┌──────────────┐           │
│  │  idle    │ ─────────────→ │ idle_thinking│           │
│  │ _neutral │                │ (LLM gen 1-2s)│          │
│  └──────────┘                └──────────────┘           │
│       ↑                              │                   │
│       │ 발화 종료                     │ TTS 첫 청크 도착     │
│       │                              ↓                   │
│  ┌──────────┐                ┌──────────────┐           │
│  │ idle     │ ←──────────── │  talking_*    │           │
│  │ _neutral │                │  (감정에 맞춰) │           │
│  └──────────┘                └──────────────┘           │
└─────────────────────────────────────────────────────────┘
```

**전환:**
- 두 루프 사이 100-200ms crossfade (Playwright/Three.js에서 video texture blend)
- 오디오는 별도 트랙, TTS streaming chunk 도착 즉시 재생

**Lip-sync 정확도:**
- 발화 중 → talking_* 루프 = "입이 계속 움직임" ✅
- 발화 안 함 → idle_* = "입 다물고 있음" ✅
- 정확한 phoneme matching = 안 됨 (그러나 카툰 + 80% 매칭이면 "AI 답다"로 패스)

### 3.4 LLM 감정 태깅

Claude가 응답 생성할 때 감정 태그도 같이 출력:

```json
{
  "text": "우와 진짜요?! 감사합니다!",
  "emotion": "excited",
  "loop": "talking_excited"
}
```

→ 런타임 state machine이 그 태그 보고 적절한 talking_* 루프 선택.

### 3.5 오디오 latency 분해

```
Chat → Claude API → 응답 텍스트:    400-800ms (Claude Haiku 4.5)
응답 텍스트 → TTS API 첫 청크:       300-700ms (Naver Clova streaming)
TTS 청크 → 렌더러 audio play:        50-100ms
───────────────────────────────────
합계:                                750-1600ms (≈ 1.5초)
```

**1.5초는 인간 응답 속도와 비슷** — 시청자가 "느리다" 안 느낌.

---

## 4. 검증 계획

### 4.1 B1 의존성

- **B1 통과 (LOOK OK):** R-Solo 진행. EchoMimic은 LOOK 검증된 도구.
- **B1 실패:** 사전 렌더 자체가 막힘 → R-Solo도 막힘 → Hedra/Live2D부터 다시 시작 (post_mortem #1 §5의 Path B3로 escalation).

### 4.2 R-Solo 검증 단계 (B1 통과 시)

| Step | 작업 | 시간 |
|---|---|---|
| **S1** | `idle_neutral` + `talking_neutral` 2개만 먼저 렌더 | ~40분 GPU |
| **S2** | Playwright 렌더러로 두 루프 + crossfade prototype 만들기 (HTML+JS) | 4-8시간 |
| **S3** | TTS 음성 (별도 트랙) + 영상 swap 동기화 데모 | 2-4시간 |
| **S4** | Founder 평가: "라이브 느낌 나는가? 입 모양 어긋남 거슬리는가?" | 30분 |

→ S4 통과하면 나머지 4개 루프 렌더 (~80분 GPU) + 감정 태깅 LLM 프롬프트 통합.

### 4.3 합격 기준 (S4)

| # | 조건 | 측정 |
|---|---|---|
| 1 | 채팅 응답 시작 latency | <2초 (스톱워치) |
| 2 | 발화 중 입 움직임 인지 가능 | 5명 reviewer 중 4명 이상 "입 움직임" 인지 |
| 3 | 발화 종료 후 1초 이내 입 닫힘 | yes/no |
| 4 | 입 모양 어긋남이 "AI 캐릭터 매력"으로 읽힘 | 5명 reviewer 중 3명 이상 긍정 (PRD §1.2 thesis 검증) |

3개 이상 통과 → R-Solo 채택. 1-2개 통과 → §5 fallback. 0-1개 통과 → §6 escalation.

---

## 5. R-Solo 실패 시 폴백 — R-Live2D

R-Solo S4에서 조건 #2-3 (입 동기화) 미달이면:

### 5.1 Live2D + AI auto-rig 검증

- Cubism Editor 5의 AI auto-rig 기능으로 `seed.png`에서 자동 리깅 시도
- 입 파라미터 1개 (mouth_open 0-1) 자동 추출 가능한지 확인
- 표정 파라미터 2-3개 (smile, surprised, angry) 수동 매핑

### 5.2 런타임 — TTS amplitude → mouth_open

```
TTS audio chunk arrive
  ↓
realtime amplitude envelope (50ms window)
  ↓
mouth_open = clamp(amplitude * gain, 0, 1)
  ↓
Live2D WebGL render @ 60fps
```

**Latency:** 오디오 도착 즉시 입 열림. 50ms 미만.

### 5.3 검증

- AI auto-rig 1일 시도 (PoC만)
- 됐으면 → 1주 더 투자해서 full rig + 표정 연동
- 안 됐으면 → §6 escalation

---

## 6. 최종 escalation — Hedra Character-3 streaming API

R-Solo, R-Live2D 다 실패 시:
- 1-2일 PoC만 (API 키 발급 + 1개 요청)
- 비용 모델 동시 검증 ($0.50-2/min → ₩30,000 방송 30분 마진 시뮬레이션)
- 통과하면 Phase 1 vendor lock-in 받아들이고 진행
- 실패하면 Phase 1 자체 재검토 (사전 렌더 only로 1차 출시 후 Phase 2에 실시간 다시 시도)

---

## 7. 의사결정 트리

```
B1 결과
├── 통과 → R-Solo S1~S4
│    ├── 4-조건 다 통과 → 6개 루프 풀 렌더 + 통합 → Phase 1 진행
│    ├── 3개 통과 → R-Solo 채택 + 미세 튜닝
│    ├── 1-2개 통과 → R-Live2D PoC
│    │    ├── PoC 성공 → R-Live2D 채택
│    │    └── PoC 실패 → R-Hedra
│    └── 0-1개 통과 → R-Hedra
└── 실패 → R-Hedra (B1 실패 시 EchoMimic 사용 못 함)
```

---

## 8. 비용 추정

| 단계 | GPU 시간 | API 비용 | 인적 시간 | 합계 |
|---|---|---|---|---|
| R-Solo S1 (2 루프) | 40분 = $0.57 | 0 | 2시간 | $0.57 + 2h |
| R-Solo S2-S4 (프로토 렌더러) | 0 | 0 | 8-14시간 | 8-14h |
| 통과 시 — 4 루프 더 | 80분 = $1.15 | 0 | 1시간 | $1.15 + 1h |
| R-Live2D PoC (실패 시) | 0 | 0 | 8-16시간 | 8-16h |
| R-Hedra PoC (최후 시) | 0 | $5-20 | 4-8시간 | 4-8h |

**Phase 0 v2 R-Solo 검증 전체:** ~$2 GPU + 11-17시간 작업. 매우 저렴.

---

## 9. 열린 질문 (B1 후 답할)

1. **B1 영상에서 EchoMimic이 idle 같은 정적 상태를 잘 렌더하는가?** — talking_* 루프는 검증됐지만, idle (mouth closed + breathing) 잘 되는지 확인 필요. S1에서 같이 확인.
2. **Daramzzi의 입 모양 변화가 한국어 phoneme과 얼마나 어긋나도 OK인가?** — B1 8초 영상 보고 founder 직감으로 판단.
3. **TTS 후보** — Naver Clova / Kakao Brain / ElevenLabs Korean 중 어느 게 streaming + 자연스러움 + 가격 최적인지 별도 비교 필요. R-Solo S2 진입 전까진 못 정해도 무방 (사전 렌더용 TTS는 일단 CosyVoice 2 또는 founder voice 으로 진행).

---

## 10. References

- `post_mortem_1.md` §5 — path-forward 분석
- `../prd.md` §1.2 — "obviously AI / failure-modes-as-style" thesis
- `../prd.md` §0 Pivot 2 — "autonomous Claude runtime" 원래 의도
- `../prd.md` §4.3 — sprite-puppet renderer spec (R-Solo의 합성 레이어와 직접 매핑)
- `~/.claude/.../memory/echomimic_vram_limits.md` — EchoMimic의 GPU/길이 제약
- `~/.claude/.../memory/project_sprite_puppet_findings.md` — 왜 v2 sprite가 실패했는지 (R-Solo가 그 함정을 어떻게 피하는지의 근거)

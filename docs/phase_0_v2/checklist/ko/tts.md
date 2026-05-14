# Checklist (KO) — TTS (CosyVoice 2)

| | |
|---|---|
| 목적 | 스크립트 JSON 으로부터 다람찌 음성으로 한국어 오디오 합성 |
| FSD 참조 | [`../../fsd/tts.md`](../../fsd/tts.md) |
| 의존성 | [`make_mascot.md`](make_mascot.md) (아틀라스는 필요 없음 — 음성은 독립) — 보통 `make_mascot` 다음에 실행 |
| 언어 정보 | 영어 원본 [`../en/tts.md`](../en/tts.md) — 이 문서는 한국어 번역 |
| 최종 수정 | 2026-05-13 |

---

## 기술 스택 (한눈에 보기)

- **CosyVoice 2** (Apache 2.0) — 한국어 TTS, zero-shot 음성 클로닝
- **librosa + soundfile** (ISC + MIT) — 오디오 I/O
- **numpy + scipy.signal** (BSD) — 연결 + SFX 믹싱
- **인프라**: RunPod L40S (`make_mascot` 와 동일 박스)
- 유료 TTS API 없음

상세 표 + 선정 근거: [`../../fsd/tts.md`](../../fsd/tts.md) §2

---

## 세션 재개

세션이 끊긴 뒤 재개 시: 첫 미완료 `[ ]` 항목부터. 모든 단계는 idempotent — 음성 레퍼런스는 재사용되고, 세그먼트별 WAV 는 이미 디스크에 있으면 건너뜀.

---

## §1. 사전 준비

- [ ] [`../../fsd/tts.md`](../../fsd/tts.md) 읽기 (특히 §3 입력, §5 파이프라인)
- [ ] RunPod L40S 실행 중 (`make_mascot` 와 동일 박스)
- [ ] CosyVoice 2 모델 가중치 (~5 GB) 다운로드 — 첫 실행 시 Hugging Face 에서 자동 다운로드
- [ ] `daramzzi-pipeline` 도커 이미지 빌드 (`make_mascot` 와 동일)

---

## §2. 1회성 작업: 음성 레퍼런스

> 캐릭터당 한 번만. 이후 모든 클립에 재사용.

- [ ] CosyVoice 2 기본 한국어 여성 프리셋으로 바이블 기반 ~10초 샘플 라인 합성하여 음성 레퍼런스 부트스트랩
- [ ] 실행: `python tts.py voice-ref --bootstrap-voice cosyvoice2:default_kr_female --output voice/daramzzi_ref.wav`
- [ ] `voice/daramzzi_ref.wav` 청취 — 다음 확인:
  - [ ] 자연스러운 한국어 운율, 로봇 같은 인공음 없음
  - [ ] 여성 보이스, 평균보다 약간 높은 음역 (바이블 §5.1)
  - [ ] 에너지 있고 약간 불안한 인턴 톤 (너무 어른스럽지 않고, 너무 어리지 않음)
- [ ] 만족스럽지 않으면: 다른 부트스트랩 샘플 텍스트로 재실행
- [ ] SHA256 기록: `sha256sum voice/daramzzi_ref.wav >> voice/voices.log`
- 예상 시간: 5분 / 비용: ~$0.01

---

## §3. 클립별 TTS 합성

> 각 프로토타입 클립마다 실행. 클립마다 자체 스크립트 JSON 보유.

### §3.1 스크립트 준비

- [ ] 스크립트 파일 존재: `scripts/test_3/scripts/<clip_name>.json`
- [ ] 스키마 검증 통과: `python orchestrator.py validate --script scripts/<clip_name>.json`
- [ ] 세그먼트 수 sanity check: 클립 길이에 부합 (대략 3분 클립당 25-40 세그먼트)

### §3.2 TTS 실행

- [ ] 실행: `python tts.py synthesize --script scripts/<clip_name>.json --voice voice/daramzzi_ref.wav --output-dir prototype_runs/<clip_name>/tts/`
- [ ] 출력 확인:
  - [ ] `tts/audio.wav` 존재, 유효한 WAV (mono 24 kHz)
  - [ ] `tts/segments/seg_*.wav` — 스크립트 세그먼트별로 하나씩
  - [ ] `tts/manifest.json` — 스키마 유효, 모든 세그먼트가 duration 과 함께 기록

### §3.3 음성 품질 검토 (수동)

- [ ] `tts/audio.wav` 전체 청취
- [ ] 확인 사항:
  - [ ] 모든 단어에 자연스러운 한국어 발음 (로봇 같은 synthesizer 티 나는 순간 없음)
  - [ ] 음성 톤이 클립 전체에 일관 — 중간에 drift 없음
  - [ ] `speed_modifier` 정상 적용 (cheek-stuffed 세그먼트 눈에 띄게 느림)
  - [ ] 세그먼트 사이 pause 자연스러움 — 너무 길거나 짧지 않음
  - [ ] 피크 레벨 클리핑 없음 (조용한 환경 또는 오디오 미터로 확인)
- 예상 시간: 3분 클립당 ~3분 / 비용: ~$0.05-0.10

### §3.4 스크립트 반복 수정

검토 시 발음 문제 발견되면:
- [ ] 스크립트의 해당 세그먼트 텍스트 편집 (음운 표기 수정, filler 추가 등)
- [ ] 해당 세그먼트만 재실행: `python tts.py synthesize --segment-idx N` (또는 해당 WAV 삭제 후 전체 재실행 — idempotent skip)
- [ ] 재검토

---

## §4. 품질 검증

- [ ] 피크 레벨: `ffmpeg -i audio.wav -af "volumedetect" -f null - 2>&1 | grep max_volume` 결과 ≤ -3 dB
- [ ] 총 duration 이 세그먼트 duration 합 + pause 와 일치 (오차 ≤ 100 ms)
- [ ] 세그먼트별 manifest 항목 모두 non-zero duration

---

## §5. 다음 단계로 (Phoneme alignment)

- [ ] `tts/audio.wav` 준비 완료
- [ ] [`phoneme_alignment.md`](phoneme_alignment.md) 진행

---

## §6. 진행 상태 보드

| 단계 | 상태 | 시작 시각 | 완료 시각 | 비고 |
|---|---|---|---|---|
| §1 사전 준비 | ⬜ 대기 | – | – | – |
| §2 음성 레퍼런스 (one-time) | ⬜ 대기 | – | – | – |
| §3.1 스크립트 준비 | ⬜ 대기 | – | – | – |
| §3.2 TTS 실행 | ⬜ 대기 | – | – | – |
| §3.3 음성 품질 검토 | ⬜ 대기 | – | – | – |
| §4 품질 검증 | ⬜ 대기 | – | – | – |

---

## §7. 트러블슈팅

| 이슈 | 원인 가능성 | 대응 |
|---|---|---|
| 한국어 텍스트에 영어 발음 drift | `language="ko"` 플래그 누락 또는 KR 구문 너무 짧음 | 명시적 lang 플래그; 짧은 발화는 padding |
| 특정 단어만 로봇 같음 | OOV 또는 비정상 음운 | 스크립트에서 음운 표기로 재작성 |
| 클립 중간에 음성 톤 drift | 세그먼트 너무 김 (모델이 prosodic context 손실) | 긴 세그먼트를 ≤ 200 자 이하로 분할 |
| 긴 입력에서 OOM | 단일 세그먼트가 모델 한계 초과 | 더 작은 세그먼트로 분할 |
| `speed_modifier` 거부됨 | [0.5, 1.5] 범위 벗어남 | 검증기에서 catch; 안되면 스크립트 수정 |

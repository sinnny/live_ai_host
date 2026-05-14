# Checklist (KO) — 다람찌 마스코트 아틀라스 생성

| | |
|---|---|
| 목적 | `make_mascot` 파이프라인 실행 — 다람찌용 24-스프라이트 레이어드 아틀라스 생성 |
| FSD 참조 | [`../../fsd/make_mascot.md`](../../fsd/make_mascot.md) |
| 캐릭터 바이블 | [`../../../characters/daramzzi.md`](../../../characters/daramzzi.md) |
| 사용 방식 | 각 단계 완료 시 `[ ]` → `[x]`. 세션 재개 시 첫 미완료 항목부터 진행 |
| 언어 정보 | 영어 원본 [`../en/make_mascot.md`](../en/make_mascot.md) — 이 문서는 한국어 번역 |
| 범위 변경 (2026-05-13) | 최초 계획 (full test_3) → 축소 (prototype 1-3분 클립). Claude API 런타임 호출 없음 (정적 prompts.json). 예산 ~$300 → ~$15 |
| 최종 수정 | 2026-05-13 |

---

## 기술 스택 (한눈에 보기)

- **Qwen-Image** (Apache 2.0) — 이미지 생성
- **AI-Toolkit** by Ostris (MIT) — LoRA 학습
- **BiRefNet** (MIT) — 배경 제거
- **MediaPipe** (Apache 2.0) — 스프라이트 앵커 정렬
- **Pillow + 커스텀 Python** — 아틀라스 패킹
- **인프라**: RunPod L40S, 전부 OSS, 유료 생성 API 없음

상세 표 + 선정 근거: [`../../fsd/make_mascot.md`](../../fsd/make_mascot.md) §2

---

## 세션 재개 시 (Session resume) — 먼저 읽으세요

세션이 끊긴 뒤 새로 시작했다면:

1. 이 체크리스트의 첫 번째 `[ ]` 항목을 찾아서 거기서부터 재개합니다.
2. 의심스러우면 RunPod L40S에 SSH 접속 → `cd scripts/test_3/mascot/daramzzi && python pipeline.py status --config daramzzi_config.yaml` 실행 → 현재 단계 확인.
3. 모든 파이프라인 단계는 **idempotent** — 재실행해도 같은 결과. 안심하고 재시도 가능.
4. 모르겠으면 [`make_mascot_fsd.md`](make_mascot_fsd.md) §10 (Session-continuity guide) 참조.

---

## §1. 사전 준비 (Prerequisites)

### §1.1 문서 검토

- [ ] [`make_mascot_fsd.md`](make_mascot_fsd.md) 전체 읽기 — 특히 §2 (기술 스택) 와 §5 (파이프라인 단계)
- [ ] [`../characters/daramzzi.md`](../characters/daramzzi.md) §3 (페르소나) + §4 (시각 정체성) 확인
- [ ] FSD §11 (Open questions for founder review) — 5개 질문에 답변 결정
  - [ ] 시드 승인 방식 (수동 OK / 자동 통과 임계값)
  - [ ] 반복 허용치 (3회 실패 시 즉시 보고)
  - [ ] 최종 아틀라스 검토 방식 (렌더러 프리뷰 / 원본 아틀라스)
  - [ ] LoRA 버전 관리 (1회 학습 후 고정 / 매 실행마다 재학습)
  - [ ] v1 아틀라스 반복 예산 (22/24 통과 시 출시 / 24/24까지 반복)

### §1.2 API 키 / 권한

- [ ] `ANTHROPIC_API_KEY` 발급 — Claude Code 와 별도 키 사용 (예산 분리 목적)
- [ ] RunPod 계정 + API 키 (`RUNPOD_API_KEY`)
- [ ] (test_3 G2 단계에서 필요) YouTube Live 비공개 방송 + RTMP 스트림 키

### §1.3 예산 승인

- [ ] FSD §8.1: 1회 실행 약 $5-7 (GPU + Claude). FSD §8.2: 하드 캡 $20
- [ ] test_3 전체 예산 $300 캡 안에 포함됨
- [ ] 명시적 승인: __________ (founder)

---

## §2. 환경 셋업 (Environment setup)

### §2.1 RunPod L40S 임대

- [ ] RunPod 대시보드 → New Pod → L40S 48GB
- [ ] 컨테이너 디스크 ≥ 100GB (Qwen-Image + BiRefNet 가중치 저장용)
- [ ] 영구 볼륨 마운트 (Persistent Volume) — 세션 끊겨도 작업물 유지
- [ ] SSH 접속 확인: `ssh root@<runpod-host>`

### §2.2 코드 + 도커 이미지

- [ ] `git clone <repo>` 후 `/workspace/live_ai_host` 위치에 코드 배치
- [ ] `cd scripts/test_3/mascot/daramzzi` (이 디렉터리에서 모든 작업 수행)
- [ ] `docker build -t daramzzi-pipeline -f Dockerfile .`
- [ ] 빌드 성공 확인: `docker images | grep daramzzi-pipeline`

### §2.3 모델 가중치 사전 다운로드 (선택, 첫 단계에서 자동으로도 받음)

- [ ] Qwen-Image: ~10GB. `huggingface-cli download Qwen/Qwen-Image`
- [ ] BiRefNet: ~1GB
- [ ] 디스크 잔여 공간 확인: `df -h` ≥ 50GB 남았는지

### §2.4 디렉터리 구조

- [ ] `mkdir -p work atlas`
- [ ] `daramzzi_config.yaml` 존재 확인 (FSD §3.2 참조)

---

## §3. 파이프라인 실행 (Pipeline execution)

각 단계는 FSD §5 + §6 와 1:1 대응. 명령어는 FSD §6.2 에서 복사.

### §3.1 Stage 5.1 — 브리프 확장 (Brief expansion) — **변경: 정적 파일 사용**

> **변경 사항 (2026-05-13):** Claude API 런타임 호출 대신 정적 `prompts.json` 사용. 24개 프롬프트는 캐릭터 바이블 기반으로 사전 작성 완료. 비용 절감 + 결정론적 재실행 가능.

- [ ] 정적 프롬프트 파일 존재 확인: `scripts/test_3/mascot/daramzzi/prompts.json`
- [ ] JSON 유효성 검증: `python -c "import json; json.load(open('prompts.json'))"`
- [ ] 24개 스프라이트 카운트 확인: 10 expression + 6 mouth + 5 tail + 3 ears
- [ ] 빠른 수동 검토: 베이스 프롬프트 + 부정 프롬프트가 캐릭터 바이블 §4 (시각 정체성)와 일치
- 예상 시간: 5분 / 비용: $0 (API 호출 없음)

### §3.2 Stage 5.2 — 시드 생성 (Seed generation) **← 승인 게이트**

- [ ] `pipeline.py seed` 실행
- [ ] 출력 확인: `work/02_seed/seed.png`
- [ ] **수동 검토 (필수)**: 다음 항목 모두 통과해야 다음 단계로 진행:
  - [ ] 다람쥐로 명확히 보임 (햄스터 아님 — 꼬리 확인)
  - [ ] 통통한 chibi 비율 (머리가 몸통보다 약 1.3배)
  - [ ] 도토리색 / cream 배색
  - [ ] 앞치마 + 헤드셋 착용
  - [ ] 캐릭터 바이블 §3.2 의 "earnest" 표정 (sassy/sarcastic 아님)
- [ ] 만족 시: `[x]` 표시 + 다음 단계로
- [ ] 불만족 시: `pipeline.py seed --new-seed N` 으로 다른 시드 시도 (최대 5회 반복 권장)
- 예상 시간: 10분 (반복 포함) / 비용: ~$0.30

### §3.3 Stage 5.3 — LoRA 데이터셋 생성

- [ ] `pipeline.py lora-dataset` 실행
- [ ] 출력 확인: `work/03_lora_dataset/` 안에 8개 이미지 + 캡션
- [ ] 빠른 시각 검토: 8개 모두 같은 캐릭터로 보이는지 (drift 없음)
- 예상 시간: 20분 / 비용: ~$1

### §3.4 Stage 5.4 — LoRA 학습

- [ ] `pipeline.py lora-train` 실행
- [ ] 학습 로그 확인: 손실(loss) 감소 추세
- [ ] 출력 확인: `work/04_lora_train/checkpoints/final.safetensors`
- [ ] 스모크 테스트: 시드 프롬프트를 LoRA 로드 후 생성 → 시드와 거의 동일하면 통과
- 예상 시간: 45분 / 비용: ~$1

### §3.5 Stage 5.5 — 스프라이트 배치 생성

- [ ] `pipeline.py sprites` 실행
- [ ] 출력 확인: `work/05_raw_sprites/` 안에 24개 스프라이트 (layer/state 구조)
  - [ ] expression 폴더: 10개 (neutral, cheek_stuff, panic, pleading, victory, sleepy, confused, sneaky, laughing, embarrassed)
  - [ ] mouth 폴더: 6개 (closed, aa, ih, ou, ee, oh)
  - [ ] tail 폴더: 5개 (relaxed, alert, puffed, curled, wagging)
  - [ ] ears 폴더: 3개 (up, flat, perked)
- [ ] 빠른 시각 검토: 캐릭터 정체성이 24개 모두에 유지되는지
- [ ] 재시도가 필요한 스프라이트가 있다면 FSD §5.5 retry budget (sprite 당 최대 3회) 안에서 처리
- 예상 시간: 50분 / 비용: ~$1.20

### §3.6 Stage 5.6 — 배경 제거 (Alpha matte)

- [ ] `pipeline.py alpha` 실행
- [ ] 출력 확인: `work/06_alpha/` 안에 24개 알파 채널 PNG
- [ ] 빠른 검토: 외곽선 깔끔한지, 배경 잔여물 없는지
- 예상 시간: 5분 / 비용: ~$0.20

### §3.7 Stage 5.7 — 앵커 정렬 (Normalization)

- [ ] `pipeline.py normalize` 실행
- [ ] 출력 확인: `work/07_normalized/` 안에 24개 정렬된 PNG
- [ ] **합성 미리보기 확인**: `python pipeline.py preview-composite` — 입 6개가 같은 위치에 정렬되는지, 꼬리 5개가 같은 부착점에 정렬되는지
- 예상 시간: 10분 / 비용: ~$0.05

### §3.8 Stage 5.8 — 아틀라스 패킹

- [ ] `pipeline.py pack` 실행
- [ ] 출력 확인:
  - [ ] `atlas/atlas.png` (6144×4096, ≤ 20MB)
  - [ ] `atlas/config.json` (FSD §4.2 스키마 일치)
  - [ ] `atlas/manifest.yaml` (provenance 완전)
  - [ ] `atlas/lora.safetensors` (학습된 LoRA 사본)
- 예상 시간: 30초 / 비용: 무시 가능

---

## §4. 품질 검증 (Quality validation)

### §4.1 스프라이트별 검증 (FSD §7.1)

24개 스프라이트 모두에 대해:
- [ ] 해상도 1024×1024
- [ ] 알파 채널 PNG
- [ ] 배경 잔여 없음 (halo, bleed 없음)
- [ ] 앵커 정렬 (±10px 이내)
- [ ] 시드와 정체성 일관 (A/B 비교)
- [ ] 의도된 감정/상태가 한눈에 읽힘
- [ ] 캐릭터 바이블 §3 + §4 준수

### §4.2 아틀라스 전체 검증 (FSD §7.2)

- [ ] 표정 10개 모두 같은 캐릭터로 보임 — 스타일 drift 없음
- [ ] 입 오버레이 6개 합성 시 동일 얼굴 위치에 정렬
- [ ] 꼬리 오버레이 5개 합성 시 동일 부착점에 정렬
- [ ] 털 색깔 hue 분산 ≤ 5%
- [ ] `atlas.png` 파일 크기 ≤ 20MB

### §4.3 합격 / 불합격 결정

- [ ] **합격 시:** 다음 섹션 (§5) 으로 진행
- [ ] **불합격 시:** FSD §7.3 (Failure-to-reach-quality response) 따라 처리
  - 개별 스프라이트 실패 → Stage 5.5 재시도 (해당 스프라이트만)
  - 정체성 drift → LoRA 재학습 (rank 64 또는 3000 steps)
  - 다수 바이블 미준수 → `prompts.json` 수동 편집 후 5.5 부터 재실행
  - 3회 전체 재생성에도 실패 → **즉시 founder 보고, 진행 정지**

---

## §5. 프로토타입 클립 렌더링 (Prototype clip rendering)

> 아틀라스가 완성된 뒤, 1-3분짜리 MP4 클립을 생성하는 단계. 자세한 내용은 [`prototype_spec.md`](prototype_spec.md) §5 참조.

### §5.1 음성 레퍼런스 준비 (one-time)

- [ ] CosyVoice 2 의 기본 한국어 여성 보이스로 ~10초 샘플 라인 합성 → `scripts/test_3/voice/daramzzi_ref.wav`
- [ ] 청취 확인: 다람찌 페르소나 (§5.1) 와 어울리는 톤인지 — 너무 어른스럽지 않고, 너무 어리지 않고, 진정성 있는 인턴 느낌
- 예상 시간: 5분 / 비용: ~$0.05

### §5.2 스크립트 작성

- [ ] `scripts/test_3/scripts/clip_01.json` 작성 (사용자 직접 작성)
- [ ] [`prototype_spec.md`](prototype_spec.md) §3.1 예시 참조
- [ ] 스키마 검증: `python -c "import json, jsonschema; jsonschema.validate(json.load(open('scripts/clip_01.json')), json.load(open('script_schema.json')))"` 통과
- [ ] 길이 확인: 1-3분 분량 (텍스트 분량 × 음절당 ~0.15초 추정)
- 예상 시간: 30분 / 비용: $0

### §5.3 Prototype Stage 1 — TTS 실행

- [ ] `prototype.py render --script clip_01.json` 의 TTS 단계 실행
- [ ] 출력 확인: `prototype_runs/clip_01/tts/audio.wav` + 세그먼트별 WAV
- [ ] 청취 검토: 한국어 발음 자연스러운지, 페르소나 톤 맞는지
- [ ] 발음 오류 시: 스크립트의 해당 단어를 음성 표기로 수정 후 재실행
- 예상 시간: 2분 / 비용: ~$0.05

### §5.4 Prototype Stage 2 — 음소 정렬 (Phoneme alignment)

- [ ] Rhubarb 실행 자동 진행
- [ ] 출력 확인: `prototype_runs/clip_01/phonemes/alignment.json`
- [ ] 샘플 비스메 (viseme) 타이밍이 오디오와 어긋나지 않는지 확인
- [ ] 한국어 음소 인식 실패 시: amplitude-envelope 폴백 사용 ([`prototype_spec.md`](prototype_spec.md) §5.2 참조)
- 예상 시간: 30초 / 비용: ~$0.01

### §5.5 Prototype Stage 3 — 렌더링

- [ ] three.js 렌더러 자동 실행 (headless Chrome via Playwright)
- [ ] 출력 확인: 이미지 시퀀스 OR 직접 ffmpeg 으로 스트리밍
- [ ] 빠른 검토 (수동): 처음 5초 프레임 보고 표정 전환 / 입 모양 / 위치 정렬 확인
- 예상 시간: 5분 / 비용: ~$0.20

### §5.6 Prototype Stage 4 — 인코딩

- [ ] FFmpeg + libx264 자동 실행
- [ ] 출력 확인: `prototype_runs/clip_01/output.mp4` (≤ 50MB, 1080p, H.264/AAC)
- 예상 시간: 1분 / 비용: 무시 가능

### §5.7 프로토타입 판정 (Pass/fail decision)

[`prototype_spec.md`](prototype_spec.md) §1.3 의 4가지 합격 조건 모두 통과해야 함:

- [ ] **Recognizable** — 다람찌로 명확히 인식됨 (햄스터 아님, 일반 애니메이션 캐릭터 아님)
- [ ] **Watchable** — 고통스러운 uncanny 순간 없음. 입 모양이 오디오와 대략 맞음. 표정 전환 자연스러움
- [ ] **On-brand** — earnest + lovable + intern 에너지. sassy 또는 flat 아님
- [ ] **Worth iterating** — "더 잘 만들 노력을 투자할 의향 있음"

**모두 통과 시:** test_3 (실시간 자율 방송 검증) 계획 단계 진입
**일부 실패 시:** `phase_0_v2/post_mortem_<n>.md` 작성, 원인 분석, 재계획

---

## §6. 진행 상태 보드 (Status board)

한눈에 보는 진행 상태 — 매 단계 완료 시 업데이트.

### Part A — 마스코트 아틀라스 (make_mascot)

| 단계 | 상태 | 시작 시각 | 종료 시각 | 비용 | 비고 |
|---|---|---|---|---|---|
| §1 사전 준비 | ⬜ 대기 | – | – | – | – |
| §2 환경 셋업 | ⬜ 대기 | – | – | – | – |
| §3.1 Stage 5.1 (정적 prompts.json) | ⬜ 대기 | – | – | $0 | API 호출 없음 |
| §3.2 Stage 5.2 (seed) | ⬜ 대기 | – | – | – | 시드 승인 게이트 |
| §3.3 Stage 5.3 (lora-dataset) | ⬜ 대기 | – | – | – | – |
| §3.4 Stage 5.4 (lora-train) | ⬜ 대기 | – | – | – | – |
| §3.5 Stage 5.5 (sprites) | ⬜ 대기 | – | – | – | – |
| §3.6 Stage 5.6 (alpha) | ⬜ 대기 | – | – | – | – |
| §3.7 Stage 5.7 (normalize) | ⬜ 대기 | – | – | – | – |
| §3.8 Stage 5.8 (pack) | ⬜ 대기 | – | – | – | – |
| §4 품질 검증 | ⬜ 대기 | – | – | – | – |

### Part B — 프로토타입 클립 렌더링 (prototype 1-3분)

| 단계 | 상태 | 시작 시각 | 종료 시각 | 비용 | 비고 |
|---|---|---|---|---|---|
| §5.1 음성 레퍼런스 | ⬜ 대기 | – | – | – | one-time |
| §5.2 스크립트 작성 | ⬜ 대기 | – | – | $0 | 사용자 작성 |
| §5.3 TTS | ⬜ 대기 | – | – | – | – |
| §5.4 Phoneme alignment | ⬜ 대기 | – | – | – | – |
| §5.5 Render | ⬜ 대기 | – | – | – | – |
| §5.6 Encode | ⬜ 대기 | – | – | – | – |
| §5.7 프로토타입 판정 | ⬜ 대기 | – | – | – | go/no-go for test_3 |

상태 표시: ⬜ 대기 / 🟡 진행 중 / 🟢 완료 / 🔴 실패 / ⚪ 건너뜀

---

## §7. 알려진 이슈 / 트러블슈팅

실행 중 발생하는 이슈와 해결책을 누적 기록.

| 일시 | 단계 | 증상 | 원인 | 해결 |
|---|---|---|---|---|
| – | – | – | – | – |

### 자주 마주칠 만한 이슈 (사전 정리)

| 이슈 | 원인 가능성 | 대응 |
|---|---|---|
| 시드가 햄스터 같아 보임 | 프롬프트의 squirrel/chipmunk 강조 부족 | 프롬프트 명시 강화 + 꼬리 강조 + 시드 변경 |
| LoRA 학습 손실이 감소 안 함 | 데이터셋 일관성 부족 | 데이터셋 재생성 (3.3 재실행) |
| 입 오버레이 합성 시 어긋남 | MediaPipe 가 cartoon face 인식 실패 | FSD §5.7 fallback — 수동 앵커 지정 |
| 표정 panic 이 neutral 과 구분 안 됨 | 감정 표현 프롬프트 약함 | 프롬프트에 "tail visibly puffed, eyes wide white" 강조 추가 후 재생성 |
| 도커 빌드 OOM | RunPod 컨테이너 메모리 한계 | RunPod GPU 사양 확인 — L40S 권장 |
| Hugging Face 다운로드 실패 | 네트워크 / rate limit | `HF_HOME` 환경변수 + `huggingface-cli login` |

---

## §8. 완료 후 정리

전체 파이프라인 성공 + 통합 검증 합격 시:

- [ ] `manifest.yaml` 의 모든 필드 채워졌는지 확인
- [ ] `git add atlas/ && git commit -m "..."` — 아틀라스 + LoRA 커밋
- [ ] `work/` 디렉터리는 `.gitignore` 처리 (중간 산출물, repo 에 포함 X)
- [ ] [`test_3_spec.md`](test_3_spec.md) §S3 (renderer 검증) 으로 이동
- [ ] 이 체크리스트는 보존 — 향후 새 캐릭터 생성 시 동일 절차의 템플릿이 됨

---

## §9. 다음 캐릭터 (post-MVP 예고)

이 체크리스트는 다람찌 인스턴스 1회용이 아니라, 향후 캐릭터에도 재사용 가능한 템플릿. v2 이후 추가 마스코트가 필요할 때:

1. `docs/characters/<new_mascot>.md` 새 바이블 작성
2. `daramzzi_config.yaml` 복제 → `<new_mascot>_config.yaml` 로 수정
3. 이 체크리스트 복사 → 캐릭터명만 치환
4. §1 부터 같은 절차로 실행

`make_mascot` 파이프라인이 일반화되면 (test_3 통과 후 작업) 단계 자체가 더 줄어들 예정.

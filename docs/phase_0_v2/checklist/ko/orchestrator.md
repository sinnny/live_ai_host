# Checklist (KO) — Orchestrator (end-to-end 파이프라인)

| | |
|---|---|
| 목적 | 4단계 prototype 파이프라인 end-to-end 실행; 최종 MP4 생성 |
| FSD 참조 | [`../../fsd/orchestrator.md`](../../fsd/orchestrator.md) |
| 포함 단계 | [`make_mascot`](make_mascot.md) (1회), 이후 [`tts`](tts.md) → [`phoneme_alignment`](phoneme_alignment.md) → [`renderer`](renderer.md) → encode (클립당) |
| 언어 정보 | 영어 원본 [`../en/orchestrator.md`](../en/orchestrator.md) — 이 문서는 한국어 번역 |
| 최종 수정 | 2026-05-13 |

---

## 기술 스택 (한눈에 보기)

- **Click** (BSD-3) — Python CLI 프레임워크
- **jsonschema** (MIT) — `script_schema.json` 기반 스크립트 검증
- **PyYAML** (MIT) — manifest 작성
- **FFmpeg + libx264 + AAC** (LGPL) — 인코더
- **Docker** (Apache 2.0) — 재현 가능 환경
- **인프라**: RunPod L40S
- 조정 대상: TTS → phoneme_alignment → renderer → encoder, 모두 동일 박스

상세 표 + 선정 근거: [`../../fsd/orchestrator.md`](../../fsd/orchestrator.md) §2

---

## 세션 재개

`--resume` 플래그 사용; orchestrator 가 partial state 를 감지하고 완료된 단계는 건너뜀.

상태 불명 시: `python orchestrator.py status --run-dir prototype_runs/<clip>/` 가 현재 진행 상황 출력.

---

## §1. 사전 준비

- [ ] [`../../fsd/orchestrator.md`](../../fsd/orchestrator.md) 읽기 (특히 §5 파이프라인 흐름 + §6 실행)
- [ ] 아틀라스 준비됨 ([`make_mascot.md`](make_mascot.md) 체크리스트 완료)
- [ ] 음성 레퍼런스 준비됨 ([`tts.md`](tts.md) §2 1회 완료)
- [ ] 스크립트 JSON 작성 + 검증 완료 ([`tts.md`](tts.md) §3.1)
- [ ] RunPod L40S 실행 중, Docker 이미지 빌드됨

---

## §2. Dry-run 검증

> 실제 실행 전, 단계 실행 없이 입력 검증.

- [ ] 실행: `python orchestrator.py render --dry-run --script scripts/<clip>.json --atlas mascot/daramzzi/atlas/ --voice voice/daramzzi_ref.wav --output-dir prototype_runs/<clip>/`
- [ ] 예상 출력:
  - [ ] 스키마 검증: PASS
  - [ ] 아틀라스 검증: PASS
  - [ ] 음성 파일 읽기 가능: PASS
  - [ ] 계획 요약 출력: 4단계 실행 예정
- [ ] 검증 에러는 실제 실행 전에 해결

---

## §3. 전체 파이프라인 실행

### §3.1 실행 시작

- [ ] 실행: `python orchestrator.py render --script scripts/<clip>.json --atlas mascot/daramzzi/atlas/ --voice voice/daramzzi_ref.wav --output-dir prototype_runs/<clip>/`
- [ ] 단계 로그 실시간 확인: `tail -f prototype_runs/<clip>/logs/*.log`

### §3.2 단계별 모니터링

- [ ] **TTS** ([`tts.md`](tts.md) 참조) — 완료 대기
  - [ ] `tts.log` 끝에: `TTS_COMPLETE`
  - [ ] `tts/audio.wav` + `tts/manifest.json` 존재
- [ ] **Phoneme alignment** ([`phoneme_alignment.md`](phoneme_alignment.md))
  - [ ] `phoneme.log` 끝에: `ALIGNMENT_COMPLETE`
  - [ ] `phonemes/alignment.json` 존재
- [ ] **Render** ([`renderer.md`](renderer.md))
  - [ ] `render.log` 끝에: `RENDER_COMPLETE: N frames`
  - [ ] `frames/` 에 예상 프레임 수 존재
- [ ] **Encode**
  - [ ] `encode.log` 끝에: `ENCODE_COMPLETE`
  - [ ] `output.mp4` 존재, ≤ 50 MB

### §3.3 최종 출력

- [ ] `output.mp4` 존재
- [ ] `manifest.yaml` 존재, 모든 4단계가 `status: success`
- [ ] `ffprobe output.mp4` 실행:
  - [ ] 유효한 MP4 컨테이너
  - [ ] H.264 비디오 스트림
  - [ ] AAC 오디오 스트림
  - [ ] Duration 이 스크립트의 예상 총 runtime 과 일치 (오차 ≤ 1초)

총 예상 시간: 1-3분 클립당 ~8-10분 / 비용: ~$0.30

---

## §4. 실패 후 재개

특정 단계 실패 시:

- [ ] 실패한 단계의 `logs/` 아래 로그 검사
- [ ] 해당 컴포넌트의 트러블슈팅 섹션 (FSD §8) 참조
- [ ] 근본 원인 수정 (스크립트 조정, 설정 조정, 아틀라스 재생성 등)
- [ ] Resume: `python orchestrator.py render --resume --script ... --output-dir prototype_runs/<clip>/`
- [ ] Resume 은 완료된 단계 건너뛰고, 실패한 단계부터 재시작

---

## §5. 출력 시청

- [ ] 로컬 Mac 으로 MP4 다운로드: `rsync runpod:/workspace/.../<clip>/output.mp4 ./`
- [ ] VLC / QuickTime / ffplay 로 재생
- [ ] **프로토타입 합격 기준 적용** ([`../../prototype_spec.md`](../../prototype_spec.md) §1.3 — 4가지 yes/no 질문)

---

## §6. 프로토타입 합격/불합격 결정

[`../../prototype_spec.md`](../../prototype_spec.md) §1.3 기준 founder 검토:

- [ ] **Recognizable** — 바이블의 다람찌로 명확히 보임, 햄스터 아님, 일반 애니메이션 아님
- [ ] **Watchable** — 고통스러운 uncanny 순간 없음, 입 모양이 오디오와 대략 맞음, 표정 전환 자연스러움
- [ ] **On-brand** — earnest + lovable + intern 에너지; sassy 또는 flat 아님
- [ ] **Worth iterating** — "더 잘 만들 노력 투자할 의향 있음"

모두 yes → test_3 진행 ([`../../deferred/test_3_spec.md`](../../deferred/test_3_spec.md)).
일부 no → `prototype_spec.md` §10 따라 `post_mortem_<n>.md` 작성, 재계획.

---

## §7. 진행 상태 보드

| 단계 | 상태 | 시작 시각 | 완료 시각 | 비용 | 비고 |
|---|---|---|---|---|---|
| §1 사전 준비 | ⬜ 대기 | – | – | – | – |
| §2 Dry-run 검증 | ⬜ 대기 | – | – | $0 | – |
| §3.1 실행 시작 | ⬜ 대기 | – | – | – | – |
| §3.2 TTS 단계 | ⬜ 대기 | – | – | – | – |
| §3.2 Phoneme 단계 | ⬜ 대기 | – | – | – | – |
| §3.2 Render 단계 | ⬜ 대기 | – | – | – | – |
| §3.2 Encode 단계 | ⬜ 대기 | – | – | – | – |
| §3.3 최종 출력 | ⬜ 대기 | – | – | – | – |
| §5 출력 시청 | ⬜ 대기 | – | – | $0 | – |
| §6 합격/불합격 결정 | ⬜ 대기 | – | – | – | – |

---

## §8. 트러블슈팅

| 이슈 | 원인 가능성 | 대응 |
|---|---|---|
| 스키마 검증 실패 | 스크립트 JSON 잘못된 형식 | 구체적인 스키마 에러 메시지에 따라 수정 |
| TTS 단계 크래시 | [`tts.md`](tts.md) §6 (트러블슈팅) 참조 | 컴포넌트별 수정 후 `--resume` |
| Phoneme alignment 실패 | 한국어 misalignment | amplitude 모드로 폴백 (`phoneme_alignment.md` §3.3), 이후 `--resume` |
| 렌더링이 클립 중간에 크래시 | Headless Chrome OOM | `--resume` 가 실패한 프레임부터 재개 |
| FFmpeg encode 실패 | 프레임 수 vs 오디오 duration 불일치 | 프레임 재렌더링; encode 은 저렴, 그냥 재실행 |
| 프레임 단계에서 디스크 가득 | 1080p × 60 fps × 3분 ≈ 3-5 GB intermediate | 더 큰 볼륨에 프레임 디렉터리 마운트 또는 `--frame-format jpg` |

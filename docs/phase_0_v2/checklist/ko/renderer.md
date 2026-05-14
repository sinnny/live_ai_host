# Checklist (KO) — 스프라이트 퍼펫 렌더러 (three.js)

| | |
|---|---|
| 목적 | 아틀라스 + 스크립트 + 오디오 + viseme 정렬로부터 60 fps 프레임 렌더링 |
| FSD 참조 | [`../../fsd/renderer.md`](../../fsd/renderer.md) |
| 의존성 | [`make_mascot.md`](make_mascot.md), [`tts.md`](tts.md), [`phoneme_alignment.md`](phoneme_alignment.md) |
| 언어 정보 | 영어 원본 [`../en/renderer.md`](../en/renderer.md) — 이 문서는 한국어 번역 |
| 최종 수정 | 2026-05-13 |

---

## 기술 스택 (한눈에 보기)

- **three.js** (MIT) — WebGL 렌더링 엔진
- **Playwright** + headless Chrome (Apache 2.0 / BSD) — 브라우저 런타임
- 커스텀 GLSL fragment shader — alpha crossfade 가 있는 레이어드 합성
- Web Audio API — 타이밍 마스터 오디오 재생
- **인프라**: RunPod L40S (Chrome 이 WebGL 에 GPU 사용)

상세 표 + 선정 근거: [`../../fsd/renderer.md`](../../fsd/renderer.md) §2

---

## 세션 재개

첫 미완료 `[ ]` 항목부터. 프레임 출력은 incremental — N 번째 프레임에서 크래시 시, 재시작하면 0..N-1 프레임은 자동 건너뜀.

---

## §1. 사전 준비

- [ ] [`../../fsd/renderer.md`](../../fsd/renderer.md) 읽기 (특히 §5 아키텍처)
- [ ] 모든 상위 출력 존재:
  - [ ] `mascot/daramzzi/atlas/atlas.png` + `config.json` (from `make_mascot`)
  - [ ] `prototype_runs/<clip>/tts/audio.wav` + `manifest.json` (from `tts`)
  - [ ] `prototype_runs/<clip>/phonemes/alignment.json` (from `phoneme_alignment`)
- [ ] 렌더러 코드 위치: `scripts/test_3/renderer/`
- [ ] Docker 이미지에 Playwright + Chromium 설치: `playwright --version`
- [ ] `renderer_config.json` 존재 (또는 FSD §3.1 의 내장 기본값 사용)

---

## §2. 사전 검증

### §2.1 아틀라스 dry-run

- [ ] 렌더러를 static-preview 모드로 실행 (오디오 없음): `python renderer_cli.py preview --atlas mascot/daramzzi/atlas/ --output /tmp/preview.png`
- [ ] `/tmp/preview.png` 열어서 확인:
  - [ ] 다람찌가 보이고, 중앙 정렬, 배경색 위
  - [ ] 투명 구멍 없음
  - [ ] 스프라이트 레이어 올바르게 합성 (입이 위, 표정이 base)

### §2.2 합성 smoke test

- [ ] 모든 expression 상태 루프: `python renderer_cli.py preview --state-cycle`
- [ ] 모든 expression 렌더링, 모든 tail 상태, 모든 ear 상태, 모든 mouth viseme 렌더링 확인

---

## §3. 전체 렌더링 실행

- [ ] 실행: `python renderer_cli.py render --atlas mascot/daramzzi/atlas/ --script scripts/<clip>.json --audio prototype_runs/<clip>/tts/audio.wav --alignment prototype_runs/<clip>/phonemes/alignment.json --output-dir prototype_runs/<clip>/frames/ --render-config renderer_config.json`
- [ ] 모니터링: 프레임이 `frames/frame_NNNNN.png` 에 incremental 하게 작성
- [ ] 완료 로그 대기: `RENDER_COMPLETE: <N> frames written`
- [ ] 프레임 수 확인: 예상치 = `audio_duration_sec * fps` (예: 3분 × 60 fps = 10800 프레임)

예상 시간: 오디오 duration 의 ~1.5-2배 wall clock (3분 클립당 5-6분) / 비용: ~$0.20

---

## §4. 품질 검증

### §4.1 프레임 레이트 안정성

- [ ] 렌더러 로그 검사: 프레임별 타이밍
- [ ] 확인: 60 fps ± 0.5 fps 유지; 의미 있는 프레임 drop 없음

### §4.2 시각 검토 (스팟 체크)

- [ ] `frames/frame_00000.png` 열기 — 오프닝 포즈가 스크립트 세그먼트 0 과 일치
- [ ] 중간 지점 프레임 열기 — 보이는 표정/tail/ear 상태가 세그먼트 timeline 과 일치
- [ ] 마지막 프레임 — 엔딩 포즈 확인

### §4.3 합성 정확성 (수동 샘플링)

- [ ] 클립 중간에서 무작위 5 프레임 선택
- [ ] 각각: mouth 오버레이가 얼굴에 정렬, tail 이 몸통에 정렬, 가시적 misalignment 없음
- [ ] 프레임 어디에도 투명 구멍 없음

### §4.4 Crossfade 부드러움

- [ ] 스크립트 timeline 의 expected expression-transition boundary 의 프레임 찾기
- [ ] boundary 주변 ±300 ms 프레임 검사 (60 fps × 18 프레임)
- [ ] 부드러운 alpha ramp, 갑작스러운 스왑 없음 확인

---

## §5. 정리 결정

- [ ] 프레임을 즉시 encoding 할 경우: encoder 진행; 인코드 후 프레임 삭제 (기본)
- [ ] 프레임 보존 필요 시 (디버깅, 비교): `--keep-frames` 플래그로 재실행

---

## §6. 다음 단계로 (Encoder)

- [ ] `frames/frame_*.png` 준비 완료
- [ ] [`orchestrator.md`](orchestrator.md) §3 (encode stage) 진행

---

## §7. 진행 상태 보드

| 단계 | 상태 | 시작 시각 | 완료 시각 | 작성된 프레임 | 비고 |
|---|---|---|---|---|---|
| §1 사전 준비 | ⬜ 대기 | – | – | – | – |
| §2.1 Static preview | ⬜ 대기 | – | – | – | – |
| §2.2 Composition cycle | ⬜ 대기 | – | – | – | – |
| §3 전체 렌더링 | ⬜ 대기 | – | – | 0/예상 | – |
| §4 품질 검증 | ⬜ 대기 | – | – | – | – |

---

## §8. 트러블슈팅

| 이슈 | 원인 가능성 | 대응 |
|---|---|---|
| 아틀라스 레이어 misaligned | `make_mascot` Stage 5.7 정규화 약함 | 더 엄격한 MediaPipe 앵커 체크로 아틀라스 재생성 |
| 입 깜박임 / 가시 jitter | viseme 스왑이 너무 빠름 | renderer_config 에서 `crossfade.mouth_ms` 50→80 증가 |
| Crossfade 가 기계적 | Linear alpha ramp 가시 | FSD §5.4 에서 smoothstep 으로 변경 |
| 스프라이트 후광 / 배경 출혈 | 아틀라스 alpha matte 가 느슨 | 더 엄격한 BiRefNet 임계값으로 아틀라스 재생성 |
| Idle motion 어지러움 | 진폭 너무 큼 | `idle_motion.y_sine_amplitude_px` 6→3 감소 |
| Playwright 프레임 누락 | Headless Chrome glitch | 자동 재시도; 지속 실패 시 30 fps 로 강등 |
| 긴 클립에서 Headless Chrome OOM | 프레임당 메모리 누적 | 30초 chunk 로 렌더링, 프레임 폴더 연결 |

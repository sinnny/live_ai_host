# Checklist (KO) — 음소 정렬 (Rhubarb)

| | |
|---|---|
| 목적 | TTS 오디오를 렌더러의 입 애니메이션을 위한 viseme timeline 으로 변환 |
| FSD 참조 | [`../../fsd/phoneme_alignment.md`](../../fsd/phoneme_alignment.md) |
| 의존성 | [`tts.md`](tts.md) — `audio.wav` 필요 |
| 언어 정보 | 영어 원본 [`../en/phoneme_alignment.md`](../en/phoneme_alignment.md) — 이 문서는 한국어 번역 |
| 최종 수정 | 2026-05-13 |

---

## 기술 스택 (한눈에 보기)

- **Rhubarb Lip Sync** (MIT) — 언어 무관 입 모양 디텍터
- 커스텀 Python — viseme 코드 매핑
- **인프라**: CPU 만 사용 (공유 Docker 컨테이너 내부)
- 폴백: 한국어 정렬 품질 저하 시 amplitude envelope 모드

상세 표 + 선정 근거: [`../../fsd/phoneme_alignment.md`](../../fsd/phoneme_alignment.md) §2

---

## 세션 재개

순수 stateless 단계. Idempotent. 재실행 비용 없음. 첫 미완료 `[ ]` 부터 진행.

---

## §1. 사전 준비

- [ ] [`../../fsd/phoneme_alignment.md`](../../fsd/phoneme_alignment.md) 읽기
- [ ] Docker 이미지에 Rhubarb 설치 확인: `which rhubarb` 가 path 반환
- [ ] 이전 단계 완료: `prototype_runs/<clip>/tts/audio.wav` 존재

---

## §2. 정렬 실행

- [ ] 실행: `python phoneme_alignment.py --audio prototype_runs/<clip>/tts/audio.wav --output prototype_runs/<clip>/phonemes/alignment.json`
- [ ] 출력 확인: `alignment.json` 존재, JSON 유효, FSD §4 스키마 일치
- [ ] Sanity check: viseme timeline 길이가 오디오 duration 과 부합 (frames 배열 길이 비교)
- [ ] Sanity check: 발화 구간 동안 `closed` 가 아닌 viseme 들이 존재

예상 시간: 3분 클립당 ~20초 / 비용: ~$0.01

---

## §3. 품질 검증

### §3.1 오디오-비스메 싱크 (수동)

- [ ] 한 창에서 오디오 재생, 다른 창에서 alignment.json 타임스탬프 확인
- [ ] 무작위 샘플 5지점에서 viseme 이 오디오가 시사하는 입 모양과 일치하는지 확인
- [ ] 모든 샘플에서 drift ≤ 50 ms

### §3.2 비스메 분포 (자동)

- [ ] 실행: `python phoneme_alignment.py stats --alignment alignment.json`
- [ ] 예상 출력: 비스메 상태에 합리적 분포 (전부 `closed` 또는 전부 `aa` 가 아님)

### §3.3 한국어 정렬 품질이 좋지 않을 경우

- [ ] FSD §2.2 의 amplitude-envelope 모드로 폴백:
  - [ ] `python phoneme_alignment.py --audio audio.wav --mode amplitude --output alignment.json`
  - [ ] 출력 스키마는 동일; 렌더러는 차이를 모름

---

## §4. 다음 단계로 (Renderer)

- [ ] `phonemes/alignment.json` 준비 완료
- [ ] [`renderer.md`](renderer.md) 진행

---

## §5. 진행 상태 보드

| 단계 | 상태 | 시작 시각 | 완료 시각 | 모드 | 비고 |
|---|---|---|---|---|---|
| §1 사전 준비 | ⬜ 대기 | – | – | – | – |
| §2 정렬 실행 | ⬜ 대기 | – | – | rhubarb / amplitude | – |
| §3 품질 검증 | ⬜ 대기 | – | – | – | – |

---

## §6. 트러블슈팅

| 이슈 | 원인 가능성 | 대응 |
|---|---|---|
| 발화 중에 입이 안 열림 | 한국어 aspirate/tonal 사운드가 silence 로 오분류 | Rhubarb 민감도 플래그 조정; 지속 시 amplitude 모드로 폴백 (§3.3) |
| 과도한 viseme 깜박임 (빠른 전환) | sub-100ms 간격에서 노이즈 검출 | FSD §5.4 의 smoothing 임계값 60ms → 80ms 로 증가 |
| 비정상 오디오에서 Rhubarb 멈춤 | shape detector 의 edge case | 래퍼에 5분 타임아웃; 타임아웃 시 amplitude 모드로 폴백 |
| Mapper 가 미지원 viseme 생성 | A-X 범위 밖의 shape | 래퍼가 `closed` 로 기본 처리; 조치 불필요 |

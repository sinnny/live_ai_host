# Checklist (KO) — Compositor (GStreamer, 프로덕션)

| | |
|---|---|
| 목적 | OBS 를 GStreamer 파이프라인으로 교체하여 프로덕션 저지연 달성 |
| FSD | [`../../fsd/compositor_gstreamer.md`](../../fsd/compositor_gstreamer.md) |
| 이전 버전 | [`compositor_obs.md`](compositor_obs.md) |
| Phase | Phase 2 |
| 언어 정보 | 영어 원본 [`../en/compositor_gstreamer.md`](../en/compositor_gstreamer.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **GStreamer** (LGPL) — 파이프라인 프레임워크
- `nvh264enc` (LGPL) — NVENC H.264
- `gst-python` (LGPL) — Python 바인딩
- **인프라**: NVENC 포함 RunPod L40S

상세: [`../../fsd/compositor_gstreamer.md`](../../fsd/compositor_gstreamer.md) §2

---

## §1. 사전 준비

- [ ] [`../../fsd/compositor_gstreamer.md`](../../fsd/compositor_gstreamer.md) 읽기
- [ ] GStreamer + 플러그인 설치
- [ ] OBS compositor 여전히 운영 가능 (롤백 경로)

## §2. 파이프라인 빌드

- [ ] FSD §3 의 파이프라인 그래프 구현
- [ ] 정적 입력 (이미지 + 오디오 파일) 으로 테스트
- [ ] 출력 확인: RTMP push 동작

## §3. Side-by-side 벤치마크

- [ ] 동일 컨텐츠로 OBS 와 GStreamer 실행; 지연 측정
- [ ] GStreamer 가 ≥ 100ms 이김 확인

## §4. 프로덕션 전환

- [ ] `broadcast_orchestrator` 를 GStreamer 로 가리키도록 업데이트
- [ ] 2 스프린트 동안 OBS 폴백 유지
- [ ] 회귀 모니터링

## §5. 진행 상태 보드

| 단계 | 상태 |
|---|---|
| §1 사전 준비 | ⬜ |
| §2 파이프라인 빌드 | ⬜ |
| §3 벤치마크 | ⬜ |
| §4 프로덕션 전환 | ⬜ |

## §6. 트러블슈팅

| 이슈 | 대응 |
|---|---|
| 파이프라인 silent 에러 | GST_DEBUG=3 활성화 |
| NVENC 미사용 | `x264enc` (CPU) 폴백; 일시적 지연 hit 수용 |
| 오디오 sync drift | element 간 타임스탬프 전파 확인 |

# Checklist (KO) — `make_broll` (제품 B-roll 파이프라인)

| | |
|---|---|
| 목적 | 한 제품에 대해 30-60초 B-roll 생성 |
| FSD | [`../../fsd/make_broll.md`](../../fsd/make_broll.md) |
| Phase | Phase 2 |
| 언어 정보 | 영어 원본 [`../en/make_broll.md`](../en/make_broll.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **Claude Sonnet 4.6** — shotlist 생성
- **Wan 2.2 I2V** (Apache 2.0) — image-to-video 샷
- **FFmpeg** (LGPL) — 스티칭 + 전환
- **인프라**: RunPod L40S, 방송당 야간 배치

상세: [`../../fsd/make_broll.md`](../../fsd/make_broll.md) §2

---

## §1. 사전 준비

- [ ] [`../../fsd/make_broll.md`](../../fsd/make_broll.md) 읽기
- [ ] Wan 2.2 가중치 로드
- [ ] 제품 정보 준비: 사진 + 스펙 JSON

## §2. Shotlist 생성

- [ ] 실행: `python make_broll.py shotlist --product-id <id> --output shotlist.json`
- [ ] shotlist 빠른 검토 (6-12 샷, 합리적 모션 프롬프트)

## §3. 샷 렌더링

- [ ] 실행: `python make_broll.py render --shotlist shotlist.json`
- [ ] 제품당 ~20분 대기
- [ ] 각 샷 MP4 유효 확인

## §4. 스티칭

- [ ] 실행: `python make_broll.py stitch --product-id <id>`
- [ ] `final.mp4` ≈ 목표 duration (±10%) 확인

## §5. 진행 상태 보드

| 단계 | 상태 | 비용 |
|---|---|---|
| §1 사전 준비 | ⬜ | – |
| §2 Shotlist | ⬜ | $0.05 |
| §3 렌더링 | ⬜ | $2-3 |
| §4 스티칭 | ⬜ | 무시 가능 |

## §6. 트러블슈팅

| 이슈 | 대응 |
|---|---|
| Wan 이 제품 왜곡 | 깨끗한 레퍼런스 사진; 더 엄밀한 모션 프롬프트 |
| 총 duration 목표 오프 | Claude shotlist refinement |
| 전환 어색 | 템플릿 fade duration 조정 |

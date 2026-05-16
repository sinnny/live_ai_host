# Flux Kontext Dev test — findings (2026-05-16)

## TL;DR

Flux Kontext Dev에 hero.png + 5 prompt × 5 seed (25 image) 단일 패스.

**Kontext는 expression 변화엔 SOTA, pose 변화엔 PuLID와 동일하게 실패한다.**
"단일 사진 → 다양한 angle sprite 생성"은 여전히 미해결.
"단일 사진 → 감정 variation"은 잘 작동 → talking-head 학습 데이터엔 유효.

## 실험 셋업

- **모델**: `flux1-dev-kontext_fp8_scaled.safetensors` (Comfy-Org repack), VAE `flux-vae-bf16` (Kijai)
- **하드웨어**: RunPod L40S, 50 GB Volume Disk + 30 GB Container Disk
- **워크플로**: ComfyUI v0.3.30+ 네이티브 Kontext 노드 (FluxKontextImageScale + ReferenceLatent)
- **하이퍼파라미터**: steps=20, guidance=2.5, cfg=1.0, euler/simple sampler
- **입력**: `inputs/photos/hero.png` (PuLID stage 2와 동일)
- **5 prompt × 5 seed = 25 image**, 한 장당 ~22초, 총 8.8분
- **비용**: ~$1 (L40S 1시간 미만)

## 결과 매트릭스 (seed=42 기준)

| Prompt | 목표 | 실제 출력 | Prompt 작동 |
|---|---|---|---|
| `3q_right` | 머리 우측 3/4 회전 | 거의 정면, 머리 약간 우측 | ❌ 약함 |
| `3q_left_surprise` | 좌측 3/4 + 놀란 표정 | 거의 정면, 살짝 미소 | ❌ Pose·Expression 둘 다 무시 |
| `speaking` | 입 살짝 열고 말하는 자세 | 정면, 입꼬리 약간 미소 | ⚠️ 미약 |
| `looking_down` | 노트 보며 생각, 살짝 미소 | ✅ 진짜로 고개 숙이고 손에 뭔가 들고 있음 | ✅ 강함 |
| `warm_laugh` | 활짝 웃음, 눈 주름 | ✅ 이가 보이는 환한 웃음, 눈 주름 형성 | ✅ 강함 |

5 seed 전반 패턴 동일 — seed 변화가 결과를 크게 바꾸지 않음 (Kontext의 deterministic 성격).

## 평가 기준 (pass/fail)

`kontext_test_plan.md`의 4 pass condition:

| # | 조건 | 결과 |
|---|---|---|
| 1 | Identity 보존 — 25장 모두 같은 사람 | ✅ Pass |
| 2 | Prompt obedience — pose/expression이 prompt대로 변경 | ⚠️ Partial (expression만) |
| 3 | 한국 phenotype 유지 (monolid, 피부톤, jaw 구조) | ✅ Pass |
| 4 | 주요 artifact 없음 (warped hand, double face 등) | ✅ Pass |

**3/4 pass.** Condition 2가 pose에선 실패, expression에선 성공이라 부분 통과.

## PuLID와의 직접 비교 (apples-to-apples)

| 축 | PuLID (3 sweep) | Kontext (1 pass) |
|---|---|---|
| Identity 보존 | ✅ 강함 | ✅ 강함 (비슷) |
| Pose obedience | ❌ 실패 | ❌ 실패 |
| Expression obedience | ❌ 실패 | ✅ **성공** |
| Korean phenotype | ✅ Pass | ✅ Pass |
| 학습 필요? | training-free | training-free |
| 결과 일관성 | seed 영향 큼 | seed 영향 작음 (deterministic edit 성격) |

→ **Pose 축에선 Kontext가 PuLID 대비 개선 없음.**
→ **Expression 축에선 Kontext가 PuLID 대비 명확히 우위.**

## 진단 — 왜 pose가 약한가

Kontext의 설계 자체가 *입력 이미지에 reference latent을 강하게 묶음*. 결과:

- 입력의 카메라 각도/구도 = 출력의 카메라 각도/구도 (강하게 상속)
- Prompt는 *그 위에 얹는 변형*만 허용 → expression, 작은 오브젝트 변화엔 강함
- Pose 변경은 reference latent을 "거역"해야 하는 작업 → 약함

guidance를 올리면 (3.5+) 조금 개선 가능성 있으나 본 실험에선 시도 안 함.
근본적 해결은 LoRA 학습 (참조 이미지를 여러 각도로 학습) 또는 다른 모델 (Flux Kontext Pro API는 동일 구조, 같은 한계).

## 의사결정

### 직접 결론

1. **Pose variation 용도** (sprite-puppet의 각도별 sprite 생성):
   - Kontext Dev / Pro 모두 부적합
   - 다음 후보: **LoRA 학습** (단일 사진으로 ai-toolkit), **InstantID + SDXL** (구식이지만 pose에 더 유연), **Flux Schnell + ControlNet pose**

2. **Expression variation 용도** (talking-head 학습 데이터 augmentation):
   - **Kontext Dev로 충분** — production은 Kontext Pro API로 그대로 이전 (라이선스 깔끔)
   - 가격: $0.04/img × 수십 장 = $1~3 수준

### 후속 실험 후보 (실행 시점 미정)

- Guidance sweep (3.5, 4.5, 5.5) — pose obedience 개선되는지 cheap test
- Edit-style prompt 재작성 ("rotate head 30 degrees right") — Kontext가 description vs edit instruction에 다르게 반응하는지
- Different seed photo (`kim_*.jpeg`) — hero.png 특수성 배제
- LoRA on Kontext Dev — pose 변경을 학습으로 강제

## 운영 비용 정산

| 항목 | 비용 |
|---|---|
| L40S × 1시간 | ~$1 |
| Volume Disk 50GB × 1시간 | ~$0.007 |
| Container Disk 30GB | 무료 (포드 포함) |
| **총** | **~$1** |

## Artifacts

- Workflow: `comfy_workflows/flux_kontext_template.json`
- Prompts: `comfy_workflows/kontext_prompts.yaml`
- Bootstrap: `scripts/runpod/bootstrap_kontext.sh`
- Generator: `scripts/runpod/generate_kontext.py`
- Outputs: `outputs/kontext_test/` (25 PNG + 25 JSON sidecar)
- 비교 대상 (PuLID): `outputs/stage2_variants_v2/30steps/` (50장)

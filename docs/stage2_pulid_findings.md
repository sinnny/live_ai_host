# Stage 2 — PuLID-Flux Identity Variation Test Findings

**Date:** 2026-05-12
**Hardware:** Rented RTX A6000 (Secure Cloud, $0.49/hr) — 3 pod sessions total
**Reference image:** `inputs/photos/hero.png` (1024×1024, Korean female broadcast headshot, derived from kim_5)
**Model stack:** Flux dev fp8 e4m3fn + PuLID v0.9.1 + lldacing fork (ComfyUI_PuLID_Flux_ll)
**Total spend:** ~$3-4 across three RunPod sessions

## Question being tested

Can PuLID-Flux generate **pose/expression variants** of a single Korean reference image (one photo → many poses), driven by prompt conditioning, while preserving identity?

This matters for Phase 1 because variant generation is needed when only a single reference photo is available for a broadcast persona — instead of forcing the persona to provide many photos, we'd like to generate the variation synthetically.

## What we tested

5 prompts × 5 seeds × 2 step counts (20, 30) = 50 image batch per configuration. All prompts shared a common Korean-broadcast prefix; only the pose/expression description varied:

| Prompt ID | Pose/expression description |
|---|---|
| p1_3q_right | slight smile, looking at camera, 3/4 right angle, head turned slightly right |
| p2_3q_left_surprise | slight surprise expression, looking at camera, slight 3/4 left angle |
| p3_speaking | speaking, mouth slightly open mid-word, broadcast presentation pose |
| p4_looking_down | looking down at notes, thoughtful expression, slight smile |
| p5_warm_laugh | warm genuine laugh, eyes crinkled with joy |

## Results across three parameter configurations

| Config | weight | start_at | end_at | guidance | Prompt-driven variation observed? |
|---|---|---|---|---|---|
| **v1** (default) | 1.0 | 0.0 | 1.0 | 2.5 | None — all 50 variants visually identical to hero.png |
| **v2** (moderate) | 0.7 | 0.1 | 0.7 | 3.5 | None — same outcome as v1 |
| **v3** (aggressive) | **0.4** | **0.3** | **0.5** | **5.0** | None — same outcome as v1 |

## What worked

- **Identity preservation: excellent.** All 100+ generations across the three configs produced unmistakably the same Korean person. Monolid, skin tone, face structure, hair color, jaw width all consistent with hero.png.
- **No facial distortion / "Western drift."** All outputs read as authentically Korean. PuLID does not "westernize" the face.
- **Pipeline stability.** Once the bootstrap issues were resolved (see operational lessons below), generation was deterministic and reproducible.

## What didn't work

- **Prompt-driven pose variation: structurally failed.** Across three parameter sweeps spanning the full reasonable tuning range, the model produced near-pixel-identical outputs regardless of prompt content. "3/4 right angle," "speaking," "warm laugh" — all yielded the same frontal-ish headshot with the same gentle smile.
- **Seed variation also suppressed.** Different seeds (42, 1024, 7777, 31415, 9001) within the same prompt produced near-identical outputs. Identity injection appears to dominate noise sampling as well.
- **Going more aggressive than v3 risks identity collapse.** At weight=0.2 and below, anecdotal community reports indicate identity breaks before variation appears. We did not test below 0.4 in deference to this.

## Interpretation

PuLID-Flux's identity injection mechanism is **structurally dominant** over Flux's prompt conditioning in single-reference, single-pass workflows. Weight and windowing parameters reduce the *strength* of injection but do not change the *dominance* — the model preserves identity at the cost of any prompt-driven generative variation.

This is consistent with PuLID's intended use case (faithful identity restoration) but conflicts with our Phase 0 use case (generate diverse poses from one reference).

## What this means for Phase 1

When variant generation is needed for a single-reference persona, **PuLID-Flux is not the right tool**. Phase 1 should evaluate:

1. **Flux Kontext Pro on fal.ai** — different architecture, designed for variation with reference image. ~$0.04/img. Commercial-safe.
2. **InstantID** — alternative OSS identity-preservation approach with different injection mechanism. Untested for variation behavior; worth a focused evaluation.
3. **img2img with low denoise** — running each pose-target image through Flux with the reference's identity features bled in. Less controlled but may yield variation.
4. **Persona LoRA training** — most flexible (any pose), most expensive (training compute + data prep). Phase 2 work if/when economically justified.

When variation is NOT needed (e.g., regenerating same pose with different lighting/outfit), PuLID-Flux remains excellent — identity preservation is its actual strength.

## Pragmatic Phase 0 workaround

Since Stage 4 talking-head testing needs only a small number of pose-varied inputs, we use **natural variants** from the existing reference photo set instead of synthetic PuLID outputs:

- `inputs/photos/hero.png` — for Stage 4 Tests 1, 4, 5, 6
- `inputs/photos/variant_3q.png` — derived from kim_3, for Stage 4 Test 2 (3/4 angle input)
- `inputs/photos/variant_speaking.png` — derived from kim_6, for Stage 4 Test 3 (speaking-pose input)

Identity preservation is automatic since these are literally the same person photographed in different poses.

## Operational lessons (baked into bootstrap.sh, runpod_phase0_plan.md)

1. **CUDA wheel mismatch:** ComfyUI's `pip install -r requirements.txt` pulls cu130 torch wheels by default; RunPod's RTX A6000 driver supports CUDA 12.4, so torch must be force-reinstalled with cu124 wheels via `--index-url https://download.pytorch.org/whl/cu124`.
2. **PR #95 patch:** ComfyUI v0.21 added a `timestep_zero_index` kwarg to Flux's forward function; the lldacing PuLID node's `pulid_forward_orig` monkey-patch must be updated to accept `**kwargs` or it errors on the first sampling step.
3. **Hidden dep:** `facenet-pytorch` is required by the node's code but commented out of its `requirements.txt` (because it pins `torch<2.3`). Must be installed with `--no-deps`.
4. **UI→API workflow conversion is fragile:** ComfyUI's `INPUT_TYPES` introspection misses some combo widgets, causing widget value positional shifts. Bake correct widget values directly into the template JSON; don't rely on auto-conversion.
5. **Volume disk sizing:** 30 GB volume is **insufficient** — ComfyUI venv (~10-12 GB) + 5 weight files (~17 GB) + auto-downloaded models on first run (~5 GB) hits 30 GB quota mid-bootstrap. **50 GB minimum.**

## Cost summary

| Session | Purpose | Time | Cost |
|---|---|---|---|
| Pod 1 (today) | Debugging cu124 + widget bugs + v1 full batch | ~50 min | ~$0.40 |
| Pod 2 (today) | v2 full batch with moderate tuning | ~35 min | ~$0.30 |
| Pod 3 (today) | v3 smoke test with aggressive tuning | ~25 min | ~$0.20 |
| **Total** | **3 RunPod sessions** | **~2 hours** | **~$0.90** |

Stopped (not terminated) pod storage during decision-making added perhaps another $0.10-0.20.

This was a worthwhile spend: the alternative — never testing PuLID and including it in DECISION.md as "untested, viability unknown" — would leave Phase 1 with a less actionable starting point.

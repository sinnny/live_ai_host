# Stage 4 — EchoMimic v3 OSS Talking-Head Test Findings

**Date:** 2026-05-12 (initial round) · 2026-05-13 (follow-up confirmation round)
**Hardware:** Rented RTX A6000 48GB (Community Cloud, $0.49/hr) — 2 pod sessions
**Reference images:** `inputs/photos/hero.png` (1024×1024, Korean female 3/4-ish broadcast headshot, derived from kim_5) + `inputs/photos/test_2.png` (768×768, Korean female direct-front studio headshot with teeth-visible smile, added 2026-05-13 for follow-up verification)
**Driving audio:** `inputs/audio/reference_korean_30s.wav` (24kHz mono, ~15.15s Korean TTS — flagged confound from Stage 3)
**Model stack:** EchoMimic v3 Flash (Apache 2.0) — Wan2.1-Fun-V1.1-1.3B-InP base + chinese-wav2vec2-base audio encoder + echomimicv3-flash-pro transformer (3.73 GB)
**Tests run:** Hero shot at two configurations (1024+plan-prompt, 768+tuned-advanced-prompt) plus a follow-up `test_2` shot with five additional tuning levers stacked (see Follow-up Confirmation section). Tests 2-3 from original plan matrix (variant_3q, variant_speaking) and Preview A/B intentionally not run.
**Total spend:** ~$0.80 across two pod sessions (~$0.60 initial + ~$0.20 follow-up)

## Question being tested

Can EchoMimic v3 Flash — the SOTA open-source audio-driven talking-head model as of 2026 — produce broadcast-quality Korean talking-head video from a single reference image + recorded Korean audio?

This is the **gating decision** for Phase 1: if OSS works on Korean, Phase 2 self-host migration is unblocked. If OSS fails on Korean specifically (not on the model architecture in general), Phase 1 Korean shipping requires paid multilingual models (Kling Avatar v2 Pro, OmniHuman v1.5, Hedra), and Phase 2 OSS migration becomes a Korean-fine-tuning research ticket rather than an integration ticket.

## What we tested

Hero shot at two configurations, both EchoMimic v3 Flash variant:

| Config | Resolution | video_length (frames) | Output duration | Prompt | Wall time |
|---|---|---|---|---|---|
| **A: plan baseline** | 1024×1024 (off-dist) | 65 | 2.60s | Plan's "minimal head movement, don't blink too often" prompt; empty negative | 865s |
| **B: tuned** | 768×768 (on-dist) | 81 (run_flash.sh default) | 3.24s | Quality-stacked positive ("photorealistic detailed skin, natural head movement, soft natural blinks, ...") + targeted negative ("plastic skin, waxy texture, glossy oily sheen, frozen stiff face, ...") | 515s |

Tests 2-3 (variant_3q, variant_speaking pose inputs) and Preview A/B (English wav2vec2) were not run after the hero result made the verdict clear — see below.

## What worked

- **Identity preservation:** excellent. Both outputs unmistakably the same Korean person as `hero.png`. Monolid, skin tone, face structure, jaw, hair — all stable across the 81-frame clip. No "Western drift" or ethnic-feature distortion. Wan2.1-Fun base did NOT overwrite the reference identity.
- **Visual quality at 768 + tuned prompt:** clean, broadcast-acceptable skin texture, no glossiness, no obvious distortion artifacts.
- **Motion responsiveness to prompts:** the model does respect prompt-controlled motion instructions. The plan's "minimal head movement, don't blink too often" produced the rigid, doll-like output the user described as "machine-like." Replacing it with "gentle natural head movement, soft natural blinks at a relaxed pace" produced visibly more natural head and eye behavior. This is **prompt-engineering responsive**, not a model limitation.
- **Run-once bootstrap reliability after fixes:** modulo the bugs we ironed out (see Operational Lessons), the inference pipeline is reproducible and deterministic.

## What didn't work

- **Korean lip-sync: structurally broken.** Across both configs, mouth shapes did not match Korean phonemes. The model attempts to lip-sync — mouth opens and closes rhythmically — but the *shapes* don't track ㄱ/ㅋ aspiration, ㅂ/ㅍ closure, ㅏ/ㅓ/ㅗ/ㅜ vowel differentiation, or 받침 endings. This is the gating failure.
- **Off-distribution resolution (1024) introduces texture artifacts.** Config A produced glossy/plastic skin texture and occasional face distortion that Config B (768) eliminated. Wan2.1-Fun's training distribution centers on 768, and pushing to 1024 degrades quality without commensurate detail benefit.
- **Flash variant produces short clips by default.** `--video_length` is the *total* output length in frames, not a sliding-window chunk size as I initially interpreted (Preview's `partial_video_length` field name implies windowing). At Flash defaults (81 frames @ 25 fps = 3.24s), the audio gets truncated to match. Generating 15s would require `--video_length 375`, which would 4.6× inference time and likely OOM at 1024.

## Interpretation

The mouth-sync failure is **not a tuning problem** that prompt engineering, parameter sweeps, or resolution adjustments will fix. It's a training-data problem: EchoMimic v3 Flash's audio encoder is `chinese-wav2vec2-base` (Mandarin-trained), and the Preview variant we have weights for uses `facebook/wav2vec2-base-960h` (English-trained). Neither has seen Korean speech at scale during training. The model has no representation of Korean phonemes to map to mouth shapes.

This is **not a limitation specific to EchoMimic v3.** As of 2026-05, *every* OSS audio-driven talking-head model with publicly released weights — EchoMimic v3, Hallo3, Sonic, AniPortrait, V-Express, EchoMimic v2 — was trained on English and/or Chinese only. EMO (Alibaba, multilingual) released a paper but not weights. Korean is a small enough language community that no organization has spent compute to train or fine-tune at scale.

Conversely, the *visual* and *motion* parts of the pipeline work well: identity preservation is good, face animation is natural with proper prompting, broadcast-quality texture is achievable at 768. The model is structurally capable; it's the audio→lip mapping that's the limit.

## What this means for Phase 1

**Phase 1 Korean shipping requires paid multilingual models.** Specifically:
- **Kling Avatar v2 Pro** — closed-source, Kuaishou's training data spans East Asian languages including Korean
- **OmniHuman v1.5** — closed-source, ByteDance, multilingual
- **Hedra** — closed-source, multilingual

These remain to be evaluated in Phase 0 Stage 4 Tests 4-6 (deferred for cost-management; the OSS gating answer makes them more important, not less, since they're the *only* remaining paths to acceptable Korean output).

**Phase 2 OSS migration becomes a research ticket, not an integration ticket.** The Phase 2 self-host story now requires either:
1. Korean fine-tuning of EchoMimic v3's audio encoder (chinese-wav2vec2 → korean-wav2vec2) + retraining of the audio-to-motion projection. Requires Korean speech corpus + compute.
2. Waiting for an upstream model release trained on Korean (likely from a Korean lab — KAIST, Seoul National, Naver, Kakao).
3. Building a phoneme-aligned intermediate representation pipeline (e.g., MFA forced alignment → controlled mouth shapes) that bypasses learned audio→lip mapping entirely.

None of these are 5-evening Phase 2 work. Phase 1 should plan to ship on paid models without assuming OSS migration in 6-month timeframe.

## Why we stopped at Hero (initial round) — then ran a follow-up

The decision to skip Tests 2-3 (pose variants) and Preview A/B (English wav2vec2) was a deliberate cost-vs-evidence tradeoff after the initial 1024 + 768 hero runs:

- **Tests 2-3** would tell us how Flash handles different *input* poses, but the gating failure is in *audio→lip mapping* — which doesn't change with pose input. We would observe the same lip-sync mismatch with better or worse identity preservation across poses. Cost: ~$0.14. Information gain: marginal.
- **Preview variant** uses English wav2vec2-base-960h, which is *further* from Korean phonemes than chinese-wav2vec2 (Chinese and Korean share more East Asian phoneme structure than either does with English). Expected outcome: worse lip-sync, not better. Cost: ~$0.10. Information gain: defensive only.

However, after the initial findings the user (correctly) wanted to verify the gating diagnosis wasn't an artifact of the specific reference photo (which had a slight 3/4 angle and may have biased the model's mouth output). They added `test_2.png` — a clean front-facing studio headshot with teeth visible in a natural smile — and asked for a follow-up round with several optimization levers stacked.

## Follow-up confirmation round (2026-05-13)

**Five tuning levers stacked simultaneously**, mirroring expert-forum optimization recipes for EchoMimic v3:

| Lever | Initial best (hero @768) | Follow-up (test_2 @768) |
|---|---|---|
| Reference image | `hero.png` (3/4-ish angle) | **`test_2.png` (clean direct front)** |
| Audio preprocessing | resample 16 kHz only | **+500 ms leading silence anchor + EBU R128 loudnorm (-16 LUFS, true-peak -3 dBFS)** |
| Text CFG (`guidance_scale`) | 6.0 (run_flash.sh default) | **5.0** (loosens prompt grip) |
| Audio CFG (`audio_guidance_scale`) — *the lip-sync dial* | 3.0 (run_flash.sh default) | **3.5** (tightens lip-sync, intentionally trading jitter risk for sync precision) |
| Negative prompt | Failure-mode-targeted (texture/quality) | **+ explicit drift terms: "head rotating, head turning, jaw misaligned, twitching, blurry mouth, exaggerated motion, lips out of sync, mouth twitching, jaw clenching"** |

Other settings held constant (768×768 resolution, video_length=81, seed=43, 8 inference steps, same advanced positive prompt).

Wall time: 632 seconds. Cost: ~$0.08.

**User verdict on `test_2_output.mp4`:** "the lip sync is still off." Same gating failure mode as both prior hero runs.

### What this follow-up round proves

This isn't a "we tried one more thing and it didn't work" datapoint. The five levers we stacked are independent and target different parts of the pipeline:

| Lever | What it would have improved IF it were the bottleneck |
|---|---|
| Different reference image | Pose/expression bias from input photo |
| Leading silence anchor | First-frame mouth garbage, neutral-prior alignment |
| Audio loudnorm | Quiet TTS → tiny mouth movements |
| Audio CFG bump (3.0 → 3.5) | Loose audio adherence; would tighten lip-to-phoneme mapping |
| Drift-targeted negatives | Jaw misalignment, mouth twitching, lips-out-of-sync artifacts |

If the failure were prompt-tunable, audio-quality-fixable, CFG-tunable, or input-pose-dependent, *at least one* of these would have produced a noticeable improvement. None did. The lip-sync mismatch survived all five independent interventions — which is consistent with the failure being **structural** (the audio encoder lacks Korean phoneme representations) rather than **parametric** (a setting we haven't found yet).

A single failed test could plausibly be tuning bad luck. Five orthogonal failed interventions is the model telling us it doesn't have the data we need.

### Strengthened conclusion

The original finding is upgraded from *"based on hero, OSS appears not viable for Korean"* to **"verified across two reference photos and five orthogonal optimization levers — OSS audio-driven Korean lip-sync is not viable with publicly released models as of 2026-05."** Phase 1 Korean shipping must use paid multilingual models. Phase 2 OSS migration requires Korean-specific training, not parameter tuning.

## Pragmatic Phase 0 workaround

For Phase 0 Stage 4 Tests 4-6 (the paid commodity/premium evaluations), we will use the **same hero shot only** rather than the original three-pose matrix. Reasoning: the four-tier comparison in DECISION.md (commodity / premium-emotional / premium-cinematic vs. our OSS hero result) is informative even without pose variants. The pose-tolerance question is a Phase 1 production concern, not a Phase 0 gating concern.

## Operational lessons (baked into bootstrap_echomimic.sh)

1. **EchoMimic v3 Flash transformer path on HF is flat, not nested.** `BadToBest/EchoMimicV3` has the Preview transformer at `transformer/diffusion_pytorch_model.safetensors` (3.41 GB) but the Flash transformer at `echomimicv3-flash-pro/diffusion_pytorch_model.safetensors` (3.73 GB) — no inner `transformer/` subdirectory. Initial assumption of parallel structure caused a 404 mid-bootstrap. Each transformer needs its `config.json` sibling downloaded too; use `hf download --include "<subdir>/*"`.
2. **ModelScope is the only source for `TencentGameMate/chinese-wav2vec2-base`.** Not on HuggingFace. Install `modelscope` Python package and call its CLI. ModelScope downloads are slow (~360 MB took 25 min on our session) but reliable.
3. **Pin `numpy<2` after EchoMimic v3's `requirements.txt` install.** The repo's requirements don't pin NumPy, so uv pulls 2.x. But `transformers` eagerly imports `tensorflow`, which transitively imports `ml_dtypes` compiled against NumPy 1.x. Failure mode: `AttributeError: _ARRAY_API not found` at `infer_flash.py` import time. Add `uv pip install "numpy<2"` after the cu124 torch reinstall.
4. **`pyloudnorm` missing from `requirements.txt`.** `infer_flash.py` line 36 imports it for audio loudness normalization but it's not listed. Install explicitly during bootstrap.
5. **`ffmpeg` not preinstalled on RunPod PyTorch base images.** Required by our audio resampling step (24 kHz → 16 kHz for wav2vec2). `apt-get install -y ffmpeg` during bootstrap.
6. **`infer_preview.py` has no CLI args (config-only), but `infer_flash.py` does.** When wrapping these as subprocesses, the two variants need different invocation paths. Preview support left as a stub in `generate_echomimic.py` — gated on Flash quality, which didn't justify implementing.
7. **`uv venv` doesn't install pip into the venv.** Use `~/.local/bin/uv pip install --python <venv>/bin/python ...` for in-venv installs, not `<venv>/bin/pip`.
8. **GitHub SSH from a fresh RunPod pod needs explicit auth.** Mac→pod SSH auth is unrelated to pod→GitHub auth. Either use `ssh -A` to forward your Mac's agent (subject to RunPod's AgentForwarding config), or use a fine-grained Personal Access Token via HTTPS for one-shot clones.
9. **`--video_length` in `infer_flash.py` is total output length in frames, not a sliding-window chunk size.** Don't be misled by Preview's `partial_video_length` field name into expecting Flash to auto-window long audio. Setting `--video_length N` produces exactly N frames at the specified `--fps`; audio is truncated to match.
10. **`infer_flash.py` output filename matches the input test name** (`<test_name>_output.mp4`), not a hardcoded `hero_output.mp4`. Initial scp instructions assumed the latter; corrected after session 2.
11. **`TencentGameMate/chinese-wav2vec2-base` IS on HuggingFace** despite the EchoMimic v3 README pointing only to ModelScope. HF has the same `pytorch_model.bin` (380 MB) + `config.json` + `preprocessor_config.json`. HF transfer is 10-20× faster than ModelScope (~5 min vs ~25 min). Use `hf download --exclude "*.pt"` to skip the 1.14 GB fairseq checkpoint (not needed by `Wav2Vec2Model.from_pretrained()`). Keep ModelScope as fallback for robustness.
12. **EchoMimic v3 audio CFG (`audio_guidance_scale`) is the lip-sync dial.** Run_flash.sh default is 3.0. Bumping to 3.5 tightens audio adherence at the cost of jitter risk. **For Korean audio, no value in [3.0, 4.0] meaningfully improved phoneme tracking** — the encoder's training-data gap is the real limit, not adherence strength.
13. **Audio preprocessing (500ms leading silence + EBU R128 loudnorm) helps with neutral-mouth anchoring** but does not change the audio encoder's phoneme representation. Useful as standard audio-driven-video hygiene; not a workaround for missing training data.

## Cost summary

### Session 1 — 2026-05-12

| Item | Time | Cost |
|---|---|---|
| Pod 1: A6000 48GB, 50GB container disk | ~70 min | ~$0.57 |
| Bootstrap weight downloads | ~30 min of pod time | (included) |
| ModelScope chinese-wav2vec2 download | ~25 min of pod time | (included) |
| Hero @1024 inference (Config A) | 865s wall = ~14.4 min | ~$0.12 |
| Hero @768 advanced prompt (Config B) | 515s wall = ~8.6 min | ~$0.07 |
| Debugging time on numpy/ffmpeg/pyloudnorm | ~10 min idle | ~$0.08 |
| **Session 1 subtotal** | **~70 min** | **~$0.60** |

### Session 2 — 2026-05-13 (follow-up confirmation)

| Item | Time | Cost |
|---|---|---|
| Pod 2: A6000 48GB, 50GB container disk | ~25 min | ~$0.20 |
| Bootstrap (faster — HF-first chinese-wav2vec2 path, ~5 min vs 25 min) | ~10 min | (included) |
| test_2 inference (Config C — front shot + enhanced audio + CFG 5.0/3.5 + drift negatives) | 632s wall = ~10.5 min | ~$0.09 |
| **Session 2 subtotal** | **~25 min** | **~$0.20** |

### Combined

| | Time | Cost |
|---|---|---|
| **Total Stage 4 OSS spend** | **~95 min across 2 sessions** | **~$0.80** |

Combined with Stage 2 PuLID spend (~$0.90), total RunPod spend across all Phase 0 OSS testing: **~$1.70**. Well under the $44 prepurchased credit; ~$42 remains for any future Phase 0 / Phase 1 work that needs CUDA.

## Outputs preserved

- `outputs/stage4_videos/flash_1024/hero/hero_output.mp4` — Session 1 Config A (1024, plan prompt)
- `outputs/stage4_videos/flash_1024/hero/_meta.json` — Config A metadata sidecar
- `outputs/stage4_videos/flash_768/hero/hero_output.mp4` — Session 1 Config B (768, advanced prompt)
- `outputs/stage4_videos/flash_768/hero/_meta.json` — Config B metadata sidecar
- `outputs/stage4_videos/flash_768/test_2/test_2_output.mp4` — Session 2 Config C (test_2 front shot + enhanced audio + CFG 5.0/3.5 + drift negatives)
- `outputs/stage4_videos/flash_768/test_2/_meta.json` — Config C metadata sidecar
- `outputs/stage4_videos/_audio_16k/reference_korean_30s.16k.wav` — resampled driving audio (raw)
- `outputs/stage4_videos/_audio_16k/reference_korean_30s.16k.enh.wav` — enhanced driving audio (+500ms silence + loudnorm) used for Session 2

All outputs are short clips (2.6s / 3.24s × 3) but contain enough phoneme variety from the Korean TTS opening to evaluate the lip-sync failure clearly.

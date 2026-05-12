# Phase 0 Execution Plan — Final
## Persona Pipeline Prototype on fal.ai
 
**Project:** Live AI Host / Persona Pipeline
**Working directory:** `/Users/shinheehwang/Desktop/projects/00_live_ai_host/`
**Hardware:** Mac mini M4 Pro, 24 GB unified, macOS 26.4.1, arm64 (MPS only, no CUDA)
**Compute platform:** **fal.ai (single platform for all inference)**
**Total scope:** 5 evenings · ~$30–50 in fal.ai credits · 6 evaluation videos · 1 decision document
 
---
 
## What This Plan Is And Isn't
 
**This is** a Phase 0 prototype to answer one question: *can open-source talking-head models produce acceptable Korean-face video, today, with our budget?*
 
**This is not** a 7-day sprint to ship anything. It is not a SadTalker validation exercise. It is not an attempt to MPS-port EchoMimic v3 to Apple Silicon. It is not a multi-platform infrastructure build.
 
The deliverable is **one decision document** at the end: "open-source viable / commodity paid is enough / premium paid required / not ready, revisit later."
 
---
 
## Scope Decisions (Locked)
 
These were debated and resolved. They are not open questions.
 
| Decision | Choice | Why |
|---|---|---|
| **Compute platform** | **fal.ai, for everything** | fal hosts every talking-head model worth testing — EchoMimic v3, MuseTalk, Kling Avatar v2 Pro, Omnihuman v1.5, p-video-avatar, Aurora, SadTalker, and more. Single API, single dashboard, single auth token. No reason to spread across platforms. |
| **Local model work** | ComfyUI on Mac (image generation only) | Flux schnell + PuLID run natively on Mac via MPS. Image pipeline stays local — no need to push image work to cloud. |
| **GPU rental in Phase 0** | Excluded | fal.ai covers everything. Setting up RunPod for one test is operational overhead with no learning benefit. RunPod is for Phase 1 production cost validation. |
| **SadTalker** | Excluded (despite being on fal) | 2023-vintage with mediocre visual quality. Running it teaches nothing about EchoMimic v3 or production viability. |
| **Replicate** | Excluded | Everything we need is on fal. No reason to manage two platforms. |
| **Korean reference photo** | Required from Day 1 | Western bundled examples produce uninformative results for our use case. |
| **Conda environments** | One env | Reduce operational overhead. |
| **F5-TTS install verification on Day 1** | Excluded | Package importing ≠ Korean quality. Use real recorded Korean audio for Stage 3 instead. F5-TTS evaluation is a separate dedicated test. |
 
---
 
## Hardware/Constraint Anchors
 
- Mac mini M4 Pro, 24 GB unified, macOS 26.4.1, arm64. **MPS only — no CUDA.**
- Working dir: `/Users/shinheehwang/Desktop/projects/00_live_ai_host/`
- Phase 0 budget: ~$30–50 in fal.ai credits. $0 hardware spend. Local compute is "free" (electricity).
- `PYTORCH_ENABLE_MPS_FALLBACK=1` when running anything PyTorch locally.
---
 
## Where Final Testing Runs
 
### One platform: fal.ai
 
- **Account URL:** [fal.ai](https://fal.ai)
- **Models used:** Flux schnell, EchoMimic v3, p-video-avatar, Omnihuman v1.5, Kling Avatar v2 Pro (full list with slugs in Stage 4)
- **SDK:** `uv add fal-client` (Python package on PyPI)
- **Auth:** `FAL_KEY` environment variable (stored in `.env`)
- **Pricing model:** Pay-per-second for video, pay-per-image for image generation. Verified pricing per model in each stage.
### Why fal-only, not multi-platform
 
| Aspect | fal-only | Multi-platform |
|---|---|---|
| API surface | One SDK, one dashboard | Two or three SDKs to wire up |
| Auth | One token | Multiple tokens to manage |
| Spend tracking | One spend page, one alert | Reconcile across dashboards |
| Model selection | All on one platform | Look up "which platform has this" before each test |
| Reliability | One vendor's uptime | Implicit failover, at integration cost |
 
For Phase 0 (5 evenings, 6 videos), single platform wins on every dimension. If fal has an outage during your window, you wait — you don't build redundancy for a one-week evaluation.
 
### fal.ai credibility (verified before committing)
 
- **$4.5B valuation** (Dec 2025 Series D led by Sequoia + Kleiner Perkins + NVIDIA's venture arm)
- **~$400M annualized revenue** as of Feb 2026
- **Customers:** Adobe, Shopify, Canva, Perplexity, Quora (40% of Poe's image/video gen runs on fal)
- **117 employees, 600+ hosted models, 3M developers, 50M+ creations/day**
- **Verdict:** As reliable as it gets for a 2026 AI infra startup. Safe to ship Phase 0 — and arguably Phase 1+ — on.
### Total estimated Phase 0 spend
 
| Stage | What runs on fal | Est. cost |
|---|---|---|
| Stage 1 (hero shot, if generating via fal) | Flux schnell (~10–50 images) | $0–$2 |
| Stage 2 (identity variants) | Runs locally on Mac (ComfyUI + PuLID). $0 to fal. | $0 |
| Stage 3 (audio) | Real recording, no inference cost | $0 |
| Stage 4 (talking-head test matrix) | 6 videos across 4 models | ~$26 |
| Buffer | Retries, additional comparison tests | ~$10 |
| **Total expected** | | **~$30–40** |
 
Hard ceiling: **$50** (master escape trigger).
 
---
 
## Project Structure
 
```
/Users/shinheehwang/Desktop/projects/00_live_ai_host/
├── .env                      # FAL_KEY, ANTHROPIC_API_KEY (gitignored)
├── .gitignore
├── README.md
├── inputs/
│   ├── photos/               # 1–5 Korean reference photos
│   └── audio/                # Korean reference audio (30s)
├── outputs/
│   ├── stage1_hero/          # Selected/refined hero shots
│   ├── stage2_variants/      # PuLID-generated identity variants
│   ├── stage3_audio/         # Recorded driving audio
│   ├── stage4_videos/        # fal.ai-generated talking-head videos
│   └── stage5_evaluation/    # Score sheets, decision document
├── notebooks/
│   ├── 01_hero_shot.ipynb
│   ├── 02_identity_variants.ipynb
│   ├── 03_audio_prep.ipynb
│   ├── 04_talking_head.ipynb
│   └── 05_evaluation.ipynb
├── comfy_workflows/          # Saved ComfyUI JSON files
├── scripts/
│   └── fal_call.py           # Reusable fal.ai caller
├── logs/
├── pyproject.toml            # Project deps (uv-managed; committed)
├── uv.lock                   # Hash-pinned resolved deps for reproducibility (committed)
├── .python-version           # Pins Python 3.11 for `uv run`
└── .venv/                    # Local install (gitignored; recreated via `uv sync`)
```
 
---
 
## Status Tracking
 
Update this table at the end of each evening. Honest status, not aspirational.
 
| Stage | Status | Date Started | Date Completed | Notes |
|---|---|---|---|---|
| **Stage 0** — Environment setup | ✅ Done | 2026-05-11 | 2026-05-12 | uv project (not conda); ComfyUI v0.21 in tools/; lldacing PuLID-Flux; Flux dev fp8 + encoders + VAE + PuLID weights (~17 GB); ./dev dispatcher. **0.5 fal smoke test deferred** until fal.ai account funded — runs in ~1 min. |
| **Stage 1** — Hero shot | ✅ Done | 2026-05-12 | 2026-05-12 | Path A — picked kim_5 (only one with broadcast-headshot composition: direct gaze, gentle smile, even lighting, clean bg). Cropped 620x620 face-centered, LANCZOS upscaled to 1024x1024 → `inputs/photos/hero.png`. Resolution caveat: native source 620x750 (informative pixels), upscaled for ComfyUI workflow compat. Revisit with AI upscale if Stage 2 quality is weak. |
| **Stage 2** — Identity variants | ⚠ Tested on RunPod, definitive negative | 2026-05-12 | 2026-05-12 | Local PuLID skipped on Mac MPS (fp8 unsupported). Tested on rented A6000 across 3 parameter configs (default, moderate, aggressive). All three produced identical outputs across prompts — PuLID-Flux identity-locks too hard for prompt-driven pose variation. Full findings at `docs/stage2_pulid_findings.md`. Stage 4 uses natural variants (variant_3q, variant_speaking) instead. RunPod spend: ~$0.90. |
| **Stage 3** — Driving audio | ✅ Done | 2026-05-12 | 2026-05-12 | Used Korean **TTS-generated** audio (2 MP3 clips, ~7.3s + ~7.85s, concatenated to 15.15s) — not real recording per plan's preference. Confound to flag in DECISION.md: any ambiguous Stage 4 lip-sync result should get a re-test with real recording before final verdict. Output: `inputs/audio/reference_korean_30s.wav` (24kHz mono PCM). Source MP3s preserved in `inputs/audio/`. |
| **Stage 4** — Talking-head generation | ⬜ Not started | — | — | — |
| **Stage 5** — Evaluation + decision | ⬜ Not started | — | — | — |
 
Status codes: ⬜ Not started · 🟡 In progress · ✅ Done · ⚠ Escaped · ❌ Failed
 
---
 
## Stage 0 — Environment Setup (Evening 1, ~2 hours)
 
### Goal
 
Working Python environment + ComfyUI on Mac + fal.ai access. Nothing inferential happens yet — this stage exists to remove setup friction from subsequent stages.
 
### Models to use
 
Setup only. No model inference in this stage.
 
### Steps

> **Tooling note:** Stage 0 uses **uv** (Astral's package manager), not conda. Same Python (3.11), same packages, but: 10-100× faster installs, hash-pinned reproducible `uv.lock`, no manual `activate` (uv handles env isolation per-command via `uv run` / `uv add`).
 
```bash
# 1. Initialize uv project (creates pyproject.toml; --bare = no auto-generated README/main.py)
cd /Users/shinheehwang/Desktop/projects/00_live_ai_host/
uv init --bare --python 3.11 --vcs none --name live-ai-host
echo "3.11" > .python-version

# 2. Add core deps (downloads ~3-5 GB; creates .venv/ and uv.lock)
uv add \
  diffusers transformers accelerate \
  "numpy<2" torch torchvision torchaudio \
  pillow pandas \
  jupyterlab ipykernel \
  fal-client python-dotenv \
  requests pyyaml

# Numpy < 2.x for downstream model compatibility (preventive guard from prior SadTalker pain).
 
# 3. ComfyUI for local image gen (separate venv inside tools/ComfyUI/)
mkdir -p tools/ && cd tools/
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI
uv venv --python 3.11          # creates tools/ComfyUI/.venv/ (separate from project venv)
source .venv/bin/activate
uv pip install -r requirements.txt
PYTORCH_ENABLE_MPS_FALLBACK=1 python main.py --force-fp16   # UI at http://localhost:8188, Ctrl+C
deactivate
cd ../..
 
# 4. PuLID + Flux dev fp8 weights for ComfyUI
# - Install ComfyUI-Manager (custom node), then via Manager install ComfyUI_PuLID_Flux_ll (lldacing)
# - After install, manually run: cd tools/ComfyUI && uv pip install --python .venv/bin/python --no-deps facenet-pytorch
#   (the node's requirements.txt has it commented out due to a torch<2.3 pin; without it the node IMPORT FAILED)
# - Download weights via: ./dev download-weights  (~18 GB total)
#   * NOTE: PuLID-Flux requires Flux DEV (not schnell as originally planned) — PuLID needs CFG that
#     schnell distilled away. Flux dev is non-commercial license — Phase 1 caveat alongside InsightFace.
#   * fp8 quantized for Mac M4 Pro 24 GB (full fp16 ~22 GB won't fit alongside OS + ComfyUI).
#   * Auto-downloaded on first workflow run: EVA-CLIP, InsightFace antelopev2, facexlib parsing.
 
# 5. Set up .env
cat > .env <<EOF
FAL_KEY=your_fal_key_here
ANTHROPIC_API_KEY=sk-ant-xxx
EOF
 
# 6. Lock environment — uv project mode auto-writes uv.lock on every `uv add`.
#    pyproject.toml + uv.lock together ARE the lock. Commit both to git.
#    To recreate the env from scratch later: `uv sync`.
```

**uv gotcha:** when adding more packages later, use `uv add <pkg>` (tracked in `pyproject.toml`), not `uv pip install <pkg>` (untracked, wiped on next `uv sync`).
 
### Stage 0 Verification — all must be true
 
1. `uv run python -c "import torch; print(torch.__version__, torch.backends.mps.is_available())"` → version, `True`
2. `uv run python -c "import fal_client, diffusers, transformers, PIL; print('ok')"` → `ok`
3. `uv run jupyter lab` opens successfully
4. ComfyUI loads at `localhost:8188` without errors (from `tools/ComfyUI/.venv` activated shell)
5. PuLID custom node visible in ComfyUI node menu
6. fal.ai authentication test passes — running a trivial fal call (e.g. a single Flux schnell image) returns successfully
7. `pyproject.toml` and `uv.lock` exist, non-empty, and committed to git
### Stage 0 Escape Triggers
 
| If this fails | Escape to |
|---|---|
| ComfyUI won't start on MPS | Run with `--cpu` flag. Real fallback: use fal-hosted Flux schnell for Stage 1 instead of local ComfyUI. |
| PuLID node has install errors | Try InstantID custom node instead. If both fail: do Stage 2 entirely on fal using a paid identity-preservation model (~$1 total). |
| fal.ai account/billing issue | Email support@fal.ai. Phase 0 cannot start without fal access — there's no other platform we're using. |
 
---
 
## Stage 1 — Hero Shot Preparation (Evening 1 or 2, ~1 hour)
 
### Goal
 
One canonical Korean female reference image, broadcast quality, saved as `inputs/photos/hero.png` at 1024×1024 or higher.
 
### Models to use — open-source vs. paid
 
| Tier | Model | License | fal slug | Cost | Notes |
|---|---|---|---|---|---|
| **OSS primary** | **Flux schnell** | Apache 2.0 | `fal-ai/flux/schnell` | $0.003/MP | Same model used locally (ComfyUI) and on fal. Fast, strong general quality. |
| **OSS alternative** | **Hunyuan Image 3.0** | Open weights | `fal-ai/hunyuan-image/v3/text-to-image` | $0.04/img | Best Asian-face quality among open-weight models in 2026. Use if Flux schnell underperforms on Korean faces. |
| **Paid baseline** | **Imagen 4 Ultra** | Closed (Google) | `fal-ai/imagen4/preview` | $0.06/img | Photorealism benchmark. Single perfect reference if Path A photos are unsatisfactory. |
| **Paid premium** | **Flux Kontext Pro** | Closed | `fal-ai/flux-pro/kontext` | $0.04/img | Strongest identity lock when using existing photos as guidance. |
 
### Two paths
 
**Path A — Your photos are good enough:**
Pick the cleanest, well-lit, front-facing one. Crop to square, 1024×1024 minimum. Save as `inputs/photos/hero.png`. Skip to Stage 2.
 
**Path B — Generate fresh:**
Use ComfyUI with Flux schnell (local, free). Prompt:
 
```
Korean woman, late 20s, friendly warm expression, looking at camera,
professional photo, soft natural lighting, clean studio background,
broadcast-quality, photorealistic, 4K detail, natural Korean features
```
 
Negative prompt:
```
Western features, exaggerated features, anime, 3D render,
deformed, asymmetric eyes, plastic skin
```
 
Generate ~20 variants locally. Pick the best. If Flux schnell produces too-Western faces, switch to Hunyuan Image 3.0 via fal (~$0.40 for 10 attempts).
 
### Stage 1 Verification — checklist
 
The hero shot must pass ALL of these (honest assessment):
 
- [ ] Face takes 40–60% of frame
- [ ] Looking at camera, neutral or slight smile
- [ ] Even lighting, no harsh shadows
- [ ] No hands or objects covering face
- [ ] Hair edges clean (not blurred or weird)
- [ ] Background is simple
- [ ] **You'd accept this person as a broadcast host visually**
- [ ] Resolution ≥ 1024×1024
- [ ] File saved at `inputs/photos/hero.png`
If any fail, redo. **Stage 2 cannot fix a bad hero shot.**
 
### Stage 1 Escape Triggers
 
| If this fails | Escape to |
|---|---|
| Flux on Mac is too slow (>3 min/img) | Use fal-hosted Flux schnell — $0.003/img, ~5 sec each. 50 variants for ~$0.15 total. |
| Generated faces look too Western | Switch to Hunyuan Image 3.0 on fal (~$0.04/img). Much better Asian-face quality. |
| Real photo (Path A) quality too low | Generate fresh (Path B), or single Imagen 4 Ultra shot (~$0.06) for one perfect reference. |
 
---
 
## Stage 2 — Identity Variants (Evening 2, ~3 hours active + overnight)
 
### Goal
 
20–25 identity-consistent variants of the hero persona at different angles/expressions/lighting/outfits. Output to `outputs/stage2_variants/`.
 
### Models to use — open-source vs. paid
 
| Tier | Model | License | Where it runs | Cost | Notes |
|---|---|---|---|---|---|
| **OSS primary** | **PuLID + Flux schnell** | Code Apache 2.0; **runtime stack non-commercial** (InsightFace antelopev2 CC BY-NC 4.0) | Local ComfyUI workflow | $0 | The intended Phase 2 self-host approach. Accepts up to 4 reference images for identity guidance. **Phase 0 uses InsightFace for cleanest Stage 4 input quality (best-tools-for-research principle); Phase 1 commercial stack TBD — see Phase 1 escape options below.** |
| **OSS alternative** | **InstantID + Flux schnell** | Code Apache 2.0; **same InsightFace dependency** as PuLID | Local ComfyUI workflow | $0 | Different identity-preservation approach. Sometimes better on Asian faces. **Note:** does not solve the InsightFace license issue — same upstream face embedder. |
| **OSS commercial-safe** | **ComfyUI_PuLID_Flux_ll_FaceNet** (KY-2000) | Apache 2.0 + FaceNet (commercial-OK) | Local ComfyUI workflow | $0 | Drop-in PuLID swap of InsightFace → FaceNet. Only 2 stars (unproven). Phase 1 evaluation candidate, not Phase 0. |
| **Paid premium** | **Flux Kontext Pro** | Closed | `fal-ai/flux-pro/kontext` | $0.04/img | Stronger identity lock if PuLID drifts. Also the cleanest commercial path for Phase 1 if OSS-commercial route fails. 25 variants ≈ $1. |
 
### Procedure
 
Use ComfyUI with PuLID + Flux schnell. Community workflow is fine — modify only the prompts.
 
**Critical:** PuLID accepts 1–4 reference images. **Use as many Korean photos as you have.** Hero shot + 2-3 additional photos significantly improves identity preservation over a single reference.
 
Generate 5 prompts × 5 variations = 25 variants:
 
| Prompt | Purpose |
|---|---|
| `[same person], slight smile, looking at camera, 3/4 right angle` | Head turning right |
| `[same person], slight surprise, looking at camera, slight 3/4 left` | Head turning left |
| `[same person], speaking, mouth slightly open, looking at camera` | Speaking pose (input for Stage 4) |
| `[same person], looking down at notes, thoughtful expression` | Idle "reading" loop |
| `[same person], warm laugh, eyes crinkled, looking at camera` | Engagement variant |
 
### Stage 2 Verification — identity score
 
Pin all 25 variants alongside the hero shot. Score honestly:
 
| Score | Meaning | Action |
|---|---|---|
| 5/5 | All 25 are clearly the same person | Proceed |
| 4/5 | 20–24 convincing | Proceed, discard the bad ones |
| 3/5 | 15–19 pass | Borderline — add more references or escape |
| ≤ 2/5 | Identity drift too high | Stop — see escape triggers |
 
**Korean-specific failures to look for:**
 
- [ ] Monolid / single-eyelid "corrected" to double-eyelid
- [ ] Skin tone drifting toward pink/Western
- [ ] Face structure morphing (jaw width, cheekbones)
- [ ] Hair edge artifacts on profile shots
- [ ] Epicanthic fold mishandled
### Stage 2 Escape Triggers
 
| If this fails | Escape to |
|---|---|
| Identity drift >50% of variants | Add more reference photos (use all 5 if you have them). |
| Still drifting with max references | Switch PuLID → InstantID in ComfyUI. Different approach. |
| Both open-source approaches fail | Use **Flux Kontext Pro** on fal (~$1 total for 25). Stronger identity lock. |
| Even paid fails | Hero shot itself defeats identity preservation. Regenerate Stage 1 with different features. |
 
**Do not proceed to Stage 3 with bad variants.** Bad data in, broken pipeline out.
 
---
 
## Stage 3 — Driving Audio (Evening 3, ~1 hour)
 
### Goal
 
30 seconds of clean Korean speech as `inputs/audio/reference_korean_30s.wav` (24kHz mono).
 
### Models to use — recording vs. TTS
 
| Tier | Approach | License | Cost | Notes |
|---|---|---|---|---|
| **Recommended** | Real recorded Korean speech (phone OK) | N/A | $0 | Isolates Stage 4 evaluation from TTS quality. **Use this for the first iteration.** |
| **Acceptable backup** | Naver Clova Premium TTS (free trial) | Closed | $0 (trial) | Korean prosody gold standard. Closest to production sound. |
| **OSS option (not Phase 0)** | F5-TTS via fal | MIT | per-second | **Do not use for the first Stage 4 test.** Korean prosody quality is unknown. Use only for a separate dedicated TTS evaluation later. |
 
### Why real recording for the first test
 
When Stage 4 produces a result, you need to know: is the quality issue from the talking-head model, or from upstream TTS artifacts? Real recorded audio removes one variable. Once Stage 4 is validated with known-good audio, F5-TTS Korean quality becomes a separate evaluation.
 
### Stage 3 Verification
 
- [ ] `inputs/audio/reference_korean_30s.wav` exists, 24kHz mono, ~30 seconds
- [ ] Audio clear, no background noise, normal speaking pace
- [ ] Content includes variety of Korean phonemes: ㄱ/ㅋ aspiration distinction, ㅡ vowel, 받침-heavy syllables
### Stage 3 Escape Triggers
 
| If this fails | Escape to |
|---|---|
| Can't record a clean clip | Use Naver Clova free tier for one Korean sample. |
| No Korean speaker available | Naver Clova. The point of this stage is *not* to test TTS — just to get usable input audio. |
 
---
 
## Stage 4 — Talking-Head Generation (Evening 3–4, ~$27 on fal.ai)
 
### Goal
 
Six test videos that isolate variables and let you decide whether open-source talking-head models work for Korean broadcast personas.
 
### Models to use — four quality tiers
 
| Tier | Model | License | fal slug | Cost (30s clip) | Why included |
|---|---|---|---|---|---|
| **OSS — gating** ★ | **EchoMimic v3** | Apache 2.0 | `fal-ai/echomimic-v3` | $0.20/sec → ~$6 | THE model to evaluate. If this works on Korean faces, Phase 2 self-host migration is unblocked. |
| **OSS — alternative** | **MuseTalk** | MIT | `fal-ai/musetalk` | ~$1.50–2 | Lip-correction-only mode. Different category — works on existing video, not single image. Phase 2 use case: refining other models' output. |
| **Paid — commodity** | **p-video-avatar** | Closed (Pruna) | `fal-ai/p-video-avatar` | ~$0.75 | Cheapest decent option. If this is good enough, ship on it and skip everything else. |
| **Paid — premium (emotional)** | **Omnihuman v1.5** | Closed (ByteDance) | `fal-ai/bytedance/omnihuman/v1.5` | $0.16/sec → ~$4.80 | Best emotional/body language for talking heads. The "if you're paying premium, here's what you get" baseline. |
| **Paid — premium (cinematic)** | **Kling Avatar v2 Pro** | Closed (Kuaishou) | `fal-ai/kling-video/ai-avatar/v2/pro` | $0.115/sec → ~$3.45 | Premium visual quality. Sets the upper bound — "what would brand customers compare us to." |
 
### Test matrix
 
| # | Image input | Audio input | Model | Tier | Cost | What this tests |
|---|---|---|---|---|---|---|
| 1 | Hero shot | 30s Korean | EchoMimic v3 | OSS gating | ~$6 | The gating test — does open-source work on Korean? |
| 2 | Variant (3/4 angle) | 30s Korean | EchoMimic v3 | OSS gating | ~$6 | Pose tolerance of gating model |
| 3 | Variant (speaking pose, mouth slightly open) | 30s Korean | EchoMimic v3 | OSS gating | ~$6 | Does the gating model handle non-neutral mouth input? Speaking-pose variants are the realistic Phase 1 input, not just hero shots. |
| 4 | Hero shot | 30s Korean | p-video-avatar | Paid commodity | ~$0.75 | Is the cheap commodity option already good enough? |
| 5 | Hero shot | 30s Korean | Omnihuman v1.5 | Paid premium (emotional) | ~$4.80 | What does the premium-emotional baseline look like? |
| 6 | Hero shot | 30s Korean | Kling Avatar v2 Pro | Paid premium (cinematic) | ~$3.45 | What does the premium-cinematic upper bound look like? |
 
**Total baseline: ~$27. Budget $40 with retries. Hard ceiling: $50.**
 
This matrix gives a genuinely informative comparison across **four quality tiers**: commodity paid → open-source gating → premium emotional → premium cinematic. Decision logic flows naturally from this comparison.
 
### The fal.ai caller
 
`scripts/fal_call.py`:
 
```python
"""Reusable fal.ai caller for talking-head + image generation."""
 
import os
from pathlib import Path
import fal_client
from dotenv import load_dotenv
 
load_dotenv()
 
# Model registry. Verify slugs at runtime against fal.ai/models before each session.
MODELS = {
    # Stage 4 — talking-head
    "echomimic-v3":     "fal-ai/echomimic-v3",
    "p-video-avatar":   "fal-ai/p-video-avatar",
    "omnihuman-v1.5":   "fal-ai/bytedance/omnihuman/v1.5",
    "kling-avatar-v2":  "fal-ai/kling-video/ai-avatar/v2/pro",
    "musetalk":         "fal-ai/musetalk",
    # Stage 1 — image gen (if not using local ComfyUI)
    "flux-schnell":     "fal-ai/flux/schnell",
    "hunyuan-image":    "fal-ai/hunyuan-image/v3/text-to-image",
    "imagen4":          "fal-ai/imagen4/preview",
    "flux-kontext-pro": "fal-ai/flux-pro/kontext",
}
 
 
def generate_talking_head(
    model: str,
    image_path: str,
    audio_path: str,
    output_path: str,
    prompt: str = None,
):
    """Generate one talking-head video on fal. Saves to output_path."""
    if model not in MODELS:
        raise ValueError(f"Unknown model: {model}. Available: {list(MODELS)}")
 
    slug = MODELS[model]
    print(f"[{model}] {image_path} + {audio_path} → fal:{slug}")
 
    image_url = fal_client.upload_file(image_path)
    audio_url = fal_client.upload_file(audio_path)
 
    arguments = {"image_url": image_url, "audio_url": audio_url}
    if prompt:
        arguments["prompt"] = prompt
 
    result = fal_client.subscribe(slug, arguments=arguments, with_logs=True)
 
    # All these models return {"video": {"url": "..."}}
    import requests
    video_bytes = requests.get(result["video"]["url"]).content
 
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(video_bytes)
    print(f"  → {output_path}")
    return output_path
 
 
if __name__ == "__main__":
    # Test 1 — the gating test
    generate_talking_head(
        model="echomimic-v3",
        image_path="inputs/photos/hero.png",
        audio_path="inputs/audio/reference_korean_30s.wav",
        output_path="outputs/stage4_videos/test1_hero_kor_echomimic.mp4",
        prompt=(
            "A Korean woman in a relaxed pose, speaking naturally with minimal "
            "head movement. Don't blink too often. Preserve background integrity."
        ),
    )
```
 
### Stage 4 Verification
 
- [ ] All 6 videos generated, saved to `outputs/stage4_videos/`
- [ ] Each video playable (QuickTime opens and plays through, no corruption)
- [ ] Total fal.ai spend within $40 budget (check fal dashboard)
- [ ] Each video has a corresponding YAML notes file (see Stage 5)
### Stage 4 Escape Triggers
 
| If this fails | Escape to |
|---|---|
| EchoMimic v3 on fal is queueing or down | Check `status.fal.ai`. Wait an hour and retry. fal uptime is generally strong. |
| EchoMimic v3 produces obvious garbage | Try the model's `prompt` parameter — it's an important driver. Verify hero shot meets input requirements (face size, clarity, resolution). |
| fal slugs stale or schema-changed | Visit fal.ai/models, copy current slug. Update `MODELS` dict. |
| Spend running over $40 | Stop, reassess. p-video-avatar at ~$0.75/test is 8× cheaper than EchoMimic v3 — substitute it for remaining tests. Verdict becomes less conclusive but still useful. |
| Whole fal.ai outage >24 hours | Eachlabs also hosts EchoMimic v3. Or rent RunPod and run from the GitHub repo. Both are last-resort. |
 
---
 
## Stage 5 — Evaluation and Decision (Evening 4–5, ~3 hours)
 
### Goal
 
One `DECISION.md` at the end: "open-source viable / commodity paid is enough / premium paid required / not ready, revisit later." This is the actual deliverable.
 
### Models to use
 
None — this stage is human evaluation.
 
### Per-video scoring rubric
 
For each of the 6 videos, watch twice. Score 1–5 on six axes:
 
| Axis | 5 = excellent | 1 = unusable |
|---|---|---|
| Identity stability | Same person throughout 30s | Different person at end |
| Korean lip-sync | ㄱ/ㅋ aspiration visible, 받침 closed correctly | Generic English mouth shapes |
| East Asian features | Monolid/epicanthic fold preserved | Visible Western-feature drift |
| Motion artifacts | Smooth, natural micro-movement | Jitter, twitch, melt, clip |
| Skin tone consistency | Stable Korean skin tone | Drifts toward unnatural tone |
| Overall "AI detection" | Watcher doesn't notice it's AI | Obviously AI |
 
Save per-video notes as `outputs/stage5_evaluation/test{N}_notes.yaml`:
 
```yaml
test_number: 1
model: echomimic-v3
tier: open-source-gating
fal_slug: fal-ai/echomimic-v3
image_used: inputs/photos/hero.png
audio_used: inputs/audio/reference_korean_30s.wav
generation_cost_usd: 6.00
generation_time_sec: 180
scores:
  identity_stability: 4
  korean_lip_sync: 3
  east_asian_features: 4
  motion_artifacts: 4
  skin_tone: 5
  overall_ai_detection: 3
notes: |
  Lip-sync generally good but ㅡ vowel rendered as English schwa.
  Slight skin tone shift toward pink in last 5 seconds.
  Identity holds well.
evaluator: shinhee
```
 
### Multi-evaluator strongly recommended
 
Score from one evaluator is noise. Score from 2–3 evaluators is signal. If possible, recruit 1–2 native Korean speakers to score independently. A shared video link is enough — they don't need to install anything.
 
### DECISION.md template
 
```markdown
# Phase 0 Persona Pipeline — Decision
 
**Date:** YYYY-MM-DD
**Evaluator(s):** Shinhee, [+ others]
**Total fal.ai spend:** $XX.XX
**Total time invested:** N hours
 
## Average Korean-video score by model
 
| Model | Tier | Avg score | Cost per 30s |
|---|---|---|---|
| EchoMimic v3 | OSS gating | X.X / 5 | $6.00 |
| p-video-avatar | Paid commodity | X.X / 5 | $0.75 |
| Omnihuman v1.5 | Paid premium (emotional) | X.X / 5 | $4.80 |
| Kling Avatar v2 Pro | Paid premium (cinematic) | X.X / 5 | $3.45 |
 
## Verdict
- [ ] **Open-source viable** (EchoMimic v3 avg ≥ 4.0) → Proceed to longer videos, 1-hour stress test. Plan Phase 2 self-host migration.
- [ ] **Commodity good enough** (p-video-avatar avg ≥ 3.5 AND within 0.5 of best paid) → Ship on it for Phase 1. Skip the expensive path.
- [ ] **Premium paid required** (only Omnihuman or Kling clears 4.0) → Phase 1 launches paid. Plan Phase 2 fine-tuning of open-source.
- [ ] **Not ready for Korean** (nothing clears 3.5) → Revisit in 6 months. Phase 1 cannot launch as planned.
 
## Specific findings
- Best model observed: [model name]
- Failure modes identified: [list]
- Korean-specific issues: [list]
- Cost extrapolated to 60-min broadcast: $XX
 
## Next steps
[Concrete actions for the following week]
```
 
### Stage 5 Verification
 
- [ ] 6 per-video YAML score files in `outputs/stage5_evaluation/`
- [ ] At least 1 independent native Korean evaluator scored ≥ 3 of the 6 videos
- [ ] `DECISION.md` written with clear verdict (one of the four buckets)
- [ ] Decision document committed to git
---
 
## Day-by-Day Schedule
 
| Evening | Stage(s) | Effort | Cost |
|---|---|---|---|
| **E1** | Stage 0 setup + Stage 1 hero shot | 3 hours | $0 |
| **E2** | Stage 2 identity variants (mostly hands-off) | 1 hour active + overnight gen | $0 |
| **E3** | Stage 3 audio + 3 Stage 4 videos: cheap first (Test 4, p-video-avatar ~$0.75), then ONE EchoMimic v3 (Test 1, ~$6) to verify the gating model works, then ONE premium (Test 6, Kling ~$3.45). Stop and look at results. | 2.5 hours | ~$10 |
| **E4** | Remaining 3 Stage 4 videos: Tests 2 & 3 (EchoMimic v3 × 2 = ~$12), Test 5 (Omnihuman ~$4.80). Begin Stage 5 evaluation. | 3 hours | ~$17 |
| **E5** | Multi-evaluator review + DECISION.md | 2 hours | $0 |
 
**Realistic total: 5 evenings, ~$27–35 on fal.ai, one decision document. Hard ceiling $50.**
 
### Why E3 starts with the cheap one
 
If the commodity model (p-video-avatar at $0.75) already produces good Korean output, you've learned the most important thing for the lowest cost. EchoMimic v3 is more expensive — verify the gating premise works before committing to all four EchoMimic videos.
 
---
 
## Master Escape Triggers
 
If the entire plan is breaking down:
 
1. **One stage fails repeatedly** → Use that stage's escape trigger.
2. **Multiple stages fail** → Pause. The issue is likely environmental (account, API access, network). Debug one thing at a time.
3. **Approaching $50 spend without a working pipeline** → Stop. Something fundamental is wrong. Document what's been tried, sleep on it, reassess. If EchoMimic v3 specifically isn't working, the answer may just be "open-source not ready for Korean — ship paid for Phase 1." That's a valid Phase 0 outcome.
4. **End of Evening 5 without DECISION.md** → That's fine. Extend to 7 evenings. The deliverable is the decision document, not the timeline.
5. **fal.ai has major outage >24 hours** → Eachlabs (also hosts EchoMimic v3) or rent RunPod for the GitHub run. Both are last-resort fallbacks.
---
 
## Files To Touch (Reference)
 
- `.env` — `FAL_KEY`, `ANTHROPIC_API_KEY`
- `inputs/photos/hero.png` — canonical reference
- `inputs/photos/reference_extras/` — additional Korean photos for PuLID
- `inputs/audio/reference_korean_30s.wav` — driving audio for Stage 4
- `outputs/stage1_hero/` — hero shot iterations
- `outputs/stage2_variants/` — 25 identity variants
- `outputs/stage4_videos/test{1..6}_*.mp4` — six evaluation videos
- `outputs/stage5_evaluation/test{1..6}_notes.yaml` — per-video scores
- `outputs/stage5_evaluation/DECISION.md` — the deliverable
- `scripts/fal_call.py` — reusable fal.ai caller
- `comfy_workflows/pulid_flux.json` — saved ComfyUI workflow
- `pyproject.toml` — project deps (uv-managed, committed)
- `uv.lock` — hash-pinned resolved deps for reproducibility (committed)
- `.python-version` — pins Python 3.11
---
 
## What This Plan Deliberately Excludes
 
To be clear about scope (these are *not* Phase 0 problems):
 
- **1-hour broadcast stability** — Phase 0 tests 30-second clips. Hour-long stability is a separate post-Phase-0 test.
- **Real-time generation** — Stage 4 is batch generation. Real-time uses Hedra Live API in a different evaluation.
- **Production cost validation** — fal pay-per-call cost ≠ Phase 2 self-hosted GPU cost. RunPod H100 validation is a separate Phase 1 test.
- **TTS evaluation** — F5-TTS vs Naver Clova for Korean quality is a separate dedicated test, not Phase 0 scope.
- **Fine-tuning** — Not Phase 0. If results are mediocre, conclusion is "fine-tune in Phase 1," not "fine-tune now."
- **Multi-host or co-host broadcasts** — Out of scope until single-host is solid.
- **Compliance/regulatory work** — Separate workstream.
- **Replicate, RunPod, Colab** — Single platform (fal.ai) for Phase 0. Other platforms reserved for later phases or last-resort fallback.
- **Foreign faces, English voices, non-Korean evaluation** — Phase 0 is Korean face + Korean language only. Foreign-face generation, English TTS, and English talking-head evaluation are explicitly later-phase scope. The bar to clear in Phase 0 is "does this work for Korean broadcast personas" — nothing else.
---
 
## The One Thing To Remember
 
The deliverable is the **decision document**, not the videos.
 
If you end Phase 0 with one strong opinion clearly held — even if it's *"open-source isn't ready, stay paid for Phase 1"* — you've succeeded. The cost of admitting reality early is far smaller than the cost of building Phase 1 on a hopeful assumption.
 
**Begin with Stage 0. Test 4 (the commodity paid, cheapest) first in Stage 4 so you don't commit budget before validating the pipeline.**
 
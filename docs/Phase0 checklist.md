# Phase 0 Checklist
## Working companion to `Phase0 execution plan final.md`

This is the **do** doc. The plan is the **why** doc. When in doubt about reasoning or escape triggers, read the plan. When you just need to know "what's next?", check items off here.

**Conventions:**
- `[ ]` = not done, `[x]` = done. Mark as you go.
- Each stage references the plan section for escape triggers — go there if a step fails twice.
- Track running fal.ai spend in the running totals at the bottom.

---

## Pre-Flight (do before Evening 1)

- [ ] **fal.ai account created** at https://fal.ai
- [ ] **fal.ai funded with $50** (set the spend cap in the dashboard to $50 — hard ceiling)
- [ ] **`FAL_KEY` retrieved** from fal.ai dashboard, kept ready to paste into `.env`
- [ ] **1–5 Korean reference photos collected** in a folder, ready to copy to `inputs/photos/`
  - At least one front-facing, well-lit, ≥1024×1024
  - More photos = better PuLID identity preservation; collect all you have
- [ ] **30 minutes blocked tonight** for downloads (Flux schnell weights ~24 GB + PuLID weights — kick off before bed)
- [ ] **Disk space check**: at least 60 GB free on the disk holding the project dir

---

## Stage 0 — Environment Setup (Evening 1, ~2h + overnight downloads)
*Plan: §Stage 0 — Environment Setup*

### 0.1 Conda env + core deps
- [ ] `conda create -n live-ai-host python=3.11 -y && conda activate live-ai-host`
- [ ] `cd /Users/shinheehwang/Desktop/projects/00_live_ai_host/`
- [ ] Run the pip install line **with `numpy<2` pin added**:
  ```bash
  pip install \
    diffusers transformers accelerate \
    "numpy<2" torch torchvision torchaudio \
    pillow pandas \
    jupyterlab ipykernel \
    fal-client python-dotenv \
    requests pyyaml
  ```
- [ ] `python -c "import numpy; print(numpy.__version__)"` → starts with `1.`
- [ ] `python -c "import torch; print(torch.__version__, torch.backends.mps.is_available())"` → version + `True`
- [ ] `python -c "import fal_client, diffusers, transformers, PIL; print('ok')"` → `ok`

### 0.2 Project skeleton
- [ ] Create directory structure (`inputs/`, `outputs/stage{1..5}_*/`, `notebooks/`, `comfy_workflows/`, `scripts/`, `logs/`)
- [ ] Create `.env` with `FAL_KEY=...` and `ANTHROPIC_API_KEY=...`
- [ ] Create `.gitignore` excluding `.env`, `outputs/`, `models/`, `logs/`, `__pycache__/`, `*.ipynb_checkpoints/`
- [ ] `git init` if not already done

### 0.3 ComfyUI install
- [ ] Clone ComfyUI to `tools/ComfyUI/` (NOT `models/` — that's reserved for ComfyUI's own model dir)
- [ ] `cd tools/ComfyUI && pip install -r requirements.txt`
- [ ] `PYTORCH_ENABLE_MPS_FALLBACK=1 python main.py --force-fp16` launches without error
- [ ] Browser opens `http://localhost:8188` and loads the ComfyUI workspace
- [ ] Stop with Ctrl+C

### 0.4 PuLID-Flux + weights
- [ ] Install ComfyUI-Manager custom node (if not bundled)
- [ ] Via ComfyUI Manager, install **ComfyUI-PuLID-Flux** custom node
- [ ] Restart ComfyUI; PuLID-Flux nodes appear in the right-click menu
- [ ] **Start downloads (long-running, kick off and let them run):**
  - [ ] Flux schnell checkpoint → `tools/ComfyUI/models/checkpoints/`
  - [ ] PuLID weights → location specified by the custom node README
  - [ ] CLIP / VAE / encoders required by PuLID-Flux workflow (the node's README lists them)
- [ ] All downloads complete; restart ComfyUI; no missing-weights errors in console

### 0.5 fal.ai auth smoke test
- [ ] `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(bool(os.getenv('FAL_KEY')))"` → `True`
- [ ] Run a one-line fal.ai test (cheapest possible — single Flux schnell image, ~$0.003):
  ```python
  import fal_client
  result = fal_client.subscribe(
      "fal-ai/flux/schnell",
      arguments={"prompt": "a red apple", "image_size": "square_hd"},
  )
  print(result["images"][0]["url"])
  ```
- [ ] Returned URL opens in browser, shows a red apple image
- [ ] Check fal.ai dashboard: spend incremented by ~$0.003

### 0.6 Lock environment
- [ ] `pip freeze > requirements-lock.txt`
- [ ] `requirements-lock.txt` is non-empty and committed to git
- [ ] Update plan's Stage 0 status: ✅ Done

**Stage 0 spend so far: ~$0.003**

---

## Stage 1 — Hero Shot (Evening 1 or 2, ~1h)
*Plan: §Stage 1 — Hero Shot Preparation*

### 1.1 Choose path
- [ ] Decide: Path A (use existing photo) or Path B (generate fresh in ComfyUI)
- If photos in hand are broadcast-quality → Path A. Otherwise → Path B.

### 1.2 Path A — use existing photo (if applicable)
- [ ] Pick the cleanest, well-lit, front-facing photo
- [ ] Crop to square, resize to ≥1024×1024
- [ ] Save as `inputs/photos/hero.png`
- [ ] Skip 1.3, go to 1.4

### 1.3 Path B — generate fresh (if applicable)
- [ ] Open `notebooks/01_hero_shot.ipynb`
- [ ] Build a Flux schnell ComfyUI workflow with the prompt + negative prompt from plan §Stage 1
- [ ] Generate ~20 variants locally
- [ ] If faces look too Western: switch to Hunyuan Image 3.0 on fal (`fal-ai/hunyuan-image/v3/text-to-image`, ~$0.04/img × 10 = $0.40)
- [ ] Pick the best one, save as `inputs/photos/hero.png`

### 1.4 Hero shot quality checklist (ALL must pass)
- [ ] Face takes 40–60% of frame
- [ ] Looking at camera, neutral or slight smile
- [ ] Even lighting, no harsh shadows
- [ ] No hands or objects covering face
- [ ] Hair edges clean (not blurred/weird)
- [ ] Background simple
- [ ] **You'd accept this person as a broadcast host** (gut check)
- [ ] Resolution ≥ 1024×1024
- [ ] File saved at `inputs/photos/hero.png`
- [ ] Update plan's Stage 1 status: ✅ Done

**If any quality check fails: redo. Stage 2 cannot fix a bad hero shot.**

---

## Stage 2 — Identity Variants (Evening 2, ~3h active + overnight)
*Plan: §Stage 2 — Identity Variants*

### 2.1 Workflow setup
- [ ] Open `notebooks/02_identity_variants.ipynb`
- [ ] Load a PuLID-Flux community workflow in ComfyUI (or build from scratch using PuLID nodes)
- [ ] Save the workflow JSON to `comfy_workflows/pulid_flux.json`

### 2.2 Reference images
- [ ] Copy hero.png + 1–3 additional Korean reference photos into PuLID input slots
- [ ] **Use as many references as you have** (PuLID accepts up to 4) — this materially improves identity preservation

### 2.3 Generation pass — try both 4 steps and 8 steps
- [ ] Generate 5 prompts × 5 variants at **4 steps** (schnell default) → 25 images
- [ ] Save to `outputs/stage2_variants/4steps/`
- [ ] Generate the same set at **8 steps** → 25 more images
- [ ] Save to `outputs/stage2_variants/8steps/`
- [ ] Visually compare: pick the step count where identity holds best
- [ ] Move the chosen 25 to `outputs/stage2_variants/final/`

### 2.4 Identity scoring
- [ ] Open hero.png alongside all 25 variants in Preview / image grid
- [ ] Score honestly using plan §Stage 2 rubric (5/5 ↔ 1/5)
- [ ] **Korean-specific failures check:**
  - [ ] Monolid / single-eyelid not "corrected" to double-eyelid
  - [ ] Skin tone not drifting toward pink / Western
  - [ ] Face structure (jaw width, cheekbones) consistent
  - [ ] Hair edges clean on profile shots
  - [ ] Epicanthic fold preserved
- [ ] If score < 4/5: see plan §Stage 2 escape triggers (more refs → InstantID → Flux Kontext Pro paid)
- [ ] Identify the **speaking-pose variant** specifically (mouth slightly open, looking at camera) — this is needed for Stage 4 Test 3
- [ ] Update plan's Stage 2 status: ✅ Done

**Do not proceed to Stage 4 with bad variants.**

---

## Stage 3 — Driving Audio (Evening 3, ~1h)
*Plan: §Stage 3 — Driving Audio*

- [ ] Record ~30 seconds of clean Korean speech (phone Voice Memos OK)
- [ ] Speak with variety: include ㄱ/ㅋ aspiration, ㅡ vowel, 받침-heavy syllables
- [ ] Convert to 24kHz mono WAV (ffmpeg one-liner: `ffmpeg -i input.m4a -ar 24000 -ac 1 inputs/audio/reference_korean_30s.wav`)
- [ ] Listen back: clear, no background noise, normal pace
- [ ] File at `inputs/audio/reference_korean_30s.wav`, ~30 seconds, 24kHz mono confirmed
- [ ] Update plan's Stage 3 status: ✅ Done

---

## Stage 4 — Talking-Head Generation (Evening 3–4, ~$27)
*Plan: §Stage 4 — Talking-Head Generation*

### 4.0 Pre-flight (do before first call)
- [ ] **Verify all 5 fal slugs are still current** at https://fal.ai/models — pricing too. If stale, update `MODELS` dict in script.
- [ ] **Implement `scripts/fal_call.py`** — the version in the plan is a placeholder. Each model has different input/output schema:
  - [ ] EchoMimic v3: check fal docs for required fields
  - [ ] p-video-avatar: check fal docs
  - [ ] Omnihuman v1.5: check fal docs
  - [ ] Kling Avatar v2 Pro: check fal docs
  - [ ] Add per-model `INPUT_ADAPTERS` and `OUTPUT_PARSERS` dicts
- [ ] Open `notebooks/04_talking_head.ipynb` and import the script

### 4.1 Evening 3 — first three videos (cheap → gating → premium)
*Cheap first to validate pipeline before committing to expensive runs.*

- [ ] **Test 4** — `p-video-avatar` × hero.png × Korean audio (~$0.75)
  - [ ] Generated successfully
  - [ ] Saved as `outputs/stage4_videos/test4_hero_kor_pvideo.mp4`
  - [ ] Plays in QuickTime
  - [ ] Logged generation time + cost
- [ ] **Stop and look at Test 4 result before continuing.** If pipeline produced a coherent video at all, the plumbing works. If it's garbage, debug before spending $6 on the next test.
- [ ] **Test 1** — `EchoMimic v3` × hero.png × Korean audio (~$6.00)
  - [ ] Generated successfully
  - [ ] Saved as `outputs/stage4_videos/test1_hero_kor_echomimic.mp4`
  - [ ] Plays in QuickTime
  - [ ] Logged generation time + cost
- [ ] **Test 6** — `Kling Avatar v2 Pro` × hero.png × Korean audio (~$3.45)
  - [ ] Generated successfully
  - [ ] Saved as `outputs/stage4_videos/test6_hero_kor_kling.mp4`
  - [ ] Plays in QuickTime
  - [ ] Logged generation time + cost

**Evening 3 spend so far: ~$10.20. Check fal dashboard before sleeping.**

### 4.2 Evening 4 — remaining three videos
- [ ] **Test 2** — `EchoMimic v3` × 3-4 angle variant × Korean audio (~$6.00)
  - [ ] Saved as `outputs/stage4_videos/test2_variant34_kor_echomimic.mp4`
- [ ] **Test 3** — `EchoMimic v3` × **speaking-pose variant** × Korean audio (~$6.00)
  - [ ] Saved as `outputs/stage4_videos/test3_speakingpose_kor_echomimic.mp4`
- [ ] **Test 5** — `Omnihuman v1.5` × hero.png × Korean audio (~$4.80)
  - [ ] Saved as `outputs/stage4_videos/test5_hero_kor_omnihuman.mp4`

**Total Stage 4 spend: ~$27. Check fal dashboard. Hard ceiling $50 — stop if approaching.**

- [ ] All 6 videos saved to `outputs/stage4_videos/`
- [ ] All 6 play in QuickTime without corruption
- [ ] Update plan's Stage 4 status: ✅ Done

---

## Stage 5 — Evaluation + Decision (Evening 4–5, ~3h)
*Plan: §Stage 5 — Evaluation and Decision*

### 5.1 Per-video scoring (all 6 videos)
For each video, watch twice and score 1–5 on six axes:

- [ ] **Test 1** scored — `outputs/stage5_evaluation/test1_notes.yaml` saved
- [ ] **Test 2** scored — `test2_notes.yaml` saved
- [ ] **Test 3** scored — `test3_notes.yaml` saved
- [ ] **Test 4** scored — `test4_notes.yaml` saved
- [ ] **Test 5** scored — `test5_notes.yaml` saved
- [ ] **Test 6** scored — `test6_notes.yaml` saved

### 5.2 Multi-evaluator (strongly recommended)
- [ ] Recruit ≥1 native Korean evaluator
- [ ] Share video links (Google Drive / WeTransfer)
- [ ] Get their scores back on at least 3 of the 6 videos
- [ ] Save their YAML files alongside yours

### 5.3 DECISION.md
- [ ] Open `notebooks/05_evaluation.ipynb`
- [ ] Compute average score per model across all evaluators
- [ ] Fill in the DECISION.md template from plan §Stage 5
- [ ] Tick exactly **one** of the four verdict checkboxes:
  - [ ] Open-source viable (EchoMimic v3 avg ≥ 4.0)
  - [ ] Commodity good enough (p-video-avatar ≥ 3.5 AND within 0.5 of best paid)
  - [ ] Premium paid required
  - [ ] Not ready for Korean
- [ ] Document specific findings, failure modes, Korean-specific issues
- [ ] Extrapolate cost per 60-min broadcast for the chosen path
- [ ] Write next-week action items
- [ ] Save as `outputs/stage5_evaluation/DECISION.md`
- [ ] Commit DECISION.md to git
- [ ] Update plan's Stage 5 status: ✅ Done

---

## Running Spend Tracker

Update after each fal.ai call. Hard ceiling $50.

| Stage | Item | Estimated | Actual | Running total |
|---|---|---|---|---|
| 0.5 | Smoke test (Flux schnell × 1) | $0.003 | | |
| 1.3 | Hero shot generation (if Path B + Hunyuan) | $0–$0.40 | | |
| 4.1 | Test 4 (p-video-avatar) | $0.75 | | |
| 4.1 | Test 1 (EchoMimic v3) | $6.00 | | |
| 4.1 | Test 6 (Kling Avatar v2 Pro) | $3.45 | | |
| 4.2 | Test 2 (EchoMimic v3) | $6.00 | | |
| 4.2 | Test 3 (EchoMimic v3) | $6.00 | | |
| 4.2 | Test 5 (Omnihuman v1.5) | $4.80 | | |
| | **Baseline total** | **~$27** | | |
| | Buffer for retries | ~$10 | | |
| | **Working budget** | **$40** | | |
| | **Hard ceiling** | **$50** | | |

---

## Master Escape Triggers (quick reference)
*Full triggers in plan §Master Escape Triggers*

1. Stage fails repeatedly → that stage's escape trigger
2. Multiple stages fail → environmental issue, debug one thing
3. Approaching $50 without a working pipeline → stop, document, sleep on it
4. End of Evening 5 without DECISION.md → extend, the deliverable matters more than the timeline
5. fal.ai outage >24h → Eachlabs or RunPod (last-resort)

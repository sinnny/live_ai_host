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

### 0.1 uv project + core deps
*Switched from conda → uv: faster installs, `uv.lock` is hash-pinned + fully reproducible, and `uv add`/`uv run` don't need a manual `activate` step. The package list is identical.*

- [ ] `cd /Users/shinheehwang/Desktop/projects/00_live_ai_host/`
- [ ] `uv init --bare --python 3.11 --vcs none --name live-ai-host` → creates `pyproject.toml`
- [ ] `echo "3.11" > .python-version` → pin Python version for `uv run`
- [ ] Add `.venv/` to `.gitignore` (the venv is local; recreated via `uv sync`)
- [ ] Add deps (creates `.venv/`, writes `uv.lock`):
  ```bash
  uv add \
    diffusers transformers accelerate \
    "numpy<2" torch torchvision torchaudio \
    pillow pandas \
    jupyterlab ipykernel \
    fal-client python-dotenv \
    requests pyyaml
  ```
- [ ] `uv run python -c "import numpy; print(numpy.__version__)"` → starts with `1.`
- [ ] `uv run python -c "import torch; print(torch.__version__, torch.backends.mps.is_available())"` → version + `True`
- [ ] `uv run python -c "import fal_client, diffusers, transformers, PIL; print('ok')"` → `ok`

**uv gotcha:** when adding more packages later, use `uv add <pkg>` (tracked in `pyproject.toml`), not `uv pip install <pkg>` (untracked, blown away on next `uv sync`).

### 0.2 Project skeleton
- [ ] Create directory structure (`inputs/`, `outputs/stage{1..5}_*/`, `notebooks/`, `comfy_workflows/`, `scripts/`, `logs/`)
- [ ] Create `.env` with `FAL_KEY=...` and `ANTHROPIC_API_KEY=...`
- [ ] Create `.gitignore` excluding `.env`, `outputs/`, `models/`, `logs/`, `__pycache__/`, `*.ipynb_checkpoints/`
- [ ] `git init` if not already done

### 0.3 ComfyUI install
*ComfyUI gets its OWN venv inside `tools/ComfyUI/.venv/` — separate from the project's `.venv/` — so its hundreds of deps (and custom node deps later) don't pollute our `pyproject.toml`/`uv.lock` or risk conflicting with our torch/diffusers versions.*

- [ ] Clone ComfyUI to `tools/ComfyUI/` (NOT `models/` — that's reserved for ComfyUI's own model dir)
- [ ] `cd tools/ComfyUI && uv venv --python 3.11` → creates `tools/ComfyUI/.venv/`
- [ ] `source .venv/bin/activate` (or use `uv pip --python .venv/bin/python install ...`)
- [ ] `uv pip install -r requirements.txt`
- [ ] `PYTORCH_ENABLE_MPS_FALLBACK=1 python main.py --force-fp16` launches without error
- [ ] Browser opens `http://localhost:8188` and loads the ComfyUI workspace
- [ ] Stop with Ctrl+C
- [ ] `deactivate` (return to your normal shell; the project's `.venv/` is reached via `uv run` from project root)

**From now on, launch ComfyUI via the project dispatcher:**
```bash
./dev comfyui                  # default
./dev comfyui --listen         # LAN access
./dev comfyui --port 8189      # custom port
./dev comfyui --cpu            # fallback if MPS misbehaves
```
Stop with Ctrl+C. The dispatcher (`./dev`) routes to `scripts/comfyui.sh`, which handles cd + venv + MPS fallback + fp16 flags automatically. Run `./dev help` to list available subcommands.

### 0.4 PuLID-Flux + weights
- [ ] Install ComfyUI-Manager custom node (if not bundled)
- [ ] Via ComfyUI Manager, install **ComfyUI_PuLID_Flux_ll** by **lldacing** (search "pulid flux" in Manager → ID 165)
  - **Identity-preservation license note (informational, not a blocker for Phase 0):** PuLID's default face embedder is InsightFace antelopev2 (CC BY-NC 4.0, non-commercial). Using it in Phase 0 is correct experimental practice — Phase 0 evaluates *talking-head models* (Stage 4), and Stage 2 just generates inputs; best-quality inputs minimize confounding. The commercial production stack (FaceNet swap via KY-2000's fork, Flux Kontext Pro on fal, or commercial InsightFace license) is a Phase 1 concern. Document in DECISION.md.
  - Alternative forks visible in Manager search: `sipie800/ComfyUI-PuLID-Flux-Enhanced` (fork of balazik original), `KY-2000/ComfyUI_PuLID_Flux_ll_FaceNet` (commercial-safe via FaceNet, only 2 stars). Skip unless #165 fails.
- [ ] **After Manager install, fix the missing `facenet-pytorch` dep** — it's commented out of `requirements.txt` (because it pins `torch<2.3`) but the node code still imports it. Without this, the node shows `IMPORT FAILED` in Manager UI:
  ```bash
  cd tools/ComfyUI
  uv pip install --python .venv/bin/python --no-deps facenet-pytorch
  ```
  `--no-deps` is required so it doesn't downgrade your torch. Restart ComfyUI after.
- [ ] Restart ComfyUI; PuLID-Flux nodes appear in the right-click menu
- [ ] **Start downloads via `./dev download-weights`** (~18 GB, kick off and let it run; resumable + idempotent)
  - **NOTE:** Plan said "Flux schnell" but PuLID-Flux requires **Flux dev** (PuLID was trained on dev's CFG; schnell is distilled CFG-free). Flux dev is non-commercial license (FLUX.1-dev license) — same Phase 1 caveat as InsightFace, document in DECISION.md.
  - **For Mac M4 Pro 24 GB:** use **fp8 quantized** (~12 GB VRAM); full fp16 won't fit alongside ComfyUI + OS.
  - Downloads handled by `scripts/download_weights.sh`:
    - Flux dev fp8 e4m3fn (~12 GB) → `tools/ComfyUI/models/diffusion_models/`
    - T5XXL fp8 text encoder (~5 GB) → `models/text_encoders/`
    - CLIP-L text encoder (~250 MB) → `models/text_encoders/`
    - Flux VAE bf16 (~335 MB) → `models/vae/` (from `Kijai/flux-fp8/flux-vae-bf16.safetensors` — `Comfy-Org/flux1-schnell` doesn't contain a VAE, only the UNet)
    - PuLID-Flux v0.9.1 (~1.2 GB) → `models/pulid/`
  - Auto-downloaded by node on first workflow run (no manual step): EVA-CLIP, InsightFace antelopev2, facexlib parsing
- [ ] All downloads complete; restart ComfyUI (`./dev comfyui`); no missing-weights errors in console

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
*With uv project mode, `pyproject.toml` (declared deps) + `uv.lock` (resolved + hash-pinned graph) ARE the lock file. No separate `requirements-lock.txt` needed — `uv.lock` is more reproducible than `pip freeze` (content hashes per wheel).*

- [ ] Verify `pyproject.toml` exists and lists the deps you `uv add`-ed
- [ ] Verify `uv.lock` exists and is non-empty (~2000+ lines for this stack)
- [ ] Commit BOTH `pyproject.toml` and `uv.lock` to git
- [ ] Anyone (or future-you) can recreate the exact env via `uv sync`
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

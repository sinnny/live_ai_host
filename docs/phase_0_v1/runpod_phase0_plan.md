# Phase 0 RunPod Plan — what to prepare, what to do on the pod

## Why RunPod (the pivot from fal-only)

Mac MPS in PyTorch 2.11 has zero support for `Float8_e4m3fn`, so our downloaded `flux1-dev-fp8-e4m3fn.safetensors` won't run locally — local Stage 2 PuLID generation is impossible. Switching to GGUF Q8_0 would test a model variant we'd never ship to Phase 2 production CUDA. So: defer Stage 2 to a rented CUDA GPU, where the exact production model runs natively. The savings come for free — RunPod also lets us run the OSS half of Stage 4 (EchoMimic v3 ×3) for ~$2 instead of ~$18 on fal.

**Architecture (final):**
- **RunPod CUDA GPU** = OSS pipeline (Stage 2 PuLID + Stage 4 OSS Tests 1-3 EchoMimic v3)
- **fal.ai** = closed-source benchmark (Stage 4 Tests 4-6: p-video-avatar, Omnihuman, Kling Avatar — these are API-only, not downloadable)

Total estimated Phase 0 spend: **~$11-15** (vs ~$27 fal-only).

---

## What needs to be prepared *locally* (before any RunPod billing starts)

### A. Code (scripts/runpod/) — to be built
- [ ] `bootstrap.sh` — runs once on the pod after launch:
  - Clone ComfyUI-Manager + ComfyUI_PuLID_Flux_ll into `custom_nodes/`
  - Apply the PR #95 `**kwargs` patch to `PulidFluxHook.py`
  - `pip install --no-deps facenet-pytorch`
  - Download 5 weight files via `hf download` (or `wget` from HF mirrors)
  - Symlink `~/inputs/` and `~/outputs/` into ComfyUI's expected paths
  - Launch ComfyUI in background (no GUI access needed)
- [ ] `generate.py` — batch generation via ComfyUI HTTP API:
  - Read `comfy_workflows/pulid_flux_template.json`
  - For each (prompt, seed) pair in a config list, swap the placeholder fields
  - POST to `http://localhost:8188/prompt`
  - Poll `/history/<id>` until done; download result image
  - Save outputs to `outputs/stage2_variants/<step_count>/<prompt_idx>_<variant_idx>.png` with metadata sidecar (prompt, seed, timing)
  - Continue on per-image failure (don't kill the run)
- [ ] `README.md` — operational instructions for the user (upload bundle, run order, expected timing, how to download results back)

### B. Assets (already have or need to make)
- [x] `comfy_workflows/pulid_flux.json` — patched workflow (smoke-test reference)
- [ ] `comfy_workflows/pulid_flux_template.json` — parameterizable version (placeholder for prompt + seed)
- [x] `inputs/photos/hero.png` (1024×1024)
- [ ] `inputs/photos/variant_3q.png` — kim_3 face-cropped (Stage 4 Test 2 input)
- [ ] `inputs/photos/variant_speaking.png` — kim_6 face-cropped (Stage 4 Test 3 input)
- [x] `inputs/audio/reference_korean_30s.wav` (24kHz mono PCM, 15.15s)

### C. Reference data baked into generate.py
- The 5 Stage 2 prompts (per plan §Stage 2):
  1. `[hero], slight smile, looking at camera, 3/4 right angle`
  2. `[hero], slight surprise, looking at camera, slight 3/4 left`
  3. `[hero], speaking, mouth slightly open, looking at camera` ← needed for Stage 4 Test 3
  4. `[hero], looking down at notes, thoughtful expression`
  5. `[hero], warm laugh, eyes crinkled, looking at camera`
- 5 seeds per prompt × 2 step counts = 50 generations baseline
- Hero shot description prefix: "A Korean woman in her late 20s, broadcast-quality, soft studio lighting, photorealistic, …"

### D. Bundle delivery mechanism (pick one before pod launch)
- Option A: **Push to a private GitHub repo** → `git clone` on pod (~10 sec). Cleanest for repeated use.
- Option B: **Tarball + RunPod web upload** → `wget`/`scp` to pod. Fine for one-shot.
- Option C: **Public gist** — works, but project-info exposure.

**Recommendation: Option A.** Even a brand-new private repo with just `scripts/runpod/`, `comfy_workflows/`, `inputs/photos/` and `inputs/audio/` works.

---

## Decisions you need to make before launching the pod

| Decision | Choice | Notes |
|---|---|---|
| **GPU tier** | **A6000 48GB (~$0.50/hr Community Cloud)** | Plenty for Flux dev fp8 + PuLID at our batch size. Compute isn't the bottleneck — downloads + setup dominate billed time. |
| **Template** | **Generic PyTorch (e.g. `runpod/pytorch:2.4.0-py3.11-cuda12.4`)** — install ComfyUI ourselves | Reproducible, matches our local Mac setup recipe exactly. Bootstrap.sh handles install. |
| **Storage** | **Ephemeral pod disk (no Network Volume)** | Re-download weights (~10 min) every pod start. Acceptable for 2-3 total runs. Persistent volume revisited if Phase 0 → Phase 1 reuses the pod. |
| **Bundle delivery** | **Private GitHub repo** | Push project (excluding gitignored `tools/ComfyUI/`, `.venv/`, `models/`, `outputs/`); `git clone` on pod. Reusable across sessions, version-controlled. Setup task: create private GitHub repo, add as remote, push. |
| **SSH access** | **Existing SSH key (`~/.ssh/id_ed25519` or `~/.ssh/id_rsa`)** | Add public key to RunPod account settings during setup. Used to `scp` outputs back to Mac. |

---

## What happens *on* the pod (the only billed time)

Targeting ~30-60 min total for Stage 2 (first run; future runs faster if assets are cached on volume).

| Step | Time | Notes |
|---|---|---|
| 1. Spin up pod from template | 1-2 min | Pick A6000 + ComfyUI template |
| 2. SSH in / open web terminal | <1 min |  |
| 3. `git clone <your-runpod-bundle-repo>` | <1 min |  |
| 4. `bash scripts/runpod/bootstrap.sh` | 10-15 min | Mostly weight downloads from HF |
| 5. `python scripts/runpod/generate.py` | 15-30 min | 50 generations × ~30s each on A6000 |
| 6. `tar czf outputs.tar.gz outputs/` | <1 min |  |
| 7. `scp` outputs back to Mac | 1-2 min | ~50 MB of images |
| 8. **Terminate pod** | instant | Billing stops |

**Cost: ~$0.50-3 for Stage 2.**

If we extend to Stage 4 OSS (EchoMimic v3 ×3) in the same pod session: add ~30 min ⇒ another ~$0.50-1.50.

---

## What happens *back on Mac* after the RunPod session

- Inspect outputs/ → score the 25 variants against PuLID identity rubric
- Pick the best step count (compare 4-step vs 8-step output quality)
- If quality is great → continue to Stage 4 fal.ai tests for closed-source benchmarks
- If quality is poor → escape: more reference images / different PuLID weight / Flux Kontext Pro on fal as escape
- Pick the speaking-pose variant for Stage 4 Test 3

---

## Decision points where we'd pause and check in

- **After bootstrap.sh completes** — verify ComfyUI loaded the PuLID node successfully (no IMPORT FAILED), weights are in place, MPS-was-the-only-issue assumption confirmed by no `Float8_e4m3fn` errors on CUDA
- **After first 1-2 generations** — visual quality check: does PuLID actually preserve Korean facial features? Identity stability OK? If garbage → kill the run, debug, don't burn 30 more minutes generating 48 more bad images
- **Before committing to Stage 4 OSS on the same pod** — based on Stage 2 results, decide whether to also test EchoMimic v3 in this session or terminate and come back

---

## Rollback / abort criteria

- If RunPod GPU pod fails to spin up (capacity issues): try a different region or GPU tier; abort if blocked >30 min
- If bootstrap.sh fails partway through: read the log, manual recovery in the running pod (cheaper than re-spinning)
- If generation produces obviously broken output (black images, all noise, identity totally off): pause, don't keep generating

---

## What NOT to build now

- **EchoMimic v3 on RunPod setup** — defer until after Stage 2 results inform whether we want to push Phase 0 further on RunPod or revert to fal-only for Stage 4
- **Multi-reference batching for PuLID** — first run uses just hero.png; if identity preservation is weak we can retry with multiple refs in a follow-up run
- **Persistent network volume setup** — only worth it if we end up doing 4+ pod sessions

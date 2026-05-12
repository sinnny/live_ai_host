# RunPod operational guide — Phase 0 Stages 2 & 4

End-to-end procedures for running our Phase 0 OSS pipeline on a rented RunPod A6000.

- **[Stage 2 — PuLID identity variants](#stage-2--pulid-identity-variants)** (✅ done — negative finding, documented in `docs/stage2_pulid_findings.md`)
- **[Stage 4 — EchoMimic v3 talking-head, Tests 1-3](#stage-4--echomimic-v3-talking-head)** (in progress)

---

## Stage 2 — PuLID identity variants

Total billed time: ~30-60 min. Estimated cost: ~$0.50-2.

### Pre-flight (one-time setup, already done)

- [x] RunPod account funded (~$10)
- [x] GitHub linked to RunPod
- [x] SSH public key added to RunPod
- [x] Project pushed to private GitHub repo (`sinnny/live_ai_host`)

## Pod session — step by step

### 1. Spin up the pod (~2 min)

1. Go to https://www.runpod.io/console/pods
2. Click **"Deploy"** → **"GPU Pods"**
3. **GPU**: pick **RTX A6000** (~$0.50/hr Community Cloud)
4. **Template**: pick a generic PyTorch template, e.g.
   `runpod/pytorch:2.4.0-py3.11-cuda12.4-devel-ubuntu22.04`
5. **Container Disk**: 30 GB (room for ComfyUI + ~17 GB weights + buffer)
6. **Volume**: skip (we're using ephemeral storage for cost)
7. Click **Deploy**. Pod boots in 1-2 min.

### 2. SSH in (~30 sec)

Once the pod is "Running":
- Click on it → copy the SSH command. Looks like `ssh root@123.45.67.89 -p 22122 -i ~/.ssh/id_ed25519`
- Paste into your Mac terminal

### 3. Clone the project (~30 sec)

```bash
cd /workspace
git clone https://github.com/sinnny/live_ai_host.git
cd live_ai_host
```

### 4. Run bootstrap (~10-15 min)

```bash
bash scripts/runpod/bootstrap.sh
```

This will (in order):
1. Verify GPU
2. Install `uv`
3. Clone ComfyUI
4. Set up venv + install ComfyUI deps
5. Clone PuLID-Flux node + apply our PR #95 patch + install `facenet-pytorch`
6. Download 5 weight files from HuggingFace (~17 GB; the bulk of the time)
7. Symlink `inputs/` into ComfyUI
8. Launch ComfyUI in background on port 8188
9. Wait for API readiness

End state: ComfyUI is running; ready to accept generation requests.

### 5. Smoke test (1 image, ~30-60s)

Before kicking off the full 50-image batch, verify the pipeline works on a single generation:

```bash
python scripts/runpod/generate.py --limit 1
```

Expected: prints "ok" and produces `outputs/stage2_variants/20steps/p1_3q_right_seed42.png`.
If this fails, debug NOW (much cheaper than failing midway through 50 images).

### 6. Full batch (~15-30 min)

```bash
python scripts/runpod/generate.py
```

Generates 50 images: 5 prompts × 5 seeds × 2 step counts (20 vs 30). Each image takes ~20-40s on A6000.

Output structure:
```
outputs/stage2_variants/
├── 20steps/
│   ├── p1_3q_right_seed42.png
│   ├── p1_3q_right_seed42.json    ← sidecar metadata (prompt, seed, time)
│   ├── ...
│   └── p5_warm_laugh_seed9001.png
└── 30steps/
    └── (same 25 files)
```

### 7. Pack outputs (~30 sec)

```bash
tar czf /workspace/outputs.tar.gz -C /workspace/live_ai_host outputs/stage2_variants/
ls -la /workspace/outputs.tar.gz
```

### 8. Download to Mac (~1-2 min)

From your Mac (replace pod IP/port with what RunPod shows you):

```bash
scp -P 22122 -i ~/.ssh/id_ed25519 \
  root@<POD-IP>:/workspace/outputs.tar.gz \
  /Users/shinheehwang/Desktop/projects/00_live_ai_host/outputs/

cd /Users/shinheehwang/Desktop/projects/00_live_ai_host/outputs
tar xzf outputs.tar.gz
ls stage2_variants/
```

### 9. Terminate the pod (instant; STOPS BILLING)

Back in https://www.runpod.io/console/pods → click your pod → **Terminate**.

⚠ **"Stop" is NOT enough** — stopped pods still bill for storage. **Terminate** is the destructive action that fully ends billing.

## Troubleshooting

### Bootstrap fails

- **HF download stalls**: rerun `bash scripts/runpod/bootstrap.sh` — it's idempotent and `hf download` resumes
- **ComfyUI doesn't start**: check `cat /workspace/live_ai_host/logs/comfyui_pod.log`
- **Out of disk**: container disk filled up. Pick 50+ GB next time, or use a Network Volume.

### Generation fails

- **All images error with same message**: workflow/template issue. Check the error in the log; common causes are missing weight files, incorrect node IDs in template targets, or new ComfyUI API changes.
- **Some images error sporadically**: per-image OOM or transient issue. The script continues; failures listed at the end.
- **Generation hangs forever**: pod GPU might be stuck. SSH in another terminal, `nvidia-smi` to check, restart ComfyUI: `pkill -f ComfyUI/main.py && bash scripts/runpod/bootstrap.sh`

### Quality looks wrong

- **Identity not preserved**: PuLID weight too low. Edit `comfy_workflows/pulid_flux_template.json`, find the `ApplyPulidFlux` node, increase `inputs.weight` (default 1.0 → try 1.2-1.5).
- **Output is noise/garbled**: insufficient steps (try 30 or 50 in `stage2_prompts.yaml`), or fp8 issue (check `nvidia-smi` for OOM).
- **All faces look Western**: prompt prefix issue. Edit `stage2_prompts.yaml`, make the Korean phenotype more explicit.

## Cost discipline

- Run bootstrap + smoke test + full batch in ONE session — don't pause mid-session
- Terminate the pod IMMEDIATELY after `tar` completes
- If you'll come back: consider a Network Volume next time so weights persist
- Do NOT leave the pod running overnight to "come back tomorrow" — that's $12+ wasted

### What the Stage 2 script does NOT do

- Stage 4 OSS testing (EchoMimic v3) — see below
- Score the variants — that's manual visual evaluation back on the Mac
- Push results back to git — outputs stay local (gitignored)

---

## Stage 4 — EchoMimic v3 talking-head

End-to-end procedure for running EchoMimic v3 (OSS, Apache 2.0) Tests 1-3 on a rented
A6000. Estimated billed time: ~45-60 min. Estimated cost: ~$0.40-0.60.

Tests covered (all use `inputs/audio/reference_korean_30s.wav`, ~15s Korean TTS):
- **Test 1**: `hero.png` (gating test — does OSS work on Korean?)
- **Test 2**: `variant_3q.png` (pose tolerance — 3/4 angle input)
- **Test 3**: `variant_speaking.png` (non-neutral mouth input)

Locked decisions for this run:
- **Variant**: Flash (chinese-wav2vec2 → closer phoneme set to Korean than English wav2vec2-base)
- **Resolution**: 1024×1024 native (off training distribution — hero shot smoke-tested first)
- **Audio**: 15.15s clip as-is (confound flagged in `docs/stage2_pulid_findings.md` Stage 3 row)

### 1. Spin up the pod (~2 min)

Same RunPod console flow as Stage 2:
- **GPU**: RTX A6000 (~$0.50/hr Community Cloud)
- **Template**: generic PyTorch, e.g. `runpod/pytorch:2.4.0-py3.11-cuda12.4-devel-ubuntu22.04`
- **Container Disk**: **50 GB** (env + Wan2.1 base + Flash + Preview weights + buffer)
- **Volume**: skip
- Deploy.

### 2. SSH in and clone the project (~1 min)

```bash
ssh root@<POD-IP> -p <PORT> -i ~/.ssh/id_ed25519
cd /workspace
git clone https://github.com/sinnny/live_ai_host.git
cd live_ai_host
```

### 3. Run bootstrap (~10-15 min)

```bash
bash scripts/runpod/bootstrap_echomimic.sh
```

Steps performed:
1. GPU sanity check
2. Install `uv`
3. Clone `antgroup/echomimic_v3` to `/workspace/echomimic_v3`
4. Python 3.10 venv + requirements, then force-reinstall torch cu124 wheels
5. Download `alibaba-pai/Wan2.1-Fun-V1.1-1.3B-InP` (shared base, ~5-10 GB)
6. Download Flash weights: `chinese-wav2vec2-base` (ModelScope) + flash transformer
7. Download Preview weights: `wav2vec2-base-960h` + preview transformer (for optional A/B)
8. Symlink project inputs into the echomimic_v3 dir

End state: weights are in place at `echomimic_v3/{flash,preview}/`, no background service.

### 4. Hero smoke test (~5-10 min)

Before committing to all 3 tests, validate the pipeline + 1024 resolution + Korean audio
on a single generation:

```bash
python scripts/runpod/generate_echomimic.py --tests hero
```

This runs `infer_flash.py` with the locked args (1024×1024, video_length=65 for VRAM
headroom, seed=43, prompt from plan). Output lands at:

```
outputs/stage4_videos/flash_1024/hero/
├── <whatever_infer_flash.py_names_it>.mp4
└── _meta.json   ← timing, exit code, full command
```

**Inspect the output before continuing.** Decision gate:
- ✅ Mouth attempts Korean phoneme shapes, identity preserved, no major artifacts → continue
- ❌ Garbled output, identity broken, OOM, or obvious "wrong language" lip-sync → see escape ladder below

### 5. Run Tests 2-3 (~10-20 min)

If hero is clean at 1024:

```bash
python scripts/runpod/generate_echomimic.py --tests variant_3q,variant_speaking
```

If hero showed 1024 artifacts but ran without errors, fall back to 768 for all 3
(rerun hero too for consistency):

```bash
python scripts/runpod/generate_echomimic.py --resolution 768
```

### 6. Optional Preview A/B on hero (~10 min)

Only if Flash output is usable. Preview uses English wav2vec2 — expected to be worse
on Korean, but interesting as a quality ceiling reference. Preview is not wired
through `generate_echomimic.py` (intentional — gate on Flash first); to run:

```bash
cd /workspace/echomimic_v3
# Edit config/config.yaml to point at preview/ weights and a single hero test, then:
.venv/bin/python infer_preview.py
```

### 7. Pack outputs (~30 sec)

```bash
cd /workspace/live_ai_host
tar czf /workspace/stage4_outputs.tar.gz outputs/stage4_videos/
ls -la /workspace/stage4_outputs.tar.gz
```

### 8. Download to Mac (~1-2 min)

From the Mac:

```bash
scp -P <PORT> -i ~/.ssh/id_ed25519 \
  root@<POD-IP>:/workspace/stage4_outputs.tar.gz \
  /Users/shinheehwang/Desktop/projects/00_live_ai_host/outputs/

cd /Users/shinheehwang/Desktop/projects/00_live_ai_host/outputs
tar xzf stage4_outputs.tar.gz
ls stage4_videos/
```

### 9. Terminate the pod (instant; STOPS BILLING)

RunPod console → pod → **Terminate** (not Stop).

### Stage 4 escape ladder

| Failure | Mitigation |
|---|---|
| OOM at 1024, `video_length=65` | Drop to `--video-length 49` or `33` |
| Persistent OOM at 1024 | `--resolution 768` (all 3 tests; rerun hero for consistency) |
| `infer_flash.py` errors on missing `flash-attn` | Pod-side: `uv pip install --python /workspace/echomimic_v3/.venv/bin/python flash-attn --no-build-isolation` (slow compile, may need `--no-build-isolation`) |
| ModelScope download for `chinese-wav2vec2-base` fails | Try `huggingface_hub` mirror (some community uploads exist), or fall back to Preview variant with English wav2vec2 |
| Korean lip-sync is clearly wrong-language | Document — that IS the Phase 0 gating answer for OSS |
| Identity broken or artifacts at 1024 only | Fall back to 768 — adjust DECISION.md to note 1024 is unstable |

### What the Stage 4 scripts do NOT do

- Score the videos — manual viewing + scoring in Stage 5 back on Mac
- Run Tests 4-6 (paid closed-source) — those are fal.ai-side, separate pipeline
- Run Preview through `generate_echomimic.py` — intentional; gate on Flash first

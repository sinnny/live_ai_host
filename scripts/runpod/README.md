# RunPod operational guide — Phase 0 Stage 2 (PuLID variants)

End-to-end procedure for running PuLID-Flux identity variants on a rented RunPod
A6000 GPU. Total billed time: ~30-60 min. Estimated cost: ~$0.50-2.

## Pre-flight (one-time setup, already done)

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

## What this script does NOT do

- Stage 4 OSS testing (EchoMimic v3) — separate pod session, separate setup
- Score the variants — that's manual visual evaluation back on the Mac
- Push results back to git — outputs stay local (gitignored)

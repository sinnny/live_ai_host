# Flux Kontext Dev test plan

A direct apples-to-apples comparison against the PuLID stage 2 negative finding
(`docs/phase_0_v1/stage2_pulid_findings.md`). Same hero photo, same 5 prompts, same 5 seeds —
just swap the model.

The question we're answering: **can Flux Kontext Dev do the prompt-driven identity
variation that PuLID couldn't?** If yes, augmentation step for sprite/LoRA pipelines
unblocks without LoRA training. If no, we move to LoRA-on-Kontext-Dev next.

## Scope

- **Input**: `inputs/photos/hero.png` (same as PuLID stage 2)
- **Prompts**: 5 (3q_right, 3q_left_surprise, speaking, looking_down, warm_laugh)
- **Seeds**: 5 (42, 1024, 7777, 31415, 9001)
- **Total**: 25 images
- **Hardware**: RunPod L40S (~$1/hr Community Cloud) or A6000 (~$0.50/hr)
- **Budget**: ~$1-2, ~30-60 min wall time end-to-end

## Why Kontext Dev specifically (not LoRA)

See conversation log 2026-05-16 and [[feedback_research_vs_production]]. TL;DR:

1. **Training-free** — no LoRA tuning loop, lowest-friction test
2. **SOTA in OSS** for identity-preserving image edit as of 2026-05
3. **License non-commercial** but fine for Phase 0 research
4. If this fails, *then* go to LoRA on Kontext Dev; don't skip the cheap test first

## Files

| Path | Purpose |
|---|---|
| `comfy_workflows/flux_kontext_template.json` | API-format ComfyUI workflow |
| `comfy_workflows/kontext_prompts.yaml` | prompts × seeds × hyperparams |
| `scripts/runpod/bootstrap_kontext.sh` | Pod-side: install ComfyUI + Kontext weights |
| `scripts/runpod/generate_kontext.py` | Pod-side: batch via ComfyUI HTTP API |
| `dev` (subcommand `kontext`) | Mac-side: SSH wrappers |

## End-to-end run procedure

### Pre-flight (one-time)

- [x] RunPod account funded (~$10 — already done for PuLID/EchoMimic)
- [x] SSH key registered
- [x] `~/.ssh/config` alias `runpod` set (or `RUNPOD_SSH_ALIAS` env var)
- [x] Project pushed to GitHub (`sinnny/live_ai_host`)

### 1. Spin up the pod (~2 min)

1. https://www.runpod.io/console/pods → **Deploy** → **GPU Pods**
2. GPU: **RTX L40S** (~$1/hr) or **RTX A6000** (~$0.50/hr Community Cloud)
3. Template: `runpod/pytorch:2.4.0-py3.11-cuda12.4-devel-ubuntu22.04`
4. Container disk: **30 GB**
5. Volume: skip
6. Deploy → wait for "Running"

### 2. SSH config (~30 sec, one-time per pod)

Copy the SSH command from RunPod, then add to `~/.ssh/config`:

```
Host runpod
  HostName <POD-IP>
  Port <PORT>
  User root
  IdentityFile ~/.ssh/id_ed25519
  StrictHostKeyChecking no
```

Then verify: `ssh runpod 'nvidia-smi --query-gpu=name --format=csv'`

### 3. Clone + bootstrap (~10-15 min)

From the Mac:

```bash
./dev kontext bootstrap
```

This does:
1. `git push` from Mac
2. SSH into pod
3. `git pull` (or `git clone` if first time — manual; see fallback below)
4. Run `bash scripts/runpod/bootstrap_kontext.sh` which:
   - GPU sanity
   - Install uv, clone ComfyUI, set up venv, force cu124 torch
   - Download ~17 GB weights (Kontext Dev fp8 + T5XXL + CLIP-L + ae.safetensors)
   - Symlink `inputs/photos/` into ComfyUI input
   - Launch ComfyUI in background

If `./dev kontext bootstrap` fails because the project isn't cloned on the pod yet:

```bash
ssh runpod
cd /workspace
git clone https://github.com/sinnny/live_ai_host.git
cd live_ai_host
bash scripts/runpod/bootstrap_kontext.sh
exit
```

### 4. Smoke test (~30-60 sec, 1 image)

```bash
./dev kontext smoke
```

Generates 1 image (first prompt × first seed) → `outputs/kontext_test/p1_3q_right_seed42.png`.
**Inspect it.** If broken now, debug now — much cheaper than failing midway through 25.

### 5. Full batch (~10-20 min, 25 images)

```bash
./dev kontext run
```

Generates 25 images at ~15-30s each on L40S.

Output:
```
outputs/kontext_test/
├── p1_3q_right_seed42.png
├── p1_3q_right_seed42.json   ← sidecar (prompt, seed, elapsed)
├── ...
└── p5_warm_laugh_seed9001.png
```

### 6. Pull to Mac (~1 min)

```bash
./dev kontext pull
```

### 7. Terminate pod ⚠️

https://www.runpod.io/console/pods → pod → **Terminate** (NOT Stop — Stop still bills storage).

## Evaluation criteria

Same scoring rubric as PuLID stage 2 (`docs/phase_0_v1/stage2_pulid_findings.md` for the Korean
phenotype checklist), plus Kontext-specific failure modes.

### Pass conditions

1. **Identity preservation**: same person across all 25 images (no drift to a different face)
2. **Prompt obedience**: pose/expression actually shifts per prompt (the PuLID failure)
3. **Korean phenotype intact**: monolid preserved, no skin tone drift, jaw/cheekbone structure stable
4. **No major artifacts**: no warped hands, doubled faces, melted hair edges

### Kontext-specific risks to watch

- **Prompt ignored** (output ≈ input) → guidance too low or prompt phrasing wrong
- **Over-edit** (identity bleeds) → guidance too high or prompt overwhelms reference
- **Background hallucination** (clothes/setting shift) → unavoidable with current prompts, mark for later

### Decision after eval

| Outcome | Next step |
|---|---|
| 4/4 pass conditions | ✅ Use Kontext Dev for sprite-puppet LoRA dataset gen. Phase 1 → Kontext Pro API |
| Identity OK + prompts kinda work | Sweep guidance (1.5, 2.5, 3.5) on hero.png only, then re-evaluate |
| Identity drifts | Move to LoRA-on-Kontext-Dev (ai-toolkit, ~2 hr training) |
| Prompts ignored entirely | Re-phrase prompts as edit instructions ("change pose to 3/4 right") + sweep guidance |

## Cost discipline

- One session: bootstrap + smoke + full run + terminate. Don't pause mid-session.
- Total expected billed time: 30-60 min → $0.50-1
- If hero.png results are bad, **terminate before** running kim_1..kim_7 variants
- See `scripts/runpod/README.md` "Cost discipline" section for the broader playbook

## Open questions / deferred

- Which seed photo is best? (hero.png chosen for direct PuLID comparison; kim_1..kim_7
  variants left for second run if hero results look good)
- Step count sweep (20 default; sweep 30/40 only if 20 has noise issues)
- Guidance sweep (2.5 default; per ComfyUI Kontext example)

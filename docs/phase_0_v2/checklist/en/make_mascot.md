# Checklist — Daramzzi mascot atlas generation

| | |
|---|---|
| Purpose | Execute `make_mascot` pipeline → produce a 24-sprite layered atlas for Daramzzi |
| FSD reference | [`../../fsd/make_mascot.md`](../../fsd/make_mascot.md) |
| Character bible | [`../../../characters/daramzzi.md`](../../../characters/daramzzi.md) |
| Usage | Mark each step `[ ]` → `[x]` when complete. On session resume, pick up from the first unchecked item. |
| Language note | This is the English source. Korean translation at [`../ko/make_mascot.md`](../ko/make_mascot.md). |
| Last updated | 2026-05-13 |

---

## Tech stack (at a glance)

- **Qwen-Image** (Apache 2.0) — image generation
- **AI-Toolkit** by Ostris (MIT) — LoRA training
- **BiRefNet** (MIT) — background removal
- **MediaPipe** (Apache 2.0) — sprite anchor alignment
- **Pillow + custom Python** — atlas packing
- **Infra**: RunPod L40S, all OSS, no paid generation APIs

Full table with rationale: [`../../fsd/make_mascot.md`](../../fsd/make_mascot.md) §2

---

## Session resume — read first

If your session disconnected and you're picking up:

1. Find the first unchecked `[ ]` item below — that's where you resume.
2. If uncertain about state on the remote box: SSH to RunPod → `cd scripts/test_3/mascot/daramzzi && python pipeline.py status --config daramzzi_config.yaml`.
3. All pipeline stages are **idempotent** — safe to rerun. They check for existing outputs and skip work already done.
4. For deeper context, see [`../../fsd/make_mascot.md`](../../fsd/make_mascot.md) §10 (Session-continuity guide).

---

## §1. Prerequisites

### §1.1 Document review

- [ ] Read [`../../fsd/make_mascot.md`](../../fsd/make_mascot.md) — especially §2 (tech stack) and §5 (pipeline stages)
- [ ] Read [`../../../characters/daramzzi.md`](../../../characters/daramzzi.md) §3 (persona) + §4 (visual identity)
- [ ] FSD §11 (open questions) — confirm decisions:
  - [x] Seed approval gate: manual OK (locked 2026-05-13)
  - [x] 3-retry-then-halt policy: yes (locked 2026-05-13)
  - [x] Final atlas review format: rendered preview (locked 2026-05-13)
  - [x] LoRA versioning: train once, freeze (locked 2026-05-13)
  - [x] 22/24 outcome: iterate to 24/24 (locked 2026-05-13)
  - [x] Bible gender presentation: female (locked 2026-05-13)
  - [x] 사장님 ever speaks: no (locked 2026-05-13)

### §1.2 API keys / access

- [ ] RunPod account + API key (`RUNPOD_API_KEY`) — needed for L40S rental
- [ ] **No** `ANTHROPIC_API_KEY` needed at pipeline runtime (static `prompts.json` is used instead per option (a))

### §1.3 Budget approval

- [ ] FSD §8.1: typical run ~$5-7 GPU time. FSD §8.2: hard cap $20.
- [ ] Prototype phase total cap: $15 (per [`../../prototype_spec.md`](../../prototype_spec.md) §7).
- [ ] Founder explicit approval: __________

---

## §2. Environment setup

### §2.1 RunPod L40S rental

- [ ] RunPod dashboard → New Pod → L40S 48 GB
- [ ] Container disk ≥ 100 GB (for Qwen-Image + BiRefNet weights)
- [ ] Persistent volume mounted (preserves work across pod restarts)
- [ ] SSH access verified: `ssh root@<runpod-host>`

### §2.2 Code + Docker image

- [ ] `git clone <repo>` placed at `/workspace/live_ai_host`
- [ ] `cd scripts/test_3/mascot/daramzzi`
- [ ] `docker build -t daramzzi-pipeline -f Dockerfile .`
- [ ] Verify build: `docker images | grep daramzzi-pipeline`

### §2.3 Model weight pre-download (optional; first stage will auto-fetch)

- [ ] Qwen-Image weights ~10 GB: `huggingface-cli download Qwen/Qwen-Image`
- [ ] BiRefNet weights ~1 GB
- [ ] Verify disk: `df -h` shows ≥ 50 GB free after model downloads

### §2.4 Directory structure

- [ ] `mkdir -p work atlas`
- [ ] `daramzzi_config.yaml` exists (FSD §3.2 schema)

---

## §3. Pipeline execution

Each stage maps 1:1 to FSD §5 + §6. Commands copy-pasteable from FSD §6.2.

### §3.1 Stage 5.1 — Brief expansion (**static — no Claude API**)

> **Change (2026-05-13):** No runtime Claude API call. Static `prompts.json` already written from the bible. Cost = $0.

- [ ] Verify static prompts file exists: `scripts/test_3/mascot/daramzzi/prompts.json`
- [ ] Validate JSON parses: `python -c "import json; json.load(open('prompts.json'))"`
- [ ] Verify 24-sprite count: 10 expression + 6 mouth + 5 tail + 3 ears
- [ ] Quick manual review: base prompt + negative prompt align with bible §4 (visual identity)
- Estimated: 5 min / Cost: $0

### §3.2 Stage 5.2 — Seed generation **← approval gate**

- [ ] Run `pipeline.py seed`
- [ ] Verify output: `work/02_seed/seed.png`
- [ ] **Manual review (mandatory)** — all of:
  - [ ] Clearly reads as a squirrel (not hamster — tail visible and bushy)
  - [ ] Chubby chibi proportions (head ~1.3× body width)
  - [ ] Chestnut + cream color palette
  - [ ] Apron + headset visible
  - [ ] "Earnest" expression per bible §3.2 (not sassy / sarcastic)
- [ ] If pass: mark complete, proceed
- [ ] If fail: `pipeline.py seed --new-seed N` to try another seed (max 5 attempts recommended)
- Estimated: 10 min including iteration / Cost: ~$0.30

### §3.3 Stage 5.3 — LoRA dataset

- [ ] Run `pipeline.py lora-dataset`
- [ ] Verify output: `work/03_lora_dataset/` contains 8 images + captions
- [ ] Quick visual review: all 8 look like the same character (no drift)
- Estimated: 20 min / Cost: ~$1

### §3.4 Stage 5.4 — LoRA training

- [ ] Run `pipeline.py lora-train`
- [ ] Monitor training log: loss should decrease over steps
- [ ] Verify output: `work/04_lora_train/checkpoints/final.safetensors`
- [ ] Smoke test: generate seed prompt with LoRA loaded → should match seed near-identically
- Estimated: 45 min / Cost: ~$1

### §3.5 Stage 5.5 — Sprite batch generation

- [ ] Run `pipeline.py sprites`
- [ ] Verify output: `work/05_raw_sprites/` contains 24 sprites in 4 layer folders
  - [ ] `expression/`: 10 (neutral, cheek_stuff, panic, pleading, victory, sleepy, confused, sneaky, laughing, embarrassed)
  - [ ] `mouth/`: 6 (closed, aa, ih, ou, ee, oh)
  - [ ] `tail/`: 5 (relaxed, alert, puffed, curled, wagging)
  - [ ] `ears/`: 3 (up, flat, perked)
- [ ] Quick visual review: character identity holds across all 24 sprites
- [ ] If any sprite needs regen: use FSD §5.5 retry budget (max 3 per sprite)
- Estimated: 50 min / Cost: ~$1.20

### §3.6 Stage 5.6 — Background removal

- [ ] Run `pipeline.py alpha`
- [ ] Verify output: `work/06_alpha/` contains 24 alpha-channel PNGs
- [ ] Quick visual check: clean edges, no halos or background bleed
- Estimated: 5 min / Cost: ~$0.20

### §3.7 Stage 5.7 — Anchor normalization

- [ ] Run `pipeline.py normalize`
- [ ] Verify output: `work/07_normalized/` contains 24 anchor-aligned PNGs
- [ ] **Composite preview check**: `python pipeline.py preview-composite` — verify all 6 mouth overlays align at the same face position; all 5 tails attach at the same body point
- Estimated: 10 min / Cost: ~$0.05

### §3.8 Stage 5.8 — Atlas packing

- [ ] Run `pipeline.py pack`
- [ ] Verify outputs:
  - [ ] `atlas/atlas.png` (6144×4096, ≤ 20 MB)
  - [ ] `atlas/config.json` (FSD §4.2 schema)
  - [ ] `atlas/manifest.yaml` (full provenance)
  - [ ] `atlas/lora.safetensors` (trained LoRA copy)
- Estimated: 30 sec / Cost: negligible

---

## §4. Quality validation

### §4.1 Per-sprite criteria (FSD §7.1) — all 24 sprites

- [ ] Resolution 1024×1024
- [ ] Alpha channel PNG
- [ ] No background residue (no halo, no bleed)
- [ ] Anchor aligned within ±10 px tolerance
- [ ] Identity consistent with seed (A/B comparison)
- [ ] Intended state readable at a glance
- [ ] Bible §3 + §4 compliance

### §4.2 Atlas-wide criteria (FSD §7.2)

- [ ] All 10 expressions look like the same character — no style drift
- [ ] 6 mouth overlays align to consistent face position when composited
- [ ] 5 tail overlays attach to consistent body point when composited
- [ ] Fur color hue variance ≤ 5%
- [ ] `atlas.png` file size ≤ 20 MB

### §4.3 Pass / fail decision

- [ ] **Pass:** proceed to §5 (handoff to prototype rendering)
- [ ] **Fail:** apply FSD §7.3 (failure response)
  - Individual sprite fail → re-run Stage 5.5 for that sprite only
  - Identity drift → retrain LoRA (rank 64 or 3000 steps)
  - Multi-sprite bible non-compliance → edit `prompts.json` manually, re-run Stage 5.5+
  - 3 full re-generations without pass → **stop, report to founder, halt**

---

## §5. Handoff to prototype rendering

Atlas is now ready. Proceed to:

- [`tts.md`](tts.md) — TTS for the script
- [`phoneme_alignment.md`](phoneme_alignment.md) — viseme alignment
- [`renderer.md`](renderer.md) — sprite-puppet rendering
- [`orchestrator.md`](orchestrator.md) — end-to-end pipeline driver

---

## §6. Status board

Update as stages complete.

| Step | Status | Started | Completed | Cost | Notes |
|---|---|---|---|---|---|
| §1 Prerequisites | ⬜ Pending | – | – | – | – |
| §2 Environment setup | ⬜ Pending | – | – | – | – |
| §3.1 Stage 5.1 (static prompts) | ⬜ Pending | – | – | $0 | – |
| §3.2 Stage 5.2 (seed) | ⬜ Pending | – | – | – | approval gate |
| §3.3 Stage 5.3 (lora-dataset) | ⬜ Pending | – | – | – | – |
| §3.4 Stage 5.4 (lora-train) | ⬜ Pending | – | – | – | – |
| §3.5 Stage 5.5 (sprites) | ⬜ Pending | – | – | – | – |
| §3.6 Stage 5.6 (alpha) | ⬜ Pending | – | – | – | – |
| §3.7 Stage 5.7 (normalize) | ⬜ Pending | – | – | – | – |
| §3.8 Stage 5.8 (pack) | ⬜ Pending | – | – | – | – |
| §4 Quality validation | ⬜ Pending | – | – | – | – |

Status icons: ⬜ pending / 🟡 in progress / 🟢 complete / 🔴 failed / ⚪ skipped

---

## §7. Troubleshooting / known issues

Log issues encountered during execution.

| Date | Stage | Symptom | Cause | Resolution |
|---|---|---|---|---|
| – | – | – | – | – |

### Common issues (pre-documented)

| Issue | Likely cause | Response |
|---|---|---|
| Seed looks like a hamster | Squirrel/chipmunk emphasis insufficient in prompt | Strengthen squirrel keywords, emphasize tail, retry with new seed |
| LoRA loss not decreasing | Dataset inconsistency | Regenerate Stage 5.3 with stricter prompting |
| Mouth overlay misaligned in composite | MediaPipe failed on cartoon face | Fall back to manual anchor specification per FSD §5.7 |
| Panic expression looks like neutral | Emotion-specific prompt too weak | Add "tail visibly puffed, eyes wide whites showing" to prompt suffix, regenerate |
| Docker build OOM | RunPod container memory limit | Verify L40S sizing |
| Hugging Face download fail | Network / rate limit | Set `HF_HOME`, run `huggingface-cli login` |

---

## §8. After completion

When the atlas passes all quality checks:

- [ ] Verify `manifest.yaml` has all fields populated
- [ ] `git add atlas/ && git commit -m "..."` — commit atlas + LoRA
- [ ] `work/` is gitignored (intermediate artifacts, not committed)
- [ ] Proceed to [`tts.md`](tts.md) for next checklist
- [ ] Preserve this checklist — it serves as template for future characters

---

## §9. Next character (post-MVP)

This checklist is reusable for future characters. To onboard a new mascot:

1. Write `docs/characters/<new>.md` (new bible)
2. Copy `daramzzi_config.yaml` → `<new>_config.yaml`, edit
3. Copy this checklist, replace character name
4. Execute §1 onward identically

The `make_mascot` pipeline will be generalized (parameterized config) after test_3 passes.

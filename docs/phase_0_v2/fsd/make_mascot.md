# Function Spec Document — `make_mascot` pipeline (Daramzzi instantiation)

| | |
|---|---|
| Status | Spec v1 (ready to execute) |
| Document type | Function spec — defines tech stack, inputs/outputs, pipeline stages, quality criteria, failure modes |
| First instantiation | 다람찌 (Daramzzi), per `docs/characters/daramzzi.md` |
| Pipeline mode (v1) | One-shot, Daramzzi-specific. Generalized to multi-mascot parameterization post-test_3. |
| Source documents | `../prd.md` §4.2.1, `./test_3_spec.md` §S3, `../characters/daramzzi.md` |
| Last updated | 2026-05-13 |

---

## 1. Purpose and scope

### 1.1 What this FSD defines

The end-to-end pipeline that takes a character bible (one markdown file) and produces a runtime-ready 2.5D sprite-puppet atlas — without human artist labor.

Specifically for v1: instantiated for **다람찌**, producing a 24-sprite layered atlas + Three.js renderer config, suitable as the mascot for test_3 gate runs.

### 1.2 What this FSD does NOT define

- The Three.js renderer itself (lives in `test_3_spec.md` §S3 and `scripts/test_3/renderer/`)
- The runtime LLM agents (live in test_3 spec)
- The make_mascot CLI generalization for arbitrary characters (post-test_3 work)
- Per-seller customization workflows (v2+ feature)
- Voice generation (`make_voice` is a separate FSD)
- Background generation (`make_bg` is a separate FSD)

### 1.3 Success criteria for the pipeline (Daramzzi)

The pipeline succeeds when:
1. All 24 sprites are produced and pass per-sprite quality criteria (§7.1).
2. The atlas as a whole passes consistency criteria (§7.2).
3. The output atlas + config loads cleanly in the test_3 Three.js renderer.
4. Total wall-clock from launching pipeline to atlas-ready ≤ 4 hours unattended (after LoRA training data is staged).
5. Total GPU spend ≤ $20 for the full run.

### 1.4 Session-continuity note

This FSD is designed to be readable cold by a fresh Claude session. If your session disconnects mid-pipeline:
- The checklist (`./checklist_ko.md`) tracks which stage you're at.
- Every stage produces persistent artifacts under `scripts/test_3/mascot/daramzzi/work/<stage>/` — re-running a stage is idempotent.
- All commands in §6 are copy-pasteable from a fresh shell.

---

## 2. Technology stack (locked)

Per `../prd.md` §4.2.1, the locked-architecture stack. **No paid generation APIs.** Everything self-hosted on the RunPod L40S already rented for test_3.

### 2.1 Tools and licenses

| Stage | Tool | Version | License | Why this tool |
|---|---|---|---|---|
| Brief expansion | Claude Sonnet 4.6 | API, current | proprietary, paid | Korean prosody + persona consistency, already in stack |
| Image generation | **Qwen-Image** | latest from Hugging Face | Apache 2.0 | Best Apache-2.0 image model; strong stylized character; KR prompts |
| LoRA training | **AI-Toolkit** (Ostris) | tag `v0.5.x` or later | MIT | Mature, Qwen-Image-compatible, fast on L40S |
| Background removal | **BiRefNet** | `BiRefNet-portrait` model | MIT | Clean alpha matte on stylized characters |
| Anchor-point detection | **MediaPipe** | latest pip | Apache 2.0 | Face landmarks for cross-sprite alignment |
| Atlas packing | **Pillow** + custom Python | PIL license + MIT | own code | Trivial; no third-party packing tool needed |
| Runtime renderer | **three.js** + sprite-swap shader | MIT | (defined in test_3 spec) | locked in `test_3_spec.md` §S3 |
| Compute | RunPod L40S | 48 GB VRAM | rental | Same box as test_3; ~$1.20/hr |
| Storage | RunPod attached volume | – | – | Persists across instance restart |
| Orchestrator | Python 3.11 | – | – | Drives the pipeline end-to-end |

### 2.2 What is explicitly NOT in the stack

| Rejected | Why |
|---|---|
| fal.ai / Replicate / any paid image API | PRD §4.2.1 locks OSS self-host; paid APIs add unnecessary cost + vendor lock |
| FLUX.1 dev / Flux.2 | Non-commercial without paid license; license trap for B2B SaaS |
| Stable Diffusion 1.5 / 2.1 | Quality below Qwen-Image for stylized character work |
| DALL-E / Midjourney / Imagen | No self-hosted option |
| Live2D / Inochi2D rigging | Out of scope — we ship sprite-puppet, not deformable rig |
| Photoshop / manual touch-up | Violates "no human artist labor" premise |
| Stable Diffusion XL with manual prompt iteration | Without LoRA, identity drifts across sprites (Phase 0 v1 lesson) |

### 2.3 Software dependencies

Installed on the L40S box via Docker. Image specification in `scripts/test_3/mascot/daramzzi/Dockerfile`.

```
base:
  nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04
python deps:
  torch>=2.4              # CUDA 12.x compatible
  diffusers>=0.30         # Qwen-Image support
  transformers>=4.45
  accelerate
  ai-toolkit              # Ostris LoRA trainer
  Pillow
  mediapipe
  birefnet-pytorch        # or load BiRefNet weights manually
  anthropic               # Claude API client
  pyyaml
  click                   # CLI args
```

---

## 3. Inputs

### 3.1 Required inputs

| Input | Source | Format | Purpose |
|---|---|---|---|
| Character bible | `docs/characters/daramzzi.md` | Markdown | Source of truth — drives brief expansion |
| Optional reference image | `inputs/daramzzi_reference.png` (optional) | PNG | If founder has a sketch/reference; otherwise pipeline generates from prompts only |
| Anthropic API key | env `ANTHROPIC_API_KEY` | – | Claude calls for brief expansion |

### 3.2 Configuration inputs (`daramzzi_config.yaml`)

```yaml
character_name: daramzzi
display_name_kr: 다람찌
bible_path: ../../../characters/daramzzi.md
output_dir: ./work
final_atlas_dir: ./atlas
seed: 20260513
base_model: Qwen/Qwen-Image
lora_training:
  rank: 32
  steps: 1500
  learning_rate: 1e-4
  batch_size: 1
  augmentation_count: 8   # variations of seed for LoRA dataset
sprite_layers:
  expression:
    count: 10
    states:
      - neutral
      - cheek_stuff
      - panic
      - pleading
      - victory
      - sleepy
      - confused
      - sneaky
      - laughing       # extra
      - embarrassed    # extra
  mouth:
    count: 6
    states: [closed, aa, ih, ou, ee, oh]
  tail:
    count: 5
    states: [relaxed, alert, puffed, curled, wagging]
  ears:
    count: 3
    states: [up, flat, perked]
canvas:
  sprite_size: 1024
  atlas_columns: 6
  alpha_threshold: 0.1
```

### 3.3 What the pipeline derives from inputs

Claude Sonnet 4.6 reads `daramzzi.md` and emits a `prompts.json` with one prompt per sprite (24 total), grounded in bible §3 (persona), §4 (visual identity), and §5 (voice — informs facial expression intensity).

Example derived prompt (expression layer, "cheek_stuff" state):
```
A chubby chibi cartoon ground squirrel intern character, chestnut brown fur,
cream belly, simplified chipmunk stripes, wearing a half-apron with one large
pocket, headset mic too big for head, EATING POSE: cheeks bulged with food,
eyes closed in blissful satisfaction, mouth closed (food inside),
tail relaxed, ears up,
clean white background, single character centered,
stylized 2D illustration, soft cel-shading, warm autumn color palette,
home shopping channel context, full body visible
```

(Real prompts produced by Claude, not hand-written — this is illustrative.)

---

## 4. Outputs

### 4.1 Final artifacts (committed to repo)

```
scripts/test_3/mascot/daramzzi/
├── atlas/
│   ├── atlas.png                  — single PNG, 6144×4096, all 24 sprites packed
│   ├── config.json                — sprite layout, anchor points, composition rules
│   ├── lora.safetensors           — trained Daramzzi LoRA (~150 MB)
│   └── manifest.yaml              — full provenance: seed, prompts, model version, run timestamp
└── work/                          — intermediate artifacts (git-ignored)
    ├── 01_brief/prompts.json
    ├── 02_seed/seed.png
    ├── 03_lora_dataset/*.png      — augmented LoRA training set
    ├── 04_lora_train/checkpoints/
    ├── 05_raw_sprites/*.png       — 24 raw generations
    ├── 06_alpha/*.png             — background-removed
    ├── 07_normalized/*.png        — anchor-aligned
    └── 08_packed/                 — pre-final atlas check
```

### 4.2 Atlas config.json schema

```json
{
  "schema_version": 1,
  "character": "daramzzi",
  "sprite_size": 1024,
  "atlas_image": "atlas.png",
  "atlas_columns": 6,
  "layers": {
    "expression": {
      "z_order": 0,
      "anchor": {"x": 512, "y": 512},
      "states": {
        "neutral":      {"atlas_pos": [0, 0]},
        "cheek_stuff":  {"atlas_pos": [1, 0]},
        "panic":        {"atlas_pos": [2, 0]},
        "pleading":     {"atlas_pos": [3, 0]},
        "victory":      {"atlas_pos": [4, 0]},
        "sleepy":       {"atlas_pos": [5, 0]},
        "confused":     {"atlas_pos": [0, 1]},
        "sneaky":       {"atlas_pos": [1, 1]},
        "laughing":     {"atlas_pos": [2, 1]},
        "embarrassed":  {"atlas_pos": [3, 1]}
      }
    },
    "mouth": {
      "z_order": 3,
      "anchor": {"x": 512, "y": 600},
      "states": {
        "closed": {"atlas_pos": [4, 1]},
        "aa":     {"atlas_pos": [5, 1]},
        "ih":     {"atlas_pos": [0, 2]},
        "ou":     {"atlas_pos": [1, 2]},
        "ee":     {"atlas_pos": [2, 2]},
        "oh":     {"atlas_pos": [3, 2]}
      }
    },
    "tail": {
      "z_order": 1,
      "anchor": {"x": 200, "y": 700},
      "states": {
        "relaxed": {"atlas_pos": [4, 2]},
        "alert":   {"atlas_pos": [5, 2]},
        "puffed":  {"atlas_pos": [0, 3]},
        "curled":  {"atlas_pos": [1, 3]},
        "wagging": {"atlas_pos": [2, 3]}
      }
    },
    "ears": {
      "z_order": 2,
      "anchor": {"x": 512, "y": 350},
      "states": {
        "up":     {"atlas_pos": [3, 3]},
        "flat":   {"atlas_pos": [4, 3]},
        "perked": {"atlas_pos": [5, 3]}
      }
    }
  },
  "composition_order": ["expression", "tail", "ears", "mouth"],
  "default_state": {
    "expression": "neutral",
    "mouth": "closed",
    "tail": "relaxed",
    "ears": "up"
  }
}
```

### 4.3 Manifest (provenance)

```yaml
character: daramzzi
generated_at: 2026-05-13T14:00:00Z
seed: 20260513
bible_commit: <git sha of daramzzi.md>
config_commit: <git sha of daramzzi_config.yaml>
base_model: Qwen/Qwen-Image (sha:...)
lora:
  trained_for_steps: 1500
  final_loss: 0.087
  dataset_size: 8
generation:
  total_raw_sprites: 24
  retries: 3                   # sprites regenerated for quality
  total_gpu_minutes: 142
  total_cost_usd: 2.84
post_processing:
  birefnet_version: ...
  mediapipe_version: ...
  atlas_packing_method: layered_v1
```

---

## 5. Pipeline stages

Eight stages. Each stage is idempotent — re-running with the same inputs produces the same outputs (deterministic seed).

### Stage 5.1 — Brief expansion

**Input:** `daramzzi.md`, `daramzzi_config.yaml`
**Output:** `work/01_brief/prompts.json` — 24 prompts, one per sprite

**Process:**
1. Read bible markdown.
2. Single Claude Sonnet 4.6 call with system prompt: "You are a prompt engineer for character sprite generation. Produce 24 prompts following this exact schema..."
3. Validate JSON schema.
4. Write to `work/01_brief/prompts.json`.

**Wall clock:** ~30 s
**Cost:** ~$0.03 in Claude tokens
**Failure modes:** Claude returns malformed JSON → retry with stricter format prompt; on second failure, log and halt.

---

### Stage 5.2 — Seed generation

**Input:** `prompts.json` (specifically the `neutral` expression prompt + reference image if any)
**Output:** `work/02_seed/seed.png` — the canonical Daramzzi (1024×1024)

**Process:**
1. Load Qwen-Image via Diffusers.
2. Generate the canonical "neutral pose, mouth closed, tail relaxed, ears up" sprite with config seed.
3. Manual review checkpoint — founder approves the seed.
4. If rejected, regenerate with prompt tweak or different seed within the configured seed range.

**Wall clock:** ~2 min per generation; manual review variable
**Cost:** ~$0.10/generation × N iterations
**Failure modes:**
- Off-bible (wrong species, wrong color, wrong pose) → tune prompt, retry
- Identity ambiguous (could be hamster, could be squirrel) → strengthen bible-derived prompt with explicit "Korean ground squirrel chipmunk" + tail emphasis
- **Founder approval gate.** Pipeline halts here until founder confirms seed.

---

### Stage 5.3 — LoRA training dataset

**Input:** approved seed, augmentation count from config (8)
**Output:** `work/03_lora_dataset/` — 8 augmented images for LoRA training

**Process:**
1. Generate 8 variations of the canonical Daramzzi with Qwen-Image:
   - 3 with slight pose variations (sitting, standing, leaning)
   - 2 with slight angle variations (¾ left, ¾ right)
   - 2 with different expressions (already-target states: neutral + small smile)
   - 1 close-up portrait
2. All variations use the same seed family + identity-preserving prompt anchors.
3. Each captioned with consistent caption template: "a chubby chipmunk character named Daramzzi, [pose], [expression], wearing half-apron, ..."

**Wall clock:** ~20 min
**Cost:** ~$1 in GPU time
**Failure modes:**
- A variation drifts off-character → discard, regenerate. Need 8 acceptable for LoRA dataset.

---

### Stage 5.4 — LoRA training

**Input:** LoRA dataset (8 images + captions), config rank/steps
**Output:** `work/04_lora_train/checkpoints/<final>.safetensors`

**Process:**
1. AI-Toolkit (`ai-toolkit train`) on the dataset.
2. Config from `daramzzi_config.yaml`: rank 32, 1500 steps, LR 1e-4, batch 1.
3. Checkpoint every 250 steps; final is the lowest-loss one in the last 500 steps.
4. Smoke-test the LoRA: generate the seed prompt with LoRA loaded → should look identical or near-identical to the seed image.

**Wall clock:** ~45 min on L40S
**Cost:** ~$1 in GPU time
**Failure modes:**
- Training loss doesn't converge → check caption quality, dataset quality; rerun with rank 64 if needed.
- LoRA over-fits (smoke test produces near-exact seed copy and won't accept other prompts) → reduce steps to 1000.
- LoRA under-fits (smoke test loses identity) → increase steps to 2000, or add more augmentation variants.

---

### Stage 5.5 — Layered sprite batch generation

**Input:** trained LoRA, `prompts.json` (the remaining 23 prompts)
**Output:** `work/05_raw_sprites/{layer}/{state}.png`

**Process:**
1. Load Qwen-Image + Daramzzi LoRA.
2. For each prompt in `prompts.json`:
   - Generate sprite at 1024×1024.
   - Use deterministic seed offset (config seed + index) for reproducibility.
3. Layer-specific prompt conditioning:
   - **Expression layer prompts:** full character, baseline mouth/tail/ears, varying emotional state.
   - **Mouth layer prompts:** ISOLATED mouth/cheek area on transparent/white background, alpha-channel-friendly. Pose-neutral.
   - **Tail layer prompts:** ISOLATED tail on transparent background, varying state.
   - **Ear layer prompts:** ISOLATED ears on transparent background.
4. Save all to `work/05_raw_sprites/{layer}/{state}.png`.

**Wall clock:** ~40 min (24 sprites × ~100 s each)
**Cost:** ~$1 in GPU time
**Failure modes:**
- Layer prompt produces full character instead of isolated element (mouth/tail/ears) → strengthen "ONLY THE MOUTH" / "ONLY THE TAIL" emphasis; consider 2-stage: full body → crop.
- One state drifts (e.g., panic looks identical to neutral) → regenerate with stronger emotion-specific prompt.
- Cheek-stuff state hard to disambiguate from neutral with closed mouth → bible §4.4 says "cheeks bulged" — encode that visually as bulge in the silhouette.

**Retry budget:** up to 3 retries per sprite; total retry budget caps at 12 across the batch.

---

### Stage 5.6 — Background removal

**Input:** all 24 raw sprites
**Output:** `work/06_alpha/{layer}/{state}.png` — clean alpha mattes

**Process:**
1. Run BiRefNet on each sprite.
2. Verify alpha threshold (config `alpha_threshold: 0.1`) — anything below is fully transparent.
3. For overlay layers (mouth, tail, ears): apply stricter threshold; we want clean cut-out.

**Wall clock:** ~5 min
**Cost:** ~$0.20 in GPU time
**Failure modes:**
- Foreground bleed into background (halo around character) → re-run with different model variant (`BiRefNet-DIS` vs `BiRefNet-portrait`).
- Internal transparency punch-through (background showing through chest) → mask refinement pass.

---

### Stage 5.7 — Anchor-point normalization

**Input:** all 24 alpha-matted sprites
**Output:** `work/07_normalized/{layer}/{state}.png` — anchored to consistent canvas position

**Process:**
1. For expression layer (full character): MediaPipe face detection → align center-of-face to canvas (512, 512).
2. For mouth overlay: detect mouth center → align to canvas (512, 600). Same for every mouth state — ensures runtime can swap without visual jump.
3. For tail overlay: detect tail-base attachment point (heuristic: leftmost dark pixel cluster) → align to canvas (200, 700).
4. For ear overlay: align ear-attachment line to (512, 350).
5. Pad/crop all to 1024×1024 with transparent padding.

**Wall clock:** ~10 min (mostly CPU)
**Cost:** ~$0.05
**Failure modes:**
- MediaPipe fails on stylized cartoon face (no human-face landmarks) → fallback heuristic: bounding-box center alignment + manual review of 3 sprites to confirm consistency.
- Mouth alignment off across states → manually specify mouth anchor per state in config; tedious but works.

---

### Stage 5.8 — Atlas packing + config emission

**Input:** all 24 normalized sprites
**Output:** `atlas/atlas.png`, `atlas/config.json`, `atlas/manifest.yaml`, `atlas/lora.safetensors`

**Process:**
1. Lay out 24 sprites in a 6-column × 4-row grid (6144×4096 PNG).
2. Emit `config.json` per §4.2 schema with each sprite's `atlas_pos`.
3. Emit `manifest.yaml` with full provenance (§4.3).
4. Copy the trained LoRA into the atlas folder for reproducibility.

**Wall clock:** ~30 s
**Cost:** negligible
**Failure modes:** PNG too large (>20 MB) → reduce sprite size to 768 or 512.

---

## 6. Execution commands (reproducible from cold start)

These are the exact commands a fresh session (or you, after disconnect) should run to drive the pipeline. The checklist references these by name.

### 6.1 One-time environment setup

```bash
# On RunPod L40S, in /workspace/
git clone <repo> live_ai_host && cd live_ai_host
cd scripts/test_3/mascot/daramzzi
docker build -t daramzzi-pipeline -f Dockerfile .
mkdir -p work atlas
```

### 6.2 Pipeline stages

Each stage is a single CLI invocation. Idempotent on re-run.

```bash
# Stage 5.1 — Brief expansion
docker run --rm -v $(pwd):/work daramzzi-pipeline \
  python pipeline.py brief --config daramzzi_config.yaml

# Stage 5.2 — Seed generation (founder approval gate)
docker run --rm --gpus all -v $(pwd):/work daramzzi-pipeline \
  python pipeline.py seed --config daramzzi_config.yaml
# Review work/02_seed/seed.png. Re-run with --new-seed N for different attempt.

# Stage 5.3 — LoRA dataset generation
docker run --rm --gpus all -v $(pwd):/work daramzzi-pipeline \
  python pipeline.py lora-dataset --config daramzzi_config.yaml

# Stage 5.4 — LoRA training
docker run --rm --gpus all -v $(pwd):/work daramzzi-pipeline \
  python pipeline.py lora-train --config daramzzi_config.yaml

# Stage 5.5 — Sprite batch generation
docker run --rm --gpus all -v $(pwd):/work daramzzi-pipeline \
  python pipeline.py sprites --config daramzzi_config.yaml

# Stage 5.6 — Background removal
docker run --rm --gpus all -v $(pwd):/work daramzzi-pipeline \
  python pipeline.py alpha --config daramzzi_config.yaml

# Stage 5.7 — Normalization
docker run --rm -v $(pwd):/work daramzzi-pipeline \
  python pipeline.py normalize --config daramzzi_config.yaml

# Stage 5.8 — Atlas packing
docker run --rm -v $(pwd):/work daramzzi-pipeline \
  python pipeline.py pack --config daramzzi_config.yaml

# All stages at once (after seed approval):
docker run --rm --gpus all -v $(pwd):/work daramzzi-pipeline \
  python pipeline.py run-all --config daramzzi_config.yaml --start lora-dataset
```

### 6.3 Inspection commands

```bash
# View a specific sprite
docker run --rm -v $(pwd):/work daramzzi-pipeline \
  python pipeline.py view --stage 05_raw_sprites --layer expression --state panic

# Dump current status (which stages have completed)
python pipeline.py status --config daramzzi_config.yaml
```

---

## 7. Quality criteria

### 7.1 Per-sprite criteria (each sprite must pass before atlas-pack)

| Criterion | Method | Threshold |
|---|---|---|
| Resolution | file inspection | 1024×1024 |
| Format | file inspection | PNG with alpha channel |
| Alpha clean | visual review | no foreground bleed, no halos |
| Anchor aligned | overlay check | within ±10 px of expected anchor |
| Identity consistency | manual A/B vs seed | recognizably the same character |
| State expressivity | manual review | the intended emotion/state is readable at a glance |
| Bible compliance | manual review | matches `daramzzi.md` §3 + §4 |

### 7.2 Atlas-wide criteria

| Criterion | Method | Threshold |
|---|---|---|
| Identity continuity across all expression sprites | side-by-side review | all 10 expressions feel like the same character; no obvious style drift |
| Mouth-overlay alignment | composite preview | all 6 mouth overlays align to a single face position when composited |
| Tail-overlay alignment | composite preview | all 5 tail overlays attach to the same body point when composited |
| Color consistency | histogram comparison | fur color hue variance ≤ 5% across all sprites |
| File size | filesystem | atlas.png ≤ 20 MB |
| Composability | runtime preview | the test_3 renderer can load + composite all 24 successfully |

### 7.3 Failure-to-reach-quality response

If post-pipeline review fails quality:
- **Per-sprite failure:** regenerate that sprite with refined prompt (within Stage 5.5 retry budget).
- **Identity drift across atlas:** the LoRA isn't strong enough. Retrain with rank 64 or 3000 steps.
- **Bible-compliance miss on multiple sprites:** the brief expansion (Stage 5.1) underperformed. Manually edit `prompts.json` and re-run from 5.5.
- **Anchor mis-alignment:** Stage 5.7 fallback to manual anchor specification per state.
- **Three-stage retry max.** After three full atlas regenerations without passing, halt and consult founder. Hard problem; may need bible refinement.

---

## 8. Cost and time budget

### 8.1 Per-run estimates

| Stage | Wall clock | GPU cost |
|---|---|---|
| 5.1 Brief expansion | 30 s | $0.03 (Claude) |
| 5.2 Seed (incl. ~3 attempts) | ~10 min | ~$0.30 |
| 5.3 LoRA dataset | ~20 min | ~$1 |
| 5.4 LoRA training | ~45 min | ~$1 |
| 5.5 Sprite batch (incl. retries) | ~50 min | ~$1.20 |
| 5.6 Alpha matte | ~5 min | ~$0.20 |
| 5.7 Normalize | ~10 min | ~$0.10 (CPU mostly) |
| 5.8 Atlas pack | ~1 min | – |
| **Total (no retries)** | **~2.5 hrs** | **~$3.80** |
| **Total (typical, with founder iteration on seed)** | **~4 hrs** | **~$5-7** |

### 8.2 Hard cap

If the run exceeds **$20 in GPU spend** or **8 hours wall clock**, halt and consult founder. Almost certainly something is wrong with the pipeline, not the budget.

---

## 9. Generalization to multi-mascot (post-test_3 work)

This FSD is Daramzzi-instantiated. After test_3 gates pass, the pipeline generalizes by:

1. Replacing the hard-coded character bible path with a CLI argument: `make_mascot --bible <path>`.
2. Externalizing the layer config from hard-coded to a per-character `*_config.yaml`.
3. Removing the "founder approval gate" at Stage 5.2 in favor of automated quality scoring (e.g., CLIP-similarity-to-bible-keywords).
4. Adding a self-service seller upload UI (Sprint 8+) that drives this same pipeline.

The pipeline code is structured to allow this with minimal refactoring — no Daramzzi-specific logic should live in pipeline source, only in config files.

---

## 10. Session-continuity guide

If you (Claude, or any continuing session) come back to this work cold:

1. **Where am I?** Read `./checklist_ko.md` — it has check marks for completed steps.
2. **Is the env still alive?** `ssh runpod && docker ps` — Daramzzi container running?
3. **Resume from a specific stage:** all stages are idempotent. Re-running won't double-charge or duplicate work; it'll only redo what's needed.
4. **Verify previous outputs:** `python pipeline.py status --config daramzzi_config.yaml` dumps a state summary.
5. **Last good state:** check `work/manifest.yaml` for the timestamp of the last successful stage.
6. **If LoRA is trained but atlas isn't packed:** run from Stage 5.5 onward.
7. **If atlas is packed but quality failed:** review §7.3 failure-response, re-run targeted stages.

The pipeline does NOT store secrets in artifacts. `ANTHROPIC_API_KEY` and any RunPod credentials live only in environment variables.

---

## 11. Open questions for founder review (before pipeline launch)

1. **Seed approval cadence.** Stage 5.2 has a founder-approval gate. Do you want me to send you the seed image and wait for explicit OK, or can I auto-proceed if the seed visually matches a CLIP-similarity threshold? (Default: explicit OK.)
2. **Iteration tolerance.** If a sprite needs to be regenerated 3 times and still doesn't pass quality, do I halt or do I escalate immediately? (Default: halt, surface, you decide.)
3. **Final atlas review.** After Stage 5.8, do you want the renderer-preview shown to you (rendered composite in browser) or just the raw atlas.png + config? (Default: renderer preview, more useful.)
4. **LoRA versioning.** Train one LoRA and freeze it for Daramzzi? Or retrain per pipeline run? (Default: train once, freeze, reuse for all future Daramzzi generation.)
5. **Iteration budget for v1 atlas.** If first run produces a 22/24-quality atlas, do we ship it or iterate to 24/24? (Default: iterate to 24/24 within budget cap.)

---

## 12. Sign-off

- Spec author: Claude (Opus 4.7, 1M context)
- Spec reviewer (this iteration): pending founder review
- Implementer: Claude (Option A per `test_3_spec.md` §1)
- Pipeline activates: once founder reviews §11 and provides `ANTHROPIC_API_KEY` + RunPod access

---

## Appendix A — References

- Character bible: `../characters/daramzzi.md` — source of truth for visual + persona
- PRD: `../prd.md` §4.2.1 — locked tech stack
- Test spec: `./test_3_spec.md` §S3 — runtime renderer that consumes this atlas
- Project memory: `~/.claude/projects/-Users-shinheehwang-Desktop-projects-00-live-ai-host/memory/project_live_ai_host.md`

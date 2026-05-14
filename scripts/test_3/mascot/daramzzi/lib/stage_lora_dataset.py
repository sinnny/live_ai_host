"""Stage 5.3 — LoRA training dataset.

Generates `augmentation_count` variations of the canonical Daramzzi for LoRA
training. Variation strategy per FSD §5.3:
  - 3 with slight pose variations (sitting, standing, leaning)
  - 2 with slight angle variations (3/4 left, 3/4 right)
  - 2 with different expressions (neutral + small smile)
  - 1 close-up portrait
"""

from __future__ import annotations

from pathlib import Path

from .config import Config
from .prompts import load_prompts
from .qwen_pipe import generate, get_pipeline


AUGMENTATIONS = [
    # (suffix appended after base prompt, caption appended after base caption)
    ("sitting comfortably on a small wooden stool, full body visible",
     "sitting pose"),
    ("standing upright in default presenter pose, both paws relaxed at sides, full body visible",
     "standing pose"),
    ("leaning forward slightly toward the camera in an attentive presenter pose, full body visible",
     "leaning pose"),
    ("three-quarter view turned slightly to her left side, full body visible",
     "three-quarter left"),
    ("three-quarter view turned slightly to her right side, full body visible",
     "three-quarter right"),
    ("default presenter pose, a gentle warm closed-mouth smile, full body visible",
     "small smile"),
    ("default presenter pose, neutral attentive expression, full body visible",
     "neutral variant"),
    ("close-up portrait crop from chest up, focused on the face, default neutral expression",
     "portrait close-up"),
]

CAPTION_TEMPLATE = (
    "a chubby chibi cartoon Korean ground squirrel character named Daramzzi, "
    "{pose}, wearing a rust-orange half-apron with one pocket and a name tag, "
    "comically oversized headset microphone, warm chestnut brown fur with cream "
    "belly and simplified dorsal stripes, stylized 2D illustration, soft cel-shading, "
    "single character centered, clean white background"
)


def run(cfg: Config, *, force: bool = False) -> dict:
    out_dir = cfg.stage_dir("03_lora_dataset")
    out_dir.mkdir(parents=True, exist_ok=True)

    book = load_prompts(cfg.stage_dir("01_brief") / "prompts.json")
    pipe = get_pipeline(cfg.base_model)
    qwen = book.qwen_image_settings
    size = int(qwen.get("width", cfg.canvas.sprite_size))

    count = cfg.lora_training.augmentation_count
    augments = AUGMENTATIONS[:count] if count <= len(AUGMENTATIONS) else AUGMENTATIONS

    written: list[str] = []
    for i, (suffix, pose) in enumerate(augments):
        img_path = out_dir / f"daramzzi_aug_{i:02d}.png"
        cap_path = out_dir / f"daramzzi_aug_{i:02d}.txt"
        if img_path.exists() and cap_path.exists() and not force:
            written.append(str(img_path))
            continue

        positive = f"{book.base_positive} {suffix}"
        img = generate(
            pipe,
            positive=positive,
            negative=book.base_negative,
            seed=cfg.seed + i + 1,
            width=size,
            height=size,
            steps=int(qwen.get("num_inference_steps", 50)),
            guidance=float(qwen.get("guidance_scale", 7.5)),
        )
        img.save(img_path, format="PNG")
        cap_path.write_text(
            CAPTION_TEMPLATE.format(pose=pose), encoding="utf-8"
        )
        written.append(str(img_path))

    return {
        "output_dir": str(out_dir),
        "image_count": len(written),
        "images": written,
    }

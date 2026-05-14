"""Stage 5.6 — Background removal via BiRefNet.

Loads BiRefNet from Hugging Face (`ZhengPeng7/BiRefNet`) and produces a
4-channel RGBA PNG per sprite. CPU fallback if CUDA isn't available.
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torchvision import transforms
from transformers import AutoModelForImageSegmentation

from .config import Config


_MODEL = None


def _device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def _load_birefnet():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    model = AutoModelForImageSegmentation.from_pretrained(
        "ZhengPeng7/BiRefNet", trust_remote_code=True
    )
    model = model.to(_device())
    model.eval()
    if _device() == "cuda":
        model = model.half()
    _MODEL = model
    return model


def _preprocess(img: Image.Image) -> torch.Tensor:
    tf = transforms.Compose([
        transforms.Resize((1024, 1024)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    return tf(img).unsqueeze(0)


def _matte_one(model, img: Image.Image, alpha_threshold: float) -> Image.Image:
    rgb = img.convert("RGB")
    x = _preprocess(rgb).to(_device())
    if _device() == "cuda":
        x = x.half()
    with torch.no_grad():
        preds = model(x)[-1].sigmoid().cpu()
    mask = preds[0].squeeze().numpy()
    # Resize mask back to original
    mask_img = Image.fromarray((mask * 255).astype(np.uint8)).resize(
        rgb.size, Image.BILINEAR
    )
    mask_np = np.asarray(mask_img).astype(np.float32) / 255.0
    mask_np = np.clip((mask_np - alpha_threshold) / max(1 - alpha_threshold, 1e-6), 0, 1)

    rgba = np.dstack([np.asarray(rgb), (mask_np * 255).astype(np.uint8)])
    return Image.fromarray(rgba, mode="RGBA")


def run(cfg: Config, *, force: bool = False) -> dict:
    src_root = cfg.stage_dir("05_raw_sprites")
    if not src_root.exists():
        raise FileNotFoundError(f"Raw sprites missing at {src_root}. Run `sprites` first.")

    out_root = cfg.stage_dir("06_alpha")
    out_root.mkdir(parents=True, exist_ok=True)

    model = _load_birefnet()
    threshold = cfg.canvas.alpha_threshold
    written: list[str] = []

    for layer_dir in sorted(src_root.iterdir()):
        if not layer_dir.is_dir():
            continue
        out_layer = out_root / layer_dir.name
        out_layer.mkdir(parents=True, exist_ok=True)
        for png in sorted(layer_dir.glob("*.png")):
            target = out_layer / png.name
            if target.exists() and not force:
                written.append(str(target))
                continue
            img = Image.open(png)
            matted = _matte_one(model, img, threshold)
            matted.save(target, format="PNG")
            written.append(str(target))

    return {
        "output_dir": str(out_root),
        "sprite_count": len(written),
    }

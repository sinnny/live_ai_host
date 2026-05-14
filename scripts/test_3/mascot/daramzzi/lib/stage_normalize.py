"""Stage 5.7 — Anchor-point normalization.

Per FSD §5.7:
  - Expression layer: align center-of-character to canvas (512, 512).
  - Mouth overlay:    align mouth center to canvas (512, 600).
  - Tail overlay:     align tail-base attachment to canvas (200, 700).
  - Ear overlay:      align ear-attachment line to canvas (512, 350).

MediaPipe face landmarks are unreliable on stylized cartoon faces; the
fallback heuristic (alpha-centroid for character, alpha-bbox for overlays)
is what actually carries this stage in practice.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image

from .config import Config


ANCHORS: dict[str, Tuple[int, int]] = {
    "expression": (512, 512),
    "mouth":      (512, 600),
    "tail":       (200, 700),
    "ears":       (512, 350),
}


def _alpha_centroid(rgba: np.ndarray) -> Tuple[float, float] | None:
    """Centre of mass of the alpha channel. Returns (x, y) in pixels."""
    alpha = rgba[:, :, 3]
    mask = alpha > 16  # ignore semi-transparent noise
    if not mask.any():
        return None
    ys, xs = np.where(mask)
    return float(xs.mean()), float(ys.mean())


def _alpha_bbox(rgba: np.ndarray) -> Tuple[int, int, int, int] | None:
    alpha = rgba[:, :, 3]
    mask = alpha > 16
    if not mask.any():
        return None
    ys, xs = np.where(mask)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def _shift_to_anchor(
    rgba: np.ndarray,
    centroid: Tuple[float, float],
    target: Tuple[int, int],
    canvas: int,
) -> np.ndarray:
    out = np.zeros((canvas, canvas, 4), dtype=rgba.dtype)
    dx = int(round(target[0] - centroid[0]))
    dy = int(round(target[1] - centroid[1]))

    src_h, src_w = rgba.shape[:2]
    # Source crop bounds in source coords
    sx0 = max(0, -dx)
    sy0 = max(0, -dy)
    sx1 = min(src_w, canvas - dx)
    sy1 = min(src_h, canvas - dy)
    # Destination paste
    dx0 = max(0, dx)
    dy0 = max(0, dy)
    if sx1 > sx0 and sy1 > sy0:
        out[dy0:dy0 + (sy1 - sy0), dx0:dx0 + (sx1 - sx0)] = rgba[sy0:sy1, sx0:sx1]
    return out


def _normalize_one(
    rgba: np.ndarray,
    layer: str,
    canvas: int,
) -> np.ndarray:
    target = ANCHORS[layer]
    if layer == "expression":
        centroid = _alpha_centroid(rgba)
    else:
        # For overlay layers, use a layer-specific reference point:
        #   - mouth: bbox center
        #   - tail:  bbox-left mid (the attachment side)
        #   - ears:  bbox-bottom mid (the attachment line)
        bbox = _alpha_bbox(rgba)
        if bbox is None:
            centroid = None
        else:
            x0, y0, x1, y1 = bbox
            if layer == "mouth":
                centroid = ((x0 + x1) / 2, (y0 + y1) / 2)
            elif layer == "tail":
                centroid = (x0, (y0 + y1) / 2)
            elif layer == "ears":
                centroid = ((x0 + x1) / 2, y1)
            else:
                centroid = None
    if centroid is None:
        # Empty alpha: pad to canvas, leave as-is
        out = np.zeros((canvas, canvas, 4), dtype=rgba.dtype)
        h, w = rgba.shape[:2]
        out[:min(h, canvas), :min(w, canvas)] = rgba[:min(h, canvas), :min(w, canvas)]
        return out
    return _shift_to_anchor(rgba, centroid, target, canvas)


def run(cfg: Config, *, force: bool = False) -> dict:
    src_root = cfg.stage_dir("06_alpha")
    if not src_root.exists():
        raise FileNotFoundError(f"Alpha-matted sprites missing at {src_root}. Run `alpha` first.")

    out_root = cfg.stage_dir("07_normalized")
    out_root.mkdir(parents=True, exist_ok=True)

    canvas_size = cfg.canvas.sprite_size
    written: list[str] = []

    for layer_dir in sorted(src_root.iterdir()):
        if not layer_dir.is_dir():
            continue
        layer = layer_dir.name
        if layer not in ANCHORS:
            continue
        out_layer = out_root / layer
        out_layer.mkdir(parents=True, exist_ok=True)
        for png in sorted(layer_dir.glob("*.png")):
            target = out_layer / png.name
            if target.exists() and not force:
                written.append(str(target))
                continue
            img = Image.open(png).convert("RGBA")
            rgba = np.array(img)
            normalized = _normalize_one(rgba, layer, canvas_size)
            Image.fromarray(normalized, mode="RGBA").save(target, format="PNG")
            written.append(str(target))

    return {
        "output_dir": str(out_root),
        "sprite_count": len(written),
        "anchors": ANCHORS,
    }

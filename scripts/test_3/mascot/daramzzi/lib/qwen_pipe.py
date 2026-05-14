"""Qwen-Image diffusers pipeline loader, optionally with LoRA weights attached.

Module-level cached load — same process re-uses the pipeline across calls
within a single stage invocation. Across stages (separate docker runs) the
pipeline is reloaded from HF cache — that's fine, it's ~30s.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import torch
from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler
from PIL import Image


_PIPE: Optional[DiffusionPipeline] = None
_LORA_PATH: Optional[str] = None


def _device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def get_pipeline(
    base_model: str,
    lora_safetensors: Optional[Path] = None,
    dtype: torch.dtype = torch.float16,
) -> DiffusionPipeline:
    """Return a singleton Qwen-Image pipeline. Reloads if the LoRA path changed."""
    global _PIPE, _LORA_PATH

    requested = str(lora_safetensors) if lora_safetensors else None
    if _PIPE is not None and _LORA_PATH == requested:
        return _PIPE

    device = _device()
    if device == "cpu":
        dtype = torch.float32

    pipe = DiffusionPipeline.from_pretrained(
        base_model,
        torch_dtype=dtype,
    )
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to(device)
    pipe.set_progress_bar_config(disable=True)

    if lora_safetensors is not None:
        pipe.load_lora_weights(str(lora_safetensors))

    _PIPE = pipe
    _LORA_PATH = requested
    return pipe


def generate(
    pipe: DiffusionPipeline,
    *,
    positive: str,
    negative: str,
    seed: int,
    width: int = 1024,
    height: int = 1024,
    steps: int = 50,
    guidance: float = 7.5,
) -> Image.Image:
    device = _device()
    generator = torch.Generator(device=device if device != "mps" else "cpu").manual_seed(seed)
    result = pipe(
        prompt=positive,
        negative_prompt=negative,
        width=width,
        height=height,
        num_inference_steps=steps,
        guidance_scale=guidance,
        generator=generator,
    )
    return result.images[0]

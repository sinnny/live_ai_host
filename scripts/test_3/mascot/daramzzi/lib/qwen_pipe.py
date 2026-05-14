"""Qwen-Image diffusers pipeline loader, optionally with LoRA weights attached.

Qwen-Image is a 20B-param MMDiT — the bf16 weights total ~40 GB, which
exceeds the activation headroom on a 48 GB L40S/A6000 if naively `.to('cuda')`.
We rely on `enable_model_cpu_offload()`: weights live in system RAM, only the
currently-active submodule is on GPU. Peak VRAM with offload is ~6-10 GB.
Inference is ~2-3x slower per call vs full-GPU load, which is acceptable for
our 24-sprite batch (adds ~5 min total).

Module-level cached load — same process re-uses the pipeline across calls
within a single stage invocation. Across stages (separate process invocations)
the pipeline is reloaded from HF cache — load takes ~60-90s with offload.
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
    dtype: torch.dtype = torch.bfloat16,
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
        trust_remote_code=True,
    )
    # Some Qwen-Image releases ship a non-DPM scheduler; only swap if the
    # current scheduler exposes a config we can re-instantiate from.
    try:
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    except Exception:  # noqa: BLE001 — defensive scheduler swap
        pass

    pipe.set_progress_bar_config(disable=True)

    # LoRA must load before offload — load_lora_weights walks the module tree
    # and applying it after the offload hooks fight each other.
    if lora_safetensors is not None:
        pipe.load_lora_weights(str(lora_safetensors))

    if device == "cuda":
        # Cuts peak VRAM from ~44 GB to ~6-10 GB. Submodules stream to GPU
        # one at a time during the forward pass.
        pipe.enable_model_cpu_offload()
        # Further reduce VAE peak memory at decode time.
        for attr in ("enable_vae_tiling", "enable_vae_slicing"):
            try:
                getattr(pipe, attr)()
            except (AttributeError, NotImplementedError):
                pass
        # Attention slicing helps too on 48 GB cards; safe to enable.
        try:
            pipe.enable_attention_slicing()
        except (AttributeError, NotImplementedError):
            pass
    else:
        pipe = pipe.to(device)

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
    # Generator must live on CPU when using model_cpu_offload — the input-side
    # randomness is consumed before the first submodule moves to GPU.
    generator = torch.Generator(device="cpu").manual_seed(seed)
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

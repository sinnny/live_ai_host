"""Stage 5.1 — Brief expansion.

Per FSD §5.1 (revised 2026-05-13): no runtime Claude API call. The static
`prompts.json` is the source of truth. This stage validates the file exists,
parses cleanly, and copies it into the work directory for provenance.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .config import Config
from .prompts import load_prompts


def run(cfg: Config) -> dict:
    src = Path(__file__).resolve().parent.parent / "prompts.json"
    if not src.exists():
        raise FileNotFoundError(
            f"Static prompts.json missing at {src}. "
            "See docs/phase_0_v2/README.md §'Static artifacts'."
        )

    book = load_prompts(src)
    expected = len(cfg.all_sprite_states())
    actual = len(book.all_sprites())
    if actual != expected:
        raise ValueError(
            f"prompts.json contains {actual} sprites but config expects {expected}. "
            "Check sprite_layers.*.states alignment."
        )

    out_dir = cfg.stage_dir("01_brief")
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / "prompts.json"
    shutil.copyfile(src, dst)

    # Snapshot a flattened view for downstream stages
    flat = {
        "qwen_image_settings": book.qwen_image_settings,
        "sprites": [
            {
                "index": sp.index,
                "layer": sp.layer,
                "state": sp.state,
                "positive": sp.positive,
                "negative": sp.negative,
            }
            for sp in book.all_sprites()
        ],
    }
    (out_dir / "flattened.json").write_text(
        json.dumps(flat, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {
        "source": str(src),
        "output": str(dst),
        "sprite_count": actual,
    }

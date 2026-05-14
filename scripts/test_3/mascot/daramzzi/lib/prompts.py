"""Prompt assembly from the static prompts.json.

The runtime composition rule (per prompts.json `composition_note`):
    final_positive = base.prompt + ' ' + layer.framing_instruction + ' ' + sprite.prompt_suffix
    final_negative = base.negative_prompt + (', ' + layer.framing_negative_extra if present)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SpritePrompt:
    layer: str
    state: str
    index: int
    positive: str
    negative: str
    qwen_settings: dict


@dataclass(frozen=True)
class PromptBook:
    seed_prompt: SpritePrompt
    by_layer_state: dict[tuple[str, str], SpritePrompt]
    qwen_image_settings: dict
    base_positive: str
    base_negative: str

    def get(self, layer: str, state: str) -> SpritePrompt:
        key = (layer, state)
        if key not in self.by_layer_state:
            raise KeyError(f"No prompt for layer={layer!r} state={state!r}")
        return self.by_layer_state[key]

    def all_sprites(self) -> list[SpritePrompt]:
        return list(self.by_layer_state.values())


def load_prompts(path: str | Path) -> PromptBook:
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    base_pos = data["base"]["prompt"]
    base_neg = data["base"]["negative_prompt"]
    qwen = data.get("qwen_image_settings", {})

    by_layer_state: dict[tuple[str, str], SpritePrompt] = {}
    layers = data["layers"]

    sprite_index = 0
    seed_prompt: SpritePrompt | None = None
    for layer_name in ("expression", "mouth", "tail", "ears"):
        layer = layers[layer_name]
        framing = layer.get("framing_instruction", "")
        neg_extra = layer.get("framing_negative_extra")
        for sprite in layer["sprites"]:
            state = sprite["state"]
            suffix = sprite["prompt_suffix"]
            positive = f"{base_pos} {framing} {suffix}".strip()
            negative = (
                f"{base_neg}, {neg_extra}".strip(", ") if neg_extra else base_neg
            )
            sp = SpritePrompt(
                layer=layer_name,
                state=state,
                index=sprite_index,
                positive=positive,
                negative=negative,
                qwen_settings=qwen,
            )
            by_layer_state[(layer_name, state)] = sp
            if layer_name == "expression" and state == "neutral":
                seed_prompt = sp
            sprite_index += 1

    if seed_prompt is None:
        raise ValueError("prompts.json must contain expression/neutral as the seed prompt")

    return PromptBook(
        seed_prompt=seed_prompt,
        by_layer_state=by_layer_state,
        qwen_image_settings=qwen,
        base_positive=base_pos,
        base_negative=base_neg,
    )

// Phase 0 simplified rig: expression layer only.
//
// The FSD specifies a 4-layer composite (expression z=0, tail z=1, ears z=2,
// mouth z=3) where the overlay layers are isolated body-part sprites. In
// practice, generating those isolated overlay sprites with current OSS image
// gen (Qwen-Image ± LoRA) is unreliable — the prompts get overridden by
// full-character training distribution. Until we have a working overlay
// pipeline (Phase 1 polish or different image-gen approach), we render only
// the expression layer and drive lip-sync by swapping between two expression
// sprites at the timeline level.
//
// To restore the full 4-layer composition later: set ORDER back to the FSD
// list and ensure the atlas's overlay layers are real isolated body parts.

import { SpriteLayer } from './sprite_layer.js';

const ORDER = [
  { name: 'expression', zOrder: 0, crossfadeKey: 'expression_ms' },
];

export class Puppet {
  constructor({ atlas, scene, canvasSize, characterPosition, characterScale, crossfade }) {
    this.atlas = atlas;
    this.layers = {};
    for (const { name, zOrder, crossfadeKey } of ORDER) {
      if (!atlas.layers[name]) continue;
      const layer = new SpriteLayer({
        name,
        atlas,
        anchor: atlas.layers[name].anchor,
        zOrder,
        canvasSize,
        characterPosition,
        characterScale,
        crossfadeMs: crossfade[crossfadeKey] ?? 200,
      });
      layer.addToScene(scene);
      this.layers[name] = layer;
    }
  }

  update(nowMs, states, motion) {
    for (const { name } of ORDER) {
      const layer = this.layers[name];
      if (!layer) continue;
      const desired = states[name];
      if (desired) layer.setState(desired, nowMs);
      layer.update(nowMs, motion);
    }
  }
}

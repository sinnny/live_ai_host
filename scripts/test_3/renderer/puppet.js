// Composes 4 layers (expression z=0, tail z=1, ears z=2, mouth z=3)
// per FSD renderer.md §5.2 composition order.

import { SpriteLayer } from './sprite_layer.js';

const ORDER = [
  { name: 'expression', zOrder: 0, crossfadeKey: 'expression_ms' },
  { name: 'tail',       zOrder: 1, crossfadeKey: 'tail_ms' },
  { name: 'ears',       zOrder: 2, crossfadeKey: 'ears_ms' },
  { name: 'mouth',      zOrder: 3, crossfadeKey: 'mouth_ms' },
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

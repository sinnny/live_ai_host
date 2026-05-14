// Loads atlas.png as a three.js texture + builds per-state UV regions.
//
// Atlas grid: atlas_columns × N rows of sprite_size px each. The renderer
// keeps a single Texture and per-layer/state UV rectangles; layers swap their
// UV at runtime instead of swapping textures.

import * as THREE from 'three';

const LAYER_ORDER = ['expression', 'tail', 'ears', 'mouth']; // composition z-order

export async function loadAtlas(textureUrl, atlasConfig) {
  const loader = new THREE.TextureLoader();
  const texture = await new Promise((resolve, reject) => {
    loader.load(textureUrl, resolve, undefined, reject);
  });
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.magFilter = THREE.LinearFilter;
  texture.minFilter = THREE.LinearFilter;
  texture.generateMipmaps = false;
  texture.needsUpdate = true;

  const cols = atlasConfig.atlas_columns;
  const spriteSize = atlasConfig.sprite_size;
  const atlasWidth = cols * spriteSize;
  // Rows: max y_index + 1 across all layers
  let maxRow = 0;
  for (const layer of Object.values(atlasConfig.layers)) {
    for (const state of Object.values(layer.states)) {
      maxRow = Math.max(maxRow, state.atlas_pos[1]);
    }
  }
  const rows = maxRow + 1;
  const atlasHeight = rows * spriteSize;

  const layers = {};
  for (const layerName of LAYER_ORDER) {
    const lc = atlasConfig.layers[layerName];
    if (!lc) continue;
    const states = {};
    for (const [stateName, stateCfg] of Object.entries(lc.states)) {
      const [col, row] = stateCfg.atlas_pos;
      const u0 = (col * spriteSize) / atlasWidth;
      const u1 = ((col + 1) * spriteSize) / atlasWidth;
      // three.js UV origin is bottom-left
      const v1 = 1 - (row * spriteSize) / atlasHeight;
      const v0 = 1 - ((row + 1) * spriteSize) / atlasHeight;
      states[stateName] = { u0, v0, u1, v1 };
    }
    layers[layerName] = {
      z_order: lc.z_order ?? 0,
      anchor: lc.anchor ?? { x: spriteSize / 2, y: spriteSize / 2 },
      states,
    };
  }

  return {
    texture,
    spriteSize,
    atlasWidth,
    atlasHeight,
    layers,
    defaultState: atlasConfig.default_state ?? {},
  };
}

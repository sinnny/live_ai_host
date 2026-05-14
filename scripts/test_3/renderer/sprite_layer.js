// A single layer: two textured planes (current + previous) for crossfade.
//
// Both planes share the same atlas texture; per-frame we update each plane's
// UV transform to point at the current/previous state's region, and ramp
// material opacity for crossfade.

import * as THREE from 'three';

export class SpriteLayer {
  constructor({ name, atlas, anchor, zOrder, canvasSize, characterPosition, characterScale, crossfadeMs }) {
    this.name = name;
    this.atlas = atlas;
    this.anchor = anchor; // {x, y} in atlas-canvas coords (1024 default)
    this.zOrder = zOrder;
    this.crossfadeMs = crossfadeMs;
    this.canvasSize = canvasSize;
    this.characterPosition = characterPosition;
    this.characterScale = characterScale;

    // Sprite world size scaled to canvas pixels — each sprite is sprite_size px
    // when characterScale == 1.0.
    const px = atlas.spriteSize * characterScale;
    this.spritePx = px;

    const geom = new THREE.PlaneGeometry(px, px);

    this.curr = this._makePlane(geom);
    this.prev = this._makePlane(geom);
    // initial: no previous
    this.prev.visible = false;

    this.currState = null;
    this.prevState = null;
    this.crossfadeStartMs = null;
  }

  _makePlane(geom) {
    const mat = new THREE.MeshBasicMaterial({
      map: this.atlas.texture.clone(),
      transparent: true,
      depthTest: false,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    // Each plane needs its own texture clone so we can set independent UV repeat/offset.
    mat.map.needsUpdate = true;
    return new THREE.Mesh(geom, mat);
  }

  addToScene(scene) {
    // Lay z by order (higher zOrder = on top).
    this.prev.position.z = this.zOrder * 0.01;
    this.curr.position.z = this.zOrder * 0.01 + 0.005;
    this.prev.renderOrder = this.zOrder * 2;
    this.curr.renderOrder = this.zOrder * 2 + 1;
    scene.add(this.prev);
    scene.add(this.curr);
  }

  _setUVForPlane(plane, region) {
    // Texture clones don't deep-copy GPU state cleanly across browsers, so we
    // emulate region selection with offset/repeat on a unit-mapped quad.
    const tex = plane.material.map;
    tex.repeat.set(region.u1 - region.u0, region.v1 - region.v0);
    tex.offset.set(region.u0, region.v0);
    tex.needsUpdate = true;
  }

  setState(newState, nowMs) {
    if (newState === this.currState) return;
    if (this.currState == null) {
      // first-time set: snap, no crossfade
      this.currState = newState;
      const region = this.atlas.layers[this.name].states[newState];
      if (!region) throw new Error(`Atlas missing ${this.name}/${newState}`);
      this._setUVForPlane(this.curr, region);
      this.curr.material.opacity = 1;
      return;
    }
    // Crossfade: previous = old curr, new curr = newState
    this.prevState = this.currState;
    this.currState = newState;
    const prevRegion = this.atlas.layers[this.name].states[this.prevState];
    const currRegion = this.atlas.layers[this.name].states[newState];
    if (!prevRegion || !currRegion) {
      throw new Error(`Atlas missing region for ${this.name}: ${this.prevState}|${newState}`);
    }
    this._setUVForPlane(this.prev, prevRegion);
    this._setUVForPlane(this.curr, currRegion);
    this.prev.visible = true;
    this.crossfadeStartMs = nowMs;
  }

  update(nowMs, offsets) {
    // Position both planes anchored at characterPosition with anchor-offset for this layer.
    // Atlas anchor is given in atlas-canvas coords (typical 1024px center=512,512).
    // We translate so the anchor lands on the character's screen position.
    const [cw, ch] = this.canvasSize;
    const cx = this.characterPosition.x + (offsets?.offset_x_px ?? 0);
    const cy = this.characterPosition.y + (offsets?.offset_y_px ?? 0);

    // The sprite plane is centered on its mesh; we need to position the plane
    // so that the in-sprite anchor lands at (cx, cy).
    const halfPx = this.spritePx / 2;
    const anchorScale = this.characterScale;
    const anchorX = (this.anchor?.x ?? this.atlas.spriteSize / 2) * anchorScale;
    const anchorY = (this.anchor?.y ?? this.atlas.spriteSize / 2) * anchorScale;
    // Three.js OrthoCamera here has y axis going up (left=0, right=w, top=h, bottom=0).
    const planeX = cx - anchorX + halfPx;
    const planeY = ch - (cy - anchorY + halfPx);

    this.curr.position.x = planeX;
    this.curr.position.y = planeY;
    this.prev.position.x = planeX;
    this.prev.position.y = planeY;

    // Crossfade ramp
    if (this.crossfadeStartMs != null) {
      const t = (nowMs - this.crossfadeStartMs) / this.crossfadeMs;
      if (t >= 1) {
        this.curr.material.opacity = 1;
        this.prev.material.opacity = 0;
        this.prev.visible = false;
        this.crossfadeStartMs = null;
      } else {
        const alpha = Math.max(0, Math.min(1, t));
        this.curr.material.opacity = alpha;
        this.prev.material.opacity = 1 - alpha;
      }
    }
  }
}

// Procedural idle motion — Y-sine + X-jitter. Blink left as a TODO until
// the atlas ships an explicit blink frame (per FSD renderer.md §5.5).

function pseudoNoise(t) {
  // Cheap deterministic pseudo-noise for X jitter.
  const s = Math.sin(t * 12.9898) * 43758.5453;
  return (s - Math.floor(s)) * 2 - 1;
}

export class IdleMotion {
  constructor(cfg) {
    this.cfg = cfg;
    this._lastBlinkMs = 0;
    this._nextBlinkMs = (cfg.blink_period_ms_min + cfg.blink_period_ms_max) / 2;
  }

  tick(tMs) {
    const ay = this.cfg.y_sine_amplitude_px ?? 0;
    const py = this.cfg.y_sine_period_ms ?? 2400;
    const ax = this.cfg.x_jitter_amplitude_px ?? 0;

    const offset_y_px = Math.sin((2 * Math.PI * tMs) / py) * ay;
    const offset_x_px = pseudoNoise(tMs * 0.001) * ax;

    // blink_alpha not used yet — atlas needs blink sprite first.
    return { offset_y_px, offset_x_px, blink_alpha: 0 };
  }
}

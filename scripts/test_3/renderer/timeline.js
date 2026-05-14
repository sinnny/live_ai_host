// Script + alignment → per-frame state machine.
//
// At time t (ms since clip start):
//   expression/tail/ears come from the current segment (or default)
//   mouth comes from the alignment frame containing t

export class Timeline {
  constructor({ script, alignment, ttsManifest }) {
    this.script = script;
    this.alignment = alignment;
    this.ttsManifest = ttsManifest;
    this.defaultState = script.default_state ?? {};

    // Pre-compute segment windows in absolute clip time.
    // The TTS manifest has start_ms_in_full + duration_ms per segment.
    this.segments = [];
    const ttsSegments = ttsManifest.segments ?? [];
    for (let i = 0; i < this.script.segments.length; i++) {
      const seg = this.script.segments[i];
      const tts = ttsSegments[i];
      if (!tts) {
        throw new Error(`script segment ${i} has no matching TTS manifest entry`);
      }
      const startMs = tts.start_ms_in_full;
      const endMs = startMs + tts.duration_ms;
      this.segments.push({
        idx: i,
        startMs,
        endMs,
        nextStartMs: endMs + (tts.pause_after_ms ?? 0),
        expression: seg.expression ?? this.defaultState.expression ?? 'neutral',
        tail: seg.tail ?? this.defaultState.tail ?? 'relaxed',
        ears: seg.ears ?? this.defaultState.ears ?? 'up',
      });
    }

    // Sort alignment frames for binary lookup
    this.alignmentFrames = alignment.frames ?? [];
  }

  _segmentAt(timeMs) {
    // Linear scan is fine for <200 segments; binary search if it grows.
    for (let i = 0; i < this.segments.length; i++) {
      const s = this.segments[i];
      if (timeMs < s.nextStartMs) {
        // We may be mid-segment or in the gap-after-segment.
        // For expression/tail/ears, hold the segment's state through the pause.
        return s;
      }
    }
    // Past last segment — hold final
    return this.segments[this.segments.length - 1] ?? null;
  }

  _visemeAt(timeMs) {
    const frames = this.alignmentFrames;
    if (!frames.length) return 'closed';
    // Binary search
    let lo = 0, hi = frames.length - 1;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      const f = frames[mid];
      if (timeMs < f.start_ms) hi = mid - 1;
      else if (timeMs >= f.end_ms) lo = mid + 1;
      else return f.viseme;
    }
    return 'closed';
  }

  statesAt(timeMs) {
    const seg = this._segmentAt(timeMs);
    return {
      expression: seg ? seg.expression : (this.defaultState.expression ?? 'neutral'),
      tail: seg ? seg.tail : (this.defaultState.tail ?? 'relaxed'),
      ears: seg ? seg.ears : (this.defaultState.ears ?? 'up'),
      mouth: this._visemeAt(timeMs),
    };
  }

  totalDurationMs() {
    if (!this.segments.length) return 0;
    const last = this.segments[this.segments.length - 1];
    return last.nextStartMs;
  }
}

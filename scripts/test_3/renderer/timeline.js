// Script + alignment → per-frame state machine.
//
// Phase 0 simplified rig — expression layer only:
//   - When the audio is silent or low-amplitude (alignment viseme == 'closed'),
//     show the script segment's intended expression (neutral, panic, etc.).
//   - When the audio is speaking (any non-'closed' viseme), override to a
//     "talking" expression with an open mouth (default: 'laughing'). This
//     produces a PNGTuber-style amplitude-driven lip-sync.
//
// To restore the full 4-layer rig: read mouth from _visemeAt() into a
// separate `mouth` field on statesAt()'s return value, and re-instantiate
// the tail/ears/mouth layers in puppet.js's ORDER list.

const DEFAULT_TALKING_EXPRESSION = 'laughing';

// Expressions that already have an open mouth in the atlas — when the
// segment's intended expression is one of these, we DON'T override during
// speech (it'd be a downgrade). Source: docs/characters/daramzzi.md §4.4
// + visual inspection of the generated atlas.
const OPEN_MOUTH_EXPRESSIONS = new Set([
  'panic',
  'pleading',
  'victory',
  'sleepy',
  'confused',
  'laughing',
]);

export class Timeline {
  constructor({ script, alignment, ttsManifest, talkingExpression = DEFAULT_TALKING_EXPRESSION }) {
    this.script = script;
    this.alignment = alignment;
    this.ttsManifest = ttsManifest;
    this.defaultState = script.default_state ?? {};
    this.talkingExpression = talkingExpression;

    // Pre-compute segment windows in absolute clip time.
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
        // Tail/ears retained on segment for forward-compat with the full rig,
        // but Phase 0 puppet.js doesn't render them.
        tail: seg.tail ?? this.defaultState.tail ?? 'relaxed',
        ears: seg.ears ?? this.defaultState.ears ?? 'up',
      });
    }

    this.alignmentFrames = alignment.frames ?? [];
  }

  _segmentAt(timeMs) {
    for (let i = 0; i < this.segments.length; i++) {
      const s = this.segments[i];
      if (timeMs < s.nextStartMs) {
        return s;
      }
    }
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
    const baseExpression = seg
      ? seg.expression
      : (this.defaultState.expression ?? 'neutral');
    const viseme = this._visemeAt(timeMs);

    // Amplitude-driven mouth override: if the audio is speaking (non-'closed'
    // viseme) AND the segment's expression doesn't already have an open mouth,
    // swap to the talking expression for the duration of the open-mouth frame.
    const isSpeaking = viseme && viseme !== 'closed';
    const expression = (isSpeaking && !OPEN_MOUTH_EXPRESSIONS.has(baseExpression))
      ? this.talkingExpression
      : baseExpression;

    return { expression };
  }

  totalDurationMs() {
    if (!this.segments.length) return 0;
    const last = this.segments[this.segments.length - 1];
    return last.nextStartMs;
  }
}

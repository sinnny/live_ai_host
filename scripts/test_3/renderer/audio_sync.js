// Offline-render mode: audio is not played in the browser. Frames are stepped
// deterministically by the Python launcher (frame_idx / fps * 1000 = audio_ms).
//
// This module is retained for FSD §5 module layout parity; the live mode
// (test_3) re-enters here and drives audio via Web Audio API as the timing
// master.

export function audioMsForFrame(frameIdx, fps) {
  return (frameIdx * 1000) / fps;
}

export function frameCountFor(durationMs, fps) {
  return Math.ceil((durationMs * fps) / 1000);
}

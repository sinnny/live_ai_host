// R-Solo realtime renderer prototype.
//
// Verification goals (per docs/phase_0_v2/realtime_interaction_plan.md §4.3):
//   1. Swap latency <100 ms
//   2. Crossfade visually clean
//   3. Audio-only track + visual swap reads as "responding"
//   4. Static idle (seed.png) ↔ talking video transition acceptable
//
// State machine: { idle } ⇄ { talking }
//   idle    → talking : start audio + play talking video + fade body.talking ON
//   talking → idle    : stop audio + pause+reset video + fade body.talking OFF
//
// Lip-sync precision is intentionally not a goal here — the talking loop is generic
// and not phoneme-matched to the audio. We're testing whether mouth-moves-when-speaking
// (loose) and mouth-shut-when-silent (strict) reads as "live" to viewers.

const stage     = document.body;
const layerTalk = document.getElementById('layer-talk');
const btnTalk   = document.getElementById('btn-talk');
const btnIdle   = document.getElementById('btn-idle');
const btnSpeak  = document.getElementById('btn-speak');
const ttsText   = document.getElementById('tts-text');
const ttsVoice  = document.getElementById('tts-voice');
const fadeMs    = document.getElementById('fade-ms');
const statusEl  = document.getElementById('status');

let audioCtx = null;
let audioBuffer = null;
let audioSource = null;
let state = 'idle';

// load TTS-stand-in audio (founder's recording for prototype phase)
async function loadAudio() {
  audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  const resp = await fetch('./assets/voice.wav');
  const arr = await resp.arrayBuffer();
  audioBuffer = await audioCtx.decodeAudioData(arr);
  log('audio loaded', `${audioBuffer.duration.toFixed(2)}s, ${audioBuffer.sampleRate}Hz`);
}

function setFadeVar() {
  document.documentElement.style.setProperty('--crossfade-ms', fadeMs.value);
}
fadeMs.addEventListener('input', setFadeVar);

function log(...args) {
  const msg = args.map(a => typeof a === 'string' ? a : JSON.stringify(a)).join('  ');
  const t = new Date().toISOString().slice(11, 23);
  statusEl.textContent = `[${t}] ${msg}\n` + statusEl.textContent;
  // truncate to keep readable
  const lines = statusEl.textContent.split('\n');
  if (lines.length > 12) statusEl.textContent = lines.slice(0, 12).join('\n');
}

function goTalking() {
  if (state !== 'idle') return;
  state = 'talking';
  const t0 = performance.now();

  // 1. unlock audio context if needed (autoplay policy)
  if (audioCtx.state === 'suspended') audioCtx.resume();

  // 2. start audio playback
  audioSource = audioCtx.createBufferSource();
  audioSource.buffer = audioBuffer;
  audioSource.connect(audioCtx.destination);
  audioSource.onended = () => {
    // audio finished naturally → return to idle
    if (state === 'talking') {
      log('audio ended naturally → idle');
      goIdle();
    }
  };
  audioSource.start();

  // 3. play talking video (already preloaded + looping muted)
  layerTalk.currentTime = 0;
  layerTalk.play().catch(e => log('warn: video.play() rejected', e.message));

  // 4. crossfade (CSS-driven via body.talking class)
  stage.classList.add('talking');

  const t1 = performance.now();
  log(`SWAP idle → talking | trigger→start latency = ${(t1 - t0).toFixed(1)}ms`);

  btnTalk.disabled = true;
  btnIdle.disabled = false;
}

function goIdle() {
  if (state !== 'talking') return;
  state = 'idle';
  const t0 = performance.now();

  // 1. stop audio
  try {
    if (audioSource) {
      audioSource.onended = null;  // suppress re-entrant goIdle
      audioSource.stop();
    }
  } catch (e) { /* already stopped */ }

  // 2. pause + reset video
  layerTalk.pause();
  layerTalk.currentTime = 0;

  // 3. crossfade back (body.talking class removed)
  stage.classList.remove('talking');

  const t1 = performance.now();
  log(`SWAP talking → idle | trigger→stop latency = ${(t1 - t0).toFixed(1)}ms`);

  btnTalk.disabled = false;
  btnIdle.disabled = true;
}

btnTalk.addEventListener('click', goTalking);
btnIdle.addEventListener('click', goIdle);

// ─────────────────────────────────────────────────────────────
// Web Speech API path — type Korean text, hear TTS
// Decouples audio source from prerecorded voice.wav so we can test
// "user inputs text → renderer swap to talking + speak it" flow.
// macOS has built-in ko-KR voices (Yuna etc.); zero cost, <1s latency.
// ─────────────────────────────────────────────────────────────
let currentUtterance = null;

function populateVoices() {
  const voices = speechSynthesis.getVoices();
  const korean = voices.filter(v => v.lang.startsWith('ko'));
  ttsVoice.innerHTML = '<option value="">(자동)</option>';
  korean.forEach((v, i) => {
    const opt = document.createElement('option');
    opt.value = v.name;
    opt.textContent = `${v.name} (${v.lang})${v.default ? ' ★' : ''}`;
    ttsVoice.appendChild(opt);
  });
  log(`available Korean voices: ${korean.length}`);
}

function speakViaTTS() {
  const text = ttsText.value.trim();
  if (!text) { log('TTS: no text'); return; }

  // Cancel any in-flight speech
  if (speechSynthesis.speaking) speechSynthesis.cancel();
  if (state === 'talking') goIdle();

  const u = new SpeechSynthesisUtterance(text);
  u.lang = 'ko-KR';
  u.rate = 1.0;
  u.pitch = 1.0;

  const selectedName = ttsVoice.value;
  if (selectedName) {
    const voice = speechSynthesis.getVoices().find(v => v.name === selectedName);
    if (voice) u.voice = voice;
  }

  const tQueue = performance.now();
  u.onstart = () => {
    const tStart = performance.now();
    log(`TTS start (queue→start ${(tStart - tQueue).toFixed(0)}ms): "${text.slice(0, 30)}…"`);
    // Trigger talking swap on actual audio start (not queue time)
    if (state === 'idle') {
      state = 'talking';
      layerTalk.currentTime = 0;
      layerTalk.play().catch(()=>{});
      stage.classList.add('talking');
      btnTalk.disabled = true;
      btnIdle.disabled = false;
    }
  };
  u.onend = () => {
    log('TTS end → idle');
    goIdle();
  };
  u.onerror = (e) => {
    log(`TTS error: ${e.error}`);
    goIdle();
  };

  currentUtterance = u;
  speechSynthesis.speak(u);
  log(`TTS queued (text: ${text.length} chars)`);
}

btnSpeak.addEventListener('click', speakViaTTS);
ttsText.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    speakViaTTS();
  }
});

// Voices load asynchronously in most browsers
if (typeof speechSynthesis !== 'undefined') {
  populateVoices();
  speechSynthesis.onvoiceschanged = populateVoices;
}

// keyboard shortcuts (ignore when typing in text input)
document.addEventListener('keydown', (e) => {
  if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT')) return;
  if (e.key === ' ' || e.key === 'Enter') {
    e.preventDefault();
    state === 'idle' ? goTalking() : goIdle();
  }
});

// boot
(async () => {
  log('booting…');
  setFadeVar();
  try {
    await loadAudio();
    log('ready — press Space / Enter or click button to talk');
  } catch (e) {
    log('ERROR loading audio:', e.message);
  }
})();

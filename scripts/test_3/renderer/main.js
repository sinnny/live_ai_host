// Sprite-puppet renderer entry point.
// Headless-Chrome-friendly: every interaction is via window.* hooks the
// Playwright launcher invokes. Audio is never played — timing is supplied
// externally as ms-since-clip-start.

import * as THREE from 'three';
import { loadAtlas } from './atlas_loader.js';
import { Timeline } from './timeline.js';
import { Puppet } from './puppet.js';
import { IdleMotion } from './idle_motion.js';

const statusEl = document.getElementById('status');
const canvas = document.getElementById('stage');
let renderer, scene, camera, puppet, timeline, idle, config;

function setStatus(s) { statusEl.textContent = s; }

async function fetchJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`fetch ${url} → ${r.status}`);
  return r.json();
}

async function fetchTextureBlob(url) {
  // We hand the blob URL to three.js's TextureLoader for predictable decoding.
  const r = await fetch(url);
  if (!r.ok) throw new Error(`fetch ${url} → ${r.status}`);
  const blob = await r.blob();
  return URL.createObjectURL(blob);
}

window.bootRender = async function(inputs) {
  // inputs = {
  //   atlasPngUrl, atlasConfigUrl, scriptUrl, alignmentUrl, ttsManifestUrl,
  //   rendererConfig, audioDurationMs
  // }
  setStatus('boot: loading inputs');

  config = inputs.rendererConfig;
  const [w, h] = config.resolution;

  // Renderer
  renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    preserveDrawingBuffer: true, // so screenshot captures latest frame
    alpha: false,
  });
  renderer.setPixelRatio(1);
  renderer.setSize(w, h, false);
  renderer.setClearColor(new THREE.Color(config.background_color));

  scene = new THREE.Scene();
  camera = new THREE.OrthographicCamera(0, w, h, 0, -1000, 1000);
  camera.position.z = 10;

  // Load assets
  const atlasUrl = await fetchTextureBlob(inputs.atlasPngUrl);
  const atlasCfg = await fetchJSON(inputs.atlasConfigUrl);
  const script = await fetchJSON(inputs.scriptUrl);
  const alignment = await fetchJSON(inputs.alignmentUrl);
  const ttsManifest = await fetchJSON(inputs.ttsManifestUrl);

  setStatus('boot: building atlas + puppet');
  const atlas = await loadAtlas(atlasUrl, atlasCfg);

  puppet = new Puppet({
    atlas,
    scene,
    canvasSize: [w, h],
    characterPosition: config.character_position,
    characterScale: config.character_scale,
    crossfade: config.crossfade,
  });

  timeline = new Timeline({ script, alignment, ttsManifest });
  idle = new IdleMotion(config.idle_motion);

  setStatus('boot: ready');
  window.__renderReady = true;
};

window.renderFrame = function(timeMs) {
  if (!puppet || !timeline) throw new Error('renderFrame called before bootRender');
  const states = timeline.statesAt(timeMs);
  const motion = idle.tick(timeMs);
  puppet.update(timeMs, states, motion);
  renderer.render(scene, camera);
};

window.shutdown = function() {
  setStatus('shutdown');
  if (renderer) renderer.dispose();
};

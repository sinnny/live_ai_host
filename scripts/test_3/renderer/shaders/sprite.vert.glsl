// Standard three.js sprite vertex pass-through.
// We use MeshBasicMaterial in the prototype, so this file is reserved for a
// future custom-shader path (e.g. when GPU-side crossfade outperforms the
// dual-plane approach in sprite_layer.js).
//
// Inputs:
//   position, uv (provided by PlaneGeometry)
// Outputs:
//   vUv — texture coordinates for the fragment stage

varying vec2 vUv;

void main() {
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}

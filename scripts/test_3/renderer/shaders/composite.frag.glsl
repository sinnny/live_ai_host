// Reference composite fragment shader. The prototype renderer uses MeshBasicMaterial
// per-layer with material.opacity-driven crossfade in sprite_layer.js, which is
// sufficient for the four-layer stack. This shader is reserved for the production
// path (test_3+) when we move to a single full-screen quad with all four layers
// sampled and blended in one pass.
//
// Inputs:
//   uExpression / uTail / uEars / uMouth — atlas region textures (or atlas + per-layer UV)
//   uExpressionAlpha / etc. — per-layer crossfade alpha
// Output:
//   gl_FragColor — composited pixel

varying vec2 vUv;
uniform sampler2D uAtlas;
uniform vec4 uExpressionUV;   // (u0, v0, u1, v1)
uniform vec4 uTailUV;
uniform vec4 uEarsUV;
uniform vec4 uMouthUV;
uniform vec4 uPrevExpressionUV;
uniform vec4 uPrevTailUV;
uniform vec4 uPrevEarsUV;
uniform vec4 uPrevMouthUV;
uniform float uExpressionAlpha;
uniform float uTailAlpha;
uniform float uEarsAlpha;
uniform float uMouthAlpha;
uniform vec3 uBackground;

vec4 sampleRegion(vec4 region, vec2 uv) {
  vec2 sampledUV = vec2(
    mix(region.x, region.z, uv.x),
    mix(region.y, region.w, uv.y)
  );
  return texture2D(uAtlas, sampledUV);
}

vec4 blendOver(vec4 base, vec4 over) {
  float outA = over.a + base.a * (1.0 - over.a);
  vec3 outRGB = (over.rgb * over.a + base.rgb * base.a * (1.0 - over.a)) / max(outA, 1e-5);
  return vec4(outRGB, outA);
}

void main() {
  vec4 expr = mix(sampleRegion(uPrevExpressionUV, vUv), sampleRegion(uExpressionUV, vUv), uExpressionAlpha);
  vec4 tail = mix(sampleRegion(uPrevTailUV, vUv),       sampleRegion(uTailUV, vUv),       uTailAlpha);
  vec4 ears = mix(sampleRegion(uPrevEarsUV, vUv),       sampleRegion(uEarsUV, vUv),       uEarsAlpha);
  vec4 mouth = mix(sampleRegion(uPrevMouthUV, vUv),     sampleRegion(uMouthUV, vUv),      uMouthAlpha);

  vec4 acc = vec4(uBackground, 1.0);
  acc = blendOver(acc, expr);
  acc = blendOver(acc, tail);
  acc = blendOver(acc, ears);
  acc = blendOver(acc, mouth);
  gl_FragColor = acc;
}

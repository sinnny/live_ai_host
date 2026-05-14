// Frame capture utility. The Python launcher uses page.screenshot() for
// reliable PNG dumps; this helper exists so the in-page code can also export
// a data URL on demand (useful for debugging in non-headless mode).

export function canvasToBlob(canvas, type = 'image/png') {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (!blob) reject(new Error('canvas.toBlob returned null'));
      else resolve(blob);
    }, type);
  });
}

export async function canvasToDataUrl(canvas, type = 'image/png') {
  return canvas.toDataURL(type);
}

"""Headless-Chrome launcher for the three.js sprite-puppet renderer.

Drives `scripts/test_3/renderer/index.html` via Playwright. Posts inputs,
steps the page frame-by-frame, captures each frame as PNG.
"""

from __future__ import annotations

import asyncio
import json
import math
import shutil
import sys
from pathlib import Path

import click


RENDERER_DIR = Path(__file__).resolve().parents[1] / "renderer"


def _ensure_pathlike(p: str) -> Path:
    return Path(p).expanduser().resolve()


async def _serve_and_render(
    atlas_dir: Path,
    script_path: Path,
    audio_path: Path,
    alignment_path: Path,
    tts_manifest_path: Path,
    renderer_config_path: Path,
    frames_dir: Path,
    fps: int,
) -> dict:
    from playwright.async_api import async_playwright

    atlas_png = atlas_dir / "atlas.png"
    atlas_cfg = atlas_dir / "config.json"
    for p in (atlas_png, atlas_cfg, script_path, audio_path, alignment_path, tts_manifest_path, renderer_config_path):
        if not p.exists():
            raise FileNotFoundError(f"Required input missing: {p}")

    # Stage a flat working directory the headless browser can serve from.
    work = frames_dir.parent / "_renderer_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)

    # Copy renderer assets
    for src in RENDERER_DIR.glob("**/*"):
        if not src.is_file():
            continue
        rel = src.relative_to(RENDERER_DIR)
        dst = work / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)

    # Stage inputs
    shutil.copyfile(atlas_png, work / "atlas.png")
    shutil.copyfile(atlas_cfg, work / "atlas_config.json")
    shutil.copyfile(script_path, work / "script.json")
    shutil.copyfile(alignment_path, work / "alignment.json")
    shutil.copyfile(tts_manifest_path, work / "tts_manifest.json")
    shutil.copyfile(renderer_config_path, work / "renderer_config.json")

    rcfg = json.loads(renderer_config_path.read_text(encoding="utf-8"))
    width, height = rcfg["resolution"]
    tts_manifest = json.loads(tts_manifest_path.read_text(encoding="utf-8"))
    duration_ms = tts_manifest["total_duration_ms"]
    total_frames = int(math.ceil((duration_ms * fps) / 1000))

    frames_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            args=["--no-sandbox", "--disable-dev-shm-usage", "--font-render-hinting=none"],
        )
        context = await browser.new_context(viewport={"width": width, "height": height})
        page = await context.new_page()

        # Serve the staged directory via a tiny in-process file server.
        # Playwright supports file:// loads but cross-file fetch is restricted;
        # easiest reliable path is to use route() to inject responses.
        async def handle(route, request):
            url = request.url
            # External CDN requests (three.js from unpkg, etc.) bypass our
            # in-process file server. Without this, the route handler would
            # try to find these as local files and return 404, breaking the
            # ESM import map.
            EXTERNAL_HOSTS = ("unpkg.com", "cdn.jsdelivr.net", "cdn.skypack.dev",
                              "esm.sh", "cdn.cloudflare.com")
            if any(h in url for h in EXTERNAL_HOSTS):
                await route.continue_()
                return
            rel = url.split("/", 3)[-1] if "://" in url else url
            # Normalize to a file under `work`
            local = work / Path(rel).name if "/" not in rel else work / rel
            if not local.exists():
                # Fallback: try basename
                local = work / Path(rel).name
            if not local.exists():
                await route.fulfill(status=404, body=f"not found: {rel}")
                return
            ctype = (
                "text/html" if local.suffix == ".html"
                else "application/javascript" if local.suffix in (".js", ".mjs")
                else "application/json" if local.suffix == ".json"
                else "image/png" if local.suffix == ".png"
                else "audio/wav" if local.suffix == ".wav"
                else "application/octet-stream"
            )
            await route.fulfill(status=200, content_type=ctype, body=local.read_bytes())

        await context.route("**/*", handle)

        # Pipe page console messages + JS errors to our stderr so failures
        # are visible in render.log without attaching DevTools.
        page.on("console", lambda msg: print(f"[browser:{msg.type}] {msg.text}", flush=True))
        page.on("pageerror", lambda err: print(f"[browser:pageerror] {err}", flush=True))

        await page.goto("https://renderer.local/index.html", wait_until="domcontentloaded")

        # ESM module imports (incl. three.js from unpkg) finish AFTER
        # DOMContentLoaded. Wait for main.js to actually define window.bootRender
        # before we try to invoke it.
        await page.wait_for_function(
            "typeof window.bootRender === 'function'", timeout=60_000
        )

        # Boot the renderer
        await page.evaluate(
            "(args) => window.bootRender(args)",
            {
                "atlasPngUrl": "atlas.png",
                "atlasConfigUrl": "atlas_config.json",
                "scriptUrl": "script.json",
                "alignmentUrl": "alignment.json",
                "ttsManifestUrl": "tts_manifest.json",
                "rendererConfig": rcfg,
                "audioDurationMs": duration_ms,
            },
        )
        await page.wait_for_function("window.__renderReady === true", timeout=60_000)

        # Step + screenshot per frame
        for i in range(total_frames):
            time_ms = (i * 1000) / fps
            await page.evaluate("(t) => window.renderFrame(t)", time_ms)
            frame_path = frames_dir / f"frame_{i:05d}.png"
            await page.screenshot(
                path=str(frame_path),
                clip={"x": 0, "y": 0, "width": width, "height": height},
                omit_background=False,
                type="png",
            )

        await context.close()
        await browser.close()

    return {
        "frames_dir": str(frames_dir),
        "frame_count": total_frames,
        "duration_ms": duration_ms,
        "fps": fps,
    }


@click.command()
@click.option("--atlas-dir", required=True, type=click.Path(file_okay=False))
@click.option("--script", "script_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--audio", "audio_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--alignment", "alignment_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--tts-manifest", "tts_manifest_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--frames-dir", required=True, type=click.Path(file_okay=False))
@click.option("--renderer-config", default=str(RENDERER_DIR / "renderer_config.json"), show_default=True,
              type=click.Path(exists=True, dir_okay=False))
@click.option("--fps", type=int, default=60, show_default=True)
def main(atlas_dir, script_path, audio_path, alignment_path, tts_manifest_path,
         frames_dir, renderer_config, fps):
    """Render a single clip's frames to PNG sequence."""
    result = asyncio.run(_serve_and_render(
        _ensure_pathlike(atlas_dir),
        _ensure_pathlike(script_path),
        _ensure_pathlike(audio_path),
        _ensure_pathlike(alignment_path),
        _ensure_pathlike(tts_manifest_path),
        _ensure_pathlike(renderer_config),
        _ensure_pathlike(frames_dir),
        fps,
    ))
    click.echo(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

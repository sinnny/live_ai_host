#!/usr/bin/env python3
"""Batch-submit Flux Kontext Dev generations to a local ComfyUI HTTP API.

Mirrors generate.py (PuLID) but for the Kontext template.

Reads:
- comfy_workflows/flux_kontext_template.json (API-format workflow)
- comfy_workflows/kontext_prompts.yaml (input_image + prompts × seeds)

For each (prompt, seed) combination:
- Patches the workflow's positive prompt / seed / input image nodes
- POST to /prompt
- Polls /history/<id> until done
- Downloads result image from /view
- Saves to outputs/kontext_test/<prompt_name>_seed<seed>.png

Idempotent: skips combinations whose output file already exists.
Resilient: per-image failures logged, batch continues.

Run inside the pod after bootstrap_kontext.sh has launched ComfyUI:
    python scripts/runpod/generate_kontext.py            # full run (25 images)
    python scripts/runpod/generate_kontext.py --limit 1  # smoke test (1 image)
    python scripts/runpod/generate_kontext.py --input-image project_photos/kim_3.jpeg
"""

import argparse
import copy
import json
import logging
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

COMFYUI_URL = "http://127.0.0.1:8188"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = PROJECT_ROOT / "comfy_workflows" / "flux_kontext_template.json"
PROMPTS_PATH = PROJECT_ROOT / "comfy_workflows" / "kontext_prompts.yaml"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "kontext_test"
CLIENT_ID = "live-ai-host-kontext-py"


def http_post_json(url: str, data: dict) -> dict:
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def http_get_json(url: str, timeout: int = 30) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read())


def http_get_bytes(url: str, timeout: int = 60) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.read()


def wait_for_comfyui_api(timeout: int = 120) -> None:
    log.info("Waiting for ComfyUI API at %s ...", COMFYUI_URL)
    start = time.time()
    while time.time() - start < timeout:
        try:
            http_get_json(f"{COMFYUI_URL}/system_stats", timeout=3)
            log.info("  API ready after %ds", int(time.time() - start))
            return
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            time.sleep(2)
    raise RuntimeError(f"ComfyUI API not ready after {timeout}s")


def submit_prompt(workflow_dict: dict) -> str:
    payload = {"prompt": workflow_dict, "client_id": CLIENT_ID}
    result = http_post_json(f"{COMFYUI_URL}/prompt", payload)
    if "prompt_id" not in result:
        raise RuntimeError(f"Unexpected /prompt response: {result}")
    return result["prompt_id"]


def wait_for_completion(prompt_id: str, timeout: int = 600) -> dict:
    start = time.time()
    while time.time() - start < timeout:
        try:
            history = http_get_json(f"{COMFYUI_URL}/history/{prompt_id}")
            if prompt_id in history:
                entry = history[prompt_id]
                status = entry.get("status", {})
                if status.get("status_str") == "error":
                    err_messages = status.get("messages", [])
                    raise RuntimeError(f"Generation errored: {err_messages}")
                if entry.get("outputs"):
                    return entry
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            pass
        time.sleep(2)
    raise TimeoutError(f"Generation {prompt_id} timed out after {timeout}s")


def download_first_image(history_entry: dict, save_path: Path) -> None:
    outputs = history_entry.get("outputs", {})
    for node_id, node_output in outputs.items():
        images = node_output.get("images", [])
        for img in images:
            url = (
                f"{COMFYUI_URL}/view?"
                f"filename={urllib.parse.quote(img['filename'])}"
                f"&subfolder={urllib.parse.quote(img.get('subfolder', ''))}"
                f"&type={urllib.parse.quote(img.get('type', 'output'))}"
            )
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(http_get_bytes(url))
            return
    raise RuntimeError(f"No output images found in history entry: {history_entry}")


def patch_workflow(template: dict, *, positive_prompt: str, seed: int, steps: int,
                   input_image: str, targets: dict) -> dict:
    wf = copy.deepcopy(template)
    wf[targets["positive_prompt_node_id"]]["inputs"]["text"] = positive_prompt
    wf[targets["seed_node_id"]]["inputs"]["seed"] = seed
    wf[targets["steps_node_id"]]["inputs"]["steps"] = steps
    wf[targets["input_image_node_id"]]["inputs"]["image"] = input_image
    return wf


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=None,
                    help="Run only the first N (prompt, seed) combinations. Useful for smoke tests.")
    ap.add_argument("--prompts", default=str(PROMPTS_PATH), help="Path to prompts YAML")
    ap.add_argument("--template", default=str(TEMPLATE_PATH), help="Path to workflow template JSON")
    ap.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Output directory")
    ap.add_argument("--input-image", default=None,
                    help="Override input_image from prompts YAML (e.g. project_photos/kim_3.jpeg)")
    ap.add_argument("--steps", type=int, default=None, help="Override steps (default from YAML)")
    ap.add_argument("--no-skip-existing", action="store_true",
                    help="Re-generate even if output file already exists (default: skip)")
    args = ap.parse_args()

    template_data = json.loads(Path(args.template).read_text())
    template = template_data["workflow"]
    targets = template_data["_template_targets"]
    log.info("Loaded template (%d nodes); targets: %s", len(template), targets)

    config = yaml.safe_load(Path(args.prompts).read_text())
    input_image = args.input_image or config["input_image"]
    prompts = config["prompts"]
    seeds = config["seeds"]
    steps = args.steps or config["steps"]

    work = [
        {
            "prompt_id": p["id"],
            "prompt_name": p["name"],
            "prompt_text": p["text"],
            "seed": seed,
            "steps": steps,
            "input_image": input_image,
        }
        for p in prompts
        for seed in seeds
    ]
    if args.limit:
        work = work[: args.limit]

    log.info("Total combinations: %d (%d prompts × %d seeds, steps=%d, input=%s%s)",
             len(work), len(prompts), len(seeds), steps, input_image,
             f", limited to first {args.limit}" if args.limit else "")

    wait_for_comfyui_api()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    successes = 0
    failures = 0
    skipped = 0
    overall_start = time.time()

    for i, item in enumerate(work, 1):
        out_path = output_dir / f"p{item['prompt_id']}_{item['prompt_name']}_seed{item['seed']}.png"
        if out_path.exists() and not args.no_skip_existing:
            log.info("[%d/%d] SKIP (exists): %s", i, len(work), out_path.name)
            skipped += 1
            continue

        log.info("[%d/%d] %s | seed=%d steps=%d", i, len(work),
                 item["prompt_name"], item["seed"], item["steps"])
        item_start = time.time()
        try:
            wf = patch_workflow(template,
                                positive_prompt=item["prompt_text"],
                                seed=item["seed"],
                                steps=item["steps"],
                                input_image=item["input_image"],
                                targets=targets)
            prompt_id = submit_prompt(wf)
            history = wait_for_completion(prompt_id)
            download_first_image(history, out_path)
            elapsed = time.time() - item_start
            log.info("  → %s (%.1fs)", out_path.relative_to(PROJECT_ROOT), elapsed)
            (out_path.with_suffix(".json")).write_text(json.dumps({
                "prompt_id": prompt_id,
                "positive_prompt": item["prompt_text"],
                "seed": item["seed"],
                "steps": item["steps"],
                "input_image": item["input_image"],
                "elapsed_sec": round(elapsed, 1),
            }, indent=2))
            successes += 1
        except Exception as e:
            log.error("  FAILED: %s", e, exc_info=False)
            failures += 1

    total_elapsed = time.time() - overall_start
    log.info("=" * 60)
    log.info("Done in %.0fs (%.1fmin). %d ok, %d skipped, %d failed.",
             total_elapsed, total_elapsed / 60, successes, skipped, failures)
    log.info("Outputs in: %s", output_dir)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

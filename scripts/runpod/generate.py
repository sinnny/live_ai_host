#!/usr/bin/env python3
"""Batch-submit PuLID-Flux generations to a local ComfyUI HTTP API.

Reads:
- comfy_workflows/pulid_flux_template.json (API-format workflow with patches)
- comfy_workflows/stage2_prompts.yaml (prompts × seeds × step counts)

For each (prompt, seed, step_count) combination:
- Patches the workflow's positive_prompt / seed / steps nodes
- POST to /prompt
- Polls /history/<id> until done
- Downloads result image from /view
- Saves to outputs/stage2_variants/<step_count>steps/<prompt_name>_<seed>.png

Idempotent: skips combinations whose output file already exists.
Resilient: per-image failures logged, batch continues.

Run inside the pod after bootstrap.sh has launched ComfyUI:
    python scripts/runpod/generate.py            # full run (50 images)
    python scripts/runpod/generate.py --limit 1  # smoke test (1 image)
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

# Conventions
COMFYUI_URL = "http://127.0.0.1:8188"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = PROJECT_ROOT / "comfy_workflows" / "pulid_flux_template.json"
PROMPTS_PATH = PROJECT_ROOT / "comfy_workflows" / "stage2_prompts.yaml"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "stage2_variants"
CLIENT_ID = "live-ai-host-generate-py"


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
    """Block until ComfyUI's /system_stats responds."""
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
    """Submit a workflow to /prompt. Returns the prompt_id for polling."""
    payload = {"prompt": workflow_dict, "client_id": CLIENT_ID}
    result = http_post_json(f"{COMFYUI_URL}/prompt", payload)
    if "prompt_id" not in result:
        raise RuntimeError(f"Unexpected /prompt response: {result}")
    return result["prompt_id"]


def wait_for_completion(prompt_id: str, timeout: int = 600) -> dict:
    """Poll /history/<id> until the workflow completes. Returns the history entry."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            history = http_get_json(f"{COMFYUI_URL}/history/{prompt_id}")
            if prompt_id in history:
                entry = history[prompt_id]
                # Check execution status
                status = entry.get("status", {})
                if status.get("status_str") == "error":
                    err_messages = status.get("messages", [])
                    raise RuntimeError(f"Generation errored: {err_messages}")
                # Done = has outputs
                if entry.get("outputs"):
                    return entry
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            pass
        time.sleep(2)
    raise TimeoutError(f"Generation {prompt_id} timed out after {timeout}s")


def download_first_image(history_entry: dict, save_path: Path) -> None:
    """Find the first output image in the history entry, download it, save to save_path."""
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
                   targets: dict) -> dict:
    """Return a deep-copied workflow with positive prompt / seed / steps patched."""
    wf = copy.deepcopy(template)
    pid = targets["positive_prompt_node_id"]
    sid = targets["seed_node_id"]
    stid = targets["steps_node_id"]
    wf[pid]["inputs"]["text"] = positive_prompt
    wf[sid]["inputs"]["noise_seed"] = seed
    wf[stid]["inputs"]["steps"] = steps
    return wf


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=None,
                    help="Run only the first N (prompt, seed, step) combinations. Useful for smoke tests.")
    ap.add_argument("--prompts", default=str(PROMPTS_PATH), help="Path to prompts YAML")
    ap.add_argument("--template", default=str(TEMPLATE_PATH), help="Path to workflow template JSON")
    ap.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Output directory")
    ap.add_argument("--no-skip-existing", action="store_true",
                    help="Re-generate even if output file already exists (default: skip)")
    args = ap.parse_args()

    # Load config
    template_data = json.loads(Path(args.template).read_text())
    template = template_data["workflow"]
    targets = template_data["_template_targets"]
    log.info("Loaded template (%d nodes); targets: %s", len(template), targets)

    config = yaml.safe_load(Path(args.prompts).read_text())
    prefix = config["prompt_prefix"].strip()
    prompts = config["prompts"]
    seeds = config["seeds"]
    step_counts = config["step_counts"]

    # Build the full work list
    work = [
        {
            "prompt_id": p["id"],
            "prompt_name": p["name"],
            "prompt_text": f"{prefix}, {p['text']}",
            "seed": seed,
            "steps": step_count,
        }
        for p in prompts
        for seed in seeds
        for step_count in step_counts
    ]
    if args.limit:
        work = work[: args.limit]

    log.info("Total combinations to run: %d (%d prompts × %d seeds × %d step counts%s)",
             len(work), len(prompts), len(seeds), len(step_counts),
             f" [limited to first {args.limit}]" if args.limit else "")

    # Wait for ComfyUI to be ready
    wait_for_comfyui_api()

    # Run
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    successes = 0
    failures = 0
    skipped = 0
    overall_start = time.time()

    for i, item in enumerate(work, 1):
        out_path = output_dir / f"{item['steps']}steps" / f"p{item['prompt_id']}_{item['prompt_name']}_seed{item['seed']}.png"
        if out_path.exists() and not args.no_skip_existing:
            log.info("[%d/%d] SKIP (exists): %s", i, len(work), out_path.name)
            skipped += 1
            continue

        log.info("[%d/%d] %s | seed=%d steps=%d", i, len(work), item["prompt_name"], item["seed"], item["steps"])
        item_start = time.time()
        try:
            wf = patch_workflow(template, positive_prompt=item["prompt_text"],
                                seed=item["seed"], steps=item["steps"], targets=targets)
            prompt_id = submit_prompt(wf)
            history = wait_for_completion(prompt_id)
            download_first_image(history, out_path)
            elapsed = time.time() - item_start
            log.info("  → %s (%.1fs)", out_path.relative_to(PROJECT_ROOT), elapsed)
            # Sidecar metadata
            (out_path.with_suffix(".json")).write_text(json.dumps({
                "prompt_id": prompt_id,
                "positive_prompt": item["prompt_text"],
                "seed": item["seed"],
                "steps": item["steps"],
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

"""Pipeline manifest writer — full provenance per FSD §4.3."""

from __future__ import annotations

import datetime as dt
import hashlib
import subprocess
from pathlib import Path
from typing import Any

import yaml


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "missing"
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def _git_sha_for_file(path: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "log", "-n", "1", "--pretty=format:%H", "--", str(path)],
            cwd=path.parent,
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip() or "untracked"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def write_manifest(
    *,
    config_path: Path,
    bible_path: Path,
    base_model: str,
    seed: int,
    lora_metadata: dict[str, Any],
    generation_metadata: dict[str, Any],
    post_processing_metadata: dict[str, Any],
    out_path: Path,
) -> None:
    manifest = {
        "character": config_path.stem.replace("_config", ""),
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "seed": seed,
        "bible_commit": _git_sha_for_file(bible_path),
        "config_commit": _git_sha_for_file(config_path),
        "base_model": base_model,
        "lora": lora_metadata,
        "generation": generation_metadata,
        "post_processing": post_processing_metadata,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(manifest, fh, sort_keys=False, allow_unicode=True)


def file_sha(path: Path) -> str:
    return _sha256_file(path)

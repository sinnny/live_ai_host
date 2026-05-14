"""Script schema loader + validator.

The canonical schema is at scripts/test_3/script_schema.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "script_schema.json"


def load_schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def load_script(path: str | Path) -> dict:
    p = Path(path)
    with p.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    validate(data)
    return data


def validate(script: dict) -> None:
    jsonschema.validate(instance=script, schema=load_schema())

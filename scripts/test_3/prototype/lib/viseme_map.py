"""Rhubarb shape-code → our 6-viseme atlas mapping.

Per FSD phoneme_alignment.md §5.3. Unmapped shapes default to `closed`.
"""

from __future__ import annotations

SHAPE_TO_VISEME = {
    "X": "closed",
    "A": "aa",
    "B": "aa",
    "C": "ee",
    "D": "aa",
    "E": "oh",
    "F": "ou",
    "G": "ih",
    "H": "ih",
}


def map_shape(code: str) -> str:
    return SHAPE_TO_VISEME.get(code, "closed")

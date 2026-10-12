"""Offline mock vision client. Filename keywords drive the verdict for demos."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def look(image_path: str | Path, question: str) -> dict[str, Any]:
    """Return a CONTRACT.md AI look result without calling a GPU."""
    name = Path(image_path).name.lower()
    _ = question  # used by real client; fake keys off filename for now

    if "_blur_" in name or "_dark_" in name or "_occluded_" in name:
        return {
            "verdict": "cant_tell",
            "reason": "Image quality too low to judge this check.",
            "problem_box": None,
        }

    if "_bad_" in name or "_fail_" in name or "_open_" in name:
        return {
            "verdict": "no",
            "reason": "Defect visible: check does not pass.",
            "problem_box": [200, 200, 700, 700],
        }

    # Default / *_ok_* / anything else → pass
    return {
        "verdict": "yes",
        "reason": "Check looks OK on this frame.",
        "problem_box": None,
    }

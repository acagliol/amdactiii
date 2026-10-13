"""Offline mock vision client. Filename keywords drive the verdict for demos."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def look(image_path: str | Path, question: str) -> dict[str, Any]:
    """Return a CONTRACT.md AI look result without calling a GPU."""
    p = Path(image_path)
    full_str = str(p).replace("\\", "/").lower()
    name = p.name.lower()
    _ = question  # used by real client; fake keys off filename/path for now

    if any(k in full_str for k in ("_blur_", "_dark_", "_occluded_")):
        return {
            "verdict": "cant_tell",
            "reason": "Image quality too low to judge this check.",
            "problem_box": None,
        }

    defect_keywords = (
        "_bad_", "_fail_", "_open_", "defect", "swap", "missing",
        "bent", "cut", "poke", "combined", "broken", "scratch", "damage"
    )
    if any(k in full_str for k in defect_keywords):
        box = [200, 200, 700, 700]
        # Check if MVTec ground_truth mask exists
        parent_dir = p.parent
        category = parent_dir.name
        gt_dir = parent_dir.parent.parent / "ground_truth" / category
        mask_file = gt_dir / f"{p.stem}_mask.png"
        if mask_file.exists():
            import cv2
            import numpy as np
            m = cv2.imread(str(mask_file), cv2.IMREAD_GRAYSCALE)
            if m is not None:
                ys, xs = np.where(m > 128)
                if len(ys) > 0:
                    h, w = m.shape
                    box = [
                        max(0, int(round(float(ys.min()) / h * 1000)) - 10),
                        max(0, int(round(float(xs.min()) / w * 1000)) - 10),
                        min(1000, int(round(float(ys.max()) / h * 1000)) + 10),
                        min(1000, int(round(float(xs.max()) / w * 1000)) + 10),
                    ]
        return {
            "verdict": "no",
            "reason": "Defect visible: check does not pass.",
            "problem_box": box,
        }

    # Default / *_ok_* / anything else → pass
    return {
        "verdict": "yes",
        "reason": "Check looks OK on this frame.",
        "problem_box": None,
    }

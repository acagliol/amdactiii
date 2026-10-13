"""OpenCV photo quality gate — blur / dark / tiny frames → retake hints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np

# Tuned for real photos and workstation shots (blurs typically < 5, real photos > 15).
MIN_LAPLACIAN_VAR = 12.0
MIN_MEAN_BRIGHTNESS = 40.0
MAX_MEAN_BRIGHTNESS = 230.0
MIN_SIDE_PX = 200


def assess_quality(image_path: str | Path) -> dict[str, Any]:
    """Return whether the frame is good enough to send to the vision model.

    Shape:
      ok: bool
      hint: str | None
      metrics: {laplacian_var, mean_brightness, width, height}
    """
    path = Path(image_path)
    image = cv2.imread(str(path))
    if image is None:
        return {
            "ok": False,
            "hint": "Could not read that image. Try JPG/PNG and upload again.",
            "metrics": {},
        }

    height, width = image.shape[:2]
    if min(height, width) < MIN_SIDE_PX:
        return {
            "ok": False,
            "hint": "Move closer or use a higher-resolution photo.",
            "metrics": {
                "laplacian_var": 0.0,
                "mean_brightness": 0.0,
                "width": width,
                "height": height,
            },
        }

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    mean_brightness = float(np.mean(gray))
    metrics = {
        "laplacian_var": round(lap_var, 2),
        "mean_brightness": round(mean_brightness, 2),
        "width": width,
        "height": height,
    }

    if lap_var < MIN_LAPLACIAN_VAR:
        return {
            "ok": False,
            "hint": "Too blurry — hold steady, wait for focus, then retake.",
            "metrics": metrics,
        }
    if mean_brightness < MIN_MEAN_BRIGHTNESS:
        return {
            "ok": False,
            "hint": "Too dark — add light on the workstation, then retake.",
            "metrics": metrics,
        }
    if mean_brightness > MAX_MEAN_BRIGHTNESS:
        return {
            "ok": False,
            "hint": "Too bright / glare — tilt away from the light, then retake.",
            "metrics": metrics,
        }

    return {"ok": True, "hint": None, "metrics": metrics}

"""Double-look agreement (CONTRACT.md). Reduces one-shot hallucinations."""

from __future__ import annotations

from typing import Any


def box_iou(box_a: list[ float | int ], box_b: list[ float | int ]) -> float:
    """Return Intersection-over-Union in [0.0, 1.0] for two [ymin, xmin, ymax, xmax] boxes."""
    ay1, ax1, ay2, ax2 = box_a
    by1, bx1, by2, bx2 = box_b
    inter_h = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter_w = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    inter = inter_h * inter_w
    if inter <= 0.0:
        return 0.0
    area_a = max(0.0, ay2 - ay1) * max(0.0, ax2 - ax1)
    area_b = max(0.0, by2 - by1) * max(0.0, bx2 - bx1)
    union = area_a + area_b - inter
    return inter / union if union > 0.0 else 0.0


def _merge_boxes(
    box_a: list[float | int] | None, box_b: list[float | int] | None
) -> list[float | int] | None:
    if box_a is None:
        return box_b
    if box_b is None:
        return box_a
    if box_iou(box_a, box_b) <= 0.0:
        return box_a
    merged: list[float | int] = []
    for a, b in zip(box_a, box_b):
        avg = round((float(a) + float(b)) / 2.0, 1)
        merged.append(int(avg) if avg.is_integer() else avg)
    return merged


def reconcile(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    """Combine two CONTRACT look results into one.

    yes+yes → yes
    no+no → no (consensus problem_box when overlapping, else first usable box)
    anything else → cant_tell (retake)
    """
    a = first.get("verdict")
    b = second.get("verdict")

    if a == "yes" and b == "yes":
        return {
            "verdict": "yes",
            "reason": first.get("reason") or second.get("reason") or "Confirmed on two looks.",
            "problem_box": None,
        }

    if a == "no" and b == "no":
        box = _merge_boxes(first.get("problem_box"), second.get("problem_box"))
        reason_a = (first.get("reason") or "").strip()
        reason_b = (second.get("reason") or "").strip()
        reason = reason_a
        if reason_b and reason_b.lower() not in reason_a.lower():
            reason = f"{reason_a} | also: {reason_b}".strip(" |")
        return {
            "verdict": "no",
            "reason": reason or "Defect confirmed on two looks.",
            "problem_box": box,
        }

    return {
        "verdict": "cant_tell",
        "reason": (
            f"Looks disagreed or uncertain ({a!r} vs {b!r}); retake the photo. "
            f"A: {first.get('reason', '')} B: {second.get('reason', '')}"
        ).strip(),
        "problem_box": None,
    }

"""Double-look agreement (CONTRACT.md). Reduces one-shot hallucinations."""

from __future__ import annotations

from typing import Any


def reconcile(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    """Combine two CONTRACT look results into one.

    yes+yes → yes
    no+no → no (keep first usable problem_box)
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
        box = first.get("problem_box")
        if box is None:
            box = second.get("problem_box")
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

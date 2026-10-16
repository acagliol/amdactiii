"""Turn "what correct looks like" lines typed by a user into a normal checklist file.

A custom checklist goes through exactly the same rules as the ready-made ones:
it is written as YAML, validated by the team's linter (checker/lint.py), and run by Session.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from checker.lint import lint_data

MAX_CHECKS = 6  # each check is one AI request; keep a unit well under the team's rate limit
MIN_LINE_LENGTH = 3
MAX_LINE_LENGTH = 160
MAX_NAME_LENGTH = 60
MAX_COVER_STEP_LENGTH = 80
CAMERA_HINT = "Point the camera at it, whole object in frame, good light."


class CustomChecklistError(ValueError):
    """The user's checklist can't be used; the message is safe to show to them."""


def build_custom_assembly(name: str, lines: list[str], cover_step: str | None) -> dict[str, Any]:
    """One visual check per line, plus an optional last step that stays locked until all of them pass."""
    checks = [line.strip() for line in lines if line.strip()]
    if not checks:
        raise CustomChecklistError("Write at least one check, one per line.")
    if len(checks) > MAX_CHECKS:
        raise CustomChecklistError(f"Use at most {MAX_CHECKS} checks.")
    for line in checks:
        if not MIN_LINE_LENGTH <= len(line) <= MAX_LINE_LENGTH:
            raise CustomChecklistError(f"Each check must be {MIN_LINE_LENGTH}–{MAX_LINE_LENGTH} characters.")

    used_ids: set[str] = set()
    steps: list[dict[str, Any]] = []
    for line in checks:
        check_id = unique_id(slugify(line), used_ids)
        steps.append({
            "id": f"step_{check_id}",
            "instruction": line,
            "checks": [{"id": check_id, "type": "visual", "question": as_question(line), "show": CAMERA_HINT}],
        })

    cover_step = (cover_step or "").strip()
    if cover_step:
        if len(cover_step) > MAX_COVER_STEP_LENGTH:
            raise CustomChecklistError(f"The last step must be at most {MAX_COVER_STEP_LENGTH} characters.")
        steps.append({
            "id": unique_id(slugify(cover_step), used_ids),  # shown as "Close the case lid" in the step list
            "instruction": cover_step,
            "hides": True,
            "requires": [step["checks"][0]["id"] for step in steps],
        })

    name = (name or "").strip()[:MAX_NAME_LENGTH] or "Custom check"
    return {"assembly": name, "steps": steps}


def save_custom_assembly(assembly: dict[str, Any], folder: Path) -> Path:
    """Validate with the team's linter, then write it where Session can load it."""
    errors = lint_data(assembly)
    if errors:
        raise CustomChecklistError("This checklist isn't valid: " + "; ".join(errors))
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"custom_{uuid4().hex[:12]}.yaml"
    path.write_text(yaml.safe_dump(assembly, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def as_question(line: str) -> str:
    """Questions that describe the correct state work best (our cable test: a vague question missed a swap)."""
    line = line.strip()
    if line.endswith("?"):
        return line
    return f"Correct state: {line.rstrip('.')}. Does the photo clearly show exactly that?"


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:48].rstrip("_") or "check"


def unique_id(base: str, used: set[str]) -> str:
    candidate, number = base, 2
    while candidate in used:
        candidate = f"{base}_{number}"
        number += 1
    used.add(candidate)
    return candidate

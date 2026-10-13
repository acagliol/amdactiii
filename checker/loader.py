"""Load assembly checklists from YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

CHECK_TYPES = ("visual", "manual")


def load_assembly(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or "steps" not in data:
        raise ValueError(f"Invalid assembly file (missing steps): {path}")
    return data


def iter_visual_checks(assembly: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten visual checks with parent step metadata (legacy helper)."""
    return [c for c in iter_checks(assembly) if c["kind"] == "visual"]


def iter_checks(assembly: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten every step into ordered check entries.

    kind:
      visual - camera + AI look
      manual - worker/supervisor confirms by hand (no AI)
      gate   - step with no checks of its own (e.g. close panel); only
               unlocks once everything in `requires` has passed.
    `hides: true` marks a step that covers earlier work. It defaults to true
    for a gate step that has `requires`.
    """
    out: list[dict[str, Any]] = []
    known: set[str] = set()
    for step in assembly.get("steps", []):
        requires = list(step.get("requires", []) or [])
        unknown = [r for r in requires if r not in known]
        if unknown:
            raise ValueError(
                f"Step '{step['id']}' requires unknown or later check ids: {unknown}"
            )
        checks = step.get("checks", []) or []
        hides = bool(step.get("hides", bool(requires) and not checks))
        base = {
            "step_id": step["id"],
            "instruction": step.get("instruction", ""),
            "requires": requires,
            "hides": hides,
        }
        for check in checks:
            kind = check.get("type", "visual")
            if kind not in CHECK_TYPES:
                raise ValueError(f"Check '{check.get('id')}' has unknown type '{kind}'")
            out.append(
                {
                    **base,
                    "kind": kind,
                    "check_id": check["id"],
                    "question": check["question"],
                    "show": check.get("show", ""),
                    "reference_photo": check.get("reference_photo", ""),
                }
            )
            known.add(check["id"])
        if not checks:
            out.append(
                {
                    **base,
                    "kind": "gate",
                    "check_id": step["id"],
                    "question": step.get("instruction", ""),
                    "show": "",
                    "reference_photo": "",
                }
            )
            known.add(step["id"])
    return out

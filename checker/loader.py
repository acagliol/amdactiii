"""Load assembly checklists from YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_assembly(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or "steps" not in data:
        raise ValueError(f"Invalid assembly file (missing steps): {path}")
    return data


def iter_visual_checks(assembly: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten visual checks with parent step metadata."""
    out: list[dict[str, Any]] = []
    for step in assembly.get("steps", []):
        for check in step.get("checks", []):
            if check.get("type", "visual") != "visual":
                continue
            out.append(
                {
                    "step_id": step["id"],
                    "check_id": check["id"],
                    "instruction": step.get("instruction", ""),
                    "question": check["question"],
                    "show": check.get("show", ""),
                    "requires": step.get("requires", []),
                }
            )
    return out

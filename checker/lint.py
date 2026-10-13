"""Lint assembly checklist YAML before it reaches a worker.

Usage (from repo root):
  python -m checker.lint                 # all assemblies/**/*.yaml
  python -m checker.lint path/to/x.yaml
Exit code 1 if any file has errors.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .loader import CHECK_TYPES, iter_checks, load_assembly

ROOT = Path(__file__).resolve().parents[1]


def lint_data(data: Any, *, root: Path = ROOT) -> list[str]:
    """Return human-readable problems; empty list means the checklist is OK."""
    errors: list[str] = []
    if not isinstance(data, dict) or not data.get("steps"):
        return ["file has no steps"]
    if not str(data.get("assembly", "")).strip():
        errors.append("missing 'assembly' name")

    seen: set[str] = set()
    for i, step in enumerate(data["steps"]):
        sid = step.get("id")
        where = f"step {i + 1} ({sid or 'no id'})"
        if not sid:
            errors.append(f"{where}: missing id")
        elif sid in seen:
            errors.append(f"{where}: duplicate id '{sid}'")
        seen.add(sid)
        if not str(step.get("instruction", "")).strip():
            errors.append(f"{where}: missing instruction")
        checks = step.get("checks") or []
        if step.get("hides") and not step.get("requires"):
            errors.append(f"{where}: hides earlier work but has no 'requires'")
        if not checks and not step.get("requires"):
            errors.append(f"{where}: no checks and no 'requires' - nothing to verify")
        for check in checks:
            cid = check.get("id")
            cwhere = f"{where} check '{cid or 'no id'}'"
            if not cid:
                errors.append(f"{cwhere}: missing id")
            elif cid in seen:
                errors.append(f"{cwhere}: duplicate id '{cid}'")
            seen.add(cid)
            kind = check.get("type", "visual")
            if kind not in CHECK_TYPES:
                errors.append(f"{cwhere}: unknown type '{kind}' (use {', '.join(CHECK_TYPES)})")
            question = str(check.get("question", "")).strip()
            if not question:
                errors.append(f"{cwhere}: missing question")
            elif "?" not in question:
                errors.append(f"{cwhere}: question should be a yes/no question ending in '?'")
            ref = check.get("reference_photo")
            if ref and not (root / ref).exists():
                errors.append(f"{cwhere}: reference_photo not found: {ref}")

    try:
        iter_checks(data)
    except (ValueError, KeyError) as exc:
        errors.append(str(exc))
    return errors


def lint_file(path: str | Path) -> list[str]:
    try:
        data = load_assembly(path)
    except Exception as exc:  # bad YAML or missing steps
        return [str(exc)]
    return lint_data(data)


def main(argv: list[str]) -> int:
    paths = [Path(p) for p in argv] or sorted((ROOT / "assemblies").rglob("*.yaml"))
    bad = 0
    for p in paths:
        errors = lint_file(p)
        if errors:
            bad += 1
            print(f"FAIL {p}")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"OK   {p}")
    print(f"\n{len(paths) - bad}/{len(paths)} checklists OK")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

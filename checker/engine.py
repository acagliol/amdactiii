"""Step session + single-look check → UI action (CONTRACT.md)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_client import look as ai_look

from .loader import iter_visual_checks, load_assembly
from .quality import assess_quality


def verdict_to_action(verdict: str) -> str:
    if verdict == "yes":
        return "pass"
    if verdict == "no":
        return "fix"
    return "retake"


class Session:
    """Tracks passed checks, retakes, and gated steps for one unit."""

    def __init__(self, assembly_path: str | Path):
        self.assembly = load_assembly(assembly_path)
        self.checks = iter_visual_checks(self.assembly)
        self.passed: set[str] = set()
        self.retake_streak = 0
        self.index = 0
        self.overrides: list[dict[str, str]] = []

    def current(self) -> dict[str, Any] | None:
        if self.index >= len(self.checks):
            return None
        return self.checks[self.index]

    def progress(self) -> tuple[int, int]:
        return self.index, len(self.checks)

    def gate_blocked(self, check: dict[str, Any]) -> list[str]:
        missing = [r for r in check.get("requires", []) if r not in self.passed]
        return missing

    def advance_if_pass(self, check_id: str) -> None:
        self.passed.add(check_id)
        self.retake_streak = 0
        self.index += 1

    def override_pass(self, reason: str) -> dict[str, Any]:
        """Supervisor/worker override — advance with written justification."""
        check = self.current()
        if check is None:
            return {
                "action": "pass",
                "reason": "All checks complete.",
                "problem_box": None,
                "hint": None,
                "step_id": "",
                "check_id": "",
            }
        reason = (reason or "").strip()
        if len(reason) < 8:
            return {
                "action": "retake",
                "reason": "Override needs a short written reason (min 8 chars).",
                "problem_box": None,
                "hint": "Explain why this check is skipped or accepted.",
                "step_id": check["step_id"],
                "check_id": check["check_id"],
            }
        self.overrides.append(
            {
                "check_id": check["check_id"],
                "reason": reason,
            }
        )
        self.advance_if_pass(check["check_id"])
        return {
            "action": "pass",
            "reason": f"Override accepted: {reason}",
            "problem_box": None,
            "hint": None,
            "step_id": check["step_id"],
            "check_id": check["check_id"],
        }


def _bump_retake(session: Session, check: dict[str, Any], reason: str, hint: str) -> dict[str, Any]:
    session.retake_streak += 1
    action = "supervisor" if session.retake_streak >= 3 else "retake"
    return {
        "action": action,
        "reason": reason,
        "problem_box": None,
        "hint": hint,
        "step_id": check["step_id"],
        "check_id": check["check_id"],
    }


def run_check(
    session: Session,
    image_path: str | Path,
    *,
    check: dict[str, Any] | None = None,
    skip_quality: bool = False,
) -> dict[str, Any]:
    """Run quality gate + one visual check; update session on pass / retake streak."""
    check = check or session.current()
    if check is None:
        return {
            "action": "pass",
            "reason": "All checks complete.",
            "problem_box": None,
            "hint": None,
            "step_id": "",
            "check_id": "",
        }

    missing = session.gate_blocked(check)
    if missing:
        return {
            "action": "retake",
            "reason": f"Blocked until these pass: {', '.join(missing)}",
            "problem_box": None,
            "hint": "Finish required checks before this step.",
            "step_id": check["step_id"],
            "check_id": check["check_id"],
        }

    if not skip_quality:
        quality = assess_quality(image_path)
        if not quality["ok"]:
            return _bump_retake(
                session,
                check,
                reason="Photo quality gate failed.",
                hint=quality.get("hint") or "Retake the photo.",
            )

    look = ai_look(image_path, check["question"])
    action = verdict_to_action(look["verdict"])

    if action == "pass":
        session.advance_if_pass(check["check_id"])
        hint = None
    elif action == "fix":
        session.retake_streak = 0
        hint = check.get("show") or "Fix the highlighted issue, then check again."
    else:
        session.retake_streak += 1
        hint = check.get("show") or "Reframe: closer, steadier, more light."
        if session.retake_streak >= 3:
            action = "supervisor"

    return {
        "action": action,
        "reason": look.get("reason", ""),
        "problem_box": look.get("problem_box"),
        "hint": hint,
        "step_id": check["step_id"],
        "check_id": check["check_id"],
    }

"""Step session + single-look check → UI action (CONTRACT.md)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from ai_client import look as ai_look

from .evidence import EvidenceLog
from .loader import iter_visual_checks, load_assembly


def verdict_to_action(verdict: str) -> str:
    if verdict == "yes":
        return "pass"
    if verdict == "no":
        return "fix"
    return "retake"


class Session:
    """Tracks passed checks, retakes, and gated steps for one unit."""

    def __init__(
        self,
        assembly_path: str | Path,
        *,
        unit_id: str | None = None,
        evidence_log: EvidenceLog | None = None,
    ):
        self.assembly = load_assembly(assembly_path)
        self.checks = iter_visual_checks(self.assembly)
        self.unit_id = unit_id or uuid4().hex
        self.evidence_log = evidence_log if evidence_log is not None else EvidenceLog()
        self.last_evidence_path: Path | None = None
        self.passed: set[str] = set()
        self.retake_streak = 0
        self.index = 0

    def current(self) -> dict[str, Any] | None:
        if self.index >= len(self.checks):
            return None
        return self.checks[self.index]

    def gate_blocked(self, check: dict[str, Any]) -> list[str]:
        missing = [r for r in check.get("requires", []) if r not in self.passed]
        return missing

    def advance_if_pass(self, check_id: str) -> None:
        self.passed.add(check_id)
        self.retake_streak = 0
        self.index += 1

    def _save_evidence(
        self, image_path: str | Path, result: dict[str, Any], verdict: str | None
    ) -> None:
        self.last_evidence_path = self.evidence_log.save(
            image_path,
            unit_id=self.unit_id,
            assembly=self.assembly["assembly"],
            verdict=verdict,
            result=result,
        )


def run_check(
    session: Session,
    image_path: str | Path,
    *,
    check: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run and log one check, then update the session only after storage succeeds."""
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
        result = {
            "action": "retake",
            "reason": f"Blocked until these pass: {', '.join(missing)}",
            "problem_box": None,
            "hint": "Finish required checks before this step.",
            "step_id": check["step_id"],
            "check_id": check["check_id"],
        }
        session._save_evidence(image_path, result, verdict=None)
        return result

    look = ai_look(image_path, check["question"])
    action = verdict_to_action(look["verdict"])

    if action == "pass":
        hint = None
    elif action == "fix":
        hint = check.get("show") or "Fix the highlighted issue, then check again."
    else:
        hint = check.get("show") or "Reframe: closer, steadier, more light."
        if session.retake_streak + 1 >= 3:
            action = "supervisor"

    result = {
        "action": action,
        "reason": look.get("reason", ""),
        "problem_box": look.get("problem_box"),
        "hint": hint,
        "step_id": check["step_id"],
        "check_id": check["check_id"],
    }
    session._save_evidence(image_path, result, verdict=look["verdict"])
    if action == "pass":
        session.advance_if_pass(check["check_id"])
    elif action == "fix":
        session.retake_streak = 0
    else:
        session.retake_streak += 1
    return result

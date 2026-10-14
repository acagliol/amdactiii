"""Step session + single-look check → UI action (CONTRACT.md)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from ai_client import look as ai_look

from .evidence import EvidenceLog
from .loader import iter_checks, load_assembly
from .quality import assess_quality


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
        self.checks = iter_checks(self.assembly)
        self.unit_id = unit_id or uuid4().hex
        self.evidence_log = evidence_log if evidence_log is not None else EvidenceLog()
        self.last_evidence_path: Path | None = None
        self.passed: set[str] = set()
        self.retake_streak = 0
        self.index = 0
        self.overrides: list[dict[str, str]] = []
        self.manual_log: list[dict[str, Any]] = []

    def current(self) -> dict[str, Any] | None:
        if self.index >= len(self.checks):
            return None
        return self.checks[self.index]

    def progress(self) -> tuple[int, int]:
        return self.index, len(self.checks)

    def gate_blocked(self, check: dict[str, Any]) -> list[str]:
        missing = [r for r in check.get("requires", []) if r not in self.passed]
        return missing

    def gate_status(self, check: dict[str, Any] | None = None) -> dict[str, Any]:
        """For the UI: is this (hiding) step locked, and by what?"""
        check = check or self.current()
        if check is None:
            return {"blocked": False, "missing": [], "hides": False}
        missing = self.gate_blocked(check)
        return {"blocked": bool(missing), "missing": missing, "hides": check.get("hides", False)}

    def confirm_manual(
        self, ok: bool, note: str = "", image_path: str | Path | None = None
    ) -> dict[str, Any]:
        """Record a by-hand check. ok=True passes; ok=False means fix (note required)."""
        check = self.current()
        if check is None:
            return _done_result()
        if check.get("kind") != "manual":
            return _result(
                "retake", check, "Current step is not a manual check.",
                hint="Use the camera check for this step.",
            )
        missing = self.gate_blocked(check)
        if missing:
            return _result("retake", check, _blocked_reason(missing), hint=_blocked_hint(check))
        note = (note or "").strip()
        if not ok and len(note) < 3:
            return _result(
                "retake", check, "Say what is wrong before marking a manual check failed.",
                hint="Add a short note.",
            )
        action = "pass" if ok else "fix"
        reason = f"Manual check {'confirmed' if ok else 'failed'}" + (f": {note}" if note else ".")
        result = _result(action, check, reason, hint=None if ok else check.get("show") or None)
        self.manual_log.append({"check_id": check["check_id"], "ok": ok, "note": note})
        if image_path is not None:
            self._save_evidence(image_path, result, verdict="yes" if ok else "no")
        if ok:
            self.advance_if_pass(check["check_id"])
        else:
            self.retake_streak = 0
        return result

    def summary(self) -> dict[str, Any]:
        """Plain snapshot of this unit's progress (read-only, for any UI)."""
        current = self.current()
        done, total = self.progress()
        return {
            "unit_id": self.unit_id,
            "assembly": self.assembly["assembly"],
            "done": done,
            "total": total,
            "complete": current is None,
            "current_check_id": current["check_id"] if current else None,
            "current_kind": current.get("kind") if current else None,
            "passed": sorted(self.passed),
            "retake_streak": self.retake_streak,
            "overrides": list(self.overrides),
            "manual_log": list(self.manual_log),
            "gate": self.gate_status(current),
        }

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

    def override_pass(self, reason: str) -> dict[str, Any]:
        """Supervisor/worker override — advance with written justification."""
        check = self.current()
        if check is None:
            return _done_result()
        reason = (reason or "").strip()
        if len(reason) < 8:
            return _result(
                "retake", check, "Override needs a short written reason (min 8 chars).",
                hint="Explain why this check is skipped or accepted.",
            )
        self.overrides.append({"check_id": check["check_id"], "reason": reason})
        self.advance_if_pass(check["check_id"])
        return _result("pass", check, f"Override accepted: {reason}")


def _result(
    action: str, check: dict[str, Any], reason: str, *, hint: str | None = None, box=None
) -> dict[str, Any]:
    return {
        "action": action,
        "reason": reason,
        "problem_box": box,
        "hint": hint,
        "step_id": check["step_id"],
        "check_id": check["check_id"],
    }


def _done_result() -> dict[str, Any]:
    return {
        "action": "pass",
        "reason": "All checks complete.",
        "problem_box": None,
        "hint": None,
        "step_id": "",
        "check_id": "",
    }


def _blocked_reason(missing: list[str]) -> str:
    return f"Blocked until these pass: {', '.join(missing)}"


def _blocked_hint(check: dict[str, Any]) -> str:
    if check.get("hides"):
        return "Do not do this step yet: it hides earlier work. Finish the required checks first."
    return "Finish required checks before this step."


def _bump_retake(
    session: Session, check: dict[str, Any], image_path: str | Path, reason: str, hint: str
) -> dict[str, Any]:
    action = "supervisor" if session.retake_streak + 1 >= 3 else "retake"
    result = _result(action, check, reason, hint=hint)
    session._save_evidence(image_path, result, verdict=None)
    session.retake_streak += 1
    return result


def run_check(
    session: Session,
    image_path: str | Path,
    *,
    check: dict[str, Any] | None = None,
    skip_quality: bool = False,
) -> dict[str, Any]:
    """Run quality gate and AI, log the attempt, then update session state."""
    check = check or session.current()
    if check is None:
        return _done_result()

    missing = session.gate_blocked(check)
    if missing:
        result = _result("retake", check, _blocked_reason(missing), hint=_blocked_hint(check))
        session._save_evidence(image_path, result, verdict=None)
        return result

    if check.get("kind") == "gate":
        result = _result(
            "pass", check,
            f"Prerequisites verified ({', '.join(check['requires']) or 'none'}). Step unlocked.",
        )
        session._save_evidence(image_path, result, verdict=None)
        session.advance_if_pass(check["check_id"])
        return result

    if check.get("kind") == "manual":
        return _result(
            "retake", check, "Manual check: confirm by hand, not by camera.",
            hint=check["question"],
        )

    if not skip_quality:
        quality = assess_quality(image_path)
        if not quality["ok"]:
            return _bump_retake(
                session,
                check,
                image_path,
                reason="Photo quality gate failed.",
                hint=quality.get("hint") or "Retake the photo.",
            )

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

    result = _result(action, check, look.get("reason", ""), hint=hint, box=look.get("problem_box"))
    session._save_evidence(image_path, result, verdict=look["verdict"])
    if action == "pass":
        session.advance_if_pass(check["check_id"])
    elif action == "fix":
        session.retake_streak = 0
    else:
        session.retake_streak += 1
    return result

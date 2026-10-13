"""Hiding-step gate, manual checks, and checklist YAML validity."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

os.environ["USE_FAKE_AI"] = "true"

from checker import Session, run_check  # noqa: E402
from checker.evidence import EvidenceLog  # noqa: E402
from checker.loader import iter_checks, load_assembly  # noqa: E402

from ._images import write_sharp  # noqa: E402

ASSEMBLY = ROOT / "assemblies" / "pc_build.yaml"


def _session(tmp: Path) -> Session:
    return Session(ASSEMBLY, evidence_log=EvidenceLog(tmp / "evidence"))


def test_hiding_step_blocked_then_unlocked() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="multilond_gate_"))
    s = _session(tmp)
    gate = s.checks[-1]
    assert gate["kind"] == "gate" and gate["hides"] and gate["check_id"] == "close_panel"

    r = run_check(s, write_sharp("panel_01.jpg", tmp), check=gate)
    assert r["action"] == "retake"
    assert "Blocked until" in r["reason"]
    assert "hides earlier work" in r["hint"]
    assert "close_panel" not in s.passed
    assert s.gate_status(gate)["blocked"]

    for _ in range(len(s.checks) - 1):
        s.override_pass("verified by hand for gate test")
    assert s.current()["check_id"] == "close_panel"
    assert not s.gate_status()["blocked"]
    r = run_check(s, write_sharp("panel_02.jpg", tmp))
    assert r["action"] == "pass"
    assert s.current() is None
    print("OK  test_step_checker.hiding_gate")


def test_manual_check() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="multilond_manual_"))
    s = _session(tmp)
    while s.current()["kind"] != "manual":
        s.override_pass("skip to manual for test")
    r = run_check(s, write_sharp("fan_01.jpg", tmp))
    assert r["action"] == "retake"  # camera cannot answer a manual check

    assert s.confirm_manual(False)["action"] == "retake"  # failing needs a note
    r = s.confirm_manual(False, "fan cable loose")
    assert r["action"] == "fix"
    assert s.current()["check_id"] == "fan_header_connected"

    r = s.confirm_manual(True, image_path=write_sharp("fan_02.jpg", tmp))
    assert r["action"] == "pass"
    assert "fan_header_connected" in s.passed
    assert s.last_evidence_path is not None and s.last_evidence_path.exists()
    print("OK  test_step_checker.manual")


def test_all_checklists_valid() -> None:
    paths = [ASSEMBLY, *sorted((ROOT / "assemblies" / "mvtec").glob("*.yaml"))]
    assert len(paths) == 16, len(paths)
    for p in paths:
        entries = iter_checks(load_assembly(p))
        assert entries and entries[-1]["kind"] == "gate", p
    print("OK  test_step_checker.checklists")


def test_unknown_requires_rejected() -> None:
    bad = {"assembly": "x", "steps": [{"id": "a", "requires": ["nope"]}]}
    try:
        iter_checks(bad)
    except ValueError:
        print("OK  test_step_checker.unknown_requires")
        return
    raise AssertionError("unknown requires should raise")
